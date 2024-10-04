# pyright: basic


from database import TimeSeriesDB
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.websockets import WebSocket
from model.car import Car
from tinyflux import Point, TagQuery


class WebsocketClientManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)


app = FastAPI()
ts_database = TimeSeriesDB("../database.db")


@app.put("/cars/{car_id}", response_model=Car)
async def update_car(car_id: str, car: Car):
    ts_database.insert(car_id, car)

    return car


@app.get("/car/{car_id}", response_model=list[Car])
def read_car(car_id: str, count: int = 10):
    return ts_database.get_car(car_id, count)


@app.get("/cars/today", response_model=dict[str, list[Car]])
def read_car_today(count: int = 10):
    return ts_database.get_cars_today(count)


@app.delete("/cars/{car_id}")
def delete_car(car_id: str):
    Tag = TagQuery()
    query = Tag.id == car_id

    deleted_points = ts_database.remove(query)
    return {
        "message": "Car deleted",
        "deleted_points": deleted_points,
    }


websocket_manager = WebsocketClientManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            car = Car(**data)
            point = Point(
                tags={
                    "id": data["id"],
                },
                fields={
                    "latitude": car.latitude,
                    "longitude": car.longitude,
                    "status": car.status,
                    "battery": car.battery,
                    "at_home": car.at_home,
                },
            )
            ts_database.insert(point)

            await websocket_manager.broadcast(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

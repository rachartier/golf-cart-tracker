# pyright: basic

from datetime import datetime, timezone

from fastapi import FastAPI, WebSocketDisconnect
from fastapi.websockets import WebSocket
from pydantic import BaseModel
from tinyflux import Point, TagQuery, TimeQuery, TinyFlux


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


class CarInfo(BaseModel):
    latitude: float
    longitude: float
    status: int
    battery: int


app = FastAPI()
db = TinyFlux("cars.db")


def get_car_from_db(car_id: str, count: int = 10) -> list[CarInfo]:
    Tag = TagQuery()
    query = Tag.id == car_id

    results = db.search(query)[-count:]
    print(len(results))

    # convert results to json
    results_list = [CarInfo(**result.fields) for result in results]

    return results_list


def get_car_from_today(count_by_car: int) -> dict[str, list[CarInfo]]:
    Tag = TagQuery()

    results = db.search(
        TimeQuery()
        > datetime.now()
        .replace(minute=0, second=0, microsecond=0)
        .astimezone(timezone.utc),
        sorted=True,
    )

    grouped_results = {}
    wanted_results = results

    wanted_results = sorted(wanted_results, key=lambda x: x.time, reverse=True)
    for result in wanted_results:
        if result.tags["id"] not in grouped_results:
            grouped_results[result.tags["id"]] = []

        if len(grouped_results[result.tags["id"]]) < count_by_car:
            grouped_results[result.tags["id"]].append(CarInfo(**result.fields))

    return grouped_results


@app.put("/cars/{car_id}", response_model=CarInfo)
async def update_car(car_id: str, car: CarInfo):
    point = Point(
        tags={
            "id": car_id,
        },
        fields={
            "latitude": car.latitude,
            "longitude": car.longitude,
            "status": car.status,
            "battery": car.battery,
        },
    )

    db.insert(point)
    return car


@app.get("/car/{car_id}", response_model=list[CarInfo])
def read_car(car_id: str, count: int = 10):
    return get_car_from_db(car_id, count)


@app.get("/cars/today", response_model=dict[str, list[CarInfo]])
def read_car_today(count: int = 10):
    return get_car_from_today(count)


websocket_manager = WebsocketClientManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            car = CarInfo(**data)
            point = Point(
                tags={
                    "id": data["id"],
                },
                fields={
                    "latitude": car.latitude,
                    "longitude": car.longitude,
                    "status": car.status,
                    "battery": car.battery,
                },
            )
            db.insert(point)

            await websocket_manager.broadcast(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

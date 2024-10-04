# pyright: basic


from fastapi import FastAPI, WebSocketDisconnect
from fastapi.websockets import WebSocket
from tinyflux import Point, TagQuery

from database import TimeSeriesDB
from model.cart import Cart


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


@app.put("/carts/{cart_id}", response_model=Cart)
async def update_cart(cart_id: str, cart: Cart):
    ts_database.insert(cart_id, cart)

    return cart


@app.get("/cart/{cart_id}", response_model=list[Cart])
def read_cart(cart_id: str, count: int = 10):
    return ts_database.get_cart(cart_id, count)


@app.get("/carts/today", response_model=dict[str, list[Cart]])
def read_cart_today(count: int = 10):
    return ts_database.get_carts_today(count)


@app.delete("/carts/{cart_id}")
def delete_cart(cart_id: str):
    Tag = TagQuery()
    query = Tag.id == cart_id

    deleted_points = ts_database.remove(query)
    return {
        "message": "cart deleted",
        "deleted_points": deleted_points,
    }


websocket_manager = WebsocketClientManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            cart = Cart(**data)
            point = Point(
                tags={
                    "id": data["id"],
                },
                fields={
                    "latitude": cart.latitude,
                    "longitude": cart.longitude,
                    "status": cart.status,
                    "battery": cart.battery,
                    "at_home": cart.at_home,
                },
            )
            ts_database.insert(point)

            await websocket_manager.broadcast(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

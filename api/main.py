# pyright: basic


import asyncio

from database import TimeSeriesDB
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.websockets import WebSocket
from model.cart import Cart
from tinyflux import TagQuery

lock = asyncio.Lock()


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
ts_database = TimeSeriesDB("./database.db")


@app.put("/carts/{cart_id}", response_model=Cart)
async def update_cart(cart_id: str, cart: Cart):
    async with lock:
        ts_database.insert(cart_id, cart)

    return cart


@app.get("/cart/{cart_id}", response_model=list[Cart])
async def read_cart(cart_id: str, count: int = 10):
    return ts_database.get_cart(cart_id, count)


@app.get("/carts/today", response_model=dict[str, list[Cart]])
async def read_cart_today(count_by_car: int = 10):
    return ts_database.get_carts_today(count_by_car)


@app.delete("/carts/{cart_id}")
async def delete_cart(cart_id: str):
    Tag = TagQuery()
    query = Tag.id == cart_id

    async with lock:
        deleted_points = ts_database.remove(query)

    return {
        "message": "cart deleted",
        "deleted_points": deleted_points,
    }


@app.delete("/carts")
async def delete_all_carts():
    async with lock:
        ts_database.remove_all()

    return {
        "message": "all carts deleted",
    }


websocket_manager = WebsocketClientManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            cart = Cart(**data)
            ts_database.insert(data["id"], cart)

            await websocket_manager.broadcast(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

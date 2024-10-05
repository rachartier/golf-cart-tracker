from pydantic import BaseModel


class Cart(BaseModel):
    latitude: float
    longitude: float
    status: int
    battery: float
    at_home: int = 0

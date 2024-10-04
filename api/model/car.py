from pydantic import BaseModel


class Car(BaseModel):
    latitude: float
    longitude: float
    status: int
    battery: int
    at_home: int = 0

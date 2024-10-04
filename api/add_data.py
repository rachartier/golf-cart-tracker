import random
import threading
import time

import requests
import websocket

ws = websocket.create_connection("ws://localhost:8000/ws")

d_lat = 45.75336519902591
d_lon = 3.0314909254483497


def send_data(car_id):
    global d_lat, d_lon
    while True:
        d_lat += random.uniform(-0.0003, 0.0003)
        d_lon += random.uniform(-0.0003, 0.0003)

        data = {
            "id": car_id,
            "latitude": f"{d_lat}",
            "longitude": f"{d_lon}",
            "battery": 80,
            "status": 1,
            "at_home": 0,
        }

        print("Sending data: ", data)

        requests.put(f"http://localhost:8000/cars/{car_id}", json=data)

        time.sleep(random.randint(1, 5))


# Nombre de threads que vous souhaitez créer
num_threads = 5

# Liste pour stocker les threads
threads = []

for i in range(num_threads):
    car_id = f"test_car_{i+1}"
    thread = threading.Thread(target=send_data, args=(car_id,))
    threads.append(thread)
    thread.start()

# Attendre que tous les threads se terminent
for thread in threads:
    thread.join()

import random
import threading
import time

import requests
import websocket

# host = "localhost:8000"
host = "192.168.1.97:8000"

ws = websocket.create_connection(f"ws://{host}/ws")

d_lat = 45.75336519902591
d_lon = 3.0314909254483497


def send_data(car_id):
    global d_lat, d_lon
    battery = random.uniform(0, 50)

    while True:
        d_lat += random.uniform(-0.00003, 0.00003)
        d_lon += random.uniform(-0.00003, 0.00003)
        battery -= random.uniform(0, 1)
        if battery < 0:
            battery = 100
        online = random.random() < 0.95
        at_home = random.random() > 0.95

        data = {
            "id": car_id,
            "latitude": f"{d_lat}",
            "longitude": f"{d_lon}",
            "battery": battery,
            "status": online,
            "at_home": at_home,
        }

        print("Sending data: ", data)

        requests.put(f"http://{host}/carts/{car_id}", json=data)

        if not online:
            time.sleep(10)

        time.sleep(2)


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

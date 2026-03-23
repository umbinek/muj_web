
import time
import board
import adafruit_dht

dht = adafruit_dht.DHT11(board.D4)

while True:
    try:
        t = dht.temperature
        h = dht.humidity
        print(t, h)
    except RuntimeError:
        print("Error: Sensor not working")
    time.sleep(2)

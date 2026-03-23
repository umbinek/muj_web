import time
import board
import adafruit_dht
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import Measurement

dht = adafruit_dht.DHT11(board.D4)

DB_PATH = "/home/cernamalina/web/smartsensor/smartsensor.db"
DB_SOURCE = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_SOURCE)
SessionLocal = sessionmaker(bind=engine)
print("--- SmartSensor Collector běží ---")
print("Ukládám data do databáze... (Ctrl+C pro ukončení)")

while True:
    try:

        t = dht.temperature
        h = dht.humidity
        
        if t is not None and h is not None:
            new_data = Measurement(temperature=t, humidity=h)
            
            session = SessionLocal()
            session.add(new_data)
            session.commit()
            session.close()
            
            print(f"ULOŽENO: Teplota={t}°C, Vlhkost={h}%")
        else:
            print("Chyba: Prázdné hodnoty ze senzoru")

    except RuntimeError:
        print("Chyba čtení senzoru (zkusím znovu)")
    
    except Exception as e:
        dht.exit()
        raise e

    time.sleep(300)

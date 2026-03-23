import os
import glob
import time
from datetime import datetime

from flask import current_app
from models import Measurement

class SensorService:
    def __init__(self):
        # These are fallback values in case the database is completely empty.
        self.temperature = 22.0
        self.humidity = 45.0
        self.error_mode = False
        self.alarm_threshold = 30.0

    def set_simulation(self, temp=None, hum=None, error=None):
        if temp is not None: self.temperature = float(temp)
        if hum is not None: self.humidity = float(hum)
        if error is not None: self.error_mode = error

    def get_status_data(self):
        # 1. If we are currently testing an error, we will send None directly (the website will turn red).
        if self.error_mode:
            return None
            
        try:
            # 2. The magic of Flask: We borrow the session maker from the running application
            db = current_app.SessionLocal()
            
            # 3. We will extract the very last measured value.
            latest = db.query(Measurement).order_by(Measurement.timestamp.desc()).first()
            
            if latest:
                return {
                    "temperature": latest.temperature,
                    "humidity": latest.humidity,
                    "alarm": float(latest.temperature) > self.alarm_threshold,
                    "timestamp": latest.timestamp.isoformat()
                }
            else:
                # If the Measurement table were empty
                return {
                    "temperature": self.temperature,
                    "humidity": self.humidity,
                    "alarm": self.temperature > self.alarm_threshold,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            # 4. Emergency brake: If the database crashes, the server will not shut down, 
            # but the error will be displayed directly on Gabča's website at teplota.
            return {
                "temperature": f"ERR: {str(e)}", 
                "humidity": 0,
                "alarm": True,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # 5. Cleanup: We always have to close the session, otherwise the database would become "clogged" after a few queries.
            if 'db' in locals():
                db.close()

    def save_air_quality(self, db_session, value):
        new_record = AirQuality(value=value)
        db_session.add(new_record)
        db_session.commit()

    def get_air_history(self, db_session, limit=100):
        # Returns data for the graph (last X measurements)
        return db_session.query(AirQuality).order_by(AirQuality.timestamp.desc()).limit(limit).all()

class VideoService:
    def __init__(self, cat_folder, phone_folder):
        self.folders = {"kocka": cat_folder, "telefon": phone_folder}

    def save_video(self, category, file):
        folder = self.folders.get(category)
        if not folder: return None
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{category}_{timestamp}.mp4"
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        
        # Deletion rules: cat leaves 3, phone (street) more
        limit = 3 if category == "kocka" else 200
        self._cleanup(folder, limit)
        return filename

    def _cleanup(self, folder, max_files):
        files = glob.glob(os.path.join(folder, "*.mp4"))
        files.sort(key=os.path.getmtime, reverse=True)
        if len(files) > max_files:
            for old_file in files[max_files:]:
                try: os.remove(old_file)
                except: pass

    def get_video_list(self, category, limit=3):
        folder = self.folders.get(category)
        if not folder or not os.path.exists(folder): return []
        
        files = glob.glob(os.path.join(folder, "*.mp4"))
        files.sort(key=os.path.getmtime, reverse=True)
        
        # Filtering by age (original logic nacti_a_uklid_videa)
        actual_time = time.time()
        result_value = []
        for f in files:
            if (actual_time - os.path.getmtime(f)) > (7 * 24 * 3600): # 7 days
                try: os.remove(f)
                except: pass
                continue
            
            if len(result_value) < limit:
                result_value.append({
                    'name': os.path.basename(f),
                    'time': datetime.fromtimestamp(os.path.getmtime(f)).strftime('%d.%m. %H:%M'),
                    'folder': category
                })
        return result_value

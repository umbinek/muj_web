import os
import time
import random
import requests
import io
import csv
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, Response, stream_with_context, send_from_directory, abort, current_app, send_file
from models import Measurement, AirQuality

main_bp = Blueprint('main', __name__)

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == current_app.config['USERNAME'] and \
           request.form.get("password") == current_app.config['PASSWORD']:
            session["logged_in"] = True
            return redirect(url_for("main.gabca"))
        return "Neplatne prihlasovaci udaje", 401
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("main.login"))

@main_bp.route("/")
def home():
    svc = current_app.sensor_service
    db = current_app.SessionLocal()
    
    # Get last value od air quality
    last_air = db.query(AirQuality).order_by(AirQuality.timestamp.desc()).first()
    db.close()
    
    air_val = last_air.value if last_air else "N/A"
    
    return render_template("index.html", 
                           temperature=svc.temperature, 
                           humidity=svc.humidity,
                           air_quality=air_val)

@main_bp.route("/gabca")
def gabca():
    svc = current_app.sensor_service
    return render_template("gabca.html", temp=svc.temperature, hum=svc.humidity, error=svc.error_mode, threshold=svc.alarm_threshold)

@main_bp.route("/api/history")
def get_history():
    db_session = current_app.SessionLocal()
    try:
        data = db_session.query(Measurement).order_by(Measurement.timestamp.desc()).limit(20).all()
        results = [{"time": m.timestamp.isoformat(), "temp": m.temperature, "hum": m.humidity} for m in data]
        return jsonify(results[::-1])
    finally:
        db_session.close()

@main_bp.route("/api/status")
def get_status():
    status = current_app.sensor_service.get_status_data()
    if status is None:
        return jsonify({"error": "Senzor nedostupný", "code": 500}), 500
    return jsonify(status)

@main_bp.route("/api/set_threshold", methods=["POST"])
def set_threshold():
    data = request.get_json()
    new_val = data.get("threshold")
    if new_val is not None:
        current_app.sensor_service.alarm_threshold = float(new_val)
        return jsonify({"status": "updated", "new_threshold": current_app.sensor_service.alarm_threshold})
    return "Bad Request", 400

@main_bp.route("/api/test/inject_data", methods=["POST"])
def inject_data():
    data = request.get_json()
    current_app.sensor_service.set_simulation(temp=data.get("temp"), hum=data.get("hum"), error=data.get("error"))
    return jsonify({"status": "Simulace nastavena"})

@main_bp.route("/api/air_quality", methods=["POST"])
def air_quality():
    data = request.get_json()
    if not data:
        return "Zadna data neprijata", 400
    
    hodnota = data.get("value")
    # unit = data.get("unit", "ppm")

    db_session = current_app.SessionLocal()
    try:

        new_record = AirQuality(value=float(hodnota))
        db_session.add(new_record)
        db_session.commit()
        print(f"--- [PŘÍJEM DAT] Kvalita vzduchu uložena: {hodnota} ---")
        return jsonify({"status": "OK", "message": "Data ulozena do DB"}), 200
    except Exception as e:
        db_session.rollback()
        print(f"Chyba zapisu kvality vzduchu: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close()

@main_bp.route("/api/air_history")
def air_history():
    """Vrací data za posledních 24 hodin pro graf."""
    db = current_app.SessionLocal()
    try:
        time_threshold = datetime.now() - timedelta(hours=24)
        data = db.query(AirQuality).filter(AirQuality.timestamp >= time_threshold).order_by(AirQuality.timestamp.asc()).all()
        
        results = [{"time": m.timestamp.isoformat(), "value": m.value} for m in data]
        return jsonify(results)
    finally:
        db.close()

@main_bp.route("/api/export_csv")
def export_csv():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Cas', 'Teplota', 'Vlhkost'])
    db = current_app.SessionLocal()
    data = db.query(Measurement).order_by(Measurement.timestamp.desc()).limit(10).all()
    for m in data: cw.writerow([m.timestamp, m.temperature, m.humidity])
    db.close()
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=history.csv"})

@main_bp.route("/kamera")
def kamera():
    if not session.get("logged_in"): return redirect(url_for("main.login"))
    try:
        with open("last_time.txt", "r") as f: last_updated = f.read()
    except: last_updated = "Neznamy cas"
    
    esp_dir = os.path.join("static", "photos", "esp32")
    esp32_photos = sorted([f for f in os.listdir(esp_dir) if f.endswith(".jpg")]) if os.path.exists(esp_dir) else []
    return render_template("kamera.html", random=random.random, last_updated=last_updated, esp32_photos=esp32_photos)

@main_bp.route("/kocka")
def kocka_tv():
    if not session.get("logged_in"): return redirect(url_for("main.login"))
    cat_vids = current_app.video_service.get_video_list("kocka", limit=3)
    street_vids = current_app.video_service.get_video_list("telefon", limit=3)
    return render_template("kocka.html", cat_videos=cat_vids, street_videos=street_vids)

@main_bp.route("/upload_photo", methods=["POST"])
def upload_photo():
    file = request.files.get("file")
    timestamp = request.form.get("timestamp", "unknown")
    source = request.form.get("source", "raspberry")
    if file:
        if source == "esp32":
            folder = os.path.join("static", "photos", "esp32")
            filename = f"{timestamp.replace(' ', '_').replace(':', '-')}.jpg"
            filepath = os.path.join(folder, filename)
        else:
            filepath = os.path.join("static", "photos", "latest.jpg")
            with open("last_time.txt", "w") as f: f.write(timestamp)
        file.save(filepath)
        return "Fotka ulozena", 200
    return "Chyba", 400

@main_bp.route("/upload_kocka", methods=['POST'])
def upload_kocka():
    file = request.files.get('file')
    if not file: return 'Zadny soubor', 400
    res = current_app.video_service.save_video("kocka", file)
    return ('Video ulozeno', 200) if res else ('Chyba', 500)

@main_bp.route('/secure_video/<category>/<filename>')
def secure_video(category, filename):
    if not session.get("logged_in"): return abort(403)
    folder = current_app.video_service.folders.get(category)
    if not folder: return abort(404)
    return send_from_directory(folder, filename)

@main_bp.route('/video_feed')
def video_feed():
    if not session.get("logged_in"): return redirect(url_for("main.login"))
    motion_url = 'http://100.64.10.126:8081/'
    def generate():
        try:
            r = requests.get(motion_url, stream=True, timeout=5)
            for chunk in r.iter_content(chunk_size=1024): yield chunk
        except Exception as e: print(f"Chyba streamu: {e}")
    return Response(stream_with_context(generate()), mimetype='multipart/x-mixed-replace; boundary=BoundaryString')

@main_bp.route("/scraping")
def scraped_data():
    file_path = "/home/cernamalina/Documents/Lego-main/analyst/top_growth.html"
    return send_file(file_path) if os.path.exists(file_path) else ("Soubor nenalezen", 404)

@main_bp.route("/omne")
def omne(): return render_template("omne.html")

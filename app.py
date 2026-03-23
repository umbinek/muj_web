from flask import Flask
from config import Config
from models import get_engine, SessionLocal, Base
from services import SensorService, VideoService
from routes import main_bp
from sqlalchemy.orm import sessionmaker

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # instaling enviroment
    Config.init_app()

    # Database
    engine = get_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    app.SessionLocal = sessionmaker(bind=engine)

    # OOP services
    app.sensor_service = SensorService()
    app.video_service = VideoService(
        cat_folder=app.config['CAT_VIDEO_FOLDER'],
        phone_folder=app.config['PHONE_VIDEO_FOLDER']
    )

    # Resgistration Blueprint
    app.register_blueprint(main_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)

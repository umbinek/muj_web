import os

class Config:
    # this is only example
    SECRET_KEY = "testovaci_tajne_heslo"
    USERNAME = "test_user"
    PASSWORD = "test_password"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    

    SECURE_BASE = os.path.join(BASE_DIR, "secure_videos_dummy")
    CAT_VIDEO_FOLDER = os.path.join(SECURE_BASE, "kocka")
    PHONE_VIDEO_FOLDER = os.path.join(SECURE_BASE, "telefon")

    DB_PATH = os.path.join(BASE_DIR, 'smartsensor', 'test_dummy.db')
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


    @classmethod
    def init_app(cls):
        os.makedirs(cls.CAT_VIDEO_FOLDER, exist_ok=True)
        os.makedirs(cls.PHONE_VIDEO_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(cls.BASE_DIR, "static", "photos", "esp32"), exist_ok=True)

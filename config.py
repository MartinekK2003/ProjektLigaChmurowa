import os
from dotenv import load_dotenv

# Wskazujemy konkretną nazwę pliku, z którego mają zostać wczytane dane
load_dotenv("dane.env")


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'domyslny_klucz_bezpieczenstwa')

    # Reszta pozostaje bez zmian
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_NAME = os.getenv('DB_NAME', 'liga_chmurowa')

    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
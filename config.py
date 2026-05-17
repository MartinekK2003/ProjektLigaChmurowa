import os
from dotenv import load_dotenv

# Wczytujemy dane z pliku dane.env
load_dotenv("dane.env")


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'domyslny_klucz_bezpieczenstwa')

    # Budujemy ścieżkę do pliku bazy danych SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_NAME = os.getenv('DB_NAME', 'liga_chmurowa.db')

    # Adres dla SQLite: sqlite:///sciezka/do/pliku.db
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, DB_NAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
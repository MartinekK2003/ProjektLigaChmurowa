# app.py
import os
from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import Config

# Rejestracja poszczególnych kontrolerów (Blueprints)
from controllers.auth import auth_bp
from controllers.kibic import kibic_bp
from controllers.trener import trener_bp
from controllers.sedzia import sedzia_bp
from controllers.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# Inicjalizacja SQLAlchemy
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("✅ Połączono z bazą SQLite: liga_chmurowa.db")
    except Exception as e:
        print(f"❌ Błąd inicjalizacji bazy: {e}")

# Konfiguracja logowania
login_manager = LoginManager(app)
# Teraz wskazujemy Flaskowi, że funkcja logowania jest wewnątrz auth_bp
login_manager.login_view = 'auth_bp.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rejestrowanie komponentów aplikacji
app.register_blueprint(auth_bp)
app.register_blueprint(kibic_bp)
app.register_blueprint(trener_bp)
app.register_blueprint(sedzia_bp)
app.register_blueprint(admin_bp)

@app.route('/zainstaluj-baze')
def zainstaluj_baze():
    from setup_sqlite import setup_database
    setup_database()
    return "Sukces! Nowe tabele i dane zostały załadowane do chmury. Wróć na stronę główną."

if __name__ == '__main__':
    app.run(debug=True)
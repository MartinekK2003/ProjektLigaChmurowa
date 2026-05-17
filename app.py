import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, Team, Player, Season, Match, Goal
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Inicjalizacja SQLAlchemy
db.init_app(app)

# --- KLUCZOWY DODATEK DLA AZURE ---
# Sprawdzamy połączenie z bazą przy starcie aplikacji
with app.app_context():
    try:
        # Ta linia stworzy tabele, jeśli plik .db jest pusty lub nowy
        db.create_all()
        print("✅ Połączono z bazą SQLite: liga_chmurowa.db")
    except Exception as e:
        print(f"❌ Błąd inicjalizacji bazy: {e}")

# Konfiguracja Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- SZABLONY HTML ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Logowanie - Liga Chmurowa</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f4f4f9; margin: 0; }
        .login-card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2 style="color: #333;">Liga Chmurowa</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for m in messages %}<p style="color:red; font-size: 0.8rem;">{{ m }}</p>{% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Login" required>
            <input type="password" name="password" placeholder="Hasło" required>
            <button type="submit">Zaloguj się</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .nav { background: #333; color: white; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .card { background: white; border: 1px solid #ddd; padding: 25px; margin-top: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .role-badge { background: #007bff; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; }
        a { color: #ff4d4d; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="nav">
        <span>Zalogowany: <b>{{ current_user.username }}</b> <span class="role-badge">{{ current_user.role.name }}</span></span>
        <a href="{{ url_for('logout') }}">Wyloguj się</a>
    </div>

    <div class="card">
        <h1>Witaj w panelu {{ current_user.role.name }}</h1>
        <hr>
        {% if current_user.role.name == 'admin' %}
            <p>🔧 <b>Uprawnienia administratora:</b> Zarządzaj bazą danych, dodawaj drużyny i edytuj użytkowników.</p>
        {% elif current_user.role.name == 'coach' %}
            <p>📋 <b>Panel trenera:</b> Zarządzasz drużyną: <span style="color: #007bff;">{{ current_user.team.name if current_user.team else 'Brak' }}</span></p>
        {% elif current_user.role.name == 'referee' %}
            <p>⚖️ <b>Panel sędziego:</b> Możesz wprowadzać oficjalne wyniki meczów i przyznawać gole.</p>
        {% else %}
            <p>⚽ <b>Panel kibica:</b> Przeglądaj statystyki ligi, wyniki i tabelę strzelców.</p>
        {% endif %}
    </div>
</body>
</html>
"""


# --- ROUTY ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Błędny login lub hasło!')

    return render_template_string(LOGIN_HTML)


@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Na Azure port jest dynamicznie przydzielany, debug=True tylko lokalnie
    app.run(debug=True)
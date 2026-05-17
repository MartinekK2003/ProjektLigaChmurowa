from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, Team, Player, Season, Match, Goal
from config import Config

app = Flask(__name__)

# Ładowanie konfiguracji z pliku config.py (który czyta dane.env)
app.config.from_object(Config)

# Inicjalizacja bazy danych SQLAlchemy
db.init_app(app)

# Konfiguracja managera logowania
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Zaloguj się, aby uzyskać dostęp do panelu."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- SZABLONY HTML (Wbudowane dla ułatwienia, możesz je przenieść do folderu templates) ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Logowanie - Liga Chmurowa</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f4f4f9; }
        .login-card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px; }
        input { width: 100%; padding: 8px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Logowanie</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}<p class="error">{{ message }}</p>{% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST">
            <label>Użytkownik:</label>
            <input type="text" name="username" required>
            <label>Hasło:</label>
            <input type="password" name="password" required>
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
    <title>Panel Główny - Liga Chmurowa</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; }
        .sidebar { width: 250px; background: #333; color: white; height: 100vh; padding: 20px; position: fixed; }
        .content { margin-left: 290px; padding: 40px; width: 100%; }
        .role-badge { padding: 5px 10px; border-radius: 4px; font-size: 0.8rem; text-transform: uppercase; }
        .admin { background: #d32f2f; } .coach { background: #388e3c; } .referee { background: #f57c00; } .user { background: #1976d2; }
        .card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-top: 20px; background: #fff; }
        hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
        a { color: #ff5252; text-decoration: none; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>Liga Chmurowa</h3>
        <p>Zalogowany: <strong>{{ current_user.username }}</strong></p>
        <span class="role-badge {{ current_user.role.name }}">{{ current_user.role.name }}</span>
        <br><br><br>
        <a href="{{ url_for('logout') }}">Wyloguj się</a>
    </div>

    <div class="content">
        <h1>Witaj w systemie zarządzania ligą</h1>
        <p>Dzisiaj jest dobry dzień na piłkę nożną!</p>

        {% if current_user.role.name == 'admin' %}
            <div class="card">
                <h2>🛠️ Panel Administratora</h2>
                <ul>
                    <li><strong>Zarządzaj klubami:</strong> Dodaj nową drużynę do sezonu lub usuń istniejącą.</li>
                    <li><strong>Użytkownicy:</strong> Nadawaj uprawnienia sędziom i trenerom.</li>
                </ul>
                <button disabled>Zarządzaj drużynami (Wkrótce)</button>
            </div>

        {% elif current_user.role.name == 'coach' %}
            <div class="card">
                <h2>📋 Panel Trenera</h2>
                <p>Drużyna: <strong>{{ current_user.team.name if current_user.team else 'Nieprzypisany' }}</strong></p>
                <ul>
                    <li><strong>Kadra:</strong> Dodaj lub usuń zawodnika ze swojej listy.</li>
                    <li><strong>Analiza:</strong> Sprawdź statystyki goli przeciwko konkretnym rywalom.</li>
                </ul>
            </div>

        {% elif current_user.role.name == 'referee' %}
            <div class="card">
                <h2>⚽ Panel Sędziego</h2>
                <ul>
                    <li><strong>Mecze:</strong> Wprowadź wyniki dzisiejszych spotkań.</li>
                    <li><strong>Gole:</strong> Przypisz strzelców do bramek w systemie.</li>
                </ul>
            </div>

        {% else %}
            <div class="card">
                <h2>👀 Panel Użytkownika</h2>
                <ul>
                    <li><strong>Sezony:</strong> Wybierz sezon, aby zobaczyć listę klubów.</li>
                    <li><strong>Statystyki:</strong> Sprawdź, kto jest aktualnym królem strzelców.</li>
                </ul>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


# --- ROUTY (Ścieżki aplikacji) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Logika sprawdzania hasła (dla celów edukacyjnych tekst jawny, w produkcji hash)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Nieprawidłowy login lub hasło')

    return render_template_string(LOGIN_HTML)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)


# Uruchomienie aplikacji
if __name__ == '__main__':
    app.run(debug=True)
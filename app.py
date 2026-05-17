from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, Team, Player, Season, Match, Goal
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Liga Chmurowa</h2>
        {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<p style="color:red">{{m}}</p>{% endfor %}{% endif %}{% endwith %}
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
        body { font-family: sans-serif; margin: 0; padding: 20px; }
        .nav { background: #333; color: white; padding: 10px; border-radius: 5px; }
        .card { border: 1px solid #ccc; padding: 20px; margin-top: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="nav">Zalogowany jako: <b>{{ current_user.username }}</b> ({{ current_user.role.name }}) | <a href="{{ url_for('logout') }}" style="color:white">Wyloguj</a></div>

    <div class="card">
        <h1>Witaj w panelu {{ current_user.role.name }}</h1>
        {% if current_user.role.name == 'admin' %}
            <p>Możesz zarządzać drużynami i użytkownikami.</p>
        {% elif current_user.role.name == 'coach' %}
            <p>Zarządzasz drużyną: {{ current_user.team.name }}</p>
        {% elif current_user.role.name == 'referee' %}
            <p>Wprowadzaj wyniki meczów.</p>
        {% else %}
            <p>Przeglądaj statystyki ligi.</p>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Błąd logowania!')
    return render_template_string(LOGIN_HTML)


@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
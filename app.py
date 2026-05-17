import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func
from models import db, User, Role, Team, Player, Season, Match, Goal
from config import Config

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

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# SZABLONY HTML (WIDOKI - VIEW)
# ==========================================

# Wspólny nagłówek z użyciem Bootstrapa dla lepszego wyglądu
BASE_HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <title>Liga Chmurowa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #f0f2f5; }</style>
</head>
"""

LOGIN_HTML = BASE_HTML_HEAD + """
<body class="d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow" style="width: 350px;">
        <h2 class="text-center text-primary mb-4">Liga Chmurowa</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for m in messages %}<div class="alert alert-danger p-2 text-center">{{ m }}</div>{% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" class="form-control mb-3" name="username" placeholder="Login" required>
            <input type="password" class="form-control mb-3" name="password" placeholder="Hasło" required>
            <button type="submit" class="btn btn-primary w-100 fw-bold">Zaloguj się</button>
        </form>
    </div>
</body>
"""

DASHBOARD_HTML = BASE_HTML_HEAD + """
<body class="container mt-4">
    <nav class="navbar navbar-dark bg-dark p-3 rounded mb-4 shadow">
        <div class="text-white">
            Zalogowany jako: <b>{{ current_user.username }}</b> 
            <span class="badge bg-primary ms-2">{{ current_user.role.name|upper }}</span>
        </div>
        <a href="{{ url_for('logout') }}" class="btn btn-danger btn-sm fw-bold">Wyloguj się</a>
    </nav>

    <div class="row mb-4">
        <div class="col-12 d-flex gap-2 justify-content-center">
            <a href="{{ url_for('tabela') }}" class="btn btn-outline-dark">Tabela Ligi</a>
            <a href="{{ url_for('strzelcy') }}" class="btn btn-outline-dark">Król Strzelców</a>

            {% if current_user.role.name == 'coach' %}
                <a href="{{ url_for('trener_sklad') }}" class="btn btn-success">Zarządzaj Składem</a>
            {% endif %}

            {% if current_user.role.name == 'referee' %}
                <a href="{{ url_for('sedzia_mecze') }}" class="btn btn-warning">Wprowadź Wyniki</a>
            {% endif %}

            {% if current_user.role.name == 'admin' %}
                <a href="{{ url_for('admin_druzyny') }}" class="btn btn-danger">Zarządzaj Drużynami</a>
            {% endif %}
        </div>
    </div>

    <div class="card shadow-sm p-4">
        {% block content %}
            <h2 class="text-center">Witaj w systemie zarządzania Ligą Chmurową!</h2>
            <p class="text-center text-muted">Wybierz moduł z menu powyżej, aby rozpocząć pracę.</p>
        {% endblock %}
    </div>
</body>
"""


# ==========================================
# ROUTY PUBLICZNE I AUTORYZACJA (KONTROLER - CONTROLLER)
# ==========================================

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
        flash('Błędny login lub hasło!')
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


# ==========================================
# FUNKCJONALNOŚCI: KIBIC (Widoczne dla wszystkich zalogowanych)
# ==========================================

@app.route('/tabela')
@login_required
def tabela():
    teams = Team.query.all()
    matches = Match.query.filter_by(is_finished=True).all()

    # Inicjalizacja słownika do zliczania punktów
    stats = {t.id: {'name': t.name, 'points': 0, 'goals_scored': 0, 'goals_lost': 0} for t in teams}

    # Przeliczanie punktów na podstawie historii meczów
    for m in matches:
        stats[m.home_team_id]['goals_scored'] += m.home_score
        stats[m.home_team_id]['goals_lost'] += m.away_score
        stats[m.away_team_id]['goals_scored'] += m.away_score
        stats[m.away_team_id]['goals_lost'] += m.home_score

        if m.home_score > m.away_score:
            stats[m.home_team_id]['points'] += 3
        elif m.home_score < m.away_score:
            stats[m.away_team_id]['points'] += 3
        else:
            stats[m.home_team_id]['points'] += 1
            stats[m.away_team_id]['points'] += 1

    # Sortowanie po punktach (malejąco)
    sorted_table = sorted(stats.values(), key=lambda x: x['points'], reverse=True)

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Tabela Ligi</h3>
    <table class="table table-striped mt-3">
        <thead class="table-dark"><tr><th>Miejsce</th><th>Drużyna</th><th>Punkty</th><th>Bramki (Z-S)</th></tr></thead>
        <tbody>
            {% for row in table %}
            <tr><td>{{ loop.index }}</td><td>{{ row.name }}</td><td><b>{{ row.points }}</b></td><td>{{ row.goals_scored }} - {{ row.goals_lost }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), table=sorted_table)


@app.route('/strzelcy')
@login_required
def strzelcy():
    # Zaawansowane zapytanie SQL łączące tabele Player i Goal
    top_scorers = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
        .join(Goal).group_by(Player.id).order_by(func.sum(Goal.goals).desc()).limit(10).all()

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Top 10 Strzelców</h3>
    <table class="table table-bordered mt-3">
        <thead class="table-dark"><tr><th>#</th><th>Zawodnik</th><th>Suma Goli</th></tr></thead>
        <tbody>
            {% for scorer in scorers %}
            <tr><td>{{ loop.index }}</td><td>{{ scorer.name }}</td><td><b>{{ scorer.total }}</b></td></tr>
            {% else %}<tr><td colspan="3">Brak zdobytych bramek w lidze.</td></tr>{% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), scorers=top_scorers)


# ==========================================
# FUNKCJONALNOŚCI: TRENER
# ==========================================

@app.route('/trener/sklad', methods=['GET', 'POST'])
@login_required
def trener_sklad():
    if current_user.role.name != 'coach':
        return "Brak uprawnień. Zaloguj się jako trener.", 403

    if not current_user.team_id:
        return "Nie przypisano Cię do żadnej drużyny!", 400

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_player = Player(name=request.form.get('player_name'), team_id=current_user.team_id)
            db.session.add(new_player)
            db.session.commit()
        elif action == 'delete':
            player = Player.query.get(request.form.get('player_id'))
            if player and player.team_id == current_user.team_id:
                db.session.delete(player)
                db.session.commit()
        return redirect(url_for('trener_sklad'))

    my_team = Team.query.get(current_user.team_id)

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Skład drużyny: <span class="text-primary">{{ team.name }}</span></h3>
    <form method="POST" class="d-flex gap-2 mt-3 mb-4">
        <input type="hidden" name="action" value="add">
        <input type="text" name="player_name" class="form-control" placeholder="Imię i nazwisko zawodnika" required>
        <button type="submit" class="btn btn-success">Dodaj zawodnika</button>
    </form>
    <ul class="list-group">
        {% for p in team.players %}
        <li class="list-group-item d-flex justify-content-between align-items-center">
            {{ p.name }}
            <form method="POST" class="m-0">
                <input type="hidden" name="action" value="delete">
                <input type="hidden" name="player_id" value="{{ p.id }}">
                <button type="submit" class="btn btn-sm btn-danger">Zwolnij</button>
            </form>
        </li>
        {% endfor %}
    </ul>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), team=my_team)


# ==========================================
# FUNKCJONALNOŚCI: SĘDZIA
# ==========================================

@app.route('/sedzia/mecze', methods=['GET', 'POST'])
@login_required
def sedzia_mecze():
    if current_user.role.name != 'referee':
        return "Brak uprawnień. Zaloguj się jako sędzia.", 403

    if request.method == 'POST':
        match_id = request.form.get('match_id')
        match = Match.query.get(match_id)
        if match and not match.is_finished:
            match.home_score = int(request.form.get('home_score'))
            match.away_score = int(request.form.get('away_score'))
            match.is_finished = True
            db.session.commit()
        return redirect(url_for('sedzia_mecze'))

    # Pokazujemy tylko mecze, które się jeszcze nie zakończyły
    pending_matches = Match.query.filter_by(is_finished=False).all()

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Wprowadzanie Wyników</h3>
    <div class="row mt-3">
        {% for m in matches %}
        <div class="col-md-6 mb-3">
            <div class="card p-3 bg-light">
                <form method="POST" class="d-flex align-items-center justify-content-between">
                    <input type="hidden" name="match_id" value="{{ m.id }}">
                    <span class="fw-bold">{{ m.home_team_id }} (Gospodarz)</span>
                    <input type="number" name="home_score" class="form-control text-center mx-2" style="width:70px;" required min="0">
                    <span> - </span>
                    <input type="number" name="away_score" class="form-control text-center mx-2" style="width:70px;" required min="0">
                    <span class="fw-bold">{{ m.away_team_id }} (Gość)</span>
                    <button type="submit" class="btn btn-warning btn-sm ms-2">Zapisz</button>
                </form>
            </div>
        </div>
        {% else %} <p class="text-muted">Brak zaplanowanych meczów do rozegrania.</p> {% endfor %}
    </div>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), matches=pending_matches)


# ==========================================
# FUNKCJONALNOŚCI: ADMINISTRATOR
# ==========================================

@app.route('/admin/druzyny', methods=['GET', 'POST'])
@login_required
def admin_druzyny():
    if current_user.role.name != 'admin':
        return "Brak uprawnień. Zaloguj się jako administrator.", 403

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_team = Team(name=request.form.get('team_name'))
            db.session.add(new_team)
            db.session.commit()
        elif action == 'delete':
            team = Team.query.get(request.form.get('team_id'))
            if team:
                db.session.delete(team)
                db.session.commit()
        return redirect(url_for('admin_druzyny'))

    teams = Team.query.all()

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3 class="text-danger">Panel Administracyjny: Drużyny</h3>
    <form method="POST" class="d-flex gap-2 mt-3 mb-4">
        <input type="hidden" name="action" value="add">
        <input type="text" name="team_name" class="form-control" placeholder="Nazwa nowego klubu" required>
        <button type="submit" class="btn btn-danger">Rejestruj drużynę</button>
    </form>
    <table class="table table-bordered">
        <thead class="table-dark"><tr><th>ID</th><th>Nazwa Klubu</th><th>Akcje</th></tr></thead>
        <tbody>
            {% for t in teams %}
            <tr>
                <td>{{ t.id }}</td><td><b>{{ t.name }}</b></td>
                <td>
                    <form method="POST" class="m-0">
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="team_id" value="{{ t.id }}">
                        <button type="submit" class="btn btn-sm btn-outline-danger">Usuń Klub</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), teams=teams)


if __name__ == '__main__':
    app.run(debug=True)
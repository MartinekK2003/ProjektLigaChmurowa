# controllers/kibic.py
from flask import Blueprint, render_template_string, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_
from models import db, Team, Match, Player, Goal, Season
from controllers import DASHBOARD_HTML

kibic_bp = Blueprint('kibic_bp', __name__)


@kibic_bp.route('/tabela')
@login_required
def tabela():
    teams = Team.query.all()
    matches = Match.query.filter_by(is_finished=True).all()

    stats = {t.id: {'name': t.name, 'points': 0, 'goals_scored': 0, 'goals_lost': 0} for t in teams}

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

    sorted_table = sorted(stats.values(), key=lambda x: x['points'], reverse=True)

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Tabela Ligi</h3>
    <table class="table table-striped mt-3">
        <thead class="table-dark"><tr><th>Miejsce</th><th>Drużyna</th><th>Punkty</th><th>Bramki (Z-S)</th></tr></thead>
        <tbody>
            {% for row in table %}
            <tr><td>{{ loop.index }}</td><td>{{ row.name }}</td><td><b>{{ row.points }}</b></td><td>{{ loop.index }} - {{ loop.index }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), table=sorted_table)


@kibic_bp.route('/strzelcy')
@login_required
def strzelcy():
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


# =========================================================================
# NOWA FUNKCJONALNOŚC: HISTORIA KLUBÓW W SEZONACH
# =========================================================================
@kibic_bp.route('/historia_klubow')
@login_required
def historia_klubow():
    # 1. Pobieramy parametry z adresu URL (np. ?season_id=1&team_id=2)
    season_id = request.args.get('season_id', type=int)
    team_id = request.args.get('team_id', type=int)

    # 2. Pobieramy listy wszystkich sezonów i klubów do menu wyboru
    seasons = Season.query.all()
    teams = Team.query.all()

    # Słownik do łatwego i bezpiecznego zmieniania ID na nazwy w szablonie HTML
    team_names = {t.id: t.name for t in teams}

    selected_season = Season.query.get(season_id) if season_id else None
    selected_team = Team.query.get(team_id) if team_id else None

    matches = []
    team_top_scorers = []

    # 3. Jeśli użytkownik wybrał ZARÓWNO sezon, JAK I konkretny klub, wyciągamy szczegóły
    if selected_season and selected_team:
        # Zapytanie: Filtrujemy mecze z wybranego sezonu, gdzie drużyna grała jako Gospodarz LUB Gość
        matches = Match.query.filter(
            Match.season_id == season_id,
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
        ).all()

        # Zaawansowane zapytanie SQL: Łączymy Player -> Goal -> Match,
        # filtrując tylko zawodników tego klubu i mecze z tego konkretnego sezonu
        team_top_scorers = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
            .join(Goal, Player.id == Goal.player_id) \
            .join(Match, Goal.match_id == Match.id) \
            .filter(Player.team_id == team_id, Match.season_id == season_id) \
            .group_by(Player.id) \
            .order_by(func.sum(Goal.goals).desc()) \
            .all()

    # Szablon HTML wykorzystujący nowoczesny podział na sekcje Bootstrap
    html = "{% extends 'dashboard' %}{% block content %}" + """
    <div class="row">
        <div class="col-md-4 border-end">
            <h4 class="mb-3">1. Wybierz Sezon</h4>
            <div class="list-group mb-4">
                {% for s in seasons %}
                    <a href="{{ url_for('kibic_bp.historia_klubow', season_id=s.id) }}" 
                       class="list-group-item list-group-item-action {% if selected_season and selected_season.id == s.id %}active{% endif %}">
                        {{ s.name }}
                    </a>
                {% endfor %}
            </div>

            {% if selected_season %}
                <h4 class="mb-3">2. Wybierz Klub</h4>
                <div class="list-group">
                    {% for t in teams %}
                        <a href="{{ url_for('kibic_bp.historia_klubow', season_id=selected_season.id, team_id=t.id) }}" 
                           class="list-group-item list-group-item-action {% if selected_team and selected_team.id == t.id %}list-group-item-success fw-bold{% endif %}">
                            {{ t.name }}
                        </a>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-info text-center p-2">Wybierz sezon z listy powyżej, aby zobaczyć kluby.</div>
            {% endif %}
        </div>

        <div class="col-md-8 ps-4">
            {% if selected_season and selected_team %}
                <div class="alert alert-dark p-3 text-center mb-4 shadow-sm">
                    <h3 class="m-0">Statystyki: <span class="text-success">{{ selected_team.name }}</span></h3>
                    <small class="text-muted">Okres: {{ selected_season.name }}</small>
                </div>

                <div class="row">
                    <div class="col-md-7 mb-4">
                        <h5 class="border-bottom pb-2 text-secondary">Rozegrane Mecze</h5>
                        {% for m in matches %}
                            <div class="card mb-2 shadow-sm p-2 {% if m.is_finished %}bg-white{% else %}bg-light text-muted{% endif %}">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="{% if m.home_team_id == selected_team.id %}fw-bold text-primary{% endif %}">
                                        {{ team_names[m.home_team_id] }}
                                    </span>
                                    <span class="badge bg-dark p-2 fs-6">
                                        {% if m.is_finished %}{{ m.home_score }} - {{ m.away_score }}{% else %}vs{% endif %}
                                    </span>
                                    <span class="{% if m.away_team_id == selected_team.id %}fw-bold text-primary{% endif %}">
                                        {{ team_names[m.away_team_id] }}
                                    </span>
                                </div>
                            </div>
                        {% else %}
                            <p class="text-muted small">Ta drużyna nie rozegrała żadnych spotkań w tym sezonie.</p>
                        {% endfor %}
                    </div>

                    <div class="col-md-5">
                        <h5 class="border-bottom pb-2 text-secondary">Strzelcy Drużyny</h5>
                        <table class="table table-sm table-hover bg-white border">
                            <thead class="table-secondary"><tr><th>Zawodnik</th><th class="text-center">Gole</th></tr></thead>
                            <tbody>
                                {% for scorer in team_top_scorers %}
                                <tr>
                                    <td>{{ scorer.name }}</td>
                                    <td class="text-center"><b>{{ scorer.total }}</b> ⚽</td>
                                </tr>
                                {% else %}
                                <tr><td colspan="2" class="text-muted small text-center">Brak strzelców w tym sezonie.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            {% else %}
                <div class="h-100 d-flex justify-content-center align-items-center text-muted" style="min-height: 300px;">
                    <div class="text-center">
                        <h4>🔍 Brak wybranej konfiguracji</h4>
                        <p>Kliknij na sezon, a następnie wybierz interesującą Cię drużynę z lewego menu.</p>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML),
                                  seasons=seasons, teams=teams, selected_season=selected_season,
                                  selected_team=selected_team, matches=matches,
                                  team_top_scorers=team_top_scorers, team_names=team_names)
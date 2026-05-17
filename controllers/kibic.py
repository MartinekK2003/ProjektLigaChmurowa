# controllers/kibic.py
from flask import Blueprint, render_template_string
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
            <tr><td>{{ loop.index }}</td><td>{{ row.name }}</td><td><b>{{ row.points }}</b></td><td>{{ row.goals_scored }} - {{ row.goals_lost }}</td></tr>
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
# NOWA FUNKCJONALNOŚC: ROZWIJANA HISTORIA KLUBÓW I SEZONÓW
# =========================================================================
@kibic_bp.route('/historia_klubow')
@login_required
def historia_klubow():
    seasons = Season.query.all()
    teams = Team.query.all()
    team_names = {t.id: t.name for t in teams}

    # Przygotowanie struktury danych: Sezon -> Kluby -> Mecze i Najlepsi strzelcy
    historia_danych = []

    for s in seasons:
        season_data = {
            'season': s,
            'teams_data': [],
            'top_scorers': []
        }
        for t in teams:
            # 1. Pobieramy mecze danej drużyny w danym sezonie
            matches = Match.query.filter(
                Match.season_id == s.id,
                or_(Match.home_team_id == t.id, Match.away_team_id == t.id)
            ).all()

            if matches:
                season_data['teams_data'].append({
                    'team': t,
                    'matches': matches
                })

                # 2. Wyliczamy najlepszego strzelca TEJ konkretnej drużyny w TYM sezonie
                top_scorer = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
                    .join(Goal, Player.id == Goal.player_id) \
                    .join(Match, Goal.match_id == Match.id) \
                    .filter(Player.team_id == t.id, Match.season_id == s.id) \
                    .group_by(Player.id) \
                    .order_by(func.sum(Goal.goals).desc()) \
                    .first()

                if top_scorer:
                    season_data['top_scorers'].append({
                        'team_name': t.name,
                        'player_name': top_scorer.name,
                        'goals': top_scorer.total
                    })

        # Dodajemy sezon do widoku tylko wtedy, gdy rozegrano w nim jakieś mecze
        if season_data['teams_data']:
            historia_danych.append(season_data)

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3 class="mb-4 text-center">Archiwum Rozgrywek</h3>

    <div class="accordion shadow-sm" id="seasonsAccordion">
        {% for s_data in historia_danych %}
        <div class="accordion-item mb-3 border">
            <h2 class="accordion-header" id="headingSeason{{ s_data.season.id }}">
                <button class="accordion-button collapsed fw-bold fs-5 bg-light text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseSeason{{ s_data.season.id }}" aria-expanded="false" aria-controls="collapseSeason{{ s_data.season.id }}">
                    🏆 {{ s_data.season.name }}
                </button>
            </h2>
            <div id="collapseSeason{{ s_data.season.id }}" class="accordion-collapse collapse" aria-labelledby="headingSeason{{ s_data.season.id }}" data-bs-parent="#seasonsAccordion">
                <div class="accordion-body bg-white">
                    <div class="row">

                        <div class="col-md-7 border-end">
                            <h5 class="mb-3 text-secondary">Kluby w sezonie:</h5>
                            <div class="accordion" id="teamsAccordion{{ s_data.season.id }}">
                                {% for t_data in s_data.teams_data %}
                                <div class="accordion-item">
                                    <h2 class="accordion-header" id="headingTeam{{ s_data.season.id }}_{{ t_data.team.id }}">
                                        <button class="accordion-button collapsed py-2" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTeam{{ s_data.season.id }}_{{ t_data.team.id }}" aria-expanded="false" aria-controls="collapseTeam{{ s_data.season.id }}_{{ t_data.team.id }}">
                                            ⚽ <strong>{{ t_data.team.name }}</strong>
                                        </button>
                                    </h2>
                                    <div id="collapseTeam{{ s_data.season.id }}_{{ t_data.team.id }}" class="accordion-collapse collapse" aria-labelledby="headingTeam{{ s_data.season.id }}_{{ t_data.team.id }}" data-bs-parent="#teamsAccordion{{ s_data.season.id }}">
                                        <div class="accordion-body p-0">
                                            <ul class="list-group list-group-flush">
                                                {% for m in t_data.matches %}
                                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                                    <span class="{% if m.home_team_id == t_data.team.id %}fw-bold text-primary{% endif %}">{{ team_names[m.home_team_id] }}</span>
                                                    <span class="badge bg-dark rounded-pill mx-2 fs-6">
                                                        {% if m.is_finished %}{{ m.home_score }} - {{ m.away_score }}{% else %}vs{% endif %}
                                                    </span>
                                                    <span class="{% if m.away_team_id == t_data.team.id %}fw-bold text-primary{% endif %}">{{ team_names[m.away_team_id] }}</span>
                                                </li>
                                                {% endfor %}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>

                        <div class="col-md-5 ps-4">
                            <h5 class="mb-3 text-secondary">Królowie Strzelców Drużyn:</h5>
                            <div class="table-responsive">
                                <table class="table table-sm table-hover border">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Klub</th>
                                            <th>Najlepszy Strzelec</th>
                                            <th class="text-center">Gole</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for scorer in s_data.top_scorers %}
                                        <tr>
                                            <td><small class="fw-bold">{{ scorer.team_name }}</small></td>
                                            <td><small>{{ scorer.player_name }}</small></td>
                                            <td class="text-center text-success fw-bold">{{ scorer.goals }}</td>
                                        </tr>
                                        {% else %}
                                        <tr>
                                            <td colspan="3" class="text-center text-muted py-3">Brak zdobytych bramek w tym sezonie.</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="alert alert-info text-center">Brak rozegranych meczów w bazie danych.</div>
        {% endfor %}
    </div>
    {% endblock %}"""

    return render_template_string(html.replace('dashboard', DASHBOARD_HTML),
                                  historia_danych=historia_danych,
                                  team_names=team_names)
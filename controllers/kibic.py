# controllers/kibic.py
from flask import Blueprint, render_template_string
from sqlalchemy import func, or_
from models import db, Team, Match, Player, Goal, Season
from controllers import NAV_HTML, FOOTER_HTML

kibic_bp = Blueprint('kibic_bp', __name__)

@kibic_bp.route('/tabela')
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

    CONTENT_HTML = """
    <h3>Tabela Ligi</h3>
    <table class="table table-striped mt-3">
        <thead class="table-dark"><tr><th>Miejsce</th><th>Drużyna</th><th>Punkty</th><th>Bramki (Z-S)</th></tr></thead>
        <tbody>
            {% for row in table %}
            <tr><td>{{ loop.index }}</td><td>{{ row.name }}</td><td><b>{{ row.points }}</b></td><td>{{ row.goals_scored }} - {{ row.goals_lost }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, table=sorted_table)


@kibic_bp.route('/strzelcy')
def strzelcy():
    top_scorers = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
        .join(Goal).group_by(Player.id).order_by(func.sum(Goal.goals).desc()).limit(10).all()

    CONTENT_HTML = """
    <h3>Top 10 Strzelców</h3>
    <table class="table table-bordered mt-3">
        <thead class="table-dark"><tr><th>#</th><th>Zawodnik</th><th>Suma Goli</th></tr></thead>
        <tbody>
            {% for scorer in scorers %}
            <tr><td>{{ loop.index }}</td><td>{{ scorer.name }}</td><td><b>{{ scorer.total }}</b></td></tr>
            {% else %}<tr><td colspan="3">Brak zdobytych bramek w lidze.</td></tr>{% endfor %}
        </tbody>
    </table>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, scorers=top_scorers)


@kibic_bp.route('/historia_klubow')
def historia_klubow():
    seasons = Season.query.all()
    teams = Team.query.all()
    team_names = {t.id: t.name for t in teams}

    # Pobieramy całą strukturę danych na raz do pamięci podręcznej
    historia_danych = []

    for s in seasons:
        season_data = {
            'season': s,
            'teams_data': [],
            'top_scorers': []
        }
        for t in teams:
            # Filtrujemy mecze dla konkretnego zespołu w tym konkretnym sezonie
            matches = Match.query.filter(
                Match.season_id == s.id,
                or_(Match.home_team_id == t.id, Match.away_team_id == t.id)
            ).all()

            if matches:
                season_data['teams_data'].append({
                    'team': t,
                    'matches': matches
                })

                # Wyliczamy najlepszego strzelca danej drużyny w tym konkretnym sezonie
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

        if season_data['teams_data']:
            historia_danych.append(season_data)

    CONTENT_HTML = """
    <h3 class="mb-4 text-center">Archiwum Rozgrywek (Lista Rozwijana)</h3>

    <div class="list-group shadow-sm">
        {% for s_data in historia_danych %}
        <div class="list-group-item p-0 border mb-2 rounded">

            <button type="button" class="btn btn-light w-100 text-start p-3 fw-bold fs-5 d-flex justify-content-between align-items-center" 
                    data-bs-toggle="collapse" data-bs-target="#collapseSeason{{ s_data.season.id }}">
                <span>🏆 {{ s_data.season.name }}</span>
                <small class="text-muted fs-6">Kliknij, aby rozwinąć sezon 🔽</small>
            </button>

            <div id="collapseSeason{{ s_data.season.id }}" class="collapse p-4 bg-white border-top">
                <div class="row">

                    <div class="col-md-7 border-end">
                        <h5 class="mb-3 text-secondary">Kluby w tym sezonie (kliknij klub, aby rozwinąć mecze):</h5>

                        <div class="list-group">
                            {% for t_data in s_data.teams_data %}
                            <div class="mb-2 border rounded">

                                <button type="button" class="btn btn-outline-primary w-100 text-start py-2 px-3 fw-bold d-flex justify-content-between align-items-center" 
                                        data-bs-toggle="collapse" data-bs-target="#collapseMatch_{{ s_data.season.id }}_{{ t_data.team.id }}">
                                    <span>⚽ {{ t_data.team.name }}</span>
                                    <small class="text-muted" style="font-size: 0.8rem;">Rozwiń mecze 📂</small>
                                </button>

                                <div id="collapseMatch_{{ s_data.season.id }}_{{ t_data.team.id }}" class="collapse bg-light">
                                    <ul class="list-group list-group-flush">
                                        {% for m in t_data.matches %}
                                        <li class="list-group-item d-flex justify-content-between align-items-center py-2 bg-light">
                                            <span class="{% if m.home_team_id == t_data.team.id %}fw-bold text-dark{% else %}text-muted{% endif %}">
                                                {{ team_names[m.home_team_id] }}
                                            </span>
                                            <span class="badge bg-dark rounded-pill mx-2">
                                                {% if m.is_finished %}{{ m.home_score }} - {{ m.away_score }}{% else %}vs{% endif %}
                                            </span>
                                            <span class="{% if m.away_team_id == t_data.team.id %}fw-bold text-dark{% else %}text-muted{% endif %}">
                                                {{ team_names[m.away_team_id] }}
                                            </span>
                                        </li>
                                        {% endfor %}
                                    </ul>
                                </div>

                            </div>
                            {% endfor %}
                        </div>
                    </div>

                    <div class="col-md-5 ps-4">
                        <h5 class="mb-3 text-secondary">Król Strzelców każdej drużyny:</h5>
                        <div class="table-responsive">
                            <table class="table table-sm table-hover border shadow-sm">
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
                                        <td><small class="fw-bold text-muted">{{ scorer.team_name }}</small></td>
                                        <td><small>{{ scorer.player_name }}</small></td>
                                        <td class="text-center text-success fw-bold">{{ scorer.goals }} ⚽</td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="3" class="text-center text-muted py-2">Brak danych o bramkach.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>
            </div>
        </div>
        {% else %}
        <div class="alert alert-info text-center">Brak rozegranych sezonów w bazie danych.</div>
        {% endfor %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  historia_danych=historia_danych,
                                  team_names=team_names)
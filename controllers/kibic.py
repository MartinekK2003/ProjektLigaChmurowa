# controllers/kibic.py
from flask import Blueprint, render_template_string
from models import db, Team, Player, Match, Goal
from sqlalchemy import func
from controllers import NAV_HTML, FOOTER_HTML

kibic_bp = Blueprint('kibic_bp', __name__)


# ==========================================
# 1. STRONA: TABELA LIGI
# ==========================================
@kibic_bp.route('/tabela')
def tabela():
    teams = Team.query.all()
    matches = Match.query.filter_by(is_finished=True).all()

    # Słownik do przechowywania statystyk każdej drużyny
    stats = {t.id: {'name': t.name, 'pts': 0, 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0, 'gd': 0} for t in teams}

    for m in matches:
        # Gole strzelone (gf - goals for) i stracone (ga - goals against)
        stats[m.home_team_id]['gf'] += m.home_score
        stats[m.home_team_id]['ga'] += m.away_score
        stats[m.away_team_id]['gf'] += m.away_score
        stats[m.away_team_id]['ga'] += m.home_score

        # Rozstrzygnięcie meczu
        if m.home_score > m.away_score:
            stats[m.home_team_id]['w'] += 1
            stats[m.home_team_id]['pts'] += 3
            stats[m.away_team_id]['l'] += 1
        elif m.home_score < m.away_score:
            stats[m.away_team_id]['w'] += 1
            stats[m.away_team_id]['pts'] += 3
            stats[m.home_team_id]['l'] += 1
        else:
            stats[m.home_team_id]['d'] += 1
            stats[m.home_team_id]['pts'] += 1
            stats[m.away_team_id]['d'] += 1
            stats[m.away_team_id]['pts'] += 1

    # Obliczanie bilansu bramkowego (gd - goal difference)
    for t_id in stats:
        stats[t_id]['gd'] = stats[t_id]['gf'] - stats[t_id]['ga']

    # Sortowanie: 1. Punkty, 2. Bilans bramek, 3. Strzelone bramki
    sorted_stats = sorted(stats.values(), key=lambda x: (x['pts'], x['gd'], x['gf']), reverse=True)

    CONTENT_HTML = """
    <div>
        <h3 class="mb-4">Tabela Ligi Chmurowej 📊</h3>
        <div class="card shadow-sm border-0">
            <div class="table-responsive">
                <table class="table table-hover table-striped mb-0 text-center align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th class="ps-3" style="width: 50px;">#</th>
                            <th class="text-start">Klub</th>
                            <th title="Punkty">PKT</th>
                            <th title="Zwycięstwa">Z</th>
                            <th title="Remisy">R</th>
                            <th title="Porażki">P</th>
                            <th title="Gole Strzelone:Stracone">Gole</th>
                            <th title="Bilans Bramkowy">Bilans</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in table %}
                        <tr class="{% if loop.index == 1 %}table-success fw-bold{% elif loop.index > table|length - 2 %}table-danger{% endif %}">
                            <td class="ps-3">{{ loop.index }}</td>
                            <td class="text-start">{{ s.name }}</td>
                            <td class="fs-5 fw-bold text-primary">{{ s.pts }}</td>
                            <td>{{ s.w }}</td>
                            <td>{{ s.d }}</td>
                            <td>{{ s.l }}</td>
                            <td>{{ s.gf }} : {{ s.ga }}</td>
                            <td>
                                {% if s.gd > 0 %}<span class="text-success">+{{ s.gd }}</span>
                                {% elif s.gd < 0 %}<span class="text-danger">{{ s.gd }}</span>
                                {% else %}{{ s.gd }}{% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="8" class="text-muted py-4">Liga jeszcze nie wystartowała. Brak rozegranych meczów.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <p class="text-muted small mt-2">
            <span class="badge bg-success">Zielony</span> - Miejsce premiowane awansem/mistrzostwem | 
            <span class="badge bg-danger">Czerwony</span> - Strefa spadkowa
        </p>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, table=sorted_stats)


# ==========================================
# 2. STRONA: KRÓL STRZELCÓW
# ==========================================
@kibic_bp.route('/strzelcy')
def strzelcy():
    # Pobieramy graczy i sumujemy gole, IGNORUJĄC gole samobójcze!
    top_scorers = db.session.query(
        Player.name,
        Team.name.label('team_name'),
        func.sum(Goal.goals).label('total_goals')
    ).join(Team, Player.team_id == Team.id) \
        .join(Goal, Goal.player_id == Player.id) \
        .filter(Goal.is_own_goal == False) \
        .group_by(Player.id) \
        .order_by(func.sum(Goal.goals).desc()) \
        .limit(15).all()

    CONTENT_HTML = """
    <div>
        <h3 class="mb-4">Król Strzelców 👑</h3>
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card shadow-sm border-0">
                    <ul class="list-group list-group-flush">
                        {% for scorer in scorers %}
                        <li class="list-group-item d-flex justify-content-between align-items-center py-3">
                            <div class="d-flex align-items-center">
                                <span class="fs-4 fw-bold text-muted me-3" style="width: 30px;">{{ loop.index }}.</span>
                                <div>
                                    <span class="fs-5 fw-bold">{{ scorer.name }}</span><br>
                                    <small class="text-muted">{{ scorer.team_name }}</small>
                                </div>
                            </div>
                            <span class="badge {% if loop.index == 1 %}bg-warning text-dark fs-4{% else %}bg-primary fs-5{% endif %} rounded-pill shadow-sm">
                                {{ scorer.total_goals }} ⚽
                            </span>
                        </li>
                        {% else %}
                        <li class="list-group-item text-center text-muted py-4">Brak zdobytych bramek w tym sezonie.</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, scorers=top_scorers)


# ==========================================
# 3. STRONA: HISTORIA KLUBÓW (KADRY)
# ==========================================
@kibic_bp.route('/historia')
def historia_klubow():
    teams = Team.query.all()

    CONTENT_HTML = """
    <div>
        <h3 class="mb-4">Historia i Kadry Klubów 📜</h3>
        <div class="row row-cols-1 row-cols-md-2 g-4">
            {% for t in teams %}
            <div class="col">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-dark text-white fw-bold fs-5">
                        {{ t.name }}
                    </div>
                    <div class="card-body">
                        <p class="card-text text-muted small mb-3">Aktualna kadra zgłoszona do rozgrywek Ligi Chmurowej.</p>
                        <div class="d-flex flex-wrap gap-1">
                            {% for p in t.players %}
                                <span class="badge bg-light text-dark border">{{ p.name }}</span>
                            {% else %}
                                <span class="text-muted small">Klub nie zarejestrował jeszcze zawodników.</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="col-12"><p class="text-muted">Brak drużyn w systemie.</p></div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, teams=teams)
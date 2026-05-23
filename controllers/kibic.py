# controllers/kibic.py
from flask import Blueprint, render_template_string
from models import db, Team, Player, Match, Goal
from sqlalchemy import func
from controllers import NAV_HTML, FOOTER_HTML

kibic_bp = Blueprint('kibic_bp', __name__)


# ==========================================
# 1. STRONA: TABELA LIGI (Z KLIKALNYMI KLUBAMI)
# ==========================================
@kibic_bp.route('/tabela')
def tabela():
    teams = Team.query.all()
    matches = Match.query.filter_by(is_finished=True).all()

    # Słownik statystyk - dodaliśmy pole 'id', aby Jinja mogła wygenerować linki url_for
    stats = {t.id: {'id': t.id, 'name': t.name, 'pts': 0, 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0, 'gd': 0} for t in
             teams}

    for m in matches:
        stats[m.home_team_id]['gf'] += m.home_score
        stats[m.home_team_id]['ga'] += m.away_score
        stats[m.away_team_id]['gf'] += m.away_score
        stats[m.away_team_id]['ga'] += m.home_score

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

    for t_id in stats:
        stats[t_id]['gd'] = stats[t_id]['gf'] - stats[t_id]['ga']

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
                            <th class="text-start">Klub (Kliknij nazwę, by zobaczyć mecze)</th>
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
                            <td class="text-start">
                                <a href="{{ url_for('kibic_bp.szczegoly_klubu', team_id=s.id) }}" class="fw-bold text-primary text-decoration-none">{{ s.name }}</a>
                            </td>
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
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, table=sorted_stats)


# ==========================================
# 2. NOWA STRONA: MECZE I STRZELCY DANEJ DRUŻYNY
# ==========================================
@kibic_bp.route('/klub/<int:team_id>')
def szczegoly_klubu(team_id):
    team = Team.query.get_or_404(team_id)

    # Pobieramy wszystkie zakończone mecze, w których brała udział ta drużyna
    matches = Match.query.filter(
        Match.is_finished == True,
        ((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
    ).order_by(Match.id.desc()).all()

    teams_dict = {t.id: t.name for t in Team.query.all()}

    match_details = []
    for m in matches:
        goals = Goal.query.filter_by(match_id=m.id).all()

        home_scorers = []
        away_scorers = []

        for g in goals:
            player = Player.query.get(g.player_id)
            scorer_text = f"{player.name} ({g.goals}x)" if g.goals > 1 else player.name

            if g.is_own_goal:
                # Logika samobójów: dopisujemy tekst pechowca do kolumny przeciwników
                if player.team_id == m.home_team_id:
                    away_scorers.append(f"{player.name} (samobój ❌)")
                else:
                    home_scorers.append(f"{player.name} (samobój ❌)")
            else:
                if player.team_id == m.home_team_id:
                    home_scorers.append(scorer_text)
                else:
                    away_scorers.append(scorer_text)

        match_details.append({
            'match': m,
            'home_team': teams_dict[m.home_team_id],
            'away_team': teams_dict[m.away_team_id],
            'home_scorers': ", ".join(home_scorers),
            'away_scorers': ", ".join(away_scorers)
        })

    CONTENT_HTML = """
    <div>
        <h3 class="mb-3">Mecze i strzelcy drużyny: <span class="text-primary">{{ team.name }}</span></h3>
        <p class="text-muted mb-4">Wykaz wszystkich rozegranych spotkań oraz zawodników, którzy zdobywali bramki.</p>

        <div class="row">
            {% for md in details %}
            <div class="col-12 mb-3">
                <div class="card shadow-sm border-light">
                    <div class="card-body">
                        <div class="row align-items-center text-center">
                            <div class="col-md-4 fw-bold fs-5 text-primary">{{ md.home_team }}</div>
                            <div class="col-md-4 fs-3 fw-bold bg-light rounded py-2 shadow-sm">{{ md.match.home_score }} : {{ md.match.away_score }}</div>
                            <div class="col-md-4 fw-bold fs-5 text-danger">{{ md.away_team }}</div>
                        </div>
                        <hr class="my-2">
                        <div class="row small text-muted">
                            <div class="col-md-6 text-md-end border-end">
                                {% if md.home_scorers %}⚽ <b>Gole:</b> {{ md.home_scorers }}{% else %}<span class="text-black-50">Brak strzelców</span>{% endif %}
                            </div>
                            <div class="col-md-6 text-md-start">
                                {% if md.away_scorers %}⚽ <b>Gole:</b> {{ md.away_scorers }}{% else %}<span class="text-black-50">Brak strzelców</span>{% endif %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="col-12 text-center text-muted py-5 bg-white rounded shadow-sm">
                Ta drużyna nie rozegrała jeszcze żadnego meczu w tym sezonie.
            </div>
            {% endfor %}
        </div>

        <div class="text-center mt-4">
            <a href="{{ url_for('kibic_bp.tabela') }}" class="btn btn-outline-dark fw-bold px-5 shadow-sm">Powrót do Tabeli Ligi</a>
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, team=team, details=match_details)


# ==========================================
# 3. STRONA: KRÓL STRZELCÓW
# ==========================================
@kibic_bp.route('/strzelcy')
def strzelcy():
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
# 4. STRONA: KADRY KLUBÓW (ZMIENIONA NAZWA)
# ==========================================
@kibic_bp.route('/kadry')
def kadry_klubow():
    teams = Team.query.all()

    CONTENT_HTML = """
    <div>
        <h3 class="mb-4">Kadry Klubów 👥</h3>
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
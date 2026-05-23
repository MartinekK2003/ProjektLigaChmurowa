# controllers/sedzia.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Match, Team, Player, Goal
from controllers import NAV_HTML, FOOTER_HTML

sedzia_bp = Blueprint('sedzia_bp', __name__)


# ==========================================
# 1. STRONA: WPROWADZANIE WYNIKÓW
# ==========================================
@sedzia_bp.route('/sedzia/mecze', methods=['GET', 'POST'])
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

            # Jeśli w meczu padły gole, przekierowujemy do przypisania strzelców
            if match.home_score > 0 or match.away_score > 0:
                return redirect(url_for('sedzia_bp.sedzia_gole', match_id=match.id))

        return redirect(url_for('sedzia_bp.sedzia_mecze'))

    pending_matches = Match.query.filter_by(is_finished=False).all()

    # Słownik do podmiany ID na prawdziwe nazwy drużyn
    teams_dict = {t.id: t.name for t in Team.query.all()}

    CONTENT_HTML = """
    <div>
        <h3 class="text-warning mb-3">Wprowadzanie Wyników ⚖️</h3>
        <p class="text-muted mb-4">Podaj końcowy wynik spotkania. Jeśli padły bramki, system automatycznie poprosi Cię o wskazanie strzelców w następnym kroku.</p>
        <div class="row mt-3">
            {% for m in matches %}
            <div class="col-md-12 mb-3">
                <div class="card p-3 shadow-sm border-warning">
                    <form method="POST" class="d-flex align-items-center justify-content-between">
                        <input type="hidden" name="match_id" value="{{ m.id }}">

                        <div class="text-end fw-bold fs-5 text-primary" style="flex: 1;">{{ teams[m.home_team_id] }}</div>

                        <div class="d-flex align-items-center mx-4">
                            <input type="number" name="home_score" class="form-control text-center form-control-lg border-secondary" style="width:80px;" required min="0" placeholder="0">
                            <span class="fs-4 mx-2 fw-bold text-muted">:</span>
                            <input type="number" name="away_score" class="form-control text-center form-control-lg border-secondary" style="width:80px;" required min="0" placeholder="0">
                        </div>

                        <div class="text-start fw-bold fs-5 text-danger" style="flex: 1;">{{ teams[m.away_team_id] }}</div>

                        <button type="submit" class="btn btn-warning fw-bold px-4">Zapisz Wynik</button>
                    </form>
                </div>
            </div>
            {% else %} 
            <div class="col-12"><p class="text-muted text-center py-4 bg-white shadow-sm rounded">Brak zaplanowanych meczów do rozegrania. Administrator musi dodać nowe spotkania.</p></div> 
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, matches=pending_matches, teams=teams_dict)


# ==========================================
# 2. STRONA: PRZYPISYWANIE STRZELCÓW
# ==========================================
@sedzia_bp.route('/sedzia/gole/<int:match_id>', methods=['GET', 'POST'])
@login_required
def sedzia_gole(match_id):
    if current_user.role.name != 'referee':
        return "Brak uprawnień.", 403

    match = Match.query.get_or_404(match_id)

    if request.method == 'POST':
        player_id = request.form.get('player_id')
        goals_count = int(request.form.get('goals_count', 1))

        new_goal = Goal(match_id=match.id, player_id=player_id, goals=goals_count)
        db.session.add(new_goal)
        db.session.commit()
        return redirect(url_for('sedzia_bp.sedzia_gole', match_id=match.id))

    home_team = Team.query.get(match.home_team_id)
    away_team = Team.query.get(match.away_team_id)

    added_goals = Goal.query.filter_by(match_id=match.id).all()
    players_dict = {p.id: p.name for p in Player.query.all()}

    # Liczymy, ile goli już przypisano w systemie, aby sędzia wiedział, kiedy skończyć
    total_assigned_goals = sum(g.goals for g in added_goals)
    total_match_goals = match.home_score + match.away_score

    CONTENT_HTML = """
    <div>
        <h3 class="text-warning mb-3">Strzelcy Bramek ⚽</h3>
        <div class="alert alert-info shadow-sm fs-5">
            Mecz: <strong class="text-primary">{{ home_team.name }}</strong> <strong>{{ match.home_score }} : {{ match.away_score }}</strong> <strong class="text-danger">{{ away_team.name }}</strong>
            <hr>
            Przypisano bramek: <strong>{{ assigned_goals }} / {{ match_goals }}</strong>
        </div>

        {% if assigned_goals < match_goals %}
        <div class="card shadow-sm mb-4 border-warning">
            <div class="card-header bg-warning text-dark fw-bold">Dodaj strzelca</div>
            <div class="card-body bg-light">
                <form method="POST" class="row g-3 align-items-end">
                    <div class="col-md-7">
                        <label class="form-label fw-bold">Wybierz zawodnika</label>
                        <select name="player_id" class="form-select" required>
                            <option value="" disabled selected>-- Wybierz strzelca --</option>
                            <optgroup label="{{ home_team.name }} (Gospodarze)">
                                {% for p in home_team.players %}
                                    <option value="{{ p.id }}">{{ p.name }}</option>
                                {% endfor %}
                            </optgroup>
                            <optgroup label="{{ away_team.name }} (Goście)">
                                {% for p in away_team.players %}
                                    <option value="{{ p.id }}">{{ p.name }}</option>
                                {% endfor %}
                            </optgroup>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">Liczba goli</label>
                        <input type="number" name="goals_count" class="form-control" value="1" min="1" max="{{ match_goals - assigned_goals }}" required>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-success w-100 fw-bold">Zapisz</button>
                    </div>
                </form>
            </div>
        </div>
        {% else %}
        <div class="alert alert-success shadow-sm fw-bold">
            Wszystkie bramki z tego meczu zostały już przypisane do strzelców!
        </div>
        {% endif %}

        <h5 class="mb-3">Zapisani strzelcy w tym meczu:</h5>
        <ul class="list-group shadow-sm mb-4">
            {% for g in added_goals %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span class="fs-5">{{ players_dict[g.player_id] }}</span>
                <span class="badge bg-primary rounded-pill fs-6">{{ g.goals }} ⚽</span>
            </li>
            {% else %}
            <li class="list-group-item text-muted">Jeszcze nie przypisano żadnego strzelca.</li>
            {% endfor %}
        </ul>

        <a href="{{ url_for('sedzia_bp.sedzia_mecze') }}" class="btn btn-outline-dark fw-bold px-4">Zakończ i wróć do meczów</a>
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  match=match, home_team=home_team, away_team=away_team,
                                  added_goals=added_goals, players_dict=players_dict,
                                  assigned_goals=total_assigned_goals, match_goals=total_match_goals)
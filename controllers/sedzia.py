# controllers/sedzia.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Match, Team, Player, Goal
from controllers import NAV_HTML, FOOTER_HTML

sedzia_bp = Blueprint('sedzia_bp', __name__)


# ==========================================
# 1. STRONA: WPROWADZANIE WYNIKÓW MECZÓW
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
            home_score = int(request.form.get('home_score'))
            away_score = int(request.form.get('away_score'))

            match.home_score = home_score
            match.away_score = away_score
            match.is_finished = True
            db.session.commit()

            # JEŻELI WYNIK TO 0-0 -> Mecz kończy się od razu (nie ma strzelców)
            if home_score == 0 and away_score == 0:
                return redirect(url_for('sedzia_bp.sedzia_mecze'))

            # JEŻELI PADŁY JAKIEKOLWIEK GOLE -> Sędzia MUSI rozpisać strzelców
            return redirect(url_for('sedzia_bp.sedzia_gole', match_id=match.id))

    pending_matches = Match.query.filter_by(is_finished=False).all()
    teams_dict = {t.id: t.name for t in Team.query.all()}

    CONTENT_HTML = """
    <div>
        <h3 class="text-warning mb-3">Wprowadzanie Wyników ⚖️</h3>
        <p class="text-muted mb-4">Wpisz końcowy wynik. Jeśli wynik jest inny niż 0:0, zostaniesz automatycznie poproszony o wskazanie strzelców (w tym samobójów).</p>
        <div class="row mt-3">
            {% for m in matches %}
            <div class="col-md-12 mb-3">
                <div class="card p-3 shadow-sm border-warning">
                    <form method="POST" class="d-flex align-items-center justify-content-between">
                        <input type="hidden" name="match_id" value="{{ m.id }}">

                        <div class="text-end fw-bold fs-5 text-primary" style="flex: 1;">{{ teams[m.home_team_id] }}</div>

                        <div class="d-flex align-items-center mx-4">
                            <input type="number" name="home_score" class="form-control text-center form-control-lg border-secondary" style="width:80px;" Tensor required min="0" placeholder="0">
                            <span class="fs-4 mx-2 fw-bold text-muted">:</span>
                            <input type="number" name="away_score" class="form-control text-center form-control-lg border-secondary" style="width:80px;" required min="0" placeholder="0">
                        </div>

                        <div class="text-start fw-bold fs-5 text-danger" style="flex: 1;">{{ teams[m.away_team_id] }}</div>

                        <button type="submit" class="btn btn-warning fw-bold px-4">Zapisz Wynik</button>
                    </form>
                </div>
            </div>
            {% else %} 
            <div class="col-12"><p class="text-muted text-center py-4 bg-white shadow-sm rounded">Brak meczów do rozegrania.</p></div> 
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, matches=pending_matches, teams=teams_dict)


# ==========================================
# 2. STRONA: PRZYPISYWANIE STRZELCÓW I SAMOBÓJÓW
# ==========================================
@sedzia_bp.route('/sedzia/gole/<int:match_id>', methods=['GET', 'POST'])
@login_required
def sedzia_gole(match_id):
    if current_user.role.name != 'referee':
        return "Brak uprawnień.", 403

    match = Match.query.get_or_404(match_id)
    home_team = Team.query.get(match.home_team_id)
    away_team = Team.query.get(match.away_team_id)

    error_msg = None

    # Obliczanie aktualnie przypisanych goli z uwzględnieniem logiki samobójów
    added_goals = Goal.query.filter_by(match_id=match.id).all()

    assigned_home = 0
    assigned_away = 0

    for g in added_goals:
        player = Player.query.get(g.player_id)
        if player.team_id == match.home_team_id:
            if g.is_own_goal:
                assigned_away += g.goals  # Samobój gospodarza daje punkt gościom
            else:
                assigned_home += g.goals  # Normalny gol gospodarza
        elif player.team_id == match.away_team_id:
            if g.is_own_goal:
                assigned_home += g.goals  # Samobój gościa daje punkt gospodarzom
            else:
                assigned_away += g.goals  # Normalny gol gościa

    if request.method == 'POST':
        player_id = request.form.get('player_id')
        goals_count = int(request.form.get('goals_count', 1))
        goal_type = request.form.get('goal_type')  # 'normal' lub 'own'

        chosen_player = Player.query.get(player_id)
        is_own = (goal_type == 'own')

        # Walidacja limitów bramek
        if is_own:
            # Ktoś strzelił samobója
            if chosen_player.team_id == match.home_team_id:
                # Gospodarz strzelił samobója -> sprawdź czy nie przekracza wyniku Gości
                if assigned_away + goals_count > match.away_score:
                    error_msg = f"Błąd! Goście mają wpisane tylko {match.away_score} bramek. Nie możesz przypisać tylu samobójów."
            else:
                # Gość strzelił samobója -> sprawdź czy nie przekracza wyniku Gospodarzy
                if assigned_home + goals_count > match.home_score:
                    error_msg = f"Błąd! Gospodarze mają wpisane tylko {match.home_score} bramek."
        else:
            # Klasyczny gol
            if chosen_player.team_id == match.home_team_id:
                if assigned_home + goals_count > match.home_score:
                    error_msg = f"Błąd! Gospodarze strzelili w meczu tylko {match.home_score} goli."
            else:
                if assigned_away + goals_count > match.away_score:
                    error_msg = f"Błąd! Goście strzelili w meczu tylko {match.away_score} goli."

        if not error_msg:
            new_goal = Goal(match_id=match.id, player_id=player_id, goals=goals_count, is_own_goal=is_own)
            db.session.add(new_goal)
            db.session.commit()
            return redirect(url_for('sedzia_bp.sedzia_gole', match_id=match.id))

    players_dict = {p.id: p.name for p in Player.query.all()}

    # Czy wszystkie bramki zostały rozliczone?
    all_done = (assigned_home == match.home_score and assigned_away == match.away_score)

    CONTENT_HTML = """
    <div>
        <h3 class="text-warning mb-3">Rozliczanie bramek meczu ⚽</h3>

        <div class="card bg-dark text-white p-4 text-center mb-4 shadow-sm">
            <span class="fs-5 text-muted">OFICJALNY WYNIK</span>
            <h1 class="display-4 my-2">
                <span class="text-primary">{{ home_team.name }}</span> 
                {{ match.home_score }} : {{ match.away_score }} 
                <span class="text-danger">{{ away_team.name }}</span>
            </h1>
            <div class="d-flex justify-content-center gap-5 mt-2">
                <span class="fs-5">Rozpisane bramki Gospodarzy: <b>{{ assigned_home }} / {{ match.home_score }}</b></span>
                <span class="fs-5">Rozpisane bramki Gości: <b>{{ assigned_away }} / {{ match.away_score }}</b></span>
            </div>
        </div>

        {% if error_msg %}
            <div class="alert alert-danger shadow-sm fw-bold">{{ error_msg }}</div>
        {% endif %}

        {% if not all_done %}
        <div class="card shadow-sm mb-4 border-warning">
            <div class="card-header bg-warning text-dark fw-bold">Wprowadź zdarzenie meczowe</div>
            <div class="card-body bg-light">
                <form method="POST" class="row g-3 align-items-end">
                    <div class="col-md-5">
                        <label class="form-label fw-bold">Zawodnik</label>
                        <select name="player_id" class="form-select" required>
                            <option value="" disabled selected>-- Wybierz piłkarza --</option>
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
                    <div class="col-md-4">
                        <label class="form-label fw-bold">Typ bramki</label>
                        <select name="goal_type" class="form-select" required>
                            <option value="normal" selected>Klasyczny gol (Dla swojej drużyny)</option>
                            <option value="own">Gol samobójczy ❌ (Dla przeciwnika)</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label fw-bold">Ile bramek</label>
                        <input type="number" name="goals_count" class="form-control" value="1" min="1" required>
                    </div>
                    <div class="col-md-1">
                        <button type="submit" class="btn btn-success w-100 fw-bold">Dodaj</button>
                    </div>
                </form>
            </div>
        </div>
        {% else %}
        <div class="alert alert-success shadow-sm fw-bold fs-5 text-center">
            🎉 Wszystkie zdobyte bramki zostały poprawnie rozliczone w systemie!
        </div>
        {% endif %}

        <h5 class="mb-3">Zarejestrowane trafienia:</h5>
        <ul class="list-group shadow-sm mb-4">
            {% for g in added_goals %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span class="fs-5">
                    <strong>{{ players_dict[g.player_id] }}</strong>
                    {% if g.is_own_goal %}
                        <span class="text-danger fw-bold ms-2">(GOL SAMOBÓJCZY ❌)</span>
                    {% endif %}
                </span>
                <span class="badge {% if g.is_own_goal %}bg-danger{% else %}bg-primary{% endif %} rounded-pill fs-6">{{ g.goals }} ⚽</span>
            </li>
            {% else %}
            <li class="list-group-item text-muted text-center py-3">Brak wpisanych zdarzeń.</li>
            {% endfor %}
        </ul>

        <div class="text-center">
            <a href="{{ url_for('sedzia_bp.sedzia_mecze') }}" class="btn btn-outline-dark fw-bold px-5 {% if not all_done %}disabled{% endif %}">
                {% if all_done %}Zakończ i wróć do meczów{% else %}Musisz rozpisać wszystkie bramki, aby wyjść{% endif %}
            </a>
        </div>
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  match=match, home_team=home_team, away_team=away_team,
                                  added_goals=added_goals, players_dict=players_dict,
                                  assigned_home=assigned_home, assigned_away=assigned_away,
                                  all_done=all_done, error_msg=error_msg)
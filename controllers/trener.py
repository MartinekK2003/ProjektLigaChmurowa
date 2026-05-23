# controllers/trener.py
from flask import Blueprint, render_template_string, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_
from models import db, Team, Player, Goal, Match
from controllers import NAV_HTML, FOOTER_HTML

trener_bp = Blueprint('trener_bp', __name__)


# ==========================================
# 1. STRONA: ZARZĄDZANIE SKŁADEM
# ==========================================
@trener_bp.route('/trener/sklad', methods=['GET', 'POST'])
@login_required
def trener_sklad():
    if current_user.role.name != 'coach':
        return "Brak uprawnień. Zaloguj się jako trener.", 403

    if not current_user.team_id:
        return "Nie przypisano Cię do żadnej drużyny!", 400

    if request.method == 'POST':
        action = request.form.get('action')
        # Dodawanie zawodnika
        if action == 'add':
            new_player = Player(name=request.form.get('player_name'), team_id=current_user.team_id)
            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('trener_bp.trener_sklad'))

        # Usuwanie zawodnika
        elif action == 'delete':
            player = Player.query.get(request.form.get('player_id'))
            if player and player.team_id == current_user.team_id:
                db.session.delete(player)
                db.session.commit()
            return redirect(url_for('trener_bp.trener_sklad'))

    my_team = Team.query.get(current_user.team_id)

    CONTENT_HTML = """
    <div>
        <h3 class="mb-3">Skład drużyny: <span class="text-success">{{ team.name }}</span></h3>
        <p class="text-muted mb-4">Tutaj możesz dodawać nowych zawodników do swojej kadry lub zwalniać obecnych.</p>

        <form method="POST" class="d-flex gap-2 mb-4">
            <input type="hidden" name="action" value="add">
            <input type="text" name="player_name" class="form-control" placeholder="Imię i nazwisko zawodnika" required>
            <button type="submit" class="btn btn-success fw-bold px-4">Dodaj</button>
        </form>

        <ul class="list-group shadow-sm">
            {% for p in team.players %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span><strong>{{ loop.index }}.</strong> {{ p.name }}</span>
                <form method="POST" class="m-0">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="player_id" value="{{ p.id }}">
                    <button type="submit" class="btn btn-sm btn-danger">Zwolnij</button>
                </form>
            </li>
            {% else %}
            <li class="list-group-item text-muted text-center py-4">Brak zawodników w kadrze.</li>
            {% endfor %}
        </ul>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, team=my_team)


# ==========================================
# 2. STRONA: ANALIZA RYWALA (ZMODYFIKOWANA)
# ==========================================
@trener_bp.route('/trener/analiza', methods=['GET', 'POST'])
@login_required
def trener_analiza():
    if current_user.role.name != 'coach':
        return "Brak uprawnień. Zaloguj się jako trener.", 403

    if not current_user.team_id:
        return "Nie przypisano Cię do żadnej drużyny!", 400

    best_player_name = None
    best_player_team = None
    max_goals = 0
    searched_team = None
    error_msg = None

    if request.method == 'POST':
        team_name = request.form.get('team_name')
        searched_team = Team.query.filter(Team.name.ilike(f"%{team_name}%")).first()

        if not searched_team:
            error_msg = f"Nie znaleziono drużyny o nazwie '{team_name}'."
        else:
            # ZAAWANSOWANE ZAPYTANIE: Szukamy w CAŁEJ bazie zawodnika, który strzelił najwięcej goli wybranemu klubowi
            result = db.session.query(
                Player.name.label('player_name'),
                Team.name.label('team_name'),
                func.sum(Goal.goals).label('total_goals')
            ).join(Goal, Goal.player_id == Player.id) \
                .join(Match, Match.id == Goal.match_id) \
                .join(Team, Team.id == Player.team_id) \
                .filter(Goal.is_own_goal == False) \
                .filter(or_(
                and_(Match.home_team_id == searched_team.id, Player.team_id == Match.away_team_id),
                and_(Match.away_team_id == searched_team.id, Player.team_id == Match.home_team_id)
            )) \
                .group_by(Player.id, Team.id) \
                .order_by(func.sum(Goal.goals).desc()) \
                .first()

            if result:
                best_player_name = result.player_name
                best_player_team = result.team_name
                max_goals = result.total_goals
            else:
                error_msg = f"Nikt w całej lidze nie strzelił jeszcze bramki przeciwko: {searched_team.name}."

    CONTENT_HTML = """
    <div>
        <h3 class="mb-3">Analiza Rywala 🔍</h3>
        <p class="text-muted mb-4">Wpisz nazwę dowolnego klubu, aby dowiedzieć się, który zawodnik ze <b>wszystkich drużyn w lidze</b> nastrzelał mu najwięcej bramek.</p>

        <form method="POST" class="d-flex gap-2 mb-4">
            <input type="text" name="team_name" class="form-control" placeholder="Wpisz nazwę klubu (np. KS Flask)" required>
            <button type="submit" class="btn btn-info text-white fw-bold px-4">Szukaj</button>
        </form>

        {% if error_msg %}
            <div class="alert alert-warning shadow-sm">{{ error_msg }}</div>
        {% endif %}

        {% if best_player_name %}
            <div class="card border-info shadow-sm mt-4" style="max-width: 500px; margin: 0 auto;">
                <div class="card-header bg-info text-white text-center fw-bold">
                    Największy koszmar klubu: {{ searched_team.name }} 💥
                </div>
                <div class="card-body text-center bg-light">
                    <h5 class="card-title text-muted">Zawodnik z największą liczbą goli:</h5>
                    <h2 class="text-info font-weight-bold my-2">{{ best_player_name }}</h2>
                    <p class="badge bg-secondary text-uppercase mb-3" style="font-size: 0.9rem;">Klub: {{ best_player_team }}</p>
                    <hr style="max-width: 150px; margin: 10px auto;">
                    <h1 class="display-4 text-dark mb-0 fw-bold">{{ max_goals }} ⚽</h1>
                    <p class="text-muted small mt-1 mb-0">Tyle bramek im wbił</p>
                </div>
            </div>
        {% endif %}
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  error_msg=error_msg,
                                  best_player_name=best_player_name,
                                  best_player_team=best_player_team,
                                  max_goals=max_goals,
                                  searched_team=searched_team)
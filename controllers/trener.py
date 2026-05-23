# controllers/trener.py
from flask import Blueprint, render_template_string, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from models import db, Team, Player, Goal, Match
from controllers import NAV_HTML, FOOTER_HTML

trener_bp = Blueprint('trener_bp', __name__)


@trener_bp.route('/trener/sklad', methods=['GET', 'POST'])
@login_required
def trener_sklad():
    if current_user.role.name != 'coach':
        return "Brak uprawnień. Zaloguj się jako trener.", 403

    if not current_user.team_id:
        return "Nie przypisano Cię do żadnej drużyny!", 400

    my_team = Team.query.get(current_user.team_id)

    # Zmienne dla analizy rywala
    best_player_name = None
    max_goals = 0
    searched_team = None
    error_msg = None

    if request.method == 'POST':
        action = request.form.get('action')

        # AKCJA: DODANIE ZAWODNIKA
        if action == 'add':
            new_player = Player(name=request.form.get('player_name'), team_id=current_user.team_id)
            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('trener_bp.trener_sklad'))

        # AKCJA: USUNIĘCIE ZAWODNIKA
        elif action == 'delete':
            player = Player.query.get(request.form.get('player_id'))
            if player and player.team_id == current_user.team_id:
                db.session.delete(player)
                db.session.commit()
            return redirect(url_for('trener_bp.trener_sklad'))

        # AKCJA: ANALIZA RYWALA
        elif action == 'analyze':
            team_name = request.form.get('team_name')
            searched_team = Team.query.filter(Team.name.ilike(f"%{team_name}%")).first()

            if not searched_team:
                error_msg = f"Nie znaleziono drużyny o nazwie '{team_name}'."
            elif searched_team.id == current_user.team_id:
                error_msg = "Próbujesz analizować własną drużynę! Wybierz przeciwnika."
            else:
                result = db.session.query(
                    Player.name, func.sum(Goal.goals).label('total_goals')
                ).join(Goal, Goal.player_id == Player.id) \
                    .join(Match, Match.id == Goal.match_id) \
                    .filter(Player.team_id == current_user.team_id) \
                    .filter(or_(Match.home_team_id == searched_team.id, Match.away_team_id == searched_team.id)) \
                    .group_by(Player.id) \
                    .order_by(func.sum(Goal.goals).desc()) \
                    .first()

                if result:
                    best_player_name = result.name
                    max_goals = result.total_goals
                else:
                    error_msg = f"Twoja drużyna nie strzeliła jeszcze ani jednego gola drużynie {searched_team.name} (lub nie graliście ze sobą)."

    # POŁĄCZONY WIDOK HTML (Dwie kolumny obok siebie)
    CONTENT_HTML = """
    <div class="container mt-4">
        <div class="row">

            <div class="col-md-6 border-end pe-4">
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
                    {% else %}
                    <li class="list-group-item text-muted">Brak zawodników w drużynie.</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="col-md-6 ps-4">
                <h3>Analiza Rywala</h3>
                <p class="text-muted">Sprawdź, który z Twoich zawodników radzi sobie najlepiej przeciwko wybranej drużynie.</p>

                <form method="POST" class="d-flex gap-2 mt-3 mb-4">
                    <input type="hidden" name="action" value="analyze">
                    <input type="text" name="team_name" class="form-control" placeholder="Wpisz nazwę klubu rywala (np. KS Flask)" required>
                    <button type="submit" class="btn btn-primary">Szukaj</button>
                </form>

                {% if error_msg %}
                    <div class="alert alert-warning">{{ error_msg }}</div>
                {% endif %}

                {% if best_player_name %}
                    <div class="card mt-3">
                        <div class="card-header bg-dark text-white">
                            Wynik analizy przeciwko: <strong>{{ searched_team.name }}</strong>
                        </div>
                        <div class="card-body text-center">
                            <h5 class="card-title">Najlepszy strzelec: <span class="text-success">{{ best_player_name }}</span></h5>
                            <p class="card-text h1">{{ max_goals }} ⚽</p>
                            <p class="text-muted">Liczba strzelonych bramek</p>
                        </div>
                    </div>
                {% endif %}
            </div>

        </div>
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  team=my_team,
                                  error_msg=error_msg,
                                  best_player_name=best_player_name,
                                  max_goals=max_goals,
                                  searched_team=searched_team)
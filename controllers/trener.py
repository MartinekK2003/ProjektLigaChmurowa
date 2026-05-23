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

    # Zmienne pomocnicze dla analizy rywala
    best_player_name = None
    max_goals = 0
    searched_team = None
    error_msg = None

    # Domyślnie aktywna zakładka to 'squad' (skład)
    active_tab = 'squad'

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
            # Skoro kliknięto analizę, po przeładowaniu chcemy otworzyć zakładkę 'analyze'
            active_tab = 'analyze'

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
                    error_msg = f"Twoja drużyna nie strzeliła jeszcze ani jednego gola drużynie {searched_team.name}."

    # WIDOK HTML Z ZAKŁADKAMI (TABAMI) OBOK SIEBIE
    CONTENT_HTML = """
    <div class="container mt-4">
        <div class="card shadow-sm">
            <div class="card-header bg-light">
                <ul class="nav nav-tabs card-header-tabs" id="trenerTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if active_tab == 'squad' %}active font-weight-bold{% endif %}" 
                                id="squad-tab" data-bs-toggle="tab" data-bs-target="#squad-panel" 
                                type="button" role="tab" aria-controls="squad-panel" aria-selected="true">
                            📋 Zarządzaj składem
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if active_tab == 'analyze' %}active font-weight-bold{% endif %}" 
                                id="analyze-tab" data-bs-toggle="tab" data-bs-target="#analyze-panel" 
                                type="button" role="tab" aria-controls="analyze-panel" aria-selected="false">
                            📊 Analiza rywala
                        </button>
                    </li>
                </ul>
            </div>

            <div class="card-body">
                <div class="tab-content" id="trenerTabsContent">

                    <div class="tab-pane fade {% if active_tab == 'squad' %}show active{% endif %}" id="squad-panel" role="tabpanel" aria-labelledby="squad-tab">
                        <h4 class="card-title mt-2">Skład Twojej drużyny: <span class="text-primary">{{ team.name }}</span></h4>
                        <p class="text-muted small">Tutaj możesz dodawać nowych zawodników lub zwalniać obecnych.</p>

                        <form method="POST" class="d-flex gap-2 mt-3 mb-4">
                            <input type="hidden" name="action" value="add">
                            <input type="text" name="player_name" class="form-control" placeholder="Imię i nazwisko nowego zawodnika" required>
                            <button type="submit" class="btn btn-success px-4">Dodaj</button>
                        </form>

                        <ul class="list-group">
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
                            <li class="list-group-item text-muted text-center py-3">Brak zawodników w kadrze. Dodaj pierwszego piłkarza powyżej!</li>
                            {% endfor %}
                        </ul>
                    </div>

                    <div class="tab-pane fade {% if active_tab == 'analyze' %}show active{% endif %}" id="analyze-panel" role="tabpanel" aria-labelledby="analyze-tab">
                        <h4 class="card-title mt-2">Panel Analizy Przeciwnika</h4>
                        <p class="text-muted small">Wpisz nazwę klubu, aby sprawdzić, który z Twoich podopiecznych strzelił mu najwięcej bramek.</p>

                        <form method="POST" class="d-flex gap-2 mt-3 mb-4">
                            <input type="hidden" name="action" value="analyze">
                            <input type="text" name="team_name" class="form-control" placeholder="Wpisz nazwę klubu rywala (np. KS Flask)" required>
                            <button type="submit" class="btn btn-primary px-4">Szukaj</button>
                        </form>

                        {% if error_msg %}
                            <div class="alert alert-warning mt-3">{{ error_msg }}</div>
                        {% endif %}

                        {% if best_player_name %}
                            <div class="card mt-3 border-success">
                                <div class="card-header bg-success text-white">
                                    Statystyki przeciwko klubowi: <strong>{{ searched_team.name }}</strong>
                                </div>
                                <div class="card-body text-center bg-light">
                                    <h5 class="card-title">Najskuteczniejszy zawodnik:</h5>
                                    <h2 class="text-success font-weight-bold">{{ best_player_name }}</h2>
                                    <hr style="max-width: 200px; margin: 10px auto;">
                                    <p class="card-text h1 mb-0">{{ max_goals }} ⚽</p>
                                    <p class="text-muted small">Łączna liczba strzelonych bramek</p>
                                </div>
                            </div>
                        {% endif %}
                    </div>

                </div>
            </div>
        </div>
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  team=my_team,
                                  active_tab=active_tab,
                                  error_msg=error_msg,
                                  best_player_name=best_player_name,
                                  max_goals=max_goals,
                                  searched_team=searched_team)
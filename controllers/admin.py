# controllers/admin.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Team, Match, Season
from controllers import NAV_HTML, FOOTER_HTML

admin_bp = Blueprint('admin_bp', __name__)


# ==========================================
# 1. STRONA: ZARZĄDZANIE DRUŻYNAMI
# ==========================================
@admin_bp.route('/admin/druzyny', methods=['GET', 'POST'])
@login_required
def admin_druzyny():
    if current_user.role.name != 'admin':
        return "Brak uprawnień. Zaloguj się jako administrator.", 403

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_team = Team(name=request.form.get('team_name'))
            db.session.add(new_team)
            db.session.commit()
        elif action == 'delete':
            team = Team.query.get(request.form.get('team_id'))
            if team:
                db.session.delete(team)
                db.session.commit()
        return redirect(url_for('admin_bp.admin_druzyny'))

    teams = Team.query.all()

    CONTENT_HTML = """
    <div>
        <h3 class="text-danger mb-3">Panel Administracyjny: Drużyny 🛡️</h3>
        <p class="text-muted mb-4">Dodawaj nowe kluby do ligi lub usuwaj te, które z niej spadły.</p>

        <form method="POST" class="d-flex gap-2 mb-4">
            <input type="hidden" name="action" value="add">
            <input type="text" name="team_name" class="form-control" placeholder="Nazwa nowego klubu" required>
            <button type="submit" class="btn btn-danger fw-bold px-4">Dodaj drużynę</button>
        </form>

        <div class="card shadow-sm">
            <table class="table table-hover mb-0">
                <thead class="table-dark">
                    <tr>
                        <th class="ps-3">ID</th>
                        <th>Nazwa Klubu</th>
                        <th class="text-end pe-3">Akcje</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in teams %}
                    <tr>
                        <td class="ps-3">{{ t.id }}</td>
                        <td><b>{{ t.name }}</b></td>
                        <td class="text-end pe-3">
                            <form method="POST" class="m-0">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="team_id" value="{{ t.id }}">
                                <button type="submit" class="btn btn-sm btn-outline-danger">Usuń Klub</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, teams=teams)


# ==========================================
# 2. STRONA: PLANOWANIE MECZÓW
# ==========================================
@admin_bp.route('/admin/zaplanuj-mecz', methods=['GET', 'POST'])
@login_required
def admin_zaplanuj_mecz():
    if current_user.role.name != 'admin':
        return "Brak uprawnień. Zaloguj się jako administrator.", 403

    error_msg = None
    success_msg = None

    if request.method == 'POST':
        season_id = request.form.get('season_id')
        home_team_id = request.form.get('home_team_id')
        away_team_id = request.form.get('away_team_id')

        if home_team_id == away_team_id:
            error_msg = "Błąd! Drużyna gospodarzy i gości musi być inna."
        else:
            # Tworzymy nowy mecz z domyślnym wynikiem 0:0 i statusem nierozegranym
            new_match = Match(
                season_id=season_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_score=0,
                away_score=0,
                is_finished=False
            )
            db.session.add(new_match)
            db.session.commit()
            success_msg = "Mecz został pomyślnie zapisany w terminarzu!"

    # Pobieramy dane do formularza
    teams = Team.query.all()
    seasons = Season.query.all()

    # Pobieramy listę ostatnich meczów dla podglądu, a także tworzymy słownik ułatwiający wyświetlanie nazw
    recent_matches = Match.query.order_by(Match.id.desc()).limit(5).all()
    team_dict = {t.id: t.name for t in teams}
    season_dict = {s.id: s.name for s in seasons}

    CONTENT_HTML = """
    <div>
        <h3 class="text-danger mb-3">Planowanie Terminarza 📅</h3>
        <p class="text-muted mb-4">Wybierz sezon oraz drużyny, aby zaplanować nowe spotkanie w lidze.</p>

        {% if error_msg %}
            <div class="alert alert-warning shadow-sm fw-bold">{{ error_msg }}</div>
        {% endif %}
        {% if success_msg %}
            <div class="alert alert-success shadow-sm fw-bold">{{ success_msg }}</div>
        {% endif %}

        <div class="card shadow-sm mb-5">
            <div class="card-header bg-danger text-white fw-bold">Nowy Mecz</div>
            <div class="card-body bg-light">
                <form method="POST">
                    <div class="row g-3">
                        <div class="col-md-12">
                            <label class="form-label fw-bold">Sezon</label>
                            <select name="season_id" class="form-select" required>
                                {% for s in seasons %}
                                    <option value="{{ s.id }}">{{ s.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-5">
                            <label class="form-label fw-bold">Gospodarz</label>
                            <select name="home_team_id" class="form-select" required>
                                <option value="" disabled selected>Wybierz drużynę...</option>
                                {% for t in teams %}
                                    <option value="{{ t.id }}">{{ t.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end justify-content-center">
                            <span class="fs-4 fw-bold pb-1">VS</span>
                        </div>
                        <div class="col-md-5">
                            <label class="form-label fw-bold">Gość</label>
                            <select name="away_team_id" class="form-select" required>
                                <option value="" disabled selected>Wybierz drużynę...</option>
                                {% for t in teams %}
                                    <option value="{{ t.id }}">{{ t.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-12 mt-4 text-center">
                            <button type="submit" class="btn btn-danger fw-bold px-5">Zapisz Mecz w Bazie</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <h5 class="mb-3">Ostatnio dodane mecze:</h5>
        <ul class="list-group shadow-sm">
            {% for m in recent_matches %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>
                    <span class="badge bg-secondary me-2">{{ season_dict[m.season_id] }}</span>
                    <strong>{{ team_dict[m.home_team_id] }}</strong> vs <strong>{{ team_dict[m.away_team_id] }}</strong>
                </span>
                {% if m.is_finished %}
                    <span class="badge bg-success">Zakończony ({{ m.home_score }}:{{ m.away_score }})</span>
                {% else %}
                    <span class="badge bg-warning text-dark">Oczekuje</span>
                {% endif %}
            </li>
            {% else %}
            <li class="list-group-item text-muted">Brak zaplanowanych meczów.</li>
            {% endfor %}
        </ul>
    </div>
    """

    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML,
                                  teams=teams, seasons=seasons,
                                  recent_matches=recent_matches,
                                  team_dict=team_dict, season_dict=season_dict)
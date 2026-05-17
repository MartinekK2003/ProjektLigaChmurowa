# controllers/admin.py
from flask import Blueprint, render_template_string, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Team
from controllers import NAV_HTML, FOOTER_HTML

admin_bp = Blueprint('admin_bp', __name__)

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
    <h3 class="text-danger">Panel Administracyjny: Drużyny</h3>
    <form method="POST" class="d-flex gap-2 mt-3 mb-4">
        <input type="hidden" name="action" value="add">
        <input type="text" name="team_name" class="form-control" placeholder="Nazwa nowego klubu" required>
        <button type="submit" class="btn btn-danger">Dodaj drużynę</button>
    </form>
    <table class="table table-bordered">
        <thead class="table-dark"><tr><th>ID</th><th>Nazwa Klubu</th><th>Akcje</th></tr></thead>
        <tbody>
            {% for t in teams %}
            <tr>
                <td>{{ t.id }}</td><td><b>{{ t.name }}</b></td>
                <td>
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
    """
    return render_template_string(NAV_HTML + CONTENT_HTML + FOOTER_HTML, teams=teams)
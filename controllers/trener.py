# controllers/trener.py
from flask import Blueprint, render_template_string, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Team, Player
from controllers import DASHBOARD_HTML

trener_bp = Blueprint('trener_bp', __name__)

@trener_bp.route('/trener/sklad', methods=['GET', 'POST'])
@login_required
def trener_sklad():
    if current_user.role.name != 'coach':
        return "Brak uprawnień. Zaloguj się jako trener.", 403

    if not current_user.team_id:
        return "Nie przypisano Cię do żadnej drużyny!", 400

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_player = Player(name=request.form.get('player_name'), team_id=current_user.team_id)
            db.session.add(new_player)
            db.session.commit()
        elif action == 'delete':
            player = Player.query.get(request.form.get('player_id'))
            if player and player.team_id == current_user.team_id:
                db.session.delete(player)
                db.session.commit()
        return redirect(url_for('trener_bp.trener_sklad'))

    my_team = Team.query.get(current_user.team_id)

    html = "{% extends 'dashboard' %}{% block content %}" + """
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
        {% endfor %}
    </ul>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), team=my_team)
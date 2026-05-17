# controllers/sedzia.py
from flask import Blueprint, render_template_string, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Match
from controllers import DASHBOARD_HTML

sedzia_bp = Blueprint('sedzia_bp', __name__)

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
        return redirect(url_for('sedzia_bp.sedzia_mecze'))

    pending_matches = Match.query.filter_by(is_finished=False).all()

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Wprowadzanie Wyników</h3>
    <div class="row mt-3">
        {% for m in matches %}
        <div class="col-md-6 mb-3">
            <div class="card p-3 bg-light">
                <form method="POST" class="d-flex align-items-center justify-content-between">
                    <input type="hidden" name="match_id" value="{{ m.id }}">
                    <span class="fw-bold">{{ m.home_team_id }} (Gospodarz)</span>
                    <input type="number" name="home_score" class="form-control text-center mx-2" style="width:70px;" required min="0">
                    <span> - </span>
                    <input type="number" name="away_score" class="form-control text-center mx-2" style="width:70px;" required min="0">
                    <span class="fw-bold">{{ m.away_team_id }} (Gość)</span>
                    <button type="submit" class="btn btn-warning btn-sm ms-2">Zapisz</button>
                </form>
            </div>
        </div>
        {% else %} <p class="text-muted">Brak zaplanowanych meczów do rozegrania.</p> {% endfor %}
    </div>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), matches=pending_matches)
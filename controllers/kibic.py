# controllers/kibic.py
from flask import Blueprint, render_template_string
from flask_login import login_required
from sqlalchemy import func
from models import db, Team, Match, Player, Goal
from controllers import DASHBOARD_HTML

kibic_bp = Blueprint('kibic_bp', __name__)

@kibic_bp.route('/tabela')
@login_required
def tabela():
    teams = Team.query.all()
    matches = Match.query.filter_by(is_finished=True).all()

    stats = {t.id: {'name': t.name, 'points': 0, 'goals_scored': 0, 'goals_lost': 0} for t in teams}

    for m in matches:
        stats[m.home_team_id]['goals_scored'] += m.home_score
        stats[m.home_team_id]['goals_lost'] += m.away_score
        stats[m.away_team_id]['goals_scored'] += m.away_score
        stats[m.away_team_id]['goals_lost'] += m.home_score

        if m.home_score > m.away_score:
            stats[m.home_team_id]['points'] += 3
        elif m.home_score < m.away_score:
            stats[m.away_team_id]['points'] += 3
        else:
            stats[m.home_team_id]['points'] += 1
            stats[m.away_team_id]['points'] += 1

    sorted_table = sorted(stats.values(), key=lambda x: x['points'], reverse=True)

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Tabela Ligi</h3>
    <table class="table table-striped mt-3">
        <thead class="table-dark"><tr><th>Miejsce</th><th>Drużyna</th><th>Punkty</th><th>Bramki (Z-S)</th></tr></thead>
        <tbody>
            {% for row in table %}
            <tr><td>{{ loop.index }}</td><td>{{ row.name }}</td><td><b>{{ row.points }}</b></td><td>{{ row.goals_scored }} - {{ row.goals_lost }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), table=sorted_table)

@kibic_bp.route('/strzelcy')
@login_required
def strzelcy():
    top_scorers = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
        .join(Goal).group_by(Player.id).order_by(func.sum(Goal.goals).desc()).limit(10).all()

    html = "{% extends 'dashboard' %}{% block content %}" + """
    <h3>Top 10 Strzelców</h3>
    <table class="table table-bordered mt-3">
        <thead class="table-dark"><tr><th>#</th><th>Zawodnik</th><th>Suma Goli</th></tr></thead>
        <tbody>
            {% for scorer in scorers %}
            <tr><td>{{ loop.index }}</td><td>{{ scorer.name }}</td><td><b>{{ scorer.total }}</b></td></tr>
            {% else %}<tr><td colspan="3">Brak zdobytych bramek w lidze.</td></tr>{% endfor %}
        </tbody>
    </table>
    {% endblock %}"""
    return render_template_string(html.replace('dashboard', DASHBOARD_HTML), scorers=top_scorers)
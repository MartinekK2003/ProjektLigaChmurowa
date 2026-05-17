from flask import render_template # Pamiętajcie dodać to na górze pliku!

@kibic_bp.route('/historia_klubow')
@login_required
def historia_klubow():
    season_id = request.args.get('season_id', type=int)
    team_id = request.args.get('team_id', type=int)

    seasons = Season.query.all()
    teams = Team.query.all()
    team_names = {t.id: t.name for t in teams}

    selected_season = Season.query.get(season_id) if season_id else None
    selected_team = Team.query.get(team_id) if team_id else None

    matches = []
    team_top_scorers = []

    if selected_season and selected_team:
        matches = Match.query.filter(
            Match.season_id == season_id,
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
        ).all()

        team_top_scorers = db.session.query(Player.name, func.sum(Goal.goals).label('total')) \
            .join(Goal, Player.id == Goal.player_id) \
            .join(Match, Goal.match_id == Match.id) \
            .filter(Player.team_id == team_id, Match.season_id == season_id) \
            .group_by(Player.id) \
            .order_by(func.sum(Goal.goals).desc()) \
            .all()

    # Zamiast długiego tekstu, po prostu renderujemy plik!
    return render_template('historia.html',
                           seasons=seasons, teams=teams,
                           selected_season=selected_season, selected_team=selected_team,
                           matches=matches, team_top_scorers=team_top_scorers,
                           team_names=team_names)
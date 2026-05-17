# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class League(db.Model):
    __tablename__ = 'leagues'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

    # Relacje
    schedules = db.relationship('Schedule', backref='league', lazy=True, cascade="all, delete-orphan")
    teams = db.relationship('Team', backref='league', lazy=True, cascade="all, delete-orphan")
    players = db.relationship('Player', backref='league', lazy=True, cascade="all, delete-orphan")


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id', ondelete='CASCADE'), nullable=False)

    games = db.relationship('Game', backref='schedule', lazy=True, cascade="all, delete-orphan")


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    time_zone_id = db.Column(db.String(50), nullable=False)

    games = db.relationship('Game', backref='location', lazy=True)


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id', ondelete='CASCADE'), nullable=False)

    players = db.relationship('Player', backref='team', lazy=True)


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id', ondelete='CASCADE'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    date_and_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    visitor_team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)

    # Relacja 1-do-1 do wyniku
    score = db.relationship('Score', backref='game', uselist=False, cascade="all, delete-orphan")


class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False, unique=True)
    home_score = db.Column(db.Integer, nullable=False, default=0)
    visitor_score = db.Column(db.Integer, nullable=False, default=0)
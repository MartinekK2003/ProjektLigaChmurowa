import os
from app import app, db
from models import Role, Team, User, Player, Season, Match, Goal


def setup_database():
    # Sprawdzenie, czy plik bazy danych już istnieje - jeśli tak, usuwamy go, by zacząć od zera
    db_file = "liga_chmurowa.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"--- Usunięto istniejący plik {db_file} ---")

    with app.app_context():
        print("--- Inicjalizacja nowej bazy danych SQLite ---")
        db.create_all()

        # 1. DODAWANIE RÓL
        print("Dodawanie ról...")
        roles = [
            Role(id=1, name='admin'),
            Role(id=2, name='referee'),
            Role(id=3, name='coach'),
            Role(id=4, name='user')
        ]
        db.session.add_all(roles)

        # 2. DODAWANIE SEZONÓW
        print("Dodawanie sezonów...")
        seasons = [
            Season(id=1, name='Sezon 2024/2025'),
            Season(id=2, name='Sezon 2025/2026'),
            Season(id=3, name='Sezon 2026/2027')
        ]
        db.session.add_all(seasons)

        # 3. DODAWANIE DRUŻYN
        print("Dodawanie drużyn...")
        teams = [
            Team(id=1, name='FC Gunicorn'),
            Team(id=2, name='KS Flask'),
            Team(id=3, name='Django United'),
            Team(id=4, name='FastAPI City'),
            Team(id=5, name='SQL Rovers')
        ]
        db.session.add_all(teams)

        # Zapisujemy zmiany, aby klucze obce dla graczy i użytkowników były poprawne
        db.session.commit()

        # 4. DODAWANIE UŻYTKOWNIKÓW
        print("Dodawanie użytkowników...")
        users = [
            User(id=1, username='SzefAdmin', password='haslo123', role_id=1, team_id=None),
            User(id=2, username='SedziaGlowny', password='haslo123', role_id=2, team_id=None),
            User(id=3, username='TrenerGunicorn', password='haslo123', role_id=3, team_id=1),
            User(id=4, username='TrenerFlask', password='haslo123', role_id=3, team_id=2),
            User(id=5, username='ZwyklyKibic', password='haslo123', role_id=4, team_id=None)
        ]
        db.session.add_all(users)

        # 5. DODAWANIE ZAWODNIKÓW (75 zawodników z Twojego SQL)
        print("Dodawanie zawodników (75 osób)...")
        players_data = [
            # FC Gunicorn (Team 1)
            (1, 'P1 Guni', 1), (2, 'P2 Guni', 1), (3, 'P3 Guni', 1), (4, 'P4 Guni', 1), (5, 'P5 Guni', 1),
            (6, 'P6 Guni', 1), (7, 'P7 Guni', 1), (8, 'P8 Guni', 1), (9, 'P9 Guni', 1), (10, 'P10 Guni', 1),
            (11, 'P11 Guni', 1), (12, 'R1 Guni', 1), (13, 'R2 Guni', 1), (14, 'R3 Guni', 1), (15, 'R4 Guni', 1),
            # KS Flask (Team 2)
            (16, 'P1 Flask', 2), (17, 'P2 Flask', 2), (18, 'P3 Flask', 2), (19, 'P4 Flask', 2), (20, 'P5 Flask', 2),
            (21, 'P6 Flask', 2), (22, 'P7 Flask', 2), (23, 'P8 Flask', 2), (24, 'P9 Flask', 2), (25, 'P10 Flask', 2),
            (26, 'P11 Flask', 2), (27, 'R1 Flask', 2), (28, 'R2 Flask', 2), (29, 'R3 Flask', 2), (30, 'R4 Flask', 2),
            # Django United (Team 3)
            (31, 'P1 Djan', 3), (32, 'P2 Djan', 3), (33, 'P3 Djan', 3), (34, 'P4 Djan', 3), (35, 'P5 Djan', 3),
            (36, 'P6 Djan', 3), (37, 'P7 Djan', 3), (38, 'P8 Djan', 3), (39, 'P9 Djan', 3), (40, 'P10 Djan', 3),
            (41, 'P11 Djan', 3), (42, 'R1 Djan', 3), (43, 'R2 Djan', 3), (44, 'R3 Djan', 3), (45, 'R4 Djan', 3),
            # FastAPI City (Team 4)
            (46, 'P1 Fast', 4), (47, 'P2 Fast', 4), (48, 'P3 Fast', 4), (49, 'P4 Fast', 4), (50, 'P5 Fast', 4),
            (51, 'P6 Fast', 4), (52, 'P7 Fast', 4), (53, 'P8 Fast', 4), (54, 'P9 Fast', 4), (55, 'P10 Fast', 4),
            (56, 'P11 Fast', 4), (57, 'R1 Fast', 4), (58, 'R2 Fast', 4), (59, 'R3 Fast', 4), (60, 'R4 Fast', 4),
            # SQL Rovers (Team 5)
            (61, 'P1 SQL', 5), (62, 'P2 SQL', 5), (63, 'P3 SQL', 5), (64, 'P4 SQL', 5), (65, 'P5 SQL', 5),
            (66, 'P6 SQL', 5), (67, 'P7 SQL', 5), (68, 'P8 SQL', 5), (69, 'P9 SQL', 5), (70, 'P10 SQL', 5),
            (71, 'P11 SQL', 5), (72, 'R1 SQL', 5), (73, 'R2 SQL', 5), (74, 'R3 SQL', 5), (75, 'R4 SQL', 5)
        ]
        players = [Player(id=p[0], name=p[1], team_id=p[2]) for p in players_data]
        db.session.add_all(players)

        # 6. DODAWANIE MECZÓW
        print("Dodawanie meczów...")
        matches = [
            Match(id=1, season_id=1, home_team_id=1, away_team_id=2, home_score=2, away_score=1, is_finished=True),
            Match(id=2, season_id=1, home_team_id=1, away_team_id=3, home_score=3, away_score=0, is_finished=True)
        ]
        db.session.add_all(matches)

        # 7. DODAWANIE GOLI
        print("Dodawanie bramek...")
        goals = [
            Goal(id=1, match_id=1, player_id=9, goals=2),
            Goal(id=2, match_id=1, player_id=16, goals=1),
            Goal(id=3, match_id=2, player_id=9, goals=1),
            Goal(id=4, match_id=2, player_id=10, goals=1),
            Goal(id=5, match_id=2, player_id=11, goals=1)
        ]
        db.session.add_all(goals)

        # Finalne zatwierdzenie wszystkich danych
        db.session.commit()
        print("\n✅ GOTOWE! Plik liga_chmurowa.db został utworzony i uzupełniony.")


if __name__ == "__main__":
    setup_database()
from flask import Flask, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Konfiguracja połączenia z lokalną bazą XAMPP
db_config = {
    'host': '127.0.0.1',  # lub 'localhost'
    'user': 'root',  # Domyślny użytkownik XAMPP
    'password': '',  # Domyślnie brak hasła w XAMPP
    'database': 'liga_chmurowa'
}


# Funkcja pomocnicza do nawiązywania połączenia
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return None


@app.route('/')
def home():
    # Pobieramy połączenie
    conn = get_db_connection()
    if conn is None:
        return "Błąd: Nie udało się połączyć z bazą danych 'liga_chmurowa'. Sprawdź, czy XAMPP (MySQL) jest włączony.", 500

    try:
        # Używamy dictionary=True, aby wyniki zwracane były w formie wygodnych słowników (klucz to nazwa kolumny)
        cursor = conn.cursor(dictionary=True)

        # Wykonujemy testowe zapytanie do tabeli teams z Twojego zrzutu SQL
        cursor.execute("SELECT * FROM teams;")
        teams = cursor.fetchall()

        # Zwracamy pobrane dane w formacie JSON
        return jsonify({
            "status": "success",
            "message": "Połączono z bazą liga_chmurowa!",
            "data": teams
        })

    except Error as e:
        return f"Wystąpił błąd podczas pobierania danych: {e}", 500

    finally:
        # Zawsze pamiętaj o zamykaniu kursora i połączenia
        if 'cursor' in locals():
            cursor.close()
        if conn.is_connected():
            conn.close()


if __name__ == '__main__':
    # Uruchamiamy aplikację w trybie debugowania
    app.run(debug=True)
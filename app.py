# app.py
import os
from flask import Flask, render_template_string
from models import db, League, Team, Player, Game, Score

app = Flask(__name__)

# =========================================================================
# KONFIGURACJA POŁĄCZENIA Z LOKALNYM XAMPP / PHP_MY_ADMIN
# Format: mysql+pymysql://użytkownik:hasło@host/nazwa_bazy
# =========================================================================
LOCAL_DB_URI = "mysql+pymysql://root:@localhost/liga_chmurowa"

# Dodatkowo wdrażamy "inteligentne" przełączanie: jeśli kod wykryje Azure,
# spróbuje użyć bazy chmurowej, a lokalnie połączy się z XAMPPem.
if 'WEBSITE_SITE_NAME' in os.environ:
    # 1. CHMURA AZURE: Używamy darmowego SQLite w Persistent Storage (żeby strona działała i była darmowa)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/site/liga_chmurowa.db'
else:
    # 2. LOKALNY KOMPUTER: Używamy bazy MySQL z XAMPPa (do wygodnego podglądu w phpMyAdmin)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/liga_chmurowa"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# POKAZUJE ŻYWY KOD SQL W KONSOLI PYCHARMA (Super sprawa do kontroli SQL!)
app.config['SQLALCHEMY_ECHO'] = True

# Inicjalizacja bazy danych
db.init_app(app)

# Automatyczne dopasowanie struktur (opcjonalne, jeśli tabele już stworzyliście w phpMyAdmin)
with app.app_context():
    db.create_all()


# =========================================================================
# PRZYKŁADOWA TRASA TESTOWA (ODCZYT Z BAZY XAMPP)
# =========================================================================
@app.route('/')
def index():
    # Pobieramy ligi, żeby przetestować czy Flask widzi bazę w XAMPP
    ligi = League.query.all()

    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Liga Chmurowa - XAMPP</title></head>
    <body style="font-family: Arial; margin: 50px;">
        <h1>Połączono pomyślnie z lokalną bazą MySQL w XAMPP!</h1>
        <h3>Lista lig wykrytych w phpMyAdmin:</h3>
        <ul>
        {% for liga in ligi %}
            <li><strong>{{ liga.name }}</strong> (ID: {{ liga.id }})</li>
        {% else %}
            <li>Połączenie działa, ale tabela 'leagues' jest pusta. Uruchom skrypt SQL w phpMyAdmin!</li>
        {% endfor %}
        </ul>
    </body>
    </html>
    """
    return render_template_string(html, ligi=ligi)


if __name__ == '__main__':
    app.run(debug=True)
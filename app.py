from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, Team

app = Flask(__name__)
app.secret_key = 'super_tajny_klucz_do_sesji'  # Wymagane dla Flask-Login
# Konfiguracja połączenia z lokalną bazą na XAMPP
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@127.0.0.1/liga_chmurowa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja bazy i logowania
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Gdzie przekierować, jeśli ktoś nie jest zalogowany
login_manager.login_message = "Zaloguj się, aby uzyskać dostęp."


# Funkcja ładująca użytkownika dla Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# SZABLON LOGOWANIA
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Logowanie - Liga Chmurowa</title></head>
<body>
    <h2>Zaloguj się do Ligi Chmurowej</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul style="color: red;">
        {% for message in messages %}<li>{{ message }}</li>{% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="POST">
        <label>Nazwa użytkownika:</label><br>
        <input type="text" name="username" required><br><br>
        <label>Hasło:</label><br>
        <input type="password" name="password" required><br><br>
        <button type="submit">Zaloguj</button>
    </form>
</body>
</html>
"""

# SZABLON STRONY GŁÓWNEJ (DASHBOARD) Z PODZIAŁEM NA ROLE
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Panel Główny - Liga Chmurowa</title></head>
<body>
    <h1>Witaj, {{ current_user.username }}!</h1>
    <p>Twoja rola to: <strong>{{ current_user.role.name }}</strong></p>
    <a href="{{ url_for('logout') }}"><button>Wyloguj się</button></a>
    <hr>

    {% if current_user.role.name == 'admin' %}
        <div style="background-color: #ffebee; padding: 10px;">
            <h2>🛠️ Panel Administratora</h2>
            <p>Tutaj Admin może:</p>
            <ul>
                <li>Zarządzać użytkownikami (Sędziowie, Trenerzy)</li>
                <li>Dodawać i usuwać całe drużyny z ligi</li>
                <li>Przeglądać pełne statystyki wszystkich lig</li>
            </ul>
        </div>

    {% elif current_user.role.name == 'referee' %}
        <div style="background-color: #fff3e0; padding: 10px;">
            <h2>⚽ Panel Sędziego</h2>
            <p>Tutaj Sędzia może:</p>
            <ul>
                <li>Wprowadzać wyniki zakończonych meczów</li>
                <li>Aktualizować strzelców goli po meczu</li>
                <li>Przeglądać tabele tak jak zwykły użytkownik</li>
            </ul>
        </div>

    {% elif current_user.role.name == 'coach' %}
        <div style="background-color: #e8f5e9; padding: 10px;">
            <h2>📋 Panel Trenera</h2>
            <p>Zarządzasz drużyną: <strong>{{ current_user.team.name if current_user.team else 'Brak przypisanej drużyny' }}</strong></p>
            <p>Tutaj Trener może:</p>
            <ul>
                <li>Wyrzucać i dodawać zawodników do swojej drużyny</li>
                <li>Sprawdzać, który z jego zawodników strzelił najwięcej goli wybranemu rywalowi</li>
                <li>Przeglądać statystyki królów strzelców ligi</li>
            </ul>
        </div>

    {% elif current_user.role.name == 'user' %}
        <div style="background-color: #e3f2fd; padding: 10px;">
            <h2>👀 Panel Kibica (Użytkownika)</h2>
            <p>Tutaj możesz:</p>
            <ul>
                <li>Przeglądać kluby grające w wybranych sezonach</li>
                <li>Sprawdzać królów strzelców w każdej drużynie</li>
                <li>Oglądać wyniki meczów</li>
            </ul>
        </div>
    {% endif %}

</body>
</html>
"""


# ROUTE: LOGOWANIE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Szukamy użytkownika w bazie
        user = User.query.filter_by(username=username).first()

        # UWAGA: W wersji produkcyjnej używamy check_password_hash!
        # Tutaj sprawdzamy hasła tekstowe na podstawie Twojego zrzutu SQL.
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Błędna nazwa użytkownika lub hasło.')

    return render_template_string(LOGIN_HTML)


# ROUTE: WYLOGOWANIE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ROUTE: STRONA GŁÓWNA (DASHBOARD)
@app.route('/')
@login_required
def dashboard():
    # Widok HTML sam dopasuje treść dzięki instrukcjom {% if %} bazując na current_user.role.name
    return render_template_string(DASHBOARD_HTML)


if __name__ == '__main__':
    # Uruchamiamy aplikację
    app.run(debug=True)
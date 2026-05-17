# controllers/auth.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from controllers import BASE_HTML_HEAD, DASHBOARD_HTML

auth_bp = Blueprint('auth_bp', __name__)

LOGIN_HTML = BASE_HTML_HEAD + """
<body class="d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow" style="width: 350px;">
        <h2 class="text-center text-primary mb-4">Liga Chmurowa</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for m in messages %}<div class="alert alert-danger p-2 text-center">{{ m }}</div>{% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="{{ url_for('auth_bp.login') }}">
            <input type="text" class="form-control mb-3" name="username" placeholder="Login" required>
            <input type="password" class="form-control mb-3" name="password" placeholder="Hasło" required>
            <button type="submit" class="btn btn-primary w-100 fw-bold">Zaloguj się</button>
        </form>
    </div>
</body>
"""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth_bp.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('auth_bp.dashboard'))
        flash('Błędny login lub hasło!')
    return render_template_string(LOGIN_HTML)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)
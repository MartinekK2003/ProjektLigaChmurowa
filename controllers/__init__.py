# controllers/__init__.py

BASE_HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <title>Liga Chmurowa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #f0f2f5; }</style>
</head>
"""

NAV_HTML = BASE_HTML_HEAD + """
<body class="container mt-4">
    <nav class="navbar navbar-dark bg-dark p-3 rounded mb-4 shadow d-flex justify-content-between">
        <div class="text-white">
            {% if current_user.is_authenticated %}
                Zalogowany jako: <b>{{ current_user.username }}</b> 
                <span class="badge bg-primary ms-2">{{ current_user.role.name|upper }}</span>
            {% else %}
                <b>Tryb Gościa (Kibic)</b>
            {% endif %}
        </div>
        <div>
            {% if current_user.is_authenticated %}
                <a href="{{ url_for('auth_bp.logout') }}" class="btn btn-danger btn-sm fw-bold">Wyloguj się</a>
            {% else %}
                <a href="{{ url_for('auth_bp.login') }}" class="btn btn-success btn-sm fw-bold">Zaloguj się (Dla Klubów)</a>
            {% endif %}
        </div>
    </nav>

    <div class="row mb-4">
        <div class="col-12 d-flex gap-2 justify-content-center flex-wrap">
            <a href="{{ url_for('kibic_bp.tabela') }}" class="btn btn-outline-dark">Tabela Ligi</a>
            <a href="{{ url_for('kibic_bp.strzelcy') }}" class="btn btn-outline-dark">Król Strzelców</a>
            <a href="{{ url_for('kibic_bp.kadry_klubow') }}" class="btn btn-primary fw-bold">Kadry Klubów 👥</a>

            {% if current_user.is_authenticated %}
                {% if current_user.role.name == 'coach' %}
                    <a href="{{ url_for('trener_bp.trener_sklad') }}" class="btn btn-success fw-bold">Zarządzaj Składem</a>
                    <a href="{{ url_for('trener_bp.trener_analiza') }}" class="btn btn-info text-white fw-bold">Analiza Rywala 🔍</a>
                {% endif %}

                {% if current_user.role.name == 'referee' %}
                    <a href="{{ url_for('sedzia_bp.sedzia_mecze') }}" class="btn btn-warning fw-bold">Wprowadź Wyniki</a>
                {% endif %}

                {% if current_user.role.name == 'admin' %}
                    <a href="{{ url_for('admin_bp.admin_druzyny') }}" class="btn btn-danger fw-bold">Zarządzaj Drużynami</a>
                    <a href="{{ url_for('admin_bp.admin_zaplanuj_mecz') }}" class="btn btn-outline-danger fw-bold">Zaplanuj Mecz 📅</a>
                {% endif %}
            {% endif %}
        </div>
    </div>

    <div class="card shadow-sm p-4">
"""

FOOTER_HTML = """
    </div>
</body>
"""

DASHBOARD_HTML = NAV_HTML + """
    <h2 class="text-center">Witaj w systemie zarządzania Ligą Chmurową!</h2>
    <p class="text-center text-muted">Wybierz moduł z menu powyżej, aby przeglądać statystyki rozgrywek lub zarządzać ligą.</p>
""" + FOOTER_HTML
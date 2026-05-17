# controllers/__init__.py

BASE_HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <title>Liga Chmurowa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #f0f2f5; }</style>
</head>
"""

# Otwarcie strony i menu nawigacyjne
NAV_HTML = BASE_HTML_HEAD + """
<body class="container mt-4">
    <nav class="navbar navbar-dark bg-dark p-3 rounded mb-4 shadow">
        <div class="text-white">
            Zalogowany jako: <b>{{ current_user.username }}</b> 
            <span class="badge bg-primary ms-2">{{ current_user.role.name|upper }}</span>
        </div>
        <a href="{{ url_for('auth_bp.logout') }}" class="btn btn-danger btn-sm fw-bold">Wyloguj się</a>
    </nav>

    <div class="row mb-4">
        <div class="col-12 d-flex gap-2 justify-content-center">
            <a href="{{ url_for('kibic_bp.tabela') }}" class="btn btn-outline-dark">Tabela Ligi</a>
            <a href="{{ url_for('kibic_bp.strzelcy') }}" class="btn btn-outline-dark">Król Strzelców</a>
            <a href="{{ url_for('kibic_bp.historia_klubow') }}" class="btn btn-primary fw-bold">Historia Klubów 🕒</a>

            {% if current_user.role.name == 'coach' %}
                <a href="{{ url_for('trener_bp.trener_sklad') }}" class="btn btn-success">Zarządzaj Składem</a>
            {% endif %}

            {% if current_user.role.name == 'referee' %}
                <a href="{{ url_for('sedzia_bp.sedzia_mecze') }}" class="btn btn-warning">Wprowadź Wyniki</a>
            {% endif %}

            {% if current_user.role.name == 'admin' %}
                <a href="{{ url_for('admin_bp.admin_druzyny') }}" class="btn btn-danger">Zarządzaj Drużynami</a>
            {% endif %}
        </div>
    </div>

    <div class="card shadow-sm p-4">
"""

# Zamknięcie strony
FOOTER_HTML = """
    </div>
</body>
"""

# Pozostawiamy dla kompatybilności z auth.py strony głównej
DASHBOARD_HTML = NAV_HTML + """
    <h2 class="text-center">Witaj w systemie zarządzania Ligą Chmurową!</h2>
    <p class="text-center text-muted">Wybierz moduł z menu powyżej, aby rozpocząć pracę.</p>
""" + FOOTER_HTML
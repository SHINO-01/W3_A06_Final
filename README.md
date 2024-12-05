<body>

<h1>Inventory Management Project</h1>

<h2>Overview</h2>
<p>
This is a Django-based Inventory Management system that allows you to manage properties, locations, and accommodations. It uses PostgreSQL with PostGIS for geospatial data, integrates with Django's admin interface for data management, supports file uploads, and includes a custom <code>generate_sitemap</code> management command to build a dynamic sitemap.
</p>

<p><strong>Key Features:</strong></p>
<ul>
    <li>Hierarchical location data (countries, states, cities).</li>
    <li>Accommodations with geospatial data, amenities, and images.</li>
    <li>Property owners sign up and require superuser(admin) approval before accessing certain features.</li>
    <li>A <code>generate_sitemap</code> management command that creates a hierarchical JSON sitemap.</li>
    <li>Integration with Django admin, <code>import_export</code> for CSV imports, and <code>leaflet</code> for geospatial visualization.</li>
</ul>

<h2>Project Structure</h2>
<pre>
inventoryManagement/
├── inventoryManagement/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── properties/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── management/
│   │   └── commands/
│   │       └── generate_sitemap.py
│   ├── migrations/
│   ├── models.py
│   ├── signals.py
│   ├── templates/
│   │   ├── properties/
│   │   │   ├── home.html
│   │   │   ├── signup.html
│   │   │   └── accommodation_detail.html
│   │   └──base.html
│   ├── tests.py
│   └── views.py
├── static/
│   ├── css/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
</pre>

<h2>Prerequisites</h2>
<ul>
    <li>Docker and Docker Compose installed</li>
</ul>

<h2>Installation &amp; Setup</h2>
<ol>
    <li><strong>Clone the Repository:</strong>
        <pre>git clone https://github.com/SHINO-01/W3_A06_Final.git
cd W3_A06_Final</pre>
    </li>
    <li><strong>Set up Virtual Environment(If Any):</strong>
        <p>Create a <code>.venv</code> using <code>python3 -m venv .venv</code></p>
        <p>activate the .venv using <code>source .venv/bin/activate</code></p>
        <p>install django, psycopg2-binary in the .venv. if it does not work. use<code>pip3 install -r requirements.txt</code> </p>
    </li>
    <li><strong>Build and Run the Containers:</strong>
        <pre>docker-compose up --build</pre>
    </li>
     <li><strong>Connect to the Database Server:</strong>
        <pre>go to http://localhost:5050/login?next=/</pre>
        <p>Sign in as the admin, Email: admin@admin.com, password: admin123</p>
        <p>navigate to the dashboard and select servers, then select register from the object tools.</p>
        <p>in General-->Name: invManagement, then in connection-->hostname: postgres_db. and in connection-->Username: sakif, and password: sakif123. Hit connect</p>
    </li>
    <li><strong>Apply Migrations:</strong>
        <pre>docker exec -it inventoryManagement python manage.py makemigrations</pre>
        <pre>docker exec -it inventoryManagement python manage.py migrate</pre>
    </li>
    <li><strong>Create a Superuser:</strong>
        <pre>docker exec -it inventoryManagement python manage.py createsuperuser</pre>
        <p>add username and password of your choice and use that password to log in as the Superuser to authorise a property owner</p>
    </li>
    <li><strong>Access the Application:</strong>
        <ul>
            <li>Home Page: <a href="http://localhost:8000/">http://localhost:8000/</a></li>
            <p>here you can access signup for requesting signup as a property owner.</p>
            <p>in login, you can enter your username and password and it will automatically detect whether you are a Superuser(admin) or a property owner</p>
        </ul>
    </li>
    <li><strong>Sign-Up &amp; Approval Flow:</strong>
        <p>Users sign up at <code>/signup/</code>. They join the "Property Owners" group but are inactive. A superuser must activate them before they can manage properties.</p>
    </li>
</ol>

<h2>Running the Project</h2>
<p><strong>With Docker:</strong></p>
<pre>docker-compose up</pre>
<p>Then visit <a href="http://localhost:8000">http://localhost:8000</a></p>

<p><strong>Stopping the Project:</strong></p>
<pre>docker-compose down</pre>

<h2>Running Tests</h2>
<p>Run tests within the Docker container:</p>
<pre>docker exec -it inventoryManagement python manage.py test properties</pre>

<p>If using <code>pytest</code> and <code>pytest-django</code>:</p>
<pre>docker exec -it inventoryManagement pytest --maxfail=1 --disable-warnings --cov=properties --cov-report=term-missing</pre>

<h2>Code Coverage</h2>
<ol>
    <li><strong>Install Coverage (if not already):</strong>
        <pre>pip install coverage</pre>
    </li>
    <li><strong>Run Tests with Coverage:</strong>
        <pre>docker exec -it inventoryManagement coverage run --source='properties' manage.py test properties
docker exec -it inventoryManagement coverage report -m
docker exec -it inventoryManagement coverage html
</pre>
    </li>
    <li>Open <code>htmlcov/index.html</code> locally to see a detailed coverage report.</li>
</ol>

<h2>Sample Commands</h2>
<ul>
    <li><strong>Create a New Location via Admin:</strong>
        <p>Go to <code>/admin/</code> and add new <code>Location</code> entries.</p>
    </li>
    <li><strong>Generate Sitemap:</strong>
        <pre>docker exec -it inventoryManagement python manage.py generate_sitemap</pre>
        <p>This creates <code>Generated/sitemap.json</code> with hierarchical location data.</p>
    </li>
    <li><strong>Import Locations via Admin:</strong>
        <p>Visit <code>/admin/properties/location/import/</code> to import CSV data.</p>
    </li>
    <li><strong>Approve New User:</strong>
        <p>Log in as superuser, go to <code>/admin/auth/user/</code>, edit the user and activate them.</p>
    </li>
</ul>

<h2>Contributing</h2>
<ul>
    <li><strong>Issues &amp; Bugs:</strong> Open a GitHub issue with details and steps to reproduce.</li>
    <li><strong>Pull Requests:</strong> Fork the repo, create a feature branch, implement changes, and submit a PR.</li>
</ul>

<h2>License</h2>
<p>This project is licensed under the MIT License. See <code>LICENSE</code> for details.</p>

</body>

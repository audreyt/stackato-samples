# Django GTD

A sample Getting Things Done (GTD) app using PostgreSQL and the Django admin
interface. To create projects, actions, context or make any modifications, use
the Django admin URL at ``http://<yourapp>.yourdomain.com/admin/``.

## Local development

    pypm install -r requirements.txt
    python manage.py syncdb
    python manage.py migrate
    python manager.py runserver

## Deploying to Stackato

    stackato push djangogtd
    # Answer "yes" when asked to bind any services and select "postgresql"

    stackato run djangogtd python manage.py syncdb --noinput
    stackato run djangogtd python manage.py migrate --noinput

    # Create the admin user
    stackato run djangogtd python manage.py createsuperuser --username=admin --email=admin@mydomain.com --noinput
    stackato run djangogtd python manage.py changepassword2 admin secret123

    # Visit the app; go to /admin/ to add tasks, projects and contexts.
 
## Want to use MySQL?

To use mysql instead of postgresql on production, you need to make only a few
changes before pushing your app:

  * In requirements.txt, replace `psycopg2` with `mysql-python`
  * In settings.py, replace `django.db.backends.postgresql_psycopg2` with
    `django.db.backends.mysql`
  * In settings.py, replace `vcap_services['postgresql-8.4'][0]` with
    `vcap_services['mysql-5.1'][0]`
# Django settings for djangogtd project.
import sys, os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ROOT = os.path.abspath(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


## Pull in CloudFoundry's production settings
if 'VCAP_SERVICES' in os.environ:
    import json
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])
    # XXX: avoid hardcoding here
    mysql_srv = vcap_services['mysql-5.1'][0]
    cred = mysql_srv['credentials']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': cred['name'],                      # Or path to database file if using sqlite3.
            'USER': cred['user'],                      # Not used with sqlite3.
            'PASSWORD': cred['password'],                  # Not used with sqlite3.
            'HOST': cred['hostname'],                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': cred['port'],                      # Set to empty string for default. Not used with sqlite3.
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'dev.db',                      # Or path to database file if using sqlite3.
            'USER': '',                      # Not used with sqlite3.
            'PASSWORD': '',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
            }
        }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Vancouver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en_us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(ROOT, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '77777777777777777777777777777u9w@hs7bdxt+w1k@f2&di'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

IGNORABLE_404_STARTS = ('/cgi-bin/', '/_vti_bin', '/_vti_inf')

IGNORABLE_404_ENDS = ('mail.pl', 'mailform.pl', 'mail.cgi', 'mailform.cgi', 'favicon.ico', '.php')

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.databrowse',
    'django.contrib.humanize',
    'gtd',
    'south',
    'django_stackato',
)

# try:
#     execfile(os.path.join(ROOT, 'localsettings.py'))
# except:
#     sys.stderr.write("Error: Cant' find the file 'localsettings.py'. Please"
#                      "override the settings localy not in settings.py \n")

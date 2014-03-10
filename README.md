[![Build Status](https://travis-ci.org/casual-passer/Incidents-system.png?branch=master)](https://travis-ci.org/casual-passer/Incidents-system)
[![Coverage Status](https://coveralls.io/repos/casual-passer/Incidents-system/badge.png?branch=master)](https://coveralls.io/r/casual-passer/Incidents-system?branch=master)


INSTALLATION

# login as root
# create new user for project
useradd -m tickets-user
# install virtualenv
aptitude install --without-recommends python-virtualenv python-pip
# for postgres install
# aptitude install --without-recommends libpq-dev gcc python-dev
# log in as new user
# clone repo
git clone https://github.com/casual-passer/Incidents-system.git
virtualenv Incidents-system
cd Incidents-system
source bin/activate
pip install `cat requirements.txt`
# We will use gunicorn to run our application
pip install gunicorn
# and postgres
pip install psycopg2
# edit settings.py
# Debug = False
# TEMPLATE_DEBUG = FALSE
# ALLOWED_HOSTS = ['ip address']
# fill database settings

# Create new database
# First:  Create new user
/bin/su - postgres
createuser -D -E -P -R -S tickets-user
# Enter password for new database user
# Second: Create db for new user
createdb -O tickets-user tickets
exit

# login as system tickets-user
# cd into repo dir
source bin/activate
cd src
gunicorn_django --bind 127.0.0.1:20000
# if all ok, create new file with gunicorn settings
    import os
    BASE_DIR = os.path.dirname(__file__)
    command = os.path.join(BASE_DIR, 'bin', 'gunicorn')
    pythonpath = os.path.join(BASE_DIR, 'src')
    bind = '127.0.0.1:20000'
    workers = 4
bin/gunicorn -c gunicorn_config.py tickets_system.wsgi # everything should be ok
# choose folder for static files
# here it is root folder of virtualenv
# STATIC_ROOT = os.path.join(BASE_DIR, '..', '..', 'static')
python src/manage.py collectstatic
# configure nginx to serve static files
# and redirect other request to django
server {
    listen 80;
    location /static/ {
        alias /home/tickets-user/Incidents-system/static/;
    }
    location / {
        proxy_pass http://127.0.0.1:20000;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Real-Ip $remote_addr;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }
}

# install supervisor to run gunicorn
aptitude install --without-recommends supervisor
# create script inside tickets-user home with content
    #!/bin/bash
    set -e
    cd /home/tickets-user/Incidents-system/
    source bin/activate
    exec gunicorn -c gunicorn_conf.py tickets_system.wsgi
# create new config /etc/supervisor/conf.d/tickets.conf
    [program: tickets]
    directory = /home/tickets-user/
    user = tickets-user
    command = /home/tickets-user/tickets.sh

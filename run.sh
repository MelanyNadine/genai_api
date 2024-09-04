#!/bin/bash

# Activate the pipenv shell
pipenv shell <<EOF

# Run Django management commands
python manage.py makemigrations
python manage.py migrate

# Start the Django development server
python manage.py runserver 0.0.0.0:80

# Exit the pipenv shell
exit
EOF

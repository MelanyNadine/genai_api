@echo off

pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
pipenv run python manage.py runserver 0.0.0.0:80

pause
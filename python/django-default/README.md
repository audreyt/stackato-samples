# Django app based on its default template

This is based on the default template created by Django's
[startproject](https://docs.djangoproject.com/en/dev/intro/tutorial01/#creating-a-project)`
command.

## Local development

    pypm install -r requirements.txt
    cd hellodjango
    python manager.py runserver

## Deploying to Stackato

    stackato push django-default

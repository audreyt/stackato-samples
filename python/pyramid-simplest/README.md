# The simplest Pyramid app

## Local development

    pypm install -r requirements.txt
    pypm install gunicorn
    gunicorn wsgi

## Deploying to Stackato

    stackato push pyramid-simplest

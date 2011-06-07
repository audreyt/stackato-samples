# Tornado Chat demo

This is a multi-user chat application based on the Tornado Python
webframework. It uses your Google account for login.

## Local development

    pip install --user pycurl
    pypm install -r requirements.txt
    python app.py

## Deploying to Stackato

    stackato push tornado-chat

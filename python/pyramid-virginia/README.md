# A Pyramid sample app

This package provides a Pyramid application that is willing to serve slightly
dynamic file content from a disk directory.


## Local development

    pypm install -r requirements.txt
    paster serve development.ini

## Deploying to Stackato

    stackato push pyramid-virginia

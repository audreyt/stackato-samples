# Node Circles

A demo built on the [maga](https://github.com/stagas/maga/tree/#readme)
multi-player physics based game framework for Node.js.

## Local development

    npm install confu express express-expose maga socket.io
    node app.js

## Deploying to Stackato

Make sure that you have installed the dependencies using `npm` as the
Stackato server requires them.

    npm install confu express express-expose maga socket.io

Then deploy,

    stackato push node-circles

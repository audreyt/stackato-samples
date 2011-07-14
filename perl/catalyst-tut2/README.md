Catalyst Basics Sample
======================

A very basic Catalyst web application taken from the Catalyst Tutorial:

  http://search.cpan.org/dist/Catalyst-Manual/lib/Catalyst/Manual/Tutorial/02_CatalystBasics.pod
  
Copyright 2006-2010, Kennedy Clark, under the Creative Commons
Attribution Share-Alike License Version 3.0
(http://creativecommons.org/licenses/by-sa/3.0/us/).

Running locally
---------------

This server can be run on your local workstation, but you'll need to
install several Catalyst modules first. These are available via PPM:

    ppm install Catalyst::Runtime
    ppm install Catalyst::Engine::PSGI
    ppm install Plack::Middleware::ReverseProxy
    ppm install Catalyst::Plugin::ConfigLoader
    ppm install Catalyst::Plugin::Static::Simple
    ppm install Catalyst::Action::RenderView
    ppm install Catalyst::View::TT
    ppm install Config::General

To start the server (http://localhost:3000):

    perl script/hello_server.pl


Deploying to Stackato
---------------------

When pushing the application to Stackato, the dependencies are installed
automatically based on the list in requirements.txt. To push the app:

    stackato push tut2

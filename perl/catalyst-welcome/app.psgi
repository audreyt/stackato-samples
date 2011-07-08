use strict;
use MyApp;

MyApp->setup_engine('PSGI');
my $app = sub { MyApp->run(@_) };

use Plack::Builder;

builder {
   enable "Plack::Middleware::ReverseProxy";
   $app;
}

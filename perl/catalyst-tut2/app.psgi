#!perl

use strict;
use lib "lib";

use Hello;

Hello->setup_engine('PSGI');
my $app = sub { Hello->run(@_) };

# For Stackato we always live behind a ReverseProxy
use Plack::Middleware::ReverseProxy;
$app = Plack::Middleware::ReverseProxy->wrap($app);

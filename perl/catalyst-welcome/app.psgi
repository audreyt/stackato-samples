use strict;
use MyApp;

MyApp->setup_engine('PSGI');
my $app = sub { MyApp->run(@_) };

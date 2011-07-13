use strict;
use warnings;
use Test::More;

BEGIN { use_ok 'Catalyst::Test', 'Hello' }
BEGIN { use_ok 'Hello::Controller::Site' }

ok( request('/site')->is_success, 'Request should succeed' );
done_testing();

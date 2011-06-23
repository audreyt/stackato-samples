## The Movie Library sample Rails application

Komodo IDE has a tutorial that shows how to build this application.
It's a basic Rails app, with much of the code generated with
the scaffolder left in.  While the app fully runs under Rails 3,
and passes all tests, the code is more "Rails 2-ish".  Feel
free to upgrade.

This document shows how to deploy and run it on Stackato.

## Getting Started

1. Change to the directory that contains this file.

2. Make sure the Gemfile contains these two lines:

        gem 'thin'
        gem 'mysql2', '< 0.3'

   Also, the Rails tutorial in Komodo calls for adding the will_paginate plugin using a macro which wraps Rails' `plugin install' functionality. This will add this line to the Gemfile:

        gem 'will_paginate', :git => 'git://github.com/mislav/will_paginate.git', :branch => "rails3" 

    Be sure to delete it before moving to the next step.

3. After the Gemfile has been updated, type

        bundle install

4. Now install the application:

        stackato push dvdlender --runtime ruby18

The push command takes an optional --runtime option of
either "--runtime ruby18" or "--runtime ruby19".  We've
found better success with ruby18.  Either version will
run with Rails 3.0 on the server though.

Stackato will ask a few questions:

    Application Deployed URL: 'dvdlender.stackato.activestate.com'?
    
Say yes.

    Detected a Rails Application, is this correct ?  [Yn]: 
    Memory Reservation ?  (64M, 128M, 256M, 512M, or 1G):
    
The highlighted option of 256M should be fine.
    
    Creating Application: OK
    Would you like to bind any services to 'movie300' ?  [yN]: y
    Would you like to use an existing provisioned service ?  [yN]: n
    The following system services are available
    1. mongodb
    2. mysql  
    3. redis
    Please select one you wish to provision: 2
    Specify the name of the service [mysql-9a77b]:
    
Accept the name Stackato generates for the provisioned service.
    
    Creating Service: OK
    Binding Service: OK
    Uploading Application:
      Checking for available resources: OK
      Processing resources: 'OK
      Packing application: OK
      Uploading (10K): 97% OK

## That's It

Stackato will then install, stage, and start the application, and it
should be ready to run at <http://dvdlender.stackato..../movies> .

## Troubleshooting

Things don't always work perfectly the first time. Here are some tips for
diagnosing problems.

1. Stackato reports that it can't find logs/startup.log during staging (pushing)

    In this case, you can use the stackato run command to see the actual output:
    First see which log files were created:
    
        stackato run dvdlender ls -l ../logs
        
    The most informative are usually migration.log and stderr.log

2. You want to run rake, or a custom script, outside the Rails environment.

    Stackato starts up the Rails server in a specific environment.  If you
    want to run Rake, or a custom Ruby script that needs to load part or all
    of the Rails environment, it can be done via this command:
    
        stackato run dvdlender bundle exec rake <i>arguments</i>
        
    

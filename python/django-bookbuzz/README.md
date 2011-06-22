# Django application for finding tweets for current top-sellers on Amazon.com

## Before you start

You need a public access key and a secret access key from
Amazon.com to run this code.  Details are at
<https://affiliate-program.amazon.com/gp/advertising/api/detail/your-account.html>

Create a file amazon/amazonKeys.py with the following two lines:

    AccessKey = "xxxxxxxxxxxxxxxxxxxx"
    SecretAccessKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


## What the app does

The program displays the top ten bestselling books from Amazon.com
(all categories, both paper and electronic), finds tweets for each of
those books on each of those days, and uses Google Charts to show a
bar chart on how each of the top ten books for each day is doing in
terms of "buzz", where the buzz is calculated based on the book's
Amazon rank for that day, and what percentage of the tracked tweets
it got that day.

The program does not automatically update the database.  I do it via
a cronjob that runs this script periodically:

<pre>
#!/bin/sh
export PATH=# requires ActivePython 2.7 with django 1.3 and stackato client

doBooks=
doTweets=
for arg in $* ; do
  case $arg in
  -b) doBooks=1;;
  -t) doTweets=1;;
  esac
done
if [ ! -z $doBooks ] ; then
    stackato run bookbuzz python amazon/awsRequest.py -b
fi
if [ ! -z $doTweets ] ; then
    stackato run bookbuzz python amazon/awsRequest.py -t
fi
</pre>

I update the book list every four hours, the tweets every two hours.

Note that if you're using a MySQL database, you need to make sure the
database is using the utf8 default character set.  MySQL uses latin1
by default, and will sooner or later choke on an incoming tweet that
contains other Unicode characters.

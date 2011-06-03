
# Copyright (c) 2011 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

from amazon.models import Book, RankByDate, Tweet, TwitterUser
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import RequestContext #,Context, loader
from django.core.urlresolvers import reverse

import awsRequest
from awsRequest import calcAvg
import datetime

import logging
logging.basicConfig()
log = logging.getLogger("aws-views")
log.setLevel(logging.DEBUG)

def index(request):
    return redirect("/bookbuzz/showBookRankGraph")

def getTweets(request):
    try:
        return getTweets_aux(request)
    except:
        log.exception("Can't get tweets")

def getTweets_aux(request):
    params = request.GET
    asin = params['asin']
    isoStartDate = params['isoDate']
    log.debug("isoStartDate: %s", isoStartDate)
    startDate =  awsRequest.parseISODate(isoStartDate)
    endDate = startDate + datetime.timedelta(1)
    tweets = awsRequest.getTweetsForAsinInInterval(asin, startDate, endDate)
    log.debug("Got %d tweets", len(tweets))
    from django.utils import simplejson
    resultTweets = []
    for tweet in tweets:
        user = tweet.twitterUser
        info = { 'text': tweet.text,
                'id': tweet.id,
                'tweetID': tweet.tweetId,
                'name': user.userName,
                'img': user.profileImageUrl,
                'userID': user.userId }
        resultTweets.append(info)
    json = simplejson.dumps(resultTweets, indent=2)
    log.debug(" ==> json:%s", json)
    return HttpResponse(json, mimetype='application/json')
    
import os.path
containingDir=os.path.dirname(__file__)
mimeTypes = {
    ".png":"image/png",
    ".gif":"image/gif",
    ".jpg":"image/jpeg",
    ".jpeg":"image/jpeg",
    ".css":"text/css",
}
imageExts = ()

def serveStaticFile(request, path):
    # static file hack until we come up with a better way to serve
    # static files in django from stackato
    #print "serveStaticFile: %s" % (path,)
    import sys
    sys.stderr.write("serveStaticFile: %s\n" % (path,))
    fullPath = os.path.join(containingDir, "static", path);
    fd = open(fullPath, 'r')
    contents = fd.read();
    fd.close()
    fileExt = os.path.splitext(path)[1].lower()
    mimeType = mimeTypes.get(fileExt, "text/plain")
    return HttpResponse(contents, mimetype=mimeType)

def textBookList(request):
    book_list = Book.objects.all().order_by('-dateAdded')
    return render_to_response("amazon/index.django.html",
                              { 'books': book_list,
                               },
                              context_instance=RequestContext(request))

def showRanksByDate(request, date):
    return HttpResponse("showRanksByDate for %s" % (date,))
    
def showRanksForBook(request, asin):
    book = get_object_or_404(Book, asin=asin)
    ranks = RankByDate.objects.filter(book=book)
    tweets = Tweet.objects.filter(book=book)
    return render_to_response("amazon/showRanksForBook.django.html",
                              { 'book': book,
                               'ranks': ranks,
                               'tweets': tweets,
                               })

def collapsed_score(intervals):
    return calcAvg([calcAvg(numList) for numList in intervals])
    
def sortedAsinsByRank(asin_interval_scores):
    parts = [(collapsed_score(intervals.values()), asin)
              for asin, intervals in asin_interval_scores.items()]
    return [part[1] for part in sorted(parts, reverse=True)]
    
def showBookRankGraphError(msg, params):
    return render_to_response("amazon/showBookRankGraph.django.html",
                              {
                               'startDateISO': params['startDate'],
                               'endDateISO': params['endDate'],
                               'flashMessage': msg,
                               'flashLevel': 2, # 2 for error, 1 for warning, 0 for info
                               })
_isoFmt = "%Y-%m-%d"
def toYYMMDD(dt):
    return dt.strftime(_isoFmt)
    
def showBookRankGraph(request):
    params = request.GET
    startDateISO = params.get('startDate', None)
    endDateISO = params.get('endDate', None)
    synthesizedParams = {}
    if startDateISO is None or endDateISO is None:
        today = datetime.datetime.today() + datetime.timedelta(1)
        endDate = datetime.datetime.strptime(toYYMMDD(today), _isoFmt)
        startDate = endDate - datetime.timedelta(7)
        startDateISO = toYYMMDD(startDate)
        endDateISO = toYYMMDD(endDate)
        numIntervals = (endDate - startDate).days
    else:
        startDate = awsRequest.parseISODate(startDateISO)
        endDate = awsRequest.parseISODate(endDateISO) + datetime.timedelta(1)
        numIntervals = (endDate - startDate).days
        if numIntervals < 0:
            msg = "The start-date needs to come before the end-date."
        elif numIntervals < 2:
            msg = "The start and end dates must be between 2 and 14 days apart."
        elif numIntervals > 14:
            msg = "The start and end dates must be between 2 and 14 days apart."
        else:
            msg = None
        if msg:
            return showBookRankGraphError(msg, params)
        msg = awsRequest.checkRange(startDate, endDate)
        if msg:
            return showBookRankGraphError(msg, params)
    return showBookRangeGraphHelper(params, synthesizedParams, startDate, endDate, startDateISO, endDateISO, numIntervals)
    
def showBookRangeGraphHelper(params, synthesizedParams, startDate, endDate, startDateISO, endDateISO, numIntervals):
    info = awsRequest.Cmds().interval_by_day(False, startDate, endDate, numIntervals)
    class DataTable(object):
        pass
    class ColumnDescriptor(object):
        def __init__(self, columnType, value):
            self.columnType = columnType
            self.value = value
            
        def __str__(self):
            return self.value
        
        __unicode__ = __str__
            
    asin_interval_scores = info['asin_interval_scores']
    date_intervals = info['date_intervals']
    interval_asin_scores = info['interval_asin_scores']
    book_titles_by_asin = info['book_titles_by_asin']
    interval_asin_tweets = info['interval_asin_tweets']
    interval_asin_tweet_percentages = info['interval_asin_tweet_percentages']
    ranked_asins = sortedAsinsByRank(asin_interval_scores)
    dateFormatter = awsRequest.DateFormatterSelector(date_intervals)
    num_asins = len(ranked_asins)
    dataTable = DataTable()
    dataTable.addColumns = ([ColumnDescriptor('string', 'month')]
                            + [ColumnDescriptor('number', book_titles_by_asin[asin])
                               for asin in ranked_asins
                               ])
    rows = []
    for i in range(len(date_intervals)):
        this_interval = date_intervals[i]
        row = (["'%s'" % dateFormatter.format(this_interval)]
            + ["%.3g" % (calcAvg(interval_asin_scores[i].get(this_asin, []))
                         + (10.0 * interval_asin_tweet_percentages[i].get(this_asin, 0)))
               for this_asin in ranked_asins])
        rows.append(row)
    dataTable.addRows = rows
    
    asinPosTweetCounts = dict([(this_asin, []) for this_asin in ranked_asins])
    for i in range(len(date_intervals)):
        for this_asin in ranked_asins:
            tweets = interval_asin_tweets[i].get(this_asin, [])
            asinPosTweetCounts[this_asin].append(len(tweets))
    asinPosCollapsedTweetCounts = []
    for this_asin in ranked_asins:
        asinPosCollapsedTweetCounts.append(",".join([str(a) for a in asinPosTweetCounts[this_asin]]))
    dataTable.asinPosCollapsedTweetCounts = asinPosCollapsedTweetCounts
        
    import pprint
    print "Hey, dataTable.rows...."
    pprint.pprint(dataTable.addRows)
    books = Book.objects.all()
    book_dict = dict([(bookObject.asin, bookObject) for bookObject in books])
    import sys
    sys.stderr.write("medium urls: %s\n" %
                     ", ".join([book_dict[asin].mediumProductImageURL for asin in ranked_asins]))
    prevWeekStartDate = startDate - datetime.timedelta(numIntervals)
    prevWeekEndDate = startDate;
    prevWeekLinkOK = not awsRequest.checkRange(prevWeekStartDate, prevWeekEndDate)
    nextWeekStartDate = endDate
    nextWeekEndDate = endDate + datetime.timedelta(numIntervals)
    nextWeekLinkOK = not awsRequest.checkRange(nextWeekStartDate, nextWeekEndDate)
    return render_to_response("amazon/showBookRankGraph.django.html",
                              { 'book_asins': ranked_asins,
                               'book_titles': [book_titles_by_asin[asin] for asin in ranked_asins],
                               'product_small_urls': [book_dict[asin].smallProductImageURL for asin in ranked_asins],
                               'product_medium_urls': [book_dict[asin].mediumProductImageURL for asin in ranked_asins],
                               'startDate': startDate,
                               'endDate': endDate,
                               'isoDates': [toYYMMDD(dt) for dt in date_intervals],
                               'startDateISO': startDateISO,
                               'endDateISO': endDateISO,
                               'endDateSub1ISO': toYYMMDD(endDate - datetime.timedelta(1)),
                               'dataTable': dataTable,
                               'prevWeekStartDate': toYYMMDD(prevWeekStartDate),
                               'prevWeekEndDate': toYYMMDD(prevWeekEndDate),
                               'prevWeekLinkOK': prevWeekLinkOK,
                               'nextWeekStartDate': toYYMMDD(nextWeekStartDate),
                               'nextWeekEndDate': toYYMMDD(nextWeekEndDate),
                               'nextWeekLinkOK': nextWeekLinkOK,
                               })
    
def showTweetsForBook(request):
    params = request.GET
    asin = params['asin']
    startDateISO = params['startDate']
    endDateISO = params['endDate']
    startDate = awsRequest.parseInterval(startDateISO)
    endDate = awsRequest.parseInterval(endDateISO)
    numIntervals = getReasonableIntervalCount(startDate, endDate)
    info = awsRequest.Cmds().interval_by_day(False, startDate, endDate, numIntervals)
    class DataTable(object):
        pass
    class ColumnDescriptor(object):
        def __init__(self, columnType, value):
            self.columnType = columnType
            self.value = value
            
        def __str__(self):
            return self.value
        
        __unicode__ = __str__
    book = get_object_or_404(Book, asin=asin)
    ranks = RankByDate.objects.filter(book=book)
    tweets = Tweet.objects.filter(book=book)
    return render_to_response("amazon/showRanksForBook.django.html",
                              { 'book': book,
                               'ranks': ranks,
                               'tweets': tweets,
                               })
        

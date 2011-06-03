#!python
# Copyright (c) 2011 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

import re
import urllib
import hmac, hashlib, base64
import sys
import time
import pprint

from os.path import dirname
parentDir = dirname(dirname(__file__))
sys.path.append(parentDir)

import logging
logging.basicConfig()
log = logging.getLogger("aws-test")
log.setLevel(logging.DEBUG)

from os.path import dirname
parentDir = dirname(dirname(__file__))
sys.path.append(parentDir)
import elementtree.ElementTree as ET

class AWSRequester(object):
    try:
        from amazonKeys import AccessKey, SecretAccessKey
    except LoadError:
        raise Exception("""Create a file called amazonKeys.py in the same directory
                        as awsRequest.py with the following two variables:
                        AccessKey = "xxxxxxxxxxxxxxxxxxxx"
                        SecretAccessKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                        """)
    host = "ecs.amazonaws.com"
    onca = "/onca/xml"
    BaseTemplate = {
        "Service": "AWSECommerceService",
        "AWSAccessKeyId": AccessKey,
        "Version": "2009-03-31",
    }
    AWS_NS = '{http://webservices.amazon.com/AWSECommerceService/2009-03-31}'
    
    def makeCanonicalQuery(self, template):
        return urllib.urlencode(sorted(template.items()))
        
    def sign(self, secret, message):
        digest = hmac.new(key=self.SecretAccessKey, msg=message,
                      digestmod=hashlib.sha256).digest()
        return urllib.quote_plus(base64.encodestring(digest).strip())
        
    def doRequest(self, requesterFunc, extractor):
        template = self.BaseTemplate.copy()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        requesterFunc(template)
        template["Timestamp"] = timestamp
        canonicalQuery = self.makeCanonicalQuery(template)
        print canonicalQuery
        stringToSign = "GET\n%s\n%s\n%s" % (self.host, self.onca, canonicalQuery)
        signature = self.sign(self.SecretAccessKey, stringToSign)
        signedURL = "http://%s%s?%s&Signature=%s" % (self.host, self.onca, canonicalQuery, signature)
        f = urllib.urlopen(signedURL)
        tree = ET.parse(f)  # ET.tostring(tree.getroot())
        f.close()
        try:
            return extractor(tree)
        except TypeError:
            nodes = tree.getroot().findall(extractor)
        a = []
        for node in nodes:
            data = {}
            for elt in node:
                tag_name = elt.tag
                val = elt.text
                if tag_name.startswith(self.AWS_NS):
                    tag_name = tag_name[len(self.AWS_NS):]
                data[tag_name] = elt.text
            a.append(data)
        return a
    
    def _bestSellingBooksRequester(self, template):
        template["Operation"] = "BrowseNodeLookup"
        template["BrowseNodeId"] = "283155"
        template["ResponseGroup"] = "TopSellers"
    
    def requestBestSellingBooks(self):
        xpathExpression = ".//%sTopItemSet/%sTopItem" % (self.AWS_NS, self.AWS_NS)
        return self.doRequest(self._bestSellingBooksRequester, xpathExpression)
    
    def _bookRankRequester(self, template):
        template["Operation"] = "ItemLookup"
        template["ResponseGroup"] = "SalesRank,Images"
        template["ItemId"] = ",".join(self._asins)
        
    _amazonToBookBuzz = {
        "SmallImage": "smallProductImageURL",
        "MediumImage": "mediumProductImageURL",
    }
    def extractBookInfo(self, tree):
        xpathExpression = ".//%sItems/%sItem" % (self.AWS_NS, self.AWS_NS)
        nodes = tree.getroot().findall(xpathExpression)
        a = []
        for node in nodes:
            data = {}
            for elt in node:
                tag_name = elt.tag
                if tag_name.startswith(self.AWS_NS):
                    tag_name = tag_name[len(self.AWS_NS):]
                if tag_name in ("ASIN", "SalesRank"):
                    data[tag_name] = elt.text
                elif tag_name in (self.AWS_NS + "SmallImage", self.AWS_NS + "MediumImage",
                                  "SmallImage", "MediumImage"):
                    urlNodes = [node2 for node2 in elt.getchildren()
                                if node2.tag in (self.AWS_NS + "URL", "URL")]
                    if len(urlNodes) == 1:
                        data[self._amazonToBookBuzz[tag_name]] = urlNodes[0].text
            a.append(data)
        return a
    
    def requestBookRank(self, asins):
        self._asins=asins
        return self.doRequest(self._bookRankRequester, self.extractBookInfo)
    
import os
os.environ['PYTHONPATH'] = parentDir
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from amazon.models import Book, RankByDate, TwitterUser, Tweet
import datetime

_VERBOSE_QUIET =0
_VERBOSE_MAX   =1

def updateDailyRanks(verbose=_VERBOSE_QUIET):
    if verbose==_VERBOSE_MAX:
        log.debug(">> updateDailyRanks")
    numBooksAdded = 0
    today = datetime.datetime.today()
    log.debug("Current # of books: %d", Book.objects.count())
    if False and Book.objects.count() > 0:
        fourHourDiff = datetime.timedelta(0, 0, 0, 0, 55, 3) # cron runs every 4 hours
        fourHoursAgo = today - fourHourDiff
        recentChangedBooks = Book.objects.filter(dateAdded__gte=fourHoursAgo)
        if verbose==_VERBOSE_MAX:
            log.debug("# recentChangedBooks: %d", len(recentChangedBooks))
        if len(recentChangedBooks):
            return 0
    req = AWSRequester()
    bookInfo = req.requestBestSellingBooks()
    if verbose==_VERBOSE_MAX:
        log.debug("requestBestSellingBooks => %s", bookInfo)
    asins = [item['ASIN'] for item in bookInfo]
    asinInfo = req.requestBookRank(asins)
    if verbose==_VERBOSE_MAX:
        log.debug("requestBookRank => %s", asinInfo)
    rankDict = dict([(c["ASIN"], c["SalesRank"]) for c in asinInfo])
    asinInfoByAsin = dict([(c["ASIN"], c) for c in asinInfo])
    for b in bookInfo:
        asin = b['ASIN']
        currentBook = None
        try:
            currentBook = Book.objects.get(asin=asin)
        except Book.DoesNotExist:
            pass
        except:
            log.exception("huh????")
        if currentBook:
            if verbose==_VERBOSE_MAX:
                log.debug("Update current book: %s", b['Title'])
            currentBook.dateAdded = today
            if not currentBook.smallProductImageURL:
                log.debug("Adding small URL for %s", b['Title'])
                currentBook.smallProductImageURL = asinInfoByAsin[asin]['smallProductImageURL']
            if not currentBook.mediumProductImageURL:
                log.debug("Adding medium URL for %s", b['Title'])
                currentBook.mediumProductImageURL = asinInfoByAsin[asin]['mediumProductImageURL']
        else:
            if verbose==_VERBOSE_MAX:
                log.debug("Add new book: %s", b['Title'])
            currentBook = Book(title=b['Title'],
                     author=b['Author'],
                     asin=asin,
                     productGroup=b['ProductGroup'],
                     dateAdded=today,
                     smallProductImageURL=asinInfoByAsin[asin]['smallProductImageURL'],
                     mediumProductImageURL=asinInfoByAsin[asin]['mediumProductImageURL'])
            numBooksAdded += 1
        currentBook.save()
        try:
            r = RankByDate(book=currentBook, rank=rankDict[asin], dateStamp=today)
            r.save()
        except KeyError:
            log.exception("Can't get key for rank")
        except:
            log.exception("huh????")
    return numBooksAdded

import urllib
import json

# Prob should be in a database
_spammers = {
            "AllTimeAmazon": 1,
            "AmazonFineShop": 1,
            "AmazonFull": 1,
            "AmazonGreat": 1,
            "amazonretail": 1,
            "AmazonWeekStore": 1,
            "AssociateAmazon": 1,
            "DealsSmashing": 1,
            "ExtraAmazon": 1,
            "john_willia": 1,
            "OnlineAmazon": 1,
            "OnlyAmazon": 1,
            "plastic_noodles": 1,
            "ProductTop":1,
            "RSchnieder": 1,
            "ShopAmazonDaily": 1,
}

# replace short URIs...

_linkStart_re = re.compile(r'''\A<[^>]*?href=["']\Z''')
_splitter = re.compile(r'''(<[^>]*?href=["']|http://[^"' \t]+)''')
def makeSafeViewableHTML(text):
    revEnts = (
        ('&lt;', '<'),
        ('&gt;', '>'),
        ('&quot;', '"'),
        ('&apos;', '\''),
        ('&amp;', '&'),
    )
    for src, dest in revEnts:
        text = text.replace(src, dest)
    pieces = [x for x in _splitter.split(text) if x]
    lim = len(pieces)
    piece = pieces[0]
    madeChange = False
    for i in range(1, lim):
        prevPiece = piece
        piece = pieces[i]
        if piece.startswith('http://') and not _linkStart_re.match(prevPiece):
            pieces[i] = """<a href="%s">%s</a>""" % (piece, piece)
            madeChange = True
    #TODO: Watch out for on* attributes and script & style tags
    return madeChange and "".join(pieces) or text

def getTweetsForAsinInInterval(asin, startDate, endDate):
    return Tweet.objects.all().filter(book__asin=asin, createdAt__gte=startDate).\
                    exclude(createdAt__gte=endDate)
    
def updateRecentTweetsForBook(book, verbose=_VERBOSE_QUIET):
    """
    updateRecentTweetsForBook(book, verbose=0)
    verbose levels: 0: no output, 1: error output, 2: debug output
    """
    numTweetsAdded = 0
    delay = 2
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(5)
    url_base = 'http://search.twitter.com/search.json'
    title = book.title
    idx = title.find(":")
    if idx > 10:
        # Twitter will complain that the query is too complex
        title = title[:idx]
    else:
        idx = title.find("(")
        if idx > 10:
            title = title[:idx]
    search_part = ('q=%s+%s'
           % (urllib.quote_plus(book.author),
              urllib.quote_plus(title)))
    url = url_base + "?" + search_part
    while True:
        fd = urllib.urlopen(url)
        data = json.load(fd)
        fd.close()
        next_page = data.get('next_page', None)
        num_used = 0
        results = data.get('results')
        if verbose==_VERBOSE_MAX:
            log.debug("url %s => data %r chars", url, len(data))
        if results is None:
            if verbose==_VERBOSE_MAX:
                log.debug("No more results")
            break
        for result in results:
            userName=result['from_user']
            if _spammers.get(userName, None):
                if verbose==_VERBOSE_MAX:
                    log.debug("Skip spammer %s", userName)
                # Skip the tweet but count a use in case there are
                # older tweets on the next page
                num_used += 1
                continue
            userId = result['from_user_id_str']
            tweetId = result['id']
            if verbose==_VERBOSE_MAX:
                log.debug("process tweet from user %s id %s", userId, tweetId)
            # Did we already process this tweet?
            try:
                currentTweet = Tweet.objects.get(tweetId=tweetId)
                if verbose==_VERBOSE_MAX:
                    log.debug("Already saw this tweet")
                continue
            except Tweet.DoesNotExist:
                num_used += 1
                # Add a twitter user if we don't have one yet
                try:
                    twitterUser = TwitterUser.objects.get(userId=userId)
                except TwitterUser.DoesNotExist:
                    twitterUser = TwitterUser(userId=userId,
                                              userName=userName,
                                              profileImageUrl = result['profile_image_url'])
                    twitterUser.save()
                except:
                    log.exception("huh - prob looking twitter user %s", result['from_user'])
                # Enter the tweet
                rawCreationTime=result['created_at']
                # Python 2.7: replace +0000 with %z
                parsedTime = datetime.datetime.strptime(rawCreationTime, "%a, %d %b %Y %H:%M:%S +0000")
                if parsedTime < yesterday:
                    if verbose==_VERBOSE_MAX:
                        log.debug("tweet's too old: %s", rawCreationTime)
                    continue
                text = makeSafeViewableHTML(result['text'])
                if verbose==_VERBOSE_MAX:
                    log.debug("Save tweet: text:%s(%d), book:%s(%d), user:%r, id:%r",
                          text, len(text),
                          book, len(book.title),
                          twitterUser,
                          tweetId)
                try:
                    currentTweet = Tweet(text=text,
                                         book=book,
                                         twitterUser=twitterUser,
                                         createdAt=parsedTime,
                                         tweetId=tweetId)
                    currentTweet.save()
                    numTweetsAdded += 1
                except:
                    log.exception("Can't save a tweet (text:%s(%d))", text, len(text))
            except:
                log.exception("huh - prob looking up a tweet")
        if not num_used:
            break
        if next_page is None or 'page=20' in next_page:
            if verbose==_VERBOSE_MAX:
                log.debug("Stop processing with next page of %r", next_page)
            break
        url = url_base + next_page + search_part
        time.sleep(delay)
    return numTweetsAdded

    
def updateRecentTweets(verbose):
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(5)
    recentChangedBooks = Book.objects.filter(dateAdded__gte=yesterday)
    numTweetsAdded = 0
    for book in recentChangedBooks:
        numTweetsAdded += updateRecentTweetsForBook(book, verbose)
    return numTweetsAdded

def updateTweetByAsin(verbose, asin):
    try:
        book = Book.objects.get(asin=asin)
        return updateRecentTweetsForBook(book, verbose)
    except:
        return 0

# Map the best score (1) to 10
# Lowest score (10) gets mapped to 1
# Anything off the chart will get a 0

def adjustScore(score):
    return 11 - score

def calc_epoch_and_interval_width(dt_start, dt_end, num_intervals):
    st_ord = dt_start.toordinal()
    end_ord = dt_end.toordinal()
    num_days = end_ord - st_ord
    if num_days <= 0:
        raise Exception("Invalid: start-day must be < end-day")
    epoch_st = time.mktime(dt_start.timetuple())
    epoch_end = time.mktime(dt_end.timetuple())
    interval_width = (epoch_end - epoch_st) * 1.0 / num_intervals
    return epoch_st, epoch_end, interval_width

def get_tweet_interval_for_asin(verbose, dt_start, dt_end, num_intervals, asin):
    if num_intervals <= 0:
        raise Exception("Invalid: get_tweet_interval_for_asin: num_intervals:%d", num_intervals)
    epoch_st, epoch_end, interval_width = calc_epoch_and_interval_width(dt_start, dt_end, num_intervals)
    time_next = epoch_st
    this_dt_end = datetime.datetime.fromtimestamp(time_next)
    interval_no = -1
    interval_tweets = {}
    date_intervals = []
    while True:
        interval_no += 1
        this_dt_st = this_dt_end
        time_next += interval_width
        this_dt_end = datetime.datetime.fromtimestamp(time_next)
        if this_dt_st >= dt_end:
            break
        date_intervals.append(this_dt_st)
        if this_dt_end > dt_end:
            this_dt_end = dt_end
        tweets = Tweet.objects.all().filter(book__asin=asin, createdAt__gte=this_dt_st).\
                        exclude(createdAt__gte=this_dt_end)
        interval_tweets[interval_no] = []
        print "Interval %d: %d tweets" % (interval_no, len(tweets))
        for tweet in tweets:
            interval_tweets[interval_no].append(tweet)
        
    retObj = {
        'interval_tweets': interval_tweets,
        'date_intervals': date_intervals,
    }
    return retObj
    
class Cmds(object):
    """
    updateTweets [asin...] update tweets (for asins if provided)
    
    updateBooks
    """
    
    def updateBooks(self, verbose, args):
        numBooksAdded = updateDailyRanks(verbose)
        print "Added %d book%s" % (numBooksAdded, numBooksAdded != 1 and "s" or "")
        
    _asin_spliter = re.compile(r'[\s,]+')
    def updateTweets(self, verbose, asins):
        if len(asins) > 0:
            numTweetsAdded = 0
            for asin in asins:
                numTweetsAdded +=  updateTweetByAsin(verbose, asin)
        else:
            numTweetsAdded = updateRecentTweets(verbose)
        print "Added %d tweet%s" % (numTweetsAdded, numTweetsAdded != 1 and "s" or "")
        
    def do_test(self):
        req = AWSRequester()
        res = req.requestBestSellingBooks()
        print res
        #asins = [item['ASIN'] for item in res]
        asins = ['B002YKOXB6', 'B002MQYOFW', 'B004PYDO64']
        try:
            res = req.requestBookRank(asins)
            print res
        except:
            log.exception("Error getting info")

    def interval_by_day(self, verbose, dt_start, dt_end, num_intervals=10, cull_scores=10):
        """
        cull_scores: allow at most these many scores per interval for rank info
        """
        if num_intervals <= 0:
            raise Exception("Invalid: do_interval_by_day: num_intervals:%d", num_intervals)
        # Adjust the times we search with
        tzDiff = datetime.datetime.utcnow() - datetime.datetime.today()
        # The database stores all timestamps in terms of UTC, but the server could
        # be on a different time.  
        # This keeps us from being able to "search into the future"
        # If we know a tweet was published an hour ago and it's late in the day (where the server is),
        # the server will treat it as if it was published today and not tomorrow.
        # It would be better to get the user's timezone field, and use that instead of
        # where the server lives.
        epoch_st, epoch_end, interval_width = \
            calc_epoch_and_interval_width(dt_start + tzDiff, dt_end + tzDiff, num_intervals)
        time_next = epoch_st
        this_dt_end = datetime.datetime.fromtimestamp(time_next)
        interval_no = -1
        interval_asin_count = {}
        interval_tweets = {}
        interval_asin_tweets = []
        interval_asin_tweet_percentages = []
        asin_interval_count = {}
        interval_asin_scores = {}
        asin_interval_scores = {}
        date_intervals = []
        book_titles_by_asin = dict([(book.asin, book.title) for book in Book.objects.all()])
        while True:
            interval_no += 1
            this_dt_st = this_dt_end
            time_next += interval_width
            this_dt_end = datetime.datetime.fromtimestamp(time_next)
            if this_dt_st >= dt_end:
                break
            date_intervals.append(this_dt_st)
            if this_dt_end > dt_end:
                this_dt_end = dt_end
            tweets = Tweet.objects.all().filter(createdAt__gte=this_dt_st).\
                            exclude(createdAt__gte=this_dt_end)
            interval_asin_count[interval_no] = {}
            interval_tweets[interval_no] = []
            interval_asin_tweets.append({})
            print "Interval %d: %d tweets" % (interval_no, len(tweets))
            for tweet in tweets:
                asin = tweet.book.asin
                interval_asin_count[interval_no].setdefault(asin, 0)
                interval_asin_count[interval_no][asin] += 1
                asin_interval_count.setdefault(asin, {}).setdefault(interval_no, 0)
                asin_interval_count[asin][interval_no] += 1
                interval_tweets[interval_no].append(tweet)
                interval_asin_tweets[interval_no].setdefault(asin, []).append(tweet)
            this_interval_asin_tweets = interval_asin_tweets[interval_no]
            num_tweets_this_interval = len(interval_tweets[interval_no])
            this_asin_tweet_percentages = dict([(asin, len(tweets) * 1.0 / num_tweets_this_interval)
                                                for asin, tweets in this_interval_asin_tweets.items()])
            interval_asin_tweet_percentages.append(this_asin_tweet_percentages)
            ranks = RankByDate.objects.filter(dateStamp__gte=this_dt_st).\
                            exclude(dateStamp__gte=this_dt_end).exclude(rank__gte=11)
            interval_asin_scores[interval_no] = {}
            for rank in ranks:
                asin = rank.book.asin
                score = rank.rank
                adjusted_score = adjustScore(score)
                interval_asin_scores[interval_no].setdefault(asin, []).append(adjusted_score)
                asin_interval_scores.setdefault(asin, {}).setdefault(interval_no, []).append(adjusted_score)
        if cull_scores:
            cullScores(interval_asin_scores, asin_interval_scores, interval_asin_tweets, cull_scores)
        retObj = {
            'interval_asin_count':interval_asin_count,
            'interval_tweets': interval_tweets,
            'asin_interval_count': asin_interval_count,
            'interval_asin_scores':interval_asin_scores,
            'asin_interval_scores':asin_interval_scores,
            'date_intervals': date_intervals,
            'book_titles_by_asin': book_titles_by_asin,
            'interval_asin_tweets': interval_asin_tweets,
            'interval_asin_tweet_percentages': interval_asin_tweet_percentages,
        }
        return retObj

def getCutOff(scores, numToKeep):
    scores = sorted(scores, reverse=True)
    if 1:
        badScore = scores[numToKeep]
        if badScore == scores[numToKeep - 1]:
            while numToKeep < len(scores) - 1:
                numToKeep += 1
                if scores[numToKeep] < badScore:
                    break
        return scores[numToKeep]
    else:
        return scores[-1]

def cullScores(interval_asin_scores, asin_interval_scores, interval_asin_tweets,
               cull_scores):
    for interval_no in range(len(interval_asin_scores.keys())):
        asinAvgScores = {}
        for asin, scores in interval_asin_scores[interval_no].items():
            asinAvgScores[asin] = calcAvg(scores)
        if len(asinAvgScores.keys()) > cull_scores:
            cutOffScore = getCutOff(asinAvgScores.values(), cull_scores)
            for asin, score in asinAvgScores.items():
                if score < cutOffScore:
                    del interval_asin_scores[interval_no][asin]
                    del asin_interval_scores[asin][interval_no]
                    del interval_asin_tweets[interval_no][asin]
            

def report_tweetCount_by_interval(interval_asin_count, asin_interval_count,
                                  book_titles_by_asin,
                         date_intervals):
    print "date_intervals:"
    dateFormatter = DateFormatterSelector(date_intervals)
    pprint.pprint(date_intervals)
    print "interval_asin_count"
    pprint.pprint(interval_asin_count)
    asins = sorted(asin_interval_count.keys())
    num_asins = len(asins)
    dataTable = []
    rowItem = ('string', 'month') # dynamic
    row = [rowItem] + [('number', book_titles_by_asin[asin]) for asin in asins]
    dataTable = [('addColumn', False, row)]
    rows = []
    for i in range(len(date_intervals)):
        this_row = [dateFormatter.format(date_intervals[i])]
        this_interval = interval_asin_count[i]
        for this_asin in asins:
            score = this_interval.get(this_asin, 0)
            this_row.append(score)
        rows.append(this_row)
    dataTable.append(('addRow', True, rows))
    pprint.pprint(dataTable)
    renderJSGraph(dataTable)
    
def calcAvg(array):
    if not array:
        return 0
    return (sum(array) * 1.0)/len(array)
    
def report_rank_by_interval(interval_asin_scores, asin_interval_scores,
                            book_titles_by_asin,
                            date_intervals):
    dateFormatter = DateFormatterSelector(date_intervals)
    asins = sorted(asin_interval_scores.keys())
    num_asins = len(asins)
    dataTable = []
    rowItem = ('string', 'month') # dynamic
    row = [rowItem] + [('number', book_titles_by_asin[asin]) for asin in asins]
    dataTable = [('addColumn', False, row)]
    rows = []
    for i in range(len(date_intervals)):
        this_row = [dateFormatter.format(date_intervals[i])]
        this_interval = interval_asin_scores[i]
        for this_asin in asins:
            score = calcAvg(this_interval.get(this_asin, []))
            this_row.append(score)
        rows.append(this_row)
    dataTable.append(('addRow', True, rows))
    pprint.pprint(dataTable)
    renderJSGraph(dataTable)
    
def renderJSGraph(dataTable):
    print "*" * 44 + " data table:"
    for op, isArray, items in dataTable:
        aStart = isArray and "[" or ""
        aEnd = isArray and "]" or ""
        for item in items:
            if isinstance(item, (tuple, list)):
                payload = ", ".join([deUnicode("%r" % x)for x in item])
            else:
                payload = item
            print "  data.%s(%s%s%s);" % (op, aStart, payload, aEnd)
            
def renderRankByDate():
    print """
    var chart = new google.visualization.LineChart(document.getElementById('visualization'));
    chart.draw(data, {curveType: "function",
                    title: "Tweets per day",
                    enableEvents: true,
                    width: 500, height: 400, min:0,
                    vAxis: {maxValue: 50, minValue: 0}}
            );
    google.visualization.events.addListener(chart, 'select', function(event) {
        var row = chart.getSelection()[0].row();
    });
      var thing = window._chart.;
      var row = thing.row;
      var column = thing.column;
      alert("row: " + row + ", column: " + column);
   }
    """

class DateFormatterSelector(object):
    def __init__(self, date_intervals):
        self._prevDate = None
            
    def format(self, dt):
        if self._prevDate == None:
            s = dt.strftime("%b %d, %Y")
        elif self._prevDate.year < dt.year:
            s = dt.strftime("%b %d, %Y")
        elif self._prevDate.month < dt.month:
            s = dt.strftime("%b %d")
        else:
            s = dt.strftime("%m/%d")
        self._prevDate = dt
        return s
        
def deUnicode(s):
    if isinstance(s, str) and s[0] == 'u':
        return s[1:]
    return s

def parseISODate(isoDate):
    isoDate = re.compile(r'[ T]').split(isoDate)[0]
    return datetime.datetime.strptime(isoDate, "%Y-%m-%d")
    
_dash2Splitter = re.compile("--")
def parseInterval(rawInterval):
    parts = _dash2Splitter.split(rawInterval)
    return [parseISODate(part) for part in parts]

def collapsed_score(intervals):
    return calcAvg([calcAvg(numList) for numList in intervals])
    
def sortedAsinsByRank(asin_interval_scores):
    parts = [(collapsed_score(intervals.values()), asin)
              for asin, intervals in asin_interval_scores.items()]
    return [part[1] for part in sorted(parts, reverse=True)]
    
def checkRange(startDate, endDate):
    tweets = Tweet.objects.all().order_by("createdAt")
    if tweets[0].createdAt > endDate:
        return "There are no tweets before %s" % tweets[0].createdAt.date()
    lastTweet = tweets[len(tweets) -1]
    if lastTweet.createdAt < startDate:
        return "There are no tweets after %s" % lastTweet.createdAt.date()
  
#@temporary          
def showBookRankGraph(info):
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
    ranked_asins = sortedAsinsByRank(asin_interval_scores)
    dateFormatter = DateFormatterSelector(date_intervals)
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
            + [calcAvg(interval_asin_scores[i].get(this_asin, []))
               for this_asin in ranked_asins])
        rows.append(row)
    dataTable.addRows = rows
    import pprint
    print "Hey, dataTable.rows...."
    pprint.pprint(dataTable.addRows)
    print "Hey, dataTable.addColumns...."
    pprint.pprint(dataTable.addColumns)
    
#@temporary 
def getReasonableIntervalCount(startDate, endDate):
    return 10 # can do better by looking at the dates
#@temporary 
def showTweetsForBook(info):
    print "Stop here"
    class DataTable(object):
        pass
    class ColumnDescriptor(object):
        def __init__(self, columnType, value):
            self.columnType = columnType
            self.value = value
            
        def __str__(self):
            return self.value
        
        __unicode__ = __str__
        
    dateFormatter = DateFormatterSelector(date_intervals)
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
            + [calcAvg(interval_asin_scores[i].get(this_asin, []))
               for this_asin in ranked_asins])
        rows.append(row)
    dataTable.addRows = rows
    import pprint
    print "Hey, dataTable.rows...."
    pprint.pprint(dataTable.addRows)
    print "Hey, dataTable.addColumns...."
    pprint.pprint(dataTable.addColumns)
    book = get_object_or_404(Book, asin=asin)
    ranks = RankByDate.objects.filter(book=book)
    tweets = Tweet.objects.filter(book=book)
    return render_to_response("amazon/showRanksForBook.django.html",
                              { 'book': book,
                               'ranks': ranks,
                               'tweets': tweets,
                               })
def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose",
                      help="default 0: low, 1, 2",
                      action="store_true")
    parser.add_option("--test", dest="doTest",
                      action="store_true")
    parser.add_option("-t", "--updateTweets", dest="updateTweets",
                      action="store_true")
    parser.add_option("-b", "--updateBooks", dest="updateBooks",
                      action="store_true")
    parser.add_option("-a", "--asin", dest="asin")
    #@temporary    
    parser.add_option("-g", "--showBookRankGraph", dest="showBookRankGraph",
                      action="store_true")
    parser.add_option("-w", "--showTweetsForBook", dest="showTweetsForBook",
                      action="store_true")
    parser.add_option("-d", "--dayInterval", dest="dayInterval",
                      help="eg -d 2011-05-22T00:00:00--2011-05-29T00:00:00")
    parser.add_option("-n", "--numIntervals", dest="numIntervals")
    (options, args) = parser.parse_args()

    cmdClass =  Cmds()
    didSomething = False
    if options.doTest:
        cmdClass.do_test()
        return
    if options.updateBooks:
        cmdClass.updateBooks(options.verbose, args)
        didSomething = True
    if options.updateTweets:
        cmdClass.updateTweets(options.verbose, args)
        didSomething = True
    #@temporary          
    if options.showBookRankGraph:
        if not options.dayInterval:
            dt_start = datetime.datetime(2011, 5, 24)
            dt_end = datetime.datetime(2011, 5, 27)
        else:
            dt_start, dt_end = parseInterval(options.dayInterval)
        if not options.numIntervals:
            delta = dt_end - dt_start
            secondsPerDay = 3600 * 24
            options.numIntervals = int(((delta.days * secondsPerDay + delta.seconds) * 1.0
                                        + secondsPerDay/2 - 1) / secondsPerDay)
        info = cmdClass.interval_by_day(options.verbose, dt_start, dt_end,
                                 int(options.numIntervals))
        showBookRankGraph(info)
        return
    #@temporary          
    if options.showTweetsForBook:
        if not options.asin:
            options.asin = 'B004PYDO64' # Water for Chocolate kindle book
        if not options.dayInterval:
            dt_start = datetime.datetime(2011, 5, 24)
            dt_end = datetime.datetime(2011, 5, 27)
        else:
            dt_start, dt_end = parseInterval(options.dayInterval)
        if not options.numIntervals:
            options.numIntervals = getReasonableIntervalCount(dt_start, dt_end)
        info = get_tweet_interval_for_asin(options.verbose, dt_start, dt_end,
                                           int(options.numIntervals),
                                           options.asin)
        showTweetsForBook(info)
        return
    if options.dayInterval:
        if not options.numIntervals:
            options.numIntervals = 10
        dt_start, dt_end = parseInterval(options.dayInterval)
        
        info = cmdClass.interval_by_day(options.verbose, dt_start, dt_end,
                                 int(options.numIntervals))
        report_tweetCount_by_interval(info['interval_asin_count'],
                                      info['asin_interval_count'],
                                      info['book_titles_by_asin'],
                                      info['date_intervals']);
        print "aws rank by interval:"
        report_rank_by_interval(info['interval_asin_scores'],
                                info['asin_interval_scores'],
                                info['book_titles_by_asin'],
                                info['date_intervals']);
        didSomething = True
    if not didSomething:
        print "Unexpected input: %s" % (dir(options) + ["::"] + args)

if __name__ == "__main__":
    sys.exit(main())

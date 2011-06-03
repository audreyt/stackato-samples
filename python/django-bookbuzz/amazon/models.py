
# Copyright (c) 2011 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

from django.db import models

# Create your models here.

class Book(models.Model):
    title = models.CharField(max_length=256)
    author = models.CharField(max_length=256)
    asin = models.CharField(max_length=10)
    productGroup = models.CharField(max_length=32)
    dateAdded = models.DateTimeField('date_added')
    smallProductImageURL = models.CharField(max_length=256)
    mediumProductImageURL = models.CharField(max_length=256)
    
    def __unicode__(self):
        return "[%s:%s:%s (%s)]" % (self.title, self.author, self.asin, self.productGroup)
    
class RankByDate(models.Model):
    book = models.ForeignKey(Book)
    rank = models.IntegerField()
    dateStamp = models.DateTimeField()
    
    def __unicode__(self):
        return "[%s:%s (%s)]" % (self.book.asin, self.rank, self.dateStamp)
        
class TwitterUser(models.Model):
    userId = models.CharField(max_length=16)
    userName = models.CharField(max_length=128)
    profileImageUrl = models.URLField()

    def __unicode__(self):
        return "[%s:%s (%s)]" % (self.userName, self.userId, self.profileImageUrl)
        
class Tweet(models.Model):
    text = models.CharField(max_length=300) # Allow URL duplication
    book = models.ForeignKey(Book)
    twitterUser = models.ForeignKey(TwitterUser)
    createdAt = models.DateTimeField('time_added')
    tweetId = models.CharField(max_length=32)

    def __unicode__(self):
        return "[%s:%s => %s (%s)]" % (self.twitterUser.userName, self.text, self.book.title, self.createdAt)
    

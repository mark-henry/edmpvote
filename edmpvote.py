# Datastore schema

__author__ = '/u/mark-henry'

from google.appengine.api import users
from google.appengine.ext import ndb

class Entry(ndb.Model):
  """Models a competition entry"""
  author = ndb.StringProperty(required=True)
  url = ndb.StringProperty(required=True)

class Vote(ndb.Model):
  """Models a entryid-value pair"""
  entryid = ndb.StringProperty('i', required=True)
  value = ndb.IntegerProperty('v', required=True)

class Ballot(ndb.Model):
  """Models a user's votes for a specific competition"""
  voterid = ndb.StringProperty(required=True)
  votes = ndb.StructuredProperty(Vote, repeated=True)

class Poll(ndb.Model):
  """Models a poll containing entries and votes"""
  title = ndb.StringProperty(required=True)
  entries = ndb.KeyProperty(kind=Entry, repeated=True)
  voting_enabled = ndb.BooleanProperty(required=True, default=False)
  end_date = ndb.DateTimeProperty()
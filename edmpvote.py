# Datastore models and other common stuff

__author__ = '/u/mark-henry'

import os, logging

from google.appengine.ext import ndb

import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'])

DEBUG_MODE = True
SCORE_RANGE = 10

def err(args):
  logging.error("\n>>DEBUG: %s" % args)

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
  voting_enabled = ndb.BooleanProperty(required=True, default=False)
  end_date = ndb.DateTimeProperty()

class DefaultPoll(ndb.Model):
  """A single DefaultPoll instance contains a reference to the default poll, which is displayed
      by the vote page when no poll is specified."""
  default_poll_key = ndb.KeyProperty(kind=Poll)

def getDefaultPollObject():
  """Returns an object containing a reference to the default poll"""
  query_results = DefaultPoll.query().fetch()
  if query_results:
    return query_results[0]
  else:
    # Initialize the default poll object if it does not exist
    err("initted deef poll")
    default_poll = DefaultPoll()
    default_poll.put()
    return default_poll

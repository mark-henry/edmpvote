"""Datastore models and other common stuff"""

import os
import logging

from google.appengine.ext import ndb

import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

DEBUG_MODE = False
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
    created = ndb.DateTimeProperty(auto_now_add=True)
    end_date = ndb.DateTimeProperty()


class DefaultPoll(ndb.Model):
    """A single DefaultPoll instance contains a reference to the default poll, which is displayed
      by the vote page when no poll is specified."""
    poll_key = ndb.KeyProperty(kind=Poll)

class ReceivingPoll(ndb.Model):
    """
    The singleton ReceivingPoll instance object contains a reference to the
    currently "receiving" poll, which recieves new entries from /admin/newentries.
    """
    poll_key = ndb.KeyProperty(kind=Poll)


def getDefaultPollObject():
    """Returns an object containing a reference to the default poll"""
    query_results = DefaultPoll.query().fetch()
    if query_results:
        return query_results[0]
    else:
        # Initialize the default poll object if it does not exist
        default_poll = DefaultPoll()
        default_poll.put()
        return default_poll


def getReceivingPollObject():
    """
    Reutrns an object containing a reference to the currently "receiving"
    poll (the poll that recieves new entries from /admin/newentries.)
    """
    query_results = ReceivingPoll.query().fetch()
    if query_results:
        return query_results[0]
    else:
        receiving_poll = ReceivingPoll()
        receiving_poll.poll_key = getDefaultPollObject().poll_key
        return receiving_poll
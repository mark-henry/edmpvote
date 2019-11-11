"""Datastore models and other utilites common to all modules of the app"""

import os
import logging

from google.appengine.ext import ndb

import jinja2

from protorpc import messages
from protorpc import message_types
from protorpc import remote

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

DEBUG_MODE = False
SCORE_RANGE = 5


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
    currently "receiving" poll, which receives new entries from /admin/newentries.
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



# NEW CODE - Adds a Get Entries endpoint via RPC - Import the postman_collection.json into the postman app to test

class Submission(messages.Message):
    author = messages.StringField(1, required=True)
    url = messages.StringField(2, required=True)

class Request(messages.Message):
    author = messages.StringField(1, required=False)

class Response(messages.Message):
    entries = messages.MessageField(Submission, 1, repeated=True)

class GetService(remote.Service):

    # Add the remote decorator to indicate the service methods
    @remote.method(Request, Response)
    def entries(self, request):

        if request.author:
            entries = Entry.query(Entry.author == request.author).fetch()
        else:
            entries = Entry.query().fetch()

        response = Response()

        for entry in entries:
            entry = Submission(author=entry.author, url=entry.url)
            response.entries.append(entry)
 
        return response
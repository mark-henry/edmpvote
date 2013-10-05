# Voting page by /u/mark-henry for /r/edmproduction
# Based on original voting page by /u/rxi

__author__  = "/u/mark-henry"

import os
import urllib2
import re, random

from google.appengine.ext import ndb

import cgi
import jinja2, webapp2

from edmpvote import *

example_template_vars = {
      'poll_title': 'example poll',
      'entries': [{'entryid':'mark-henry',
                    'title':'example title',
                    'author':'mark-henry',
                    'url':'http://soundcloud.com/mark-henry/cadavre-0'}],
      'ballot': {'mark-henry':4},
      'voting_enabled': True,
      'SCORE_RANGE': SCORE_RANGE,
    }

def getTitle(soundcloudurl):
  '''Gets the title for SoundCloud track specified by url'''
  # Currently implemented as a ghetto API
  #   that strips the title from the song's page's HTML with a regex
  res = urllib2.urlopen(soundcloudurl)
  content = res.read().decode(encoding='UTF-8')
  pattern = '<meta content="([^<]+?)" property="og:title" />'
  match = re.search(pattern, content)
  if match:
    return match.group(1)
  else:
    return "err"

def getVoterID():
  '''Gets a string that identifies the voter.'''
  # Right now it's just their IP address
  client_ip = os.getenv("REMOTE_ADDR")
  return client_ip

def getBallot(poll, voterid):
  query = Ballot.query(Ballot.voterid == voterid, ancestor=poll.key)
  ballot = query.fetch(1)
  if ballot:
    return ballot[0]
  else:
    newballot = Ballot(parent=poll.key, voterid=voterid)
    newballot.put()
    return newballot

def registerVote(ballot, entryid, score):
  """Enters given vote into the database and returns the modified ballot."""
  for vote in ballot.votes:
    if vote.entryid == entryid:
      vote.value = int(score)
      ballot.put()
      return ballot
  # If the entry was not in the ballot, add it
  ballot.votes.append(Vote(entryid=entryid, value=int(score)))
  ballot.put()
  return ballot

def formatBallot(ballot):
  """Formats ballot into a dictionary of votes"""
  dict = {}
  for vote in ballot.votes:
    dict.update({vote.entryid: vote.value})
  return dict

class VotePage(webapp2.RequestHandler):
  def renderPoll(self, poll, ballot):
    entries = Entry.query(ancestor=poll.key).fetch()
    for entry in entries:
      entry.title = getTitle(entry.url)
      entry.entryid = entry.author
    random.shuffle(entries)

    template_vars = {
      'entries': entries,
      'poll_title': poll.title,
      'voting_enabled': poll.voting_enabled,
      'ballot': formatBallot(ballot),
      'SCORE_RANGE': SCORE_RANGE,
    }
    template = JINJA_ENVIRONMENT.get_template('vote.html')
    self.response.write(template.render(template_vars))
    self.response.write("your id is " + getVoterID())

  def get(self):
    queries = self.request.GET
    voterid = getVoterID()
    # Load poll
    if 'poll' in queries:
      poll_key = ndb.Key(urlsafe=queries['poll'])
    else:
      poll_key = getDefaultPollObject().default_poll_key
    poll = poll_key.get()

    ballot = getBallot(poll, voterid)

    # Register vote if present
    if poll.voting_enabled:
      if 'entryid' in queries and 'score' in queries:
        ballot = registerVote(ballot, queries['entryid'], queries['score'])

    self.renderPoll(poll, ballot)

# Define webapp2 application
application = webapp2.WSGIApplication([('/.*', VotePage)], debug=DEBUG_MODE)
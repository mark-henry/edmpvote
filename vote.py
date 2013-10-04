# Voting page by /u/mark-henry for /r/edmproduction
# Based on original voting page by /u/rxi

__author__  = "/u/mark-henry"

import os
import urllib2
import re

from google.appengine.ext import ndb

import cgi
import jinja2, webapp2

import edmpvote

SCORE_RANGE = 10

def getVoterID():
  '''Gets a string that identifies the voter.'''
  # Right now it's just their IP address
  client_ip = os.getenv("REMOTE_ADDR")
  return client_ip

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

example_template_vars = {
      'entries': [{'entryid':'mark-henry',
                    'title':getTitle('http://soundcloud.com/mark-henry/cadavre-0'),
                    'author':'mark-henry',
                    'url':'http://soundcloud.com/mark-henry/cadavre-0'}],
      'uservotes': {'mark-henry':4},
      'votingclosed': False,
      'SCORE_RANGE': SCORE_RANGE,
    }

class VotePage(webapp2.RequestHandler):
  def showPoll(self, pollKey):
    poll = pollKey.get()
    template_vars = {}
    template = edmpvote.JINJA_ENVIRONMENT.get_template('vote.html')
    self.response.write(template.render(template_vars))

  def get(self):
    queries = self.request.GET
    if 'poll' in queries:
      self.showPoll(ndb.Key(urlsafe=queries['poll']))
    else:
      self.showPoll(edmpvote.getDefaultPollObject().default_poll_key)

# Define webapp2 application
application = webapp2.WSGIApplication([('/vote', VotePage)], debug=edmpvote.DEBUG_MODE)
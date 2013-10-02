# Voting page by /u/mark-henry for /r/edmproduction
# Original voting page by /u/mwd410

__author__  = "/u/mark-henry"

import os
import urllib2
import logging
import re

from google.appengine.api import users
from google.appengine.ext import ndb

import cgi
import jinja2, webapp2

SCORE_RANGE = 9
DEBUG_MODE = True

JINJA_ENVIRONMENT = jinja2.Environment(
   loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
   extensions=['jinja2.ext.autoescape'])

example_template_vars = {
      'entries': [{'entryid':'mark-henry', 'title':'Track Title', 'author':'mark-henry', 'url':'http://soundcloud.com/mark-henry/cadavre-0'}],
      'uservotes': {'mark-henry':4},
      'votingclosed': False,
      'SCORE_RANGE': SCORE_RANGE,
    }

def err(args):
   logging.error("\n>>DEBUG: %s" % args)

def getSessionID():
  '''Gets a string that identifies the voter.'''
  # Right now it's just their IP address
  client_ip = os.getenv("REMOTE_ADDR")
  return client_ip

def getTitle(soundcloudurl):
  '''Gets the title for given track on soundcloud'''
  res = urllib2.urlopen(soundcloudurl)
  content = res.read().decode(encoding='UTF-8')
  pattern = '<meta content="([^<]+?)" property="og:title" />'
  match = re.search(pattern, content)
  if match:
    return match.group(1)
  else:
    return "couldn't find it in " + content

def getDefaultPoll():
  '''Gets the poll that should be displayed when no poll is specified in query string'''
  return 0

class VotePage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('vote.html')
    template_vars = example_template_vars
    template_vars['entries'][0]['title'] = getTitle('http://soundcloud.com/mark-henry/cadavre-0')
    self.response.write(template.render(template_vars))

# Define webapp2 application
directory = [
  ('/vote', VotePage),
]
application = webapp2.WSGIApplication(directory, debug=DEBUG_MODE)
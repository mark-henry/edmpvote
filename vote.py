# Voting page by /u/mark-henry for /r/edmproduction
# Original voting page by /u/mwd410

__author__  = "/u/mark-henry"

import os
import urllib
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

import cgi
import jinja2, webapp2

SCORE_RANGE = 5
DEBUG_MODE = True

JINJA_ENVIRONMENT = jinja2.Environment(
   loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
   extensions=['jinja2.ext.autoescape'])

def err(args):
   logging.error("\n>>DEBUG: %s" % args)

# Get client IP
client_ip = os.getenv("REMOTE_ADDR")

class VotePage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('vote.html')
    template_vars = {
      'entries': [{'redditname':'mark-henry', 'title':'Track Title', 'url':'https://soundcloud.com/mark-henry/cadavre-0'}],
      'session': {'asdf':9},
      'votingclosed': False,
      'SCORE_RANGE': SCORE_RANGE,
    }
    self.response.write(template.render(template_vars))

# Define webapp2 application
directory = [
  ('/vote', VotePage),
]
application = webapp2.WSGIApplication(directory, debug=DEBUG_MODE)
__author__ = '/u/mark-henry'

import os

import edmpvote

from google.appengine.ext import ndb

import jinja2, webapp2


class AdminPage(webapp2.RequestHandler):
  def pollsList(self):
    # Fetch data
    queries = self.request.GET
    default_poll_object = edmpvote.getDefaultPollObject()
    polls = edmpvote.Poll.query().fetch()
    if not polls: polls = []

    # Update data
    if 'default' in queries:
      # Update the default poll value
      default_poll_object.default_poll_key = ndb.Key(urlsafe=queries['default'])
      default_poll_object.put()

    # Render
    template_vars = {'polls':polls, 'default_poll_key':default_poll_object.default_poll_key}
    template = edmpvote.JINJA_ENVIRONMENT.get_template('polls-list.html')
    self.response.write(template.render(template_vars))

  def editPoll(self, key):
    queries = self.request.GET
    poll = key.get()

    if 'title' in queries:
      poll.title = queries['title']
      poll.put()
    if 'voting' in queries:
      if queries['voting'] == 'enable':
        poll.voting_enabled = True
      elif queries['voting'] == 'disable':
        poll.voting_enabled = False
      poll.put()

    template = edmpvote.JINJA_ENVIRONMENT.get_template('single-poll.html')
    template_vars = {'poll':poll}
    self.response.write(template.render(template_vars))

  def newPoll(self):
    new_poll = edmpvote.Poll(title='New Poll')
    new_poll.put()
    self.editPoll(new_poll.key)

  def get(self):
    if 'delete' in self.request.GET:
      ndb.Key(urlsafe=self.request.GET['delete']).delete()
    if 'action' in self.request.GET and self.request.GET['action'] == 'newpoll':
      self.newPoll()
    elif 'poll' in self.request.GET:
      self.editPoll(ndb.Key(urlsafe=self.request.GET['poll']))
    else:
      self.pollsList()

application = webapp2.WSGIApplication(
    [('/admin.*', AdminPage)], 
    debug=edmpvote.DEBUG_MODE)
__author__ = '/u/mark-henry'

import os

from edmpvote import *

from google.appengine.ext import ndb

import jinja2, webapp2


def makePollResults(entries, ballots):
  """Renders a sorted list of standings"""

  # Collect the votes
  votes_by_user = {}
  for entry in entries:
    votes_by_user.update({entry.author: []})
  for ballot in ballots:
    for vote in ballot.votes:
      votes_by_user[vote.entryid].append(vote.value)

  # Average the scores
  standings = []
  for user in votes_by_user.keys():
    if len(votes_by_user[user]) == 0:
      score = "0"
    else:
      score = str(sum(votes_by_user[user])/float(len(votes_by_user[user])))
    standings.append(score + " " + user)

  return "\n".join(sorted(standings, reverse=True))


class AdminPage(webapp2.RequestHandler):
  def pollsList(self):
    # Fetch data
    queries = self.request.GET
    default_poll_object = getDefaultPollObject()
    polls = Poll.query().fetch()
    if not polls: polls = []

    # Update data
    if 'default' in queries:
      # Update the default poll value
      default_poll_object.default_poll_key = ndb.Key(urlsafe=queries['default'])
      default_poll_object.put()

    # Render
    template_vars = {'polls':polls, 'default_poll_key':default_poll_object.default_poll_key}
    template = JINJA_ENVIRONMENT.get_template('polls-list.html')
    self.response.write(template.render(template_vars))

  def editPoll(self, poll_key):
    queries = self.request.GET
    poll = poll_key.get()

    if 'title' in queries:
      poll.title = queries['title']
      poll.put()
    if 'voting' in queries:
      if queries['voting'] == 'enable':
        poll.voting_enabled = True
      elif queries['voting'] == 'disable':
        poll.voting_enabled = False
      poll.put()
    if 'author' in queries and 'url' in queries:
      Entry(author=queries['author'], url=queries['url'], parent=poll_key).put()

    entries = Entry.query(ancestor=poll_key).fetch()
    ballots = Ballot.query(ancestor=poll_key).fetch()
    results = makePollResults(entries, ballots)

    template = JINJA_ENVIRONMENT.get_template('single-poll.html')
    template_vars = {'poll':poll, 'entries':entries, 'ballots':ballots, 'results':results}
    self.response.write(template.render(template_vars))

  def newPoll(self):
    new_poll = Poll(title='New Poll')
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
    debug=DEBUG_MODE)
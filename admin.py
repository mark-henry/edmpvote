__author__ = '/u/mark-henry'

import os

from edmpvote import *

from google.appengine.ext import ndb

import jinja2, webapp2, logging


def makePollResults(entries, ballots):
  """Renders a sorted list of standings"""

  # Collect the votes
  votes_by_user = {}
  for entry in entries:
    votes_by_user.update({entry.author: []})
  for ballot in ballots:
    for vote in ballot.votes:
      if (votes_by_user.has_key(vote.entryid)): 
        votes_by_user[vote.entryid].append(vote.value)
        
  # Average the scores
  standings = []
  for user in votes_by_user.keys():
    if len(votes_by_user[user]) == 0:
      score = "0"
    else:
      ratio = sum(votes_by_user[user]) / float(len(votes_by_user[user]))
      score = str(round(ratio, 2))
    standings.append(score + " " + user)

  sortedstandings = sorted(standings, reverse=True)

  for i in range(len(sortedstandings)):
    sortedstandings[i] = str(i+1) + ". " + sortedstandings[i]

  return "\n".join(sortedstandings)


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

  def editPoll(self, poll_key, isPost):
    if(isPost):
      queries = self.request.POST
    else:
      queries = self.request.GET
    poll = poll_key.get()
    
    logging.info('get some editPoll')
    if 'title' in queries:
      logging.info('editting title ' + queries['title'])
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
    self.editPoll(new_poll.key, True)

  def get(self):
    self.parseRequest(self.request.GET)
	  
  def post(self):
    self.parseRequest(self.request.POST)
      
  def parseRequest(self, queries):
    if 'delete' in queries:
      ndb.Key(urlsafe=queries['delete']).delete()
    if 'action' in queries and queries['action'] == 'newpoll':
      self.newPoll()
    elif 'poll' in queries:
      self.editPoll(ndb.Key(urlsafe=queries['poll']), True)
    else:
      self.pollsList()

application = webapp2.WSGIApplication(
    [('/admin.*', AdminPage)], 
    debug=DEBUG_MODE)
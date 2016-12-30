__author__ = '/u/mark-henry'

from edmpvote import *

from google.appengine.ext import ndb

import webapp2
import logging
import datetime
import re


def makePollResults(entries, ballots):
    """Renders a sorted list of standings"""

    # Collect the votes
    votes_by_user = {}
    for entry in entries:
        votes_by_user.update({entry.author: []})
    for ballot in ballots:
        for vote in ballot.votes:
            if vote.entryid in votes_by_user:
                votes_by_user[vote.entryid].append(vote.value)

    # Average the scores
    scores = []
    for user in votes_by_user.keys():
        if len(votes_by_user[user]) == 0:
            score = "0"
        else:
            ratio = sum(votes_by_user[user]) / float(len(votes_by_user[user]))
            score = str(round(ratio, 2))
        scores.append(score + " " + user)

    sortedstandings = []
    for i, standing in enumerate(sorted(scores, reverse=True)):
        sortedstandings.append(str(i + 1) + ".  " + standing)

    return "\n".join(sortedstandings)


def parse_quickadd(quickadd):
    url = re.search('https?:.*?(?=(\s|$))', quickadd).group(0)
    from_match = re.search('from (\w*)', quickadd)
    if from_match:
        username = from_match.group(1)
    else:
        username = re.search('\w*', quickadd).group(0)
    return (username, url)


class AdminPage(webapp2.RequestHandler):
    def pollsList(self):
        # Fetch data
        queries = self.request.POST
        default_poll_object = getDefaultPollObject()
        receiving_poll_object = getReceivingPollObject()
        polls = Poll.query().fetch() or []
        polls.sort(reverse=True, key=lambda p: p.created or datetime.datetime.min)

        # Update data
        if 'default' in queries:
            # Update the default poll value
            default_poll_object.poll_key = ndb.Key(urlsafe=queries['default'])
            default_poll_object.put()
        if 'receiving' in queries:
            # Update the default poll value
            receiving_poll_object.poll_key = ndb.Key(urlsafe=queries['receiving'])
            receiving_poll_object.put()

        # Render
        template_vars = {
            'polls': polls,
            'default_poll_key': default_poll_object.poll_key,
            'receiving_poll_key': receiving_poll_object.poll_key
        }
        template = JINJA_ENVIRONMENT.get_template('polls-list.html')
        self.response.write(template.render(template_vars))

    def editPoll(self, poll_key):
        queries = self.request.POST
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
        if 'quickadd' in queries:
            author, url = parse_quickadd(queries['quickadd'])
            if author and url:
                Entry(author=author, url=url, parent=poll_key).put()

        entries = Entry.query(ancestor=poll_key).fetch()
        ballots = Ballot.query(ancestor=poll_key).fetch()
        results = makePollResults(entries, ballots)

        template = JINJA_ENVIRONMENT.get_template('single-poll.html')
        template_vars = {'poll': poll, 'entries': entries, 'ballots': ballots, 'results': results}
        self.response.write(template.render(template_vars))

    def newPoll(self):
        new_poll = Poll(title='New Poll')
        new_poll.put()
        return self.redirect("/admin?poll=" + new_poll.key.urlsafe())

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
            self.editPoll(ndb.Key(urlsafe=queries['poll']))
        else:
            self.pollsList()


class NewEntries(webapp2.RequestHandler):
    def put(self):
        poll_key = getReceivingPollObject().poll_key
        payload = self.request.POST

        valid_secrets = ['redditbot']

        if 'author' in payload and 'url' in payload:
            if 'secret' in payload and payload['secret'] in valid_secrets:
                Entry(author=payload['author'], url=payload['url'], parent=poll_key).put()
                logging.info("New entry created via PUT endpoint")


application = webapp2.WSGIApplication(
    [(r'/admin/newentries', NewEntries),
        (r'/admin.*', AdminPage)],
    debug=DEBUG_MODE)
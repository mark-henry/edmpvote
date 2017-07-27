__author__ = '/u/mark-henry'

from edmpvote import *

from google.appengine.ext import ndb

import webapp2
import logging
import datetime
import re


def collate_votes_by_entry(entries, ballots):
    """
    Turns a list of entries and a list of ballots into a dict of votes per authorname.
    """
    # Also does some complicated dynamic-range scaling.
    # FIXME: refactor this
    votes_by_entry = {}
    for entry in entries:
        votes_by_entry.update({entry.author: []})

    for ballot in ballots:
        # Normalize each ballot values to the full scale
        values = [vote.value for vote in ballot.votes]
        if min(values) == max(values):
            continue  # Ballots which express no preference do not count
        translate = min(values)
        scale = float(SCORE_RANGE - 1) / (max(values) - min(values))
        for vote in ballot.votes:
            scaled_value = ((vote.value - translate) * scale) + 1
            if vote.entryid in votes_by_entry:
                votes_by_entry[vote.entryid].append(scaled_value)

    return votes_by_entry

def average_score_as_str(vote_values):
    """Given a list of vote values, render the score string.
    Score is a float to two decimal places or "(no votes)"
    """
    if len(vote_values) == 0:
        return "(no votes)"
    else:
        mean = sum(vote_values) / float(len(vote_values))
        return str(round(mean, 2))


def average_score_per_entry(votes_by_entry):
    """Returns a list of strings???"""
    scores = []
    for user in votes_by_entry.keys():
        vote_values = votes[user]
        score = average_score_as_str(votes[user])
        scores.append(score + " " + user)
    return scores


def renderPollResultsString(entries, ballots):
    """
    Renders a sorted list of standings, returns string
    entries is a list of {author, url} objects
    ballots is a list of {voterid, votes} objects, where votes is a list of {entriyid, value}
    """
    # Filter out the single-entry ballots
    ballots = filter(lambda ballot: len(ballot.votes) > 1, ballots)

    # Create an entry in a dict for each author name
    votes_by_entry = collate_votes_by_entry(entries, ballots)

    # Average the scores
    scores = average_score_per_entry(votes_by_entry)

    return "\n".join([
        str(i+1) + ". " + standing
        for i, standing in enumerate(sorted(scores, reverse=True))])


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
        results = renderPollResultsString(entries, ballots)

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
import datetime
import re
from collections import defaultdict

import webapp2
from google.appengine.ext import ndb

from edmpvote import *

__author__ = '/u/mark-henry'


def filter_boring_ballots(ballots):
    return [
        ballot for ballot in ballots
        if len(ballot) > 1 and  # filter out empty ballots and one-vote ballots
        min(ballot.values()) != max(ballot.values())  # filter out ballots which express no preferences
        ]


def maximize(ballot):
    """Expands the vote scores to fill the full range of scores.
    For example, if someone voted only 1s, 2s and 3s, these would be expanded to fill the full 1-5 point range.
    :type ballot: dict
    """
    scores = ballot.values()
    translate = min(scores)
    current_dynamic_range = max(scores) - min(scores)
    full_dynamic_range = SCORE_RANGE - 1
    scale = float(full_dynamic_range) / current_dynamic_range
    for contestant, score in ballot.items():
        ballot[contestant] = ((score - translate) * scale) + 1
    return ballot


def collate_scores_by_contestant(ballots):
    """
    Turns a list of ballots into a dict of votes per authorname.
    """
    votes_by_author = defaultdict(list)
    for ballot in ballots:
        for contestant, score in ballot.items():
            print votes_by_author[contestant]
            votes_by_author[contestant].append(score)

    return votes_by_author


def average_score_as_str(vote_values):
    """Given a list of vote values, render the score string.
    Score string is a float to two decimal places or "(no votes)"
    """
    if len(vote_values) == 0:
        return "(no votes)"
    else:
        mean = sum(vote_values) / float(len(vote_values))
        return str(round(mean, 2))


def flatten_ballots(ballots):
    """
    :rtype: list(dict)
    :return: list of ballots flattened into dicts
    :type ballots: list
    :param ballots: list of Ballot objects"""
    return [{
                vote.entryid: vote.value
                for vote in ballot.votes
                }
            for ballot in ballots
            ]


def calculate_standings_and_render_results_string(ballots):
    """
    :rtype: string
    :type ballots: list
    :param ballots: list of Ballot objects
    :return: standings for display to the user
    """

    ballots_flat = flatten_ballots(ballots)
    ballots_flat = filter_boring_ballots(ballots_flat)
    for ballot in ballots_flat:
        maximize(ballot)
    scores_by_contestant = collate_scores_by_contestant(ballots_flat)

    scores = []
    for user, votes in scores_by_contestant.items():
        score = average_score_as_str(votes)
        scores.append(score + " " + user)

    return "\n".join([str(i + 1) + ". " + standing for i, standing in enumerate(sorted(scores, reverse=True))])


def parse_quickadd(quickadd):
    url = re.search('https?:.*?(?=(\s|$))', quickadd).group(0)
    from_match = re.search('from (\w*)', quickadd)
    if from_match:
        username = from_match.group(1)
    else:
        username = re.search('\w*', quickadd).group(0)
    return (username, url)


class AdminPage(webapp2.RequestHandler):
    def show_polls_list(self):
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

    def edit_poll(self, poll_key):
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
        results = calculate_standings_and_render_results_string(ballots)

        template = JINJA_ENVIRONMENT.get_template('single-poll.html')
        template_vars = {'poll': poll, 'entries': entries, 'ballots': ballots, 'results': results}
        self.response.write(template.render(template_vars))

    def new_poll(self):
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
            self.new_poll()
        elif 'poll' in queries:
            self.edit_poll(ndb.Key(urlsafe=queries['poll']))
        else:
            self.show_polls_list()


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

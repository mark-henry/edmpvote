__author__ = '/u/mark-henry'

import webapp2

import io
import unittest
import HTMLTestRunner

from app import admin


class TestAdmin(unittest.TestCase):
    def assertBallotScaling(self, ballot, expected):


    def test_renderPollResultsString_empty(self):
        self.assertEqual(
            admin.calculate_standings_and_render_results_string([]),
            "")

    def test_renderPollResultsString_oldscale(self):
        """Assert that a 1-10 ballot is rescaled to a 1-5 range"""
        self.assertBallotScaling([1, 10], [1, 5])
        self.assertBallotScaling([1, 4, 10], [1, 2, 5])

    def test_renderPollResultsString_dynamicrange(self):
        """Assert that a scoreset from 1-2 is expanded to the full 1-5 range"""
        self.assertBallotScaling([1, 2], [1, 5])
        pass

    def test_renderPollResultsString_nopreference(self):
        """Assert that a scoreset containing all 5 scores is equivalent to expressing no preference"""
        pass


class TestRunner(webapp2.RequestHandler):
    def html_test(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAdmin)
        # unittest.TextTestRunner(verbosity=2).run(suite)

        html_bytes = io.BytesIO()
        runner = HTMLTestRunner.HTMLTestRunner(stream=html_bytes)
        runner.run(suite)
        html = html_bytes.getvalue()

        return html

    def get(self):
        self.response.write(self.html_test())


application = webapp2.WSGIApplication(
    [(r'/admin/test', TestRunner)],
    debug=True)

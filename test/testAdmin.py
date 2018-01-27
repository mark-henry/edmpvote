import io
import unittest

import webapp2

import HTMLTestRunner
from app import admin

__author__ = '/u/mark-henry'


class TestAdmin(unittest.TestCase):
    def assertMaximize(self, input_scores, expected):
        id_counter = [0]

        def newid():
            id_counter[0] += 1
            return str(id_counter[0])

        actual = admin.maximize({"e" + newid(): score for score in input_scores}).values()
        self.assertItemsEqual(expected, actual)

    def test_renderPollResultsString_empty(self):
        self.assertEqual(
            admin.calculate_standings_and_render_results_string([]),
            "")

    def test_renderPollResultsString_oldscale(self):
        """Assert that a 1-10 ballot is rescaled to a 1-5 range"""
        self.assertMaximize([1, 10], [1, 5])
        self.assertMaximize([1, 3, 9], [1, 2, 5])

    def test_renderPollResultsString_dynamicrange(self):
        """Assert that a scoreset from 1-2 is expanded to the full 1-5 range"""
        self.assertMaximize([1, 2], [1, 5])

    def test_None_value_ignored(self):
        # self.assertMaximize([1, 2, None], [1, 5])
        pass

    def test_trivial_ballots_filtered(self):
        """Test that boring ballots which express no preferences are ignored"""
        def assertFiltered(ballot):
            pass
        assertFiltered([])
        assertFiltered([1])  # only one value
        assertFiltered([5, 5, 5])  # all of one value
        pass


class TestRunner(webapp2.RequestHandler):
    @staticmethod
    def html_test():
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

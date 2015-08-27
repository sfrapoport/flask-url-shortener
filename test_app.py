import os
import app
import unittest
import tempfile
import flask

class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        app.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'URL' in rv.data

    def shorten(self, url):
        return self.app.post('/shorten', data=dict(
            fullurl=url
            ), follow_redirects=True)

    def follow_short(self, short):
        return self.app.get('<short>', data=dict(
            short=short
            ), follow_redirects=True)

    def test_shorten(self):
        rv=self.shorten('http://www.google.com')
        # print rv.data
        assert 'Your shortened url is' in rv.data

    def test_follow_empty_short(self):
        short=''
        rv = self.follow_short(short)
        assert 'No such url' in rv.data

    def test_follow_short(self):
        app = flask.Flask(__name__)
        url = 'http://www.google.com'
        with app.test_request_context('/shorten', data=dict(
            fullurl=url
            )):
            app.preprocess_request()
            rv = app.get('/ZMSZ0', follow_redirects=True)
            print rv.data

if __name__ == '__main__':
    unittest.main()

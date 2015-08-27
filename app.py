import sqlite3
import hashlib, string

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# Helper function to keep database open only in context manager
from contextlib import closing

##################################
#        app configuration
##################################
# TODO: Switch to using env vars

ALPHANUMERIC = string.letters + string.digits
# default length 5 - hash collision occurs with probability ~ 10 E -9 
def default_hash(url, n=5):
    hashvals = hashlib.md5(url).digest()
    return ''.join([ALPHANUMERIC[ord(i) % 62] for i in hashvals[:n]])


app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('APP_SETTINGS')

def connect_to_db():
    return sqlite3.connect(app.config['DATABASE'])

# Database connections on request
@app.before_request
def before_request():
    g.db = connect_to_db()

# Teardown decorator: Called on requests that raise an exception
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def init_db():
    with closing(connect_to_db()) as db:
        with app.open_resource('schema.sql', mode = 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()

##################################
#        database lookup/storage
##################################

def get_full_url(short):
    full = g.db.execute('select fullurl from urls where shortenedurl=?', [short])
    result = full.fetchone()
    if result:
        return result[0]

def increment_access_count(short):
    g.db.execute('update urls set lookups=lookups+1 where shortenedurl=?', [short])
    g.db.commit()

def get_access_count(short):
    result = g.db.execute('select lookups from urls where shortenedurl=?', [short])
    return result.fetchone()[0]

def insert_new_url(short, full):
    g.db.execute('insert into urls (shortenedurl, fullurl, lookups) values (?, ?, ?)', [short, full, 0])
    g.db.commit()

##################################
#        routes
##################################

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    url = request.form.get('fullurl')
    if not url:
        return redirect(url_for('index'))
    short = default_hash(url)
    dburl = get_full_url(short)
    # Hypothesis - running this command is resetting the access count
    if not dburl:
        insert_new_url(short, url)
    elif dburl != url:
        raise KeyError('hash collision!')
    return render_template('show_shortened.html',
                            urlroot=request.url_root, shorturl=short,
                            number=get_access_count(short))

@app.route('/<short>', methods=['GET'])
def get_url(short):
    full = get_full_url(short)
    if full:
        increment_access_count(short)
        return redirect(full)
    else:
        flash('No such url', 'None')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()

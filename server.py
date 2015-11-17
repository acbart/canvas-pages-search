from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import flask.ext.whooshalchemy as whooshalchemy
import progressbar as pbar
import datetime
import requests
import json

with open('secrets.json', 'r') as input:
    secrets = json.load(input)

ACCESS_TOKEN = secrets["canvas-token"]
ACCESS_URL = secrets["canvas-url"]
COURSE = 5035    
    
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///index.db'

# set the location for the whoosh index
app.config['WHOOSH_BASE'] = 'whoosh_index'

# Make the database
db = SQLAlchemy(app)
db.create_all()

class Page(db.Model):
    __tablename__ = 'page'
    __searchable__ = ['title', 'body']  # these fields will be indexed by whoosh

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, unique=True)
    title = db.Column(db.UnicodeText(64))
    body = db.Column(db.UnicodeText(64))
    published = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '{0}(title={1})'.format(self.__class__.__name__, self.title)
     
def get(command, data):
    data['access_token'] = ACCESS_TOKEN
    result = requests.get(ACCESS_URL+command, data=data)
    try:
        return result.json()
    except ValueError:
        print result.text
     
@app.route("/reload_index")
def reload_index():
    pages = get('courses/{course}/pages'.format(course=COURSE), {})

    progressbar = list
    if pages > 1:
        progressbar = pbar.ProgressBar(widgets=[pbar.Bar('>'), ' ', 
                                                pbar.Percentage(), ' ', 
                                                pbar.ETA(), ' ', 
                                                pbar.FileTransferSpeed()]).start()
    num_rows_deleted = Page.query.delete()
    print "Deleted", num_rows_deleted, "existing rows."
    db.session.commit()
    for page in progressbar(pages):
        url = page['url']
        updated_at = page["updated_at"]
        # TODO: Some logic to check if the page has changed
        page_content = get('courses/{course}/pages/{url}'.format(course=COURSE, url=url), {})
        body = page_content['body'] #.encode('utf8')
        title = page_content['title']
        published = page_content['published']
        db.session.add(Page(body=body, url=url, title=title,
                                published=published))
    db.session.commit()
    whooshalchemy.whoosh_index(app, Page)
    return "Success"
    
def to_url(r):
    return '<a href="https://vt.instructure.com/courses/{course}/pages/{url}" target="_top">{title}</a>'.format(title=r.title, url=r.url, course=COURSE)
    
@app.route("/", methods=["POST", "GET"])
def index():
    results = sorted(Page.query.all(), key=lambda r: r.title)
    result = "<br>".join([to_url(r) for r in results])
    return """<html>
<head>
<script src="https://code.jquery.com/jquery-2.1.4.min.js"></script>
<script>
$(document).ready(function() {{
    $('#go').click(function() {{
        var terms = $("#searchbox").val();
        $("#result").load(terms);
    }});
}});
</script>
</head>
<body>
{}
<hr>
Search: <input type="text" name="fname" id='searchbox'>
<button id="go">Go</button>
<div id='result'></div>
</body>
</html>""".format(result)
    
@app.route("/<query>", methods=["POST", "GET"])
def search_query(query):
    results = sorted(Page.query.whoosh_search(query), key=lambda r: r.title)
    result = "<br>".join([to_url(r) for r in results])
    return "<html><body>{}</body></html>".format(result)
    
if __name__ == "__main__":
    reload_index()
    app.run(debug=True)
from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import werkzeug
from config import load_config
from sqlalchemy import desc, exc, select
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
app.config = load_config()
# app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='My API', description='No touchy touchy', decorators=[])

# cors = CORS(app, resources={r"/foo": {"origins": "*"}})
# app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

db = SQLAlchemy(app)

STRING_FAIL = 'fail'
STRING_SUCCESS = 'success'

class Book(db.Model):
  __tablename__ = "books"

  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String)
  author = db.Column(db.String)
  start_date = db.Column(db.Date)
  end_date = db.Column(db.Date)
  artwork = db.Column(db.String)
  format_id = db.Column(db.ForeignKey("format.id"))
  format = db.relationship('Format', foreign_keys=[format_id])
  word_count = db.Column(db.Integer)

  def serialize(self):
    return ({
      'id': self.id,
      'title': self.title,
      'author': self.author,
      'startDate': self.start_date.strftime("%m/%d/%Y"),
      'endDate': self.end_date.strftime("%m/%d/%Y") if self.end_date else 'Ongoing',
      'artworkUrl': self.artwork,
      'format': self.format.format_type,
      'wordCount': self.word_count if self.word_count >= 0 else 'Still being written',
    })


class Format(db.Model):
  __tablename__ = "format"

  id = db.Column(db.Integer, primary_key=True)
  format_type = db.Column(db.String)

@app.route('/')
def home():
    resp = make_response('foo bar')
    resp.headers['Access-Control-Allow-Headers'] = '*'


@api.route('/books')
class BookView(Resource):
  def get(self):
    books = db.session.scalars(
      select(Book).order_by(Book.title)
    )
    response = [book.serialize() for book in books]
    return response, 200
  
  def post(self):
    data = request.json
    newBook = Book(
        title=data['title'],
        author=data['author'],
        start_date=data['startDate'],
        end_date=data['endDate'],
        artwork=data['artworkUrl'],
        format_id=data['formatId'],
        word_count=data['wordCount']
    )

    db.session.add(newBook)
    db.session.commit()

    return {'message': 'Success'}, 200
  
  def delete(self):
      pass
    

@api.route('/formats')
class FormatView(Resource):
  def get(self):
    formats = db.session.scalars(
        select(Format)
    )

    response = [{ 'id': format.id, 'type': format.format_type } for format in formats]
    return make_response(jsonify(response), 200)


@app.route('/favicon.ico')
def favicon():
  return 'what is this?'


@app.errorhandler(werkzeug.exceptions.NotFound)
def not_found(e):
    return 'Endpoint does not exist', 404


# -------------------- Helpers -------------------------
def session_commit():
	try :
		db.session.commit()
		return jsonify(meta = STRING_SUCCESS)
	except exc.IntegrityError:
		print ("IntegrityError while adding new user")
		db.session.rollback()
		return jsonify(meta = STRING_FAIL)

@app.after_request
def apply_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        res.headers['Access-Control-Allow-Headers'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS,POST,DELETE'
        return res

# -------------------- Startup -------------------------
if __name__ == '__main__':
  app.run(host='localhost', debug=True)
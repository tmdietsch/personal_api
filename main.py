from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import werkzeug
from config import load_config
from sqlalchemy import exc


app = Flask(__name__)
app.config = load_config()
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

  def serialize(self):
    return ({
      'id': self.id,
      'title': self.title,
      'author': self.author,
      'start': self.start_date.strftime("%m/%d/%Y"),
      'end': self.end_date.strftime("%m/%d/%Y"),
      'artworkUrl': self.artwork,
      'format': self.format.format_type
    })


class Format(db.Model):
  __tablename__ = "format"

  id = db.Column(db.Integer, primary_key=True)
  format_type = db.Column(db.String)


@app.route('/')
def home():
  return 'Dumb Book API'


@app.route('/books', methods=['GET'])
def bookAll():
  books = Book.query.all()
  response = [book.serialize() for book in books]
  print(response)
  return jsonify(response), 200


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

# -------------------- Startup -------------------------
if __name__ == '__main__':
  app.run(host='localhost', port=8080)
import datetime
from re import sub
from flask import Flask, Response, make_response, request
from flask_cors import CORS
from flask_restx import Api, Resource
import psycopg2
import werkzeug
from config import load_config


app = Flask(__name__)
app.config = load_config()

def connect(config):
  """ Connect to the PostgreSQL database server """
  try:
    conn = psycopg2.connect(host='localhost',
                            dbname='postgres',
                            user='postgres',
                            password='NCXLJ9VM')
    return conn
  except (psycopg2.DatabaseError, Exception) as error:
    print("Error connecting to server: " + error.__str__())

api = Api(app, version='1.0', title='My API', description='No touchy touchy', decorators=[])
cors = CORS(app)
db = connect(app.config)

STRING_FAIL = 'fail'
STRING_SUCCESS = 'success'


@app.route('/')
def home():
  resp = make_response('foo bar')
  resp.headers['Access-Control-Allow-Headers'] = '*'


@api.route('/books')
class BookView(Resource):
  def get(self):
    try:
      response = query('SELECT * FROM books JOIN format ON books.format_id = format.id ORDER BY books.start_date desc;', db)
      return response, 200
    except Exception as error:
      print('Error: ' + error.__str__())
      return [], 404
  
  def post(self):
    data = request.json

    try: 
      my_tuple = (data['title'], data['author'], data['startDate'], data['endDate'], data['artworkUrl'], data['formatId'], data['wordCount'], None)

      insert("""INSERT INTO books (title, author, start_date, end_date, artwork, format_id, word_count, series_id) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""", 
             my_tuple,
             db)
    except Exception as error:
      print(error)
      return {'message': 'Fail'}, 404

    return {'message': 'Success'}, 200
  
  def delete(self):
    pass
    

@api.route('/formats')
class FormatView(Resource):
  def get(self):
    try:
      response = query('SELECT * FROM format', db)
      return response, 200
    except Exception as error:
      print(error)
      return [], 404


@app.route('/favicon.ico')
def favicon():
  return 'what is this?'


@app.errorhandler(werkzeug.exceptions.NotFound)
def not_found(e):
    return 'Endpoint does not exist', 404


# -------------------- Helpers -------------------------
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
    
def get_column_names(cursor):
   return [desc[0] for desc in cursor.description]

def clean_input(col_names, data):
  response = [ { n: p for p, n in zip(d, col_names) } for d in data]

  result = []
  for d in data:
    clean_data = {}
    for n, p in zip(col_names, d):
      if isinstance(p, datetime.date):
        p = p.strftime("%m/%d/%Y")
      clean_data[camel_case(n)] = p
    result.append(clean_data)

  return result

def query(stmt, database):
  cur = database.cursor()
  cur.execute(stmt)
  data = cur.fetchall()

  names = get_column_names(cur)
  response = clean_input(names, data)

  cur.close()

  return response

def insert(stmt, data, database):
  cur = database.cursor()
  cur.execute(stmt, data)

  database.commit()

def camel_case(s):
  # Use regular expression substitution to replace underscores and hyphens with spaces,
  # then title case the string (capitalize the first letter of each word), and remove spaces
  s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
  
  # Join the string, ensuring the first letter is lowercase
  return ''.join([s[0].lower(), s[1:]])

# -------------------- Startup -------------------------
if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
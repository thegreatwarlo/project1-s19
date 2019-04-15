#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "cp2984"
DB_PASSWORD = "k3cawO6Y38"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

engine.execute("""CREATE TABLE IF NOT EXISTS users(
                                                 id int,
                                                 name text,
                                                 address text,
                                                 PRIMARY KEY (id)
                                                 );""")
engine.execute("""CREATE TABLE IF NOT EXISTS hops(
                                                 id int,
                                                 name text,
                                                 PRIMARY KEY (id)
                                                 );""")
engine.execute("""CREATE TABLE IF NOT EXISTS breweries(
                                                      id int,
                                                      name text,
                                                      location text,
                                                      PRIMARY KEY (id)
                                                      );""")

engine.execute("""CREATE TABLE IF NOT EXISTS beers(
                                                  id int,
                                                  brewer_id int REFERENCES breweries(id) ON DELETE CASCADE,
                                                  first_produced date,
                                                  price float,
                                                  hop_id int REFERENCES hops(id),
                                                  type text,
                                                  ABV float,
                                                  is_available boolean,
                                                  IBU float,
                                                  PRIMARY KEY (id)
                                                  );""")

engine.execute("""CREATE TABLE IF NOT EXISTS ratings(
                                                    id int,
                                                    beer_id int REFERENCES beers (id) ON DELETE CASCADE,
                                                    user_id int REFERENCES users (id) ON DELETE CASCADE,
                                                    datetime date,
                                                    location text,
                                                    comment text,
                                                    score float,
                                                    PRIMARY KEY (id)
                                                    );""")
engine.execute("""CREATE TABLE IF NOT EXISTS recommendations(
                                                            user_id int REFERENCES users (id) ON DELETE CASCADE,
                                                            beer_id int REFERENCES beers (id) ON DELETE CASCADE,
                                                            rank int,
                                                            datetime date,
                                                            is_current boolean,
                                                            PRIMARY KEY (user_id, beer_id, datetime)
                                                            );""")
@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def home():
  #if not session.get('logged_in'):
  return render_template('GetNameAndAddress.html')

@app.route('/GetNameAndAddress', methods=['POST'])
def GetNameAndAddress():
  name = request.form['name']
  address = request.form['address']  
  
  cmd = ("SELECT COUNT(*) FROM users WHERE name = :Name AND address = :Address;")
  count = g.conn.execute(text(cmd), Name=name, Address=address)
  
  if count.fetchone()[0] > 0:
    # user is already in users
      cursor3 = g.conn.execute("""SELECT beers.name, beers.type, breweries.name, beers.price
                        FROM beers
                        LEFT JOIN breweries
                            ON beers.brewer_id = breweries.id
                        WHERE beers.is_available = TRUE;
                        """
                    )
      items=[]
      for result in cursor3:
        items.append([result[0], result[1], result[2], result[3], "..."])
      
      return render_template('/storefront.html', data=items)

  else:
    # add record to users table
    cursor2 = g.conn.execute("SELECT max(id) + 1 FROM users;")
    max_id = cursor2.fetchone()[0]
    cmd = "INSERT INTO users(id, name, address) VALUES (:Max_age, :Name, :Address);"
    g.conn.execute(text(cmd), Max_age = max_id, Name = name, Address = address)
    
    cursor3 = g.conn.execute("""SELECT beers.name, beers.type, breweries.name, beers.price
                        FROM beers
                        LEFT JOIN breweries
                            ON beers.brewer_id = breweries.id
                        WHERE beers.is_available = TRUE;
                        """
                    )
    items=[]
    for result in cursor3:
      items.append([result[0], result[1], result[2], result[3], "..."])
    
    return render_template('/storefront.html', data=items)

@app.route('/storefront/', methods=['POST','GET'])
def storefront():
    items = []
    
    for result in cursor:
        items.append(result[0])  # can also be accessed using result[0]
    cursor.close()
    
    
    context = dict(data = items)
    return ("storefront.html")

if __name__ == "__main__":
  import click
  app.secret_key = os.urandom(12)
  app.run(debug=True,host='0.0.0.0', port=8085)
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()

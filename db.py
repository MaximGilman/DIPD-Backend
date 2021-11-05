import psycopg2
import psycopg2.extras
from flask import current_app, g
from flask.cli import with_appcontext
import os

def get_db():
    if "db" not in g:
        g.con = psycopg2.connect(host=os.getenv("POSTGRESQL_HOST"), 
                        port=os.getenv("POSTGRESQL_PORT"), 
                        user=os.getenv("POSTGRESQL_USER"),  
                        password=os.getenv("POSTGRESQL_PASS"), 
                        dbname=os.getenv("POSTGRESQL_DB"))
        g.con.autocommit = True
        g.db = g.con.cursor(cursor_factory = psycopg2.extras.DictCursor)
    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)


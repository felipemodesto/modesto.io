import os
basedir = os.path.abspath(os.path.dirname(__file__))
WHOOSH_ENABLED = os.environ.get('HEROKU') is None
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_migrations')
SQLALCHEMY_TRACK_MODIFICATIONS = False

print ">> Config File Loaded."
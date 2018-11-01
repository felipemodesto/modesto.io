from app import *
from datetime import *
from config import WHOOSH_ENABLED

enable_search = WHOOSH_ENABLED
if enable_search:
	import flask_sqlalchemy as sqlalchemy
	#import flask_whooshalchemy as whooshalchemy

######################################################
################################### LOGIN DATABASE
######################################################


################################
#Client (List of all IPs that have connected to the website and the last time they connected
class Client(db.Model):
	__tablename__ = "client"
	ip = db.Column("ip",db.String(64), primary_key=True,index=True)
	location = db.Column("location",db.String(64),unique=False)
	lastAccess = db.Column('lastAccess' ,db.DateTime,unique=False)
	accessCount = db.Column("accessCount",db.Integer,unique=False)

	def __init__(self , ip):
		self.ip = ip
		self.location = "unknown"
		self.lastAccess = datetime.utcnow()
		self.accessCount = 1

	#def __pref__(self):
	#	return '<Client %r>' %(self.ip)
#	def __pref__(self):
#		return '<Client %r>' %(self.ip)

################################
#List of all Requests ever made to server
class Visit(db.Model):
	__tablename__ = "Visit"
	id = db.Column(db.Integer,primary_key=True)
	ip = db.Column(db.Integer, db.ForeignKey('client.ip'))
	time = db.Column('time' , db.DateTime)

	def __init__(self , ip):
		bigIdVisit = Visit.query.all()[len(Visit.query.all())-1]
		self.id = 	bigIdVisit.id + 1
		self.ip = ip
		self.time = datetime.utcnow()

	def __pref__(self):
		return '<Visit %r>' %(self.ip)


################################
#List of all Heartrates known to server
class Heartrate(db.Model):
	__tablename__ = "Heartrate"
	ip = db.Column(db.Integer, db.ForeignKey('client.ip'))
	time = db.Column('time' , db.DateTime)
	heartrate = db.Column(db.Integer,unique=False)
	accuracy = db.Column(db.Integer,unique=False)
	deviceID = db.Column(db.String(64),unique=True,primary_key=True)
	deviceHash = db.Column(db.String(64),unique=True)

	def __init__(self ,ip, heartrate, accuracy, deviceID, deviceHash):
		self.ip = ip
		self.time = datetime.utcnow()
		self.heartrate = heartrate
		self.accuracy = accuracy
		self.deviceID = deviceID
		self.deviceHash = deviceHash

	def __pref__(self):
		return '<Heartrate %r>' %(self.ip)


print ">> Models File Loaded."
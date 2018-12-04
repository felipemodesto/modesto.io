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


################################
#List of all Requests ever made to server
class Visit(db.Model):
	__tablename__ = "Visit"
	id = db.Column(db.Integer,primary_key=True)
	ip = db.Column(db.Integer, db.ForeignKey('client.ip'))
	time = db.Column('time' , db.DateTime)

	def __init__(self , ip):
		try:
			visitList = Visit.query.all()
			bigIdVisit = visitList[len(visitList)-1]
			self.id = 	bigIdVisit.id + 1
			self.ip = ip
			self.time = datetime.utcnow()
		except:
			pass

	def __pref__(self):
		return '<Visit %r>' %(self.ip)


################################
#List of all Heartrates known to server
class Heartrate(db.Model):
	__tablename__ = "Heartrate"
	ip 				= db.Column(db.Integer, db.ForeignKey('client.ip'))
	time 			= db.Column('time' , db.DateTime)
	heartrate 		= db.Column(db.Integer,unique=False)
	accuracy 		= db.Column(db.Integer,unique=False)
	deviceID 		= db.Column(db.String(64),unique=True,primary_key=True)
	deviceHash 		= db.Column(db.String(64),unique=True)

	def __init__(self ,ip, heartrate, accuracy, deviceID, deviceHash):
		self.ip = ip
		self.time = datetime.utcnow()
		self.heartrate = heartrate
		self.accuracy = accuracy
		self.deviceID = deviceID
		self.deviceHash = deviceHash

	def __pref__(self):
		return '<Heartrate %r>' %(self.ip)


############################
# Description of the game state for a specific game being played
############################
class Game(db.Model):
	__tablename__ = "game"
	gameID				= db.Column(db.String(64),unique=True,primary_key=True)
	rowCount 			= db.Column(db.Integer,unique=False)
	columnCount 		= db.Column(db.Integer,unique=False)
	gameOver			= db.Column(db.Boolean,unique=False)
	hiddenBlockCount	= db.Column(db.Integer,unique=False)

	def __init__(self, gameID, rowCount, columnCount, hiddenBlockCount):
		self.gameID				= gameID
		self.rowCount 			= rowCount
		self.columnCount 		= columnCount
		self.gameOver			= False
		self.hiddenBlockCount	= hiddenBlockCount


############################
#List of all Requests ever made to server
############################
class Tile(db.Model):
	tileID 			= db.Column(db.String(64),unique=True,primary_key=True)
	gameID 			= db.Column(db.String(64), db.ForeignKey('game.gameID'))
	tileIndex 		= db.Column(db.Integer,unique=False)
	tileRow 		= db.Column(db.Integer,unique=False)
	tileColumn 		= db.Column(db.Integer,unique=False)
	tileType 		= db.Column(db.String(64))
	tileStatus 		= db.Column(db.String(64))
	tileNeighbours	= db.Column(db.Integer,unique=False,default=0)

	def __init__(self, tileID, gameID, tileIndex, tileRow, tileColumn, tileType, tileStatus, tileNeighbours):
		self.tileID 		= tileID
		self.gameID 		= gameID
		self.tileIndex 		= tileIndex
		self.tileRow 		= tileRow
		self.tileColumn 	= tileColumn
		self.tileType 		= tileType
		self.tileStatus 	= tileStatus
		self.tileNeighbours	= tileNeighbours

print ">> Models File Loaded."
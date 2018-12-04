#!flask/bin/python

############ IMPORTS

from flask import Flask, Response, flash, session,make_response, render_template, redirect, url_for, request, jsonify, abort ,g
from flask import current_app as app
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from werkzeug.exceptions import HTTPException
from functools import update_wrapper
from datetime import *
from app import *
from pubg import *
from json2html import *
import json
import sys
import requests
import random
import string

#TODO: Make these editable
gameColumns = 7
gameRows = 13
bombCount = 20


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator








############################
#Representation of a tile for game construction purposes
############################
class TileOBJ:
	#Element "Constructor"
	def __init__(self, colVal, rowVal, tID):
		self.tileType = "WATER"		#Updated Later
		self.tileStatus = "HIDDEN"	#Updated during gameplay
		self.columnValue = colVal
		self.rowValue = rowVal
		self.tileID = tID
		self.tileIndex = (gameColumns*rowVal) + colVal
		self.bombCount = 0			#Updated later :)


############################
#Function called to generate a random string
############################
def get_random_string(stringSize):
	allchar = string.ascii_letters + string.digits
	return "".join(random.choice(allchar) for x in range(stringSize))


############################
#Function called to generate an ID for a tile
############################
def getNameForTile(game,tileRow,tileColumn):
	#
	return game.gameID+"_tile_"+str( (game.columnCount*tileRow) + tileColumn)


############################
#Matrix Initialization. Called at server startup and if player wants to restart their game
############################
def createNewGame(mapRows, mapCols, bombCount):
	print(">> Initializing New Game")

	##Generating Random String that represents the game state
	#FYI: If we get a repeated game key with the random string generated, i'm buying everyone beer, statistically speaking this won't ever happen :) (Baiting the dupe game key)
	gameID = get_random_string(16)

	##Creating new game
	gameAddQuery = models.Game(gameID, mapRows, mapCols, bombCount)
	db.session.add(gameAddQuery)
	db.session.commit()

	#Instantiating Game State Matrix
	mineMatrix = [[TileOBJ(colVal,rowVal,(getNameForTile(gameAddQuery,rowVal,colVal))) for rowVal in range(gameRows)] for colVal in range(gameColumns)]

	#Building Initial Game State
	for bIndex in range(bombCount):
		addedBomb = False
		while not addedBomb:
			curCol = random.randrange(gameColumns)
			curRow = random.randrange(gameRows)
			if mineMatrix[curCol][curRow].tileType != "BOMB":
				mineMatrix[curCol][curRow].tileType = "BOMB"
				addedBomb = True
				#print("Bomb at:",curCol,curRow)

	#Bomb at top left to facilitate debugging (Suicide Move)
	#mineMatrix[0][0].tileType = "BOMB"

	gameMatrix = "\n == GameState == \n\n "
	#Creating Tile Objects in Database
	for curRow in range(gameRows):
		for curCol in range(gameColumns):
			#Process Neighbourhood Statistics
			neighbourhoodCount = 0
			#LEFT
			if (curCol > 0) and mineMatrix[curCol-1][curRow].tileType == "BOMB":
				neighbourhoodCount+=1
			#RIGHT
			if (curCol < gameColumns-1) and mineMatrix[curCol+1][curRow].tileType == "BOMB":
				neighbourhoodCount+=1
			#TOP
			if (curRow > 0) and mineMatrix[curCol][curRow-1].tileType == "BOMB":
				neighbourhoodCount+=1
			#BOTTOM
			if (curRow < gameRows-1) and mineMatrix[curCol][curRow+1].tileType == "BOMB":
				neighbourhoodCount+=1

			if neighbourhoodCount > 0 and mineMatrix[curCol][curRow].tileType != "BOMB":
				mineMatrix[curCol][curRow].tileType = "NUMBER"
				gameMatrix = gameMatrix + str(neighbourhoodCount)
			else:
				if mineMatrix[curCol][curRow].tileType == "BOMB":
					gameMatrix = gameMatrix + "B"
					neighbourhoodCount = 0
				else:
					gameMatrix = gameMatrix + "W"

			#
			addTileQuery = models.Tile(
				mineMatrix[curCol][curRow].tileID,
				gameID,
				mineMatrix[curCol][curRow].tileIndex,
				curRow,
				curCol,
				mineMatrix[curCol][curRow].tileType,
				mineMatrix[curCol][curRow].tileStatus,
				neighbourhoodCount
			)
			db.session.add(addTileQuery)
			db.session.commit()

		gameMatrix = gameMatrix + "\n "
	gameMatrix = gameMatrix + "\n"

	#printing our game design to the console
	print(gameMatrix)

	return gameAddQuery


############################
#
############################
def RevealNeighboursOf(tile,game):
	#Ignoring expansion on non-water tiles
	if tile.tileType != "WATER":
		return

	#Calling moves that don't get processed as they are "free moves"
	#For simplicity we call on all neighbours regardless if they have been freed

	#BOTTOM
	if tile.tileRow < game.rowCount - 1:
		processMove(game.gameID,getNameForTile(game,tile.tileRow+1,tile.tileColumn),True)
	#TOP
	if tile.tileRow > 0:
		processMove(game.gameID,getNameForTile(game,tile.tileRow-1,tile.tileColumn),True)
	#RIGHT
	if tile.tileColumn < game.columnCount - 1:
		processMove(game.gameID,getNameForTile(game,tile.tileRow,tile.tileColumn+1),True)
	#LEFT
	if tile.tileColumn > 0:
		processMove(game.gameID,getNameForTile(game,tile.tileRow,tile.tileColumn-1),True)


############################
# Function used for general processing of a move on a specific tile
############################
def processMove(gameID, tileID, isSafeMove):
	#Fetching Tile from DB (Fetching on unique field, should only get 1 object)
	#Also fetching the game to evaluate
	tileEntry = None
	tileQuery = models.Tile.query.filter(models.Tile.tileID==tileID)
	if tileQuery is not None:
		tileEntry = tileQuery.first()
	else:
		return False

	gameEntry = None
	gameQuery = models.Game.query.filter(models.Game.gameID==gameID)
	if gameQuery is not None:
		gameEntry = gameQuery.first()
	else:
		return False

	#Avoiding Loop
	if tileEntry.tileStatus != "HIDDEN":
		return False

	#Updating status of tile
	if tileEntry.tileType == "BOMB":
		#Avoiding killing ourselves if we're unlocking neighbour tiles
		if isSafeMove == True:
			return False

		#Updating Game Over Status
		tileEntry.tileStatus = "KILLED"
		gameEntry.gameOver = True
		db.session.commit()

		#Updating the status of all tiles as revealed as the player lost the game
		multipleTileQuery = models.Tile.query.filter(models.Tile.gameID==gameID)
		if multipleTileQuery is not None:
			for tile in multipleTileQuery:
				tile.tileStatus = "REVEALED"
			db.session.commit()
		else:
			return False

	else:
		tileEntry.tileStatus = "REVEALED"
		gameEntry.gameOver = True
		db.session.commit()

		#Try to reveal neighbour tiles to a water
		if tileEntry.tileType == "WATER":
			RevealNeighboursOf(tileEntry,gameEntry)

	return tileEntry


######################################################
################################### MODESTO.IO WEBSITE
######################################################

######################################## Pre-page setup
#@app.before_request
#def before_request():
#    if request.url.startswith('http://'):
#        url = request.url.replace('http://', 'https://', 1)
#        code = 301
#        return redirect(url, code=code)

######################################################
################################### WEBPAGE STUFF
######################################################

heartrateRemovalTime = 60 * 30	#X Minutes until removal (X * 60)


########################################
class VisitorData(Resource):
    def get(self, visitorIP):
		query = models.Client.query.filter(models.Client.ip==visitorIP)
		if query is not None:
			visitList = models.Visit.query.filter(models.Visit.ip==str(query.first().ip)).all()
			returnableList = []
			for visit in visitList:
				returnableList.append({
					'id':visit.id,
					'ip':visit.ip,
					'time':visit.time.strftime("%Y-%m-%d %H:%M:%S")
				})
			return jsonify(result=returnableList)

			#list = [
            #{'a': 1, 'b': 2},
            #{'a': 5, 'b': 10}
           	#]
           	#return list

		return None

#Adding our API endpoint
appAPI = Api(app)
appAPI.add_resource(VisitorData, '/data/<string:visitorIP>')


########################################
def addHeart(rate,accuracy,ip,hashkey,deviceID):
	if int(rate) == -1 or int(accuracy) == -1:
		#print("Bad Data",rate,accuracy)
		return False

	heartInfo = getHeart(hashkey, deviceID)
	if heartInfo != None:
		timeDif = heartInfo.time - datetime.utcnow()
		print("Time Difference:",timeDif)
		if heartInfo.time - datetime.utcnow() > heartrateRemovalTime:
			#print("Really Old Data, Deleting User and adding it back")
			db.session.delete(heartInfo)
			db.session.commit()
		else:
			#print("Bad Hash Information")
			return False

	#print("Added Heart Rate for: " + str(deviceID))
	query = models.Heartrate(ip, int(rate), int(accuracy), deviceID, hashkey)
	db.session.add(query)
	db.session.commit()
	return True

########################################
def getHeart(hashkey,deviceID):
	query = models.Heartrate.query.filter(models.Heartrate.deviceID==deviceID)
	if query is not None:
		testUser = query.first()
		if testUser == None:
			#print("Does not exist")
			return None
		else:
			#if testUser.deviceHash != hashkey:
			#	print("Wrong Hash")
			#	return -1
			#else:
				if (datetime.utcnow() - testUser.time).total_seconds() > heartrateRemovalTime:
					#print("Old")
					db.session.delete(testUser)
					db.session.commit()
					return None
				else:
					#print("Good")
					return testUser

########################################
def updateHeart(rate,accuracy,ip,hashkey,deviceID):
	query = models.Heartrate.query.filter(models.Heartrate.deviceID==deviceID)
	if query is not None:
		testUser = query.first()
		if testUser is not None:
			#if testUser.deviceHash != hashkey:
			#	print("Wrong Hash")
			#	return False
			testUser.heartrate = rate
			testUser.accuracy = accuracy
			testUser.ip = ip
			testUser.time = datetime.utcnow()
			db.session.commit()
			#print("Updated Heart Rate to: " + str(rate))
			return True
		#print("User not found")
		addHeart(rate, accuracy, ip, hashkey, deviceID)
		#return False
	else:
		addHeart(rate, accuracy, ip, hashkey, deviceID)
	return True

########################################
def getHeartList():
	heartList = models.Heartrate.query.all()
	foundDeletable = False
	for i in range(0,(len(heartList))):
		timeDif = (datetime.utcnow() - heartList[i].time).total_seconds()
		print(timeDif)
		if timeDif > heartrateRemovalTime:
			print("This user needs deletion!")
			db.session.delete(heartList[i])
			foundDeletable = True
	if foundDeletable:
		db.session.commit()
		heartList = models.Heartrate.query.all()	
	return heartList

########################################
def getLocation(ip):
	response = requests.get('https://tools.keycdn.com/geo.json?host='+str(ip)).content
	jsonified = json.loads(response)
	if jsonified["status"] == "success":
		country = str(jsonified["data"]["geo"]["country_name"])
		code = str(jsonified["data"]["geo"]["country_code"])
		if (country != "None"):
			#print()
			return(country)
		#else:
		#	print(response)
			return(str(jsonified["data"]["geo"]["continent_name"]))
	#print("Error: "+jsonified["status"])
	return("unknown")

########################################
def updateClientList():
	query = models.Client.query.all()
	if query is not None:
		#ipList = sorted(ipList, key=lambda x: x.accessCount, reverse=True)
		index = 1
		for item in query:
			#Only updating clients with unknown locations to save on the queries to the API
			if (item.location == "unknown") or item.location == "None":
				newLocation = getLocation(item.ip)
				if (newLocation != "unknown") and (newLocation != "None"):
					#print("[" + str(index) + "] " + newLocation)
					item.location = newLocation
				else:
					print("\t \\--> still unknown")
			#else:
			#	print("[" + str(index) + "] is Already Good")
			index = index + 1
		db.session.commit()

########################################
def addVisit(request):
	myIP = str(requests.get('http://ipv4.icanhazip.com/').content).rstrip()
	ip = request.remote_addr

	if (myIP == ip) or (ip == "127.0.0.1") or (ip == "0.0.0.0"):
		print("\t \\--> Ignoring Local Visit")
		return

	print("\t \\--> Logging Visit from [" + str(ip) + "]. My IP: [" + myIP + "]")

	try:
		client = getVisitorID(ip)
		reply = False
		if (client == None):
			#print("Logging NEW user: " + str(ip))
			reply = addClient(ip)
		else:
			#print("Logging OLD user: " + str(ip) + "\tUID: <" + str(client) + ">")
			reply = updateClient(ip)

		if (reply == True):
			#Saving Visit to DB
			query = models.Visit(ip)
			#print("Saving Visit IP: [" + str(query.ip) + "]  ID: [" + str(query.id) + "]")
			db.session.add(query)
			db.session.commit()
	except:
		pass

########################################
def addClient(ip):
	#Saving Client to DB
	myIP = str(requests.get('http://ipv4.icanhazip.com/').content).rstrip()
	if (myIP == ip) or (ip == "127.0.0.1") or (ip == "0.0.0.0"):
		return False

	query = models.Client(ip)
	location = getLocation(ip)
	query.location = location
	db.session.add(query)
	db.session.commit()
	return True

########################################
def updateClient(ip):
	curUser = models.Client.query.filter_by(ip=ip).first()
	curUser.lastAccess = datetime.utcnow()
	curUser.accessCount = int(curUser.accessCount) + 1
	curUser.location = getLocation(curUser.ip)
	db.session.commit()
	return True

########################################
def getVisitorID(ip):
	#print "\t \\--> Query for Player Name: <" + name + ">"
	query = models.Client.query.filter(models.Client.ip==ip)
	if query is not None:
		return query.first()
	return None

########################################
def getClientList():
	query = models.Client.query.all()
	if query is not None:
		return query
	return None

########################################
def processMinesweeperPost(request):
	#Treating POST events (Get new game, Submit game move)
	if request.method == "POST":

		#Loading Content of Request
		incommingMessage = json.loads(request.get_data())

		##################
		#Treating New Game Requests
		if "event" in incommingMessage and incommingMessage["event"] == "newgame":
			#print(">> Treating New Game Event")

			#Full on creating a new game, we don't have user subsystems so this should be fine
			newGame = createNewGame(gameRows,gameColumns,bombCount)

			#Building response based on interpretation of the validity of the move
			response = jsonify({
				'gameID' 			:	newGame.gameID,
				'rowCount' 			:	newGame.rowCount,
				'columnCount' 		:	newGame.columnCount,
				'hiddenBlockCount' 	:	newGame.hiddenBlockCount,
			})
			return response

		#################
		#Treating Move Submission Requests
		if "event" in incommingMessage and incommingMessage["event"] == "move":
			#print(">> Treating Move Event")

			#Checking if request has the info needed
			if "tileID" in incommingMessage and "gameID" in incommingMessage and "tileIndex" in incommingMessage:

				tileIndex = int(incommingMessage["tileIndex"])
				tileID = incommingMessage["tileID"]
				gameID = incommingMessage["gameID"]

				#Checking if the request is for a valid location
				if tileIndex > gameColumns*gameRows:
					return "Bad Request - Tile Index out of range"

				#Processing game move according to game rules
				replyToMove = processMove(gameID,tileID,False)

				#Checking if the move resulted in some sort of error & basically just ignoring it if it caused an error
				if replyToMove == False:
					return "Bad Request - Bad Move"

				#Building response based on interpretation of the validity of the move
				response = jsonify({
					'tileType'		:	replyToMove.tileType,
					'tileStatus'	:	replyToMove.tileStatus,
					'tileNeighbours':	replyToMove.tileNeighbours,
				})
				return response
			#Generic response for invalid move event
			return "Bad Request - Missing Parameters"

		##################
		#Treating Game State Recall Requests
		if "event" in incommingMessage and incommingMessage["event"] == "recall":
			#print(">> Treating Recall Event")

			#Checking if request has the info needed
			if "gameID" in incommingMessage:
				gameID = incommingMessage["gameID"]

				#Fetching Game from database
				gameEntry = None
				gameQuery = models.Game.query.filter(models.Game.gameID==gameID)
				if gameQuery is not None:
					gameEntry = gameQuery.first()
					if (gameEntry == None):
						return False
				else:
					return False

				tileEntryList = []
				#Checking if the game exists
				query = models.Game.query.filter(models.Game.gameID==gameID)
				if query is not None:

					#Fetching moves that are revealed for this game
					tileQuery = models.Tile.query.filter(models.Tile.gameID==gameID).all()

					tileEntryList = []
					for tile in tileQuery:
						if tile.tileStatus == "REVEALED":
							tileEntryList.append({
								'tileID' 		: tile.tileID,
								'gameID'		: tile.gameID,
								'tileIndex'		: tile.tileIndex,
								'tileRow'		: tile.tileRow,
								'tileColumn' 	: tile.tileColumn,
								'tileType' 		: tile.tileType,
								'tileStatus' 	: tile.tileStatus,
								'tileNeighbours': tile.tileNeighbours
							})
				else:
					return False

				#Building response with the game state (visible tiles)
				response = jsonify({
					'gameID' 			:	gameEntry.gameID,
					'rowCount' 			:	gameEntry.rowCount,
					'columnCount' 		:	gameEntry.columnCount,
					'hiddenBlockCount' 	:	gameEntry.hiddenBlockCount,
					'tileList'			:	tileEntryList
				})
				return response
			#Generic response for invalid move event
			return "Bad Request - Missing Parameters"

		return  "Unknown Request Type"

######################################## Default Page Reroute to 404 template
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
	addVisit(request)
	return render_template('404.html'), 404


######################################## Error 404 Handling
@app.errorhandler(404)
def page_not_found(e):
	addVisit(request)
	return render_template('404.html'), 404

########################################
@app.route('/', methods=['GET'])
def home():
	addVisit(request)
	return render_template('index.html',error=None)

########################################
@app.route('/index', methods=['GET'])
def index():
	addVisit(request)
	return render_template('index.html',error=None)

########################################
@app.route('/stats', methods=['GET'])
def stats():
	addVisit(request)
	ipList = getClientList()
	ipList = sorted(ipList, key=lambda x: x.accessCount, reverse=True)
	index = 1
	regionList = {}
	for client in ipList:
		client.index = index
		index = index + 1

		if not client.location in regionList:
			regionList[client.location] = {
				"AccessCount" : client.accessCount,
				"RegionCode" : client.location
			}
			#print("Adding Region: " + str(client.location))
		else:
			regionList[client.location]["AccessCount"] = regionList[client.location]["AccessCount"] + client.accessCount


	return render_template('stats.html',ipList=ipList,countryList=regionList,error=None)

########################################
@app.route('/heart', methods=['GET','POST'])
def heart():
	#pass
	return heart_code("")

########################################
@app.route('/heart/<code>', methods=['GET','POST'])
def heart_code(code):
	accuracyMap = {
	 1 : "Low",
	 2 : "Medium",
	 3 : "High"
	}
	if request.method == 'GET':

		if code == "":
			heartRateInfoList = getHeartList()
			for i in range(0,(len(heartRateInfoList))):
				heartRateInfoList[i].accuracy = accuracyMap[heartRateInfoList[i].accuracy]
			return render_template('heart_list.html',heartList =heartRateInfoList )

		#heartRate = getHeart("[B@11b4a9b","27b19c8daf29df23")
		rateInfo = getHeart("does_not_matter",code)
		heartRate = None
		accuracy = None
		if rateInfo != None:
			#print(" \\--> Have Heart Rate")
			if rateInfo.heartrate != 0 and rateInfo.heartrate != -1:
				if (datetime.utcnow() - rateInfo.time).total_seconds() < 30:
					heartRate = rateInfo.heartrate
				else:
					heartRate = -1
				accuracy = accuracyMap[rateInfo.accuracy]

			return render_template('heart.html',heartRate=heartRate,accuracy=accuracy,error=None)
		else:
			print(" \\--> No Info")
			return ("BPM Information not available.<br>Information might have been deleted as it became old.")

	postString = request.get_data()
	#print(postString)

	heartrateDict = json.loads(postString)
	currentHeartrate = int(heartrateDict['heartrate'])

	returnStatus = False
	if (currentHeartrate == -1):
		#print("Attempt Add")
		returnStatus = addHeart(heartrateDict['heartrate'],heartrateDict['accuracy'],heartrateDict['ip'],heartrateDict['key'],heartrateDict['uid'])
	else:
		#print("Attempt Update")
		returnStatus = updateHeart(heartrateDict['heartrate'],heartrateDict['accuracy'],heartrateDict['ip'],heartrateDict['key'],heartrateDict['uid'])

	if returnStatus == True:
		return("GOOD")
	else:
		return("BAD")

########################################
@app.route('/test', methods=['GET'])
def test():
	ip = request.remote_addr
	#client = getVisitorID(ip)
	#updateClientList()
	return ("Your IP is: " + str(ip))

########################################
@app.route('/gallery', methods=['GET'])
def gallery():
	addVisit(request)
	return render_template('gallery.html',error=None)

########################################
@app.route('/minesweeper', methods=['GET','POST'])
@cross_origin()
@crossdomain(origin='*')
def newsweeper():
	return minesweeper("")

########################################
@app.route('/minesweeper/<gameID>', methods=['GET','POST'])
@cross_origin()
@crossdomain(origin='*')
def minesweeper(gameID):
	if request.method == 'GET':
		addVisit(request)
		return render_template('minesweeper.html',error=None)

	if request.method == 'POST':
		response = processMinesweeperPost(request)
		if response == False:
			return "ERROR"
		else:
			return response

######################################################
########################## Legacy Personal Stuff Below
######################################################

########################################
@app.route('/esg6100', methods=['GET','POST'])
def teaching():
	addVisit(request)
	return render_template('esg6100.html',error=None)

########################################
@app.route('/monitor', methods=['GET','POST'])
def monitor():
	addVisit(request)
	return render_template('monitor.html',error=None)

########################################
@app.route('/temperature', methods=['GET','POST'])
def temperature():
	addVisit(request)
	return render_template('temperature.html',error=None)

########################################
@app.route('/pubg', methods=['GET','POST'])
def pubg():
	addVisit(request)
	#Treating initial page get request
	if request.method == 'GET':
		print("GET!")
		print("Processing Request")
		return render_template('pubg.html',error=None)

	#treating POST request for info
	if request.method == 'POST':
		print("POST!")
		if request.form['submit'] == 'getPlayer':
			if ('PlayerName' in request.form):
				print("GET PLAYER!")
				pName = request.form['PlayerName']
				#Get Player Info
				jsonDump = fetchUserList([pName])
				jsonHTML = json2html.convert(json = jsonDump,table_attributes="id=\"player-info\" class=\"table table-bordered\" align=\"center\"")
				return render_template('pubg.html',error=None, jsonHTML=jsonHTML,player=pName)

		elif request.form['submit'] == 'getMatch':
			if ('MatchID' in request.form):
				print("GET MATCH!")
				matchID = request.form['MatchID']
				#Get Player Info
				jsonDump = fetchMatch(matchID)
				jsonHTML = json2html.convert(json = jsonDump,table_attributes="id=\"match-info\" class=\"table table-bordered\" align=\"center\"")


				return render_template('pubg.html',error=None, jsonHTML=jsonHTML,match=matchID)

	#Se o campo ta vazio, fodase
	return render_template('pubg.html',error=None)



#if __name__ == '__main__':
#	app.run(debug=True, port=8000)

print ">> Site File Loaded."
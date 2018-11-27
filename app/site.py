#!flask/bin/python
from flask import Flask, flash, session, render_template, redirect, url_for, request, jsonify, abort ,g
from werkzeug.exceptions import HTTPException
from datetime import *
from app import *
from pubg import *
from json2html import *
import json
import sys
import requests


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
def addHeart(rate,accuracy,ip,hashkey,deviceID):
	if int(rate) == -1 or int(accuracy) == -1:
		#print("Bad Data",rate,accuracy)
		return False

	heartInfo = getHeart( hashkey, deviceID)
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
@app.route('/minesweeper', methods=['GET'])
def minesweeper():
	if request.method == 'GET':
		addVisit(request)
		return render_template('minesweeper.html',error=None)

	if request.method == 'POST':
		#TODO: Replace with implementation made for the programming challenge
		pass

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
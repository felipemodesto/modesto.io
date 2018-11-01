import requests
import json
import json2html

PlayerName = "mrhumble"
PlayerID = "252ba7b5e64d4076a2456e74f1071768"
MatchID = "727569f2-0611-491a-b9f8-e97c1a11d01e"

FriendList = [
	"Zucca-",
	"ZeaCu",
	"BlackXIII",
	"Kyrw",
	"GuiAvila",
	"leokassio",
	"braindf",
	"lucaspessoa"
]

MatchKey = "23B776"
PrivateKey = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJhMzVjNDc5MC0xOGQ3LTAxMzYtOGRlYy01NWIwMmE2ZWVmZDkiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNTIyNjk2MzE4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Imh1bWJsZXIiLCJzY29wZSI6ImNvbW11bml0eSIsImxpbWl0IjoxMH0.qAV5lUGeLpQyjg8__nI1FyGEVZppDxEME6NEbvojbsc"

#############################################################
##
#############################################################
def fetchUser(pID = PlayerID, pKey = PrivateKey):
	r = requests.get(
						"https://api.playbattlegrounds.com/shards/pc-na/players/account."+pID,
						headers = {
							'Authorization': pKey,
							'accept':'application/vnd.api+json'
						}
					)
	#print(r)
	#print(r.json())
	return r.json()


#############################################################
##
#############################################################
def fetchUserList(pIDList = FriendList, pKey = PrivateKey):
	stringfriendList = pIDList[0]
	for i in range(1,len(pIDList)):
		stringfriendList = stringfriendList + "," + pIDList[i]

	print("making request for <"+stringfriendList+">\n")
	r = requests.get(
						"https://api.playbattlegrounds.com/shards/pc-sa/players?filter[playerNames]="+stringfriendList,
						headers = {
							'Authorization': pKey,
							'accept':'application/vnd.api+json'
						}
					)

	#filtering useless data
	jsonObject = r.json()
	jsonObject = jsonObject["data"][0]
	jsonObject["type"] = None

	#
	return jsonObject


#############################################################
##
#############################################################
def fetchMatch(mID = MatchID, pKey = PrivateKey):
	print("making request for <"+MatchID+">\n")
	r = requests.get(
						"https://api.playbattlegrounds.com/shards/pc-na/matches/"+mID,
						headers = {
							'Authorization': pKey,
							'accept':'application/vnd.api+json'
						}
					)
	#print(r)
	jsonObject = r.json()
	jsonObject["AttributeCount"] = "Number of Attribute Objects: "+str(len(jsonObject["included"]))
	jsonObject["TeamCount"] = len(jsonObject["data"]["relationships"]["rosters"]["data"])
	jsonObject["MatchId"] = jsonObject["data"]["id"]
	jsonObject["MatchType"] = jsonObject["data"]["type"]
	jsonObject["GameMode"] = jsonObject["data"]["attributes"]["gameMode"]
	jsonObject["PlayerList"] = {}

	jsonObject["PlayerCount"] = 0
	#for i in range(0,len(jsonObject["included"])):
	i = 0
	while i < len(jsonObject["included"]):
		if jsonObject["included"][i]["type"] == "participant":
			jsonObject["PlayerCount"] = jsonObject["PlayerCount"] + 1
			jsonObject["PlayerList"].update({jsonObject["PlayerCount"]:jsonObject["included"][i]["attributes"]["stats"]["name"]})
			#del jsonObject["included"][i]
		#else:
			#i = i+1
			#print(jsonObject["included"][i]["type"])

		i = i+1

	#del jsonObject["included"]		#Contains all Game Attributes
	del jsonObject["data"]			#Contains Round Specific Data(Empty), Roster List and match ID
	del jsonObject["links"]			#Empty
	del jsonObject["meta"]			#Empty
	return jsonObject


#############################################################
##
#############################################################
def fetchTelemetry(mID = MatchID, pKey = PrivateKey):
	print("BLABLA")


print ">> PUBG File Loaded."
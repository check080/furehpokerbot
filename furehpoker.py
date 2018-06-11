import requests
import json

class player:
    def __init__(self,plid,username):
        self.id=plid
        self.username=username
        self.chips=1000
        self.currentGame=0
        self.online=True

class game:
    def __init__(self):
        self.phase="wait" #can be wait, hand, or bet
        self.players=[] #list of all plid's
        self.hands={} #plid: hand
        

BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
ADMIN_IDS=[156638024,131331518]
LEADERBOARD_NUM=10

cont=True
players={} #plid: playerinstance
games=[] #list of all gameinstance's


def sendBotRequest(requestName):
    return requests.get(ACCESS_WEBSITE+requestName).content

def botUpdate(num):
    jsonData=json.loads(sendBotRequest("getupdates?offset=%d" %num))
    try:
        if(jsonData["ok"]==True):
            return jsonData["result"]
        else:
            return False
    except KeyError:
        return False

def sendMessage(chat_id,text):
    print("TO %d: %s" %(chat_id,text) )
    sendBotRequest("sendMessage?chat_id=%d&text=%s" %(chat_id,text) )

def findNumOnline(): #Returns the number of people online
    totalOnline=0
    for i in players.values():
        if(i.online):
            totalOnline+=1
    return totalOnline

def getLeaderboard(): #Returns a list of the people with the most chips, greatest to least
    scoreList={}
    for i in players.values():
        scoreList[i.username]=i.chips
    topScores=[]
    numAppended=0
    for key, value in reversed(sorted(scoreList.items(), key=(lambda k: k[1]) )):
        if(numAppended>=LEADERBOARD_NUM):
            break
        topScores.append([key,value])
    return topScores

def processCommand(usrReq):
    global cont
    global players
    global games

    userid=usrReq["from"]["id"]
    username=usrReq["from"]["username"]
    reqtext=usrReq["text"]

    print("FROM %d (%s): %s" %(userid,username,reqtext) ) #THIS will break if someone types arabic

    #USER COMMANDS
    if(reqtext=="/start"):
        if(userid in players.keys() ): #if the player is already registered
            sendMessage(userid,"Welcome back to Fur-Eh poker. Your balance is %d chips." %players[userid].chips )
            if(not players[userid].online):
                sendMessage(userid,"You are currently offline. If you want to get invited to poker games, say /online")
        else: #if they aren't
            players[userid]=player(userid,username) #add a dict entry with a new instance of the player class
            sendMessage(userid,"Welcome to Fur-Eh poker. Explanation text. Type /help for more commands. Your balance is %d chips." %players[userid].chips )
        sendMessage(userid,"%d players online." %findNumOnline())

    elif(not userid in players.keys() ): #if the player hasn't yet said /start
        sendMessage(userid,"Start the bot with /start.")
        return #don't let them do any other commands

    elif(reqtext=="/offline"):
        if(players[userid].online):
            sendMessage(userid,"Ok, you will no longer receive poker game invitations.")
        else:
            sendMessage(userid,"You are already marked as offline.")
        players[userid].online=False

    elif(reqtext=="/online"):
        if(players[userid].online):
            sendMessage(userid,"You are already marked as online.")
        else:
            sendMessage(userid,"Ok, you will now receive poker game invitations.")
        sendMessage(userid,"%d players online." %findNumOnline())
        players[userid].online=True

    elif(reqtext=="/getLeaderboard"):
        leaderList=getLeaderboard()
        retText=""
        for i in leaderList:
            retText+="\n%s: %s" %(i[0],i[1])
        sendMessage(userid,"Top chips:"+retText)
        
    if(userid in ADMIN_IDS):
        #ADMIN COMMANDS
        if(reqtext=="/quit"):
            print("Admin called quit.")
            cont=False
    

def main():
    #Initialization here
    print("Initialized.")

    numClear=0
    while cont:

        #CHECK FOR PLAYER INPUT
        reqBuf=botUpdate(numClear) #this takes time
        if(reqBuf):
                
            for i in reqBuf:
                try:
                    
                    if((i["update_id"]+1)>numClear): #find the highest update_id so they can be cleared
                        numClear=i["update_id"]+1
                        
                    processCommand(i["message"])
                    
                except KeyError:
                    continue

        #CHECK TIMERS
        
    botUpdate(numClear) #get rid of the last update queue


main()

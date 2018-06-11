import requests
import json

class player:
    def __init__(plid):
        self.id=plid
        self.chips=1000
        self.currentGame=0
        self.online=True

class game:
    def __init__():
        self.phase="wait" #can be wait, hand, or bet
        self.players=[] #list of all plid's
        self.hands={} #plid: hand
        

BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
ADMIN_IDS=[156638024,131331518]

cont=True
players={} #plid: playerinstance
games=[] #list of all gameinstance's


def sendBotRequest(requestName):
    return requests.get(ACCESS_WEBSITE+requestName).content

def botUpdate():
    jsonData=json.loads(sendBotRequest("getupdates"))
    try:
        if(jsonData["ok"]==True):
            return jsonData["result"]
        else:
            return False
    except KeyError:
        return False

def sendMessage(chat_id,text):
    sendBotRequest("sendMessage?chat_id=%d&text=%s" %(chat_id,text) )

def processCommand(usrReq):
    global cont
    global players
    global games

    userid=usrReq["from"]["id"]
    reqtext=usrReq["text"]

    #USER COMMANDS
    if(reqtext=="/start"):
        if(userid in players.keys() ): #if the player is already registered
            sendMessage(userid,"Welcome back to Fur-Eh poker. Your balance is %d chips." %players[userid].chips )
        else: #if they aren't
            players[userid]=player(userid) #add a dict entry with a new instance of the player class
            sendMessage(userid,"Welcome message. Explanation text. Type /help for more commands. Your balance is %d." %players[userid].chips )

    if(userid in ADMIN_IDS):
        #ADMIN COMMANDS
    

def timerEvent(curTime):
    print(curTime)

def main():
    timers=[]
    
    while cont:

        #CHECK FOR PLAYER INPUT
        reqBuf=botUpdate() #this takes time
        if(reqBuf):
            for i in reqBuf:
                try:
                    processCommand(i["message"])
                except KeyError:
                    continue

        #CHECK TIMERS

main()

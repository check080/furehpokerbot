from string import printable
import requests
import json

LEGAL_CHARS=set(printable)
BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
RANK_DICT={2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"Jack",12:"Queen",13:"King",14:"Ace"}
SUIT_DICT={1:"Spades",2:"Hearts",3:"Diamonds",4:"Clubs"}
SCORE_DICT={0:"high card",1:"pair",2:"2 pairs",3:"3 of a kind",4:"straight",5:"flush",6:"full house",7:"4 of a kind",8:"straight flush",9:"royal flush"}
SAVE_FILE="furehpokerbot.json"

TIER_CUTOFFS=[5, 500, 2000] #The minimum required chips to be a member of each tier
TIER_BUYINS= [5,  10,   20] #The buyin cost for a game on that tier
ADMIN_IDS=[156638024,131331518] #Facade and Alexi
LEADERBOARD_NUM=10 #How many names to display in the leaderboard
MAX_SIMULTANEOUS_GAMES=40
STARTING_CHIPS=1000
MAX_PLAYERS_PER_GAME=3 #will change later; can't be more than 10 if only 1 deck is used
MAX_DEALS=2
BETTING_ROUNDS=2
DEAL_COSTS=[10,20] #The price of dealing based on which turn, needs to be MAX_DEALS long
CARDS_PER_HAND=5
CARD_DECKS=1 #Decks worth of cards used in each game
RESPONSE_TIME_LIMIT=120.0 #In seconds, float
GAME_START_TIME_LIMIT=300.0 #In seconds, float

#Global Lists
players={} #plid: player instance
games={} #gmid: game instance

playerSaveArray={} #plid: [username,chips]

class card:
    def __init__(self,rankid,suitid):
        self.rankid=rankid
        self.suitid=suitid
    def getName(self):
        return RANK_DICT[self.rankid]+" of "+SUIT_DICT[self.suitid]

def sendBotRequest(requestName):
    return str(requests.get(ACCESS_WEBSITE+requestName).content)

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
	
def makeKeyboard(btnList): #Accepts list of buttons e.g. makeKeyboard(["HOLD","DEAL"])
    retString="&reply_markup={\"keyboard\":["
    retString+="[\""+btnList[0]+"\"]"
    for i in btnList[1:]:
        retString+=",[\""+i+"\"]"
    retString+="]}"
    return retString
    
def removeKeyboard():
    return "&reply_markup={\"hide_keyboard\":true}"
    
def saveData():
    try:
        jsonString=json.dumps(playerSaveArray)
    except JSONDecodeError:
        print("[ERROR]: FAILED to convert player save data to json.")
        return
    try:
        fileObj=open(SAVE_FILE,"w")
        fileObj.write(jsonString)
        fileObj.close()
        print("[LOG] Saved player data.")
    except IOError:
        print("[ERROR]: FAILED to write to file %s. Nothing saved."%SAVE_FILE)
        
def loadData():
    global playerSaveArray
    try:
        fileObj=open(SAVE_FILE,"r")
        retString=fileObj.readline()
        fileObj.close()
    except IOError:
        print("[LOG] Failed to read file %s."%SAVE_FILE)
        return False
    try:
        jsonPlayerArray=json.loads(retString)
        for plid,plarr in jsonPlayerArray.items():
            if(len(plarr)!=2 or (not type(plarr[0]) is str) or (not type(plarr[1]) is int)):
                print("[LOG] File %s is in an incorrect format - invalid array size/username/chip amount"%SAVE_FILE)
                playerSaveArray={}
                return False
            playerSaveArray[int(plid)]=plarr
        print("[LOG] Loaded file %s."%SAVE_FILE)
        return True
    except ValueError:
        print("[LOG] File %s is in an incorrect format - json decode error or invalid plid"%SAVE_FILE)
        return False
    except IndexError:
        print("[LOG] File %s is in an incorrect format - invalid array size"%SAVE_FILE)

import requests
import json

class player: #send the player a game request IFF currentGame==0 AND online==True
    def __init__(self,plid,username):
        self.id=plid
        self.username=username
        self.chips=1000
        self.currentGame=0 #Player's current game id
        self.currentGameInvite=0 #Player's invite game id
        self.online=True

class game:
    def __init__(self,gmid,tiernum):
        self.id=gmid
        self.tier=tiernum #the tier of players this game is open to
        self.phase="wait" #can be wait, hand, or bet
        self.players=[] #list of all plid's
        self.hands={} #plid: hand
    def end(self):
        del games[self.id]
        

BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
ADMIN_IDS=[156638024,131331518] #Facade and Alexi
LEADERBOARD_NUM=10 #How many names to display in the leaderboard
TIER_CUTOFFS=[0, 1000, 2000, 3000, 4000] #The minimum required chips to be a member of each tier

cont=True
players={} #plid: player instance
games={} #gmid: game instance 




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

def getGameList(): #Returns a list of the games currently running/waiting for players -- UNTESTED
    tieredGames={}
    for i in range(1,len(TIER_CUTOFFS)+1):
        tieredGames[i]=[]
    for j in games.values():
        retString=""
        if(j.phase=="wait"):
            retString+="Waiting for players, "
        else:
            retString+="In progress, "
        retString+="%d players." %len(j.players)
        tieredGames[j.tier].append(retString)
    return tieredGames



def processCommand(usrReq):
    global cont
    global players
    global games

    userid=usrReq["from"]["id"]
    username=usrReq["from"]["username"]
    reqtext=usrReq["text"]

    print("FROM %d (%s): %s" %(userid,username,reqtext) ) #THIS will break if someone types arabic

    if(userid in ADMIN_IDS):
        cmdList=reqtext.split(" ")
        #ADMIN COMMANDS
        if(cmdList[0]=="/quit"):
            print("Admin called quit.")
            cont=False

        elif(cmdList[0]=="/help"):
            retString="ADMIN COMMANDS:\n" \
                      "/quit - Stop the server\n" \
                      "/startgame [tier] - Start a new game on the specified tier\n" \
                      "/gamestats - See all game stats"
            sendMessage(userid,retString)
            
        elif(cmdList[0]=="/startgame"):
            try:
                tiernum=int(cmdList[1])
            except ValueError:
                sendMessage(userid,"Usage: /startgame [tier], where [tier] is the tier the game is on from %d to %d." %(1,len(TIER_CUTOFFS)) )
                return
            except IndexError:
                sendMessage(userid,"Usage: /startgame [tier], where [tier] is the tier the game is on from %d to %d." %(1,len(TIER_CUTOFFS)) )
                return
            if(not 0<tiernum<=len(TIER_CUTOFFS)):
                sendMessage(userid,"Usage: /startgame [tier], where [tier] is the tier the game is on from %d to %d." %(1,len(TIER_CUTOFFS)) )
                return
            newGame(tiernum)

        elif(cmdList[0]=="/gamestats"):
            retString="List of games currently active:"
            tieredGames=getGameList()
            for i in tieredGames.keys():
                retString+="\nTIER %d" %i
                for j in tieredGames[i]:
                    retString+=("\n"+j)
            sendMessage(userid,retString)

    #USER COMMANDS
    if(reqtext=="/start"):
        if(userid in players.keys() ): #if the player is already registered
            sendMessage(userid,"Welcome back to Fur-Eh poker. Your balance is %d chips." %players[userid].chips )
            if(not players[userid].online):
                sendMessage(userid,"You are currently offline. If you want to get invited to poker games, say /online")
        else: #if they aren't
            players[userid]=player(userid,username) #add a dict entry with a new instance of the player class
            sendMessage(userid,"Welcome to Fur-Eh poker. Explanation text. Type /help for more commands. Your balance is %d chips." %players[userid].chips )

    elif(reqtext=="/help"):
        retString="Bot Commands:\n" \
                  "/start - Start the bot\n" \
                  "/help - Get a list of commands\n" \
                  "/online - Receive invitations to poker games\n" \
                  "/offline - Stop receiving invitations\n" \
                  "/getleaderboard - Show the top players and their chips\n" \
                  "/join - Join the game you've been invited to\n" \
                  "You cannot use these commands while in the middle of a game."
        sendMessage(userid,retString)

    elif(not userid in players.keys() ): #if the player hasn't yet said /start
        sendMessage(userid,"Start the bot with /start.")
        return #don't let them do any other commands

    elif(players[userid].currentGame!=0): #if the player is in the middle of a game
        if(reqtext[0]=="/"):
            sendMessage(userid,"You can't use bot commands in the middle of a game.")
        else:
            print("GAME REQUEST RECEIVED.")

    elif(reqtext=="/join"):
        retString=""
        if(not players[userid].online):
            sendMessage(userid,"You are currently marked as offline. Type /online to get game invitations.")
        elif(players[userid].currentGameInvite==0):
            sendMessage(userid,"No game to join yet. Wait for an invite, and then type /join")

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
        players[userid].online=True

    elif(reqtext=="/getleaderboard"):
        leaderList=getLeaderboard()
        retText="%d players online.\nTop chips:" %findNumOnline()
        for i in leaderList:
            retText+="\n%s: %s" %(i[0],i[1])
        sendMessage(userid,retText)
    
def newGame(tiernum):
    print("Starting new game for tier %d." %tiernum)
    #Access the array with tiernum-1

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

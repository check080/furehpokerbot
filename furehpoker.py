import requests
import json

class card:
    def __init__(self,rankid,suitid):
        self.rank=rankid
        self.suit=suitid

class player:
    def __init__(self,plid,username,chips):
        #SAVE STUFF
        self.id=plid
        self.username=username
        self.chips=chips

        #GAME STUFF
        self.online=True
        self.tier=1
        self.currentGame=0 #Player's current game id
        self.currentGameInvite=0 #Player's invite game id
        self.holding=False
        self.draws=0
        self.hand={}

    def updateTier(self):
        retNum=0
        if(self.chips==0):
            self.tier=0
            return
        for i in range(len(TIER_CUTOFFS)):
            if(TIER_CUTOFF[i]>self.chips):
                break
            retNum=i+1
        self.tier=retNum

    def getHand(self):
        return "I dunno dude"
            
    def acceptResponse(self,reqtext): #All user text is sent here when they are mid-game
        curGame=games[self.currentGame]
        reqtext=reqtext.upper() #Make it case insensitive
        if(curGame.players[currentTurn]==self.id): #if it's your turn
            if(curGame.phase=="hand"):
                if(reqtext=="HOLD"):
                    self.holding=True
                    curGame.consecutiveHolds+=1
                    curGame.nextTurn()
                elif(reqtext=="DRAW"):
                    if(self.draws>=MAX_DRAWS):
                        sendMessage(self.id,"You can't draw more than %d times." %MAX_DRAWS)
                    else:
                        self.draws+=1
                        #ALSO THE REST OF IT
                

class game:
    def __init__(self,gmid,tiernum):
        self.id=gmid
        self.tier=tiernum #the tier of players this game is open to
        self.phase="wait" #can be wait, hand, or bet
        self.pPlaying=[] #list of all playing plid's
        self.currentTurn=0 #array index of which player's turn it is
        self.consecutiveHolds=0 #number of holds in a row; if this >= len(players) then startBet is triggered
        self.invites=[] #list of all invited plid's
        self.deck=[] #list of all cards remaining in the deck
        self.begin()
    def shuffleDeck(self):
        print("Just randomly reorder self.deck here")
    def beginGame(self):
        #Send invitations to everyone, and set a listener for their response
        for i in players.values():
            if(i.online and i.currentGame==0 and TIER_CUTOFFS[self.tier-1]<i.chips<TIER_CUTOFFS[self.tier]): #if they're online, not in a game, and in the right tier
                self.invites.append(i.id)
                i.currentGameInvite=gmid
    def startHand(self):
        self.phase="hand"
        #Revoke all remaining invites
        for i in players.values():
            if(i.currentGameInvite==gmid):
                i.currentGameInvite=0
        #Give everyone 5 cards from the deck, then go one person at a time waiting for either a response or the expiration of the timer object
    def nextTurn(self):
        self.currentTurn=(self.currentTurn+1)%len(self.pPlaying)
        if(self.phase=="hand"):
            if(self.consecutiveHolds>=len(self.pPlaying): #if it's gone in a circle and everyone held
               self.startBet()
            else:
                self.handTurn(self.pPlaying[self.currentTurn])
        elif(self.phase=="bet"):
            self.betTurn(self.pPlaying[self.currentTurn])
    def handTurn(self,plid):
        if(players[plid].draws>=MAX_DRAWS):
               sendMessage(plid,"Cards: "+players[plid].getHand()+"\n"+makeKeyboard(["HOLD"]) )
        else:
            sendMessage(plid,"Cards: "+players[plid].getHand()+"\n"+makeKeyboard(["HOLD","DRAW"]) )
    def startBet(self):
        print("Nothing here yet")
    def endGame(self):
        del games[self.id]
        

BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
rankdict={1:"Ace",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"Jack",12:"Queen",13:"King"}
suitdict={1:"Spades",2:"Hearts",3:"Diamonds",4:"Clubs"}
ADMIN_IDS=[156638024,131331518] #Facade and Alexi
LEADERBOARD_NUM=10 #How many names to display in the leaderboard
TIER_CUTOFFS=[0, 1000, 2000, 3000, 4000] #The minimum required chips to be a member of each tier
MAX_SIMULTANEOUS_GAMES=40
STARTING_CHIPS=1000
MAX_PLAYERS_PER_GAME=2 #will change later
MAX_DRAWS=2

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
        retString="%d: " %j.id
        if(j.phase=="wait"):
            retString+="Waiting for players, "
        else:
            retString+="In progress, "
        retString+="%d players." %len(j.players)
        tieredGames[j.tier].append(retString)
    return tieredGames

def makeKeyboard(btnList): #Accepts list of buttons e.g. makeKeyboard(["HOLD","DRAW"])
    retString="&reply_markup={\"keyboard\":[["
    retString+=btnList[0]
    for i in btnList[1:]:
        retString+=",\""+i+"\""
    retString+="]],\"one_time_keyboard\":true}"
    return retString



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
                      "/gamestats - See all game stats\n" \
                      "/freeze - stop game events, stop sending invites\n" \
                      "/resume - continue game events and invites"
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
            players[userid]=player(userid,username,STARTING_CHIPS) #add a dict entry with a new instance of the player class
            sendMessage(userid,"Welcome to Fur-Eh poker. Type /rules to learn to play. Type /help for more commands. Your balance is %d chips." %players[userid].chips )

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
            players[userid].acceptResponse(reqtext)

    elif(reqtext=="/join"):
        retString=""
        if(not players[userid].online):
            sendMessage(userid,"You are currently marked as offline. Type /online to get game invitations.")
        elif(players[userid].currentGameInvite==0):
            newGame(self.tier,userid)
        else:
            players[userid].currentGame=players[userid].currentGameInvite #join the game
            players[userid].currentGameInvite=0 #clear invite
            retString="Joined game. Users at the table:"
            for i in games[players[userid].currentGame].pPlaying:
                retString+=("\n@"+players[i].username) #print usernames of everyone in the game lobby
                sendMessage(i,"%s has joined the table." %username) #also tell everyone in the lobby that you joined
            sendMessage(userid,retString)
            if(len(games[players[userid].currentGame].pPlaying)>=MAX_PLAYERS_PER_GAME): #start the game if the lobby is full
                games[players[userid].currentGame].beginGame()

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
    
def newGame(tiernum,creatorid):
    print("Starting new game for tier %d..." %tiernum)
    success=False
    gmid=0
    for i in range(1,MAX_SIMULTANEOUS_GAMES+1):
        if(not i in games):
            gmid=i
            success=True
            break
    if(not success):
        sendMessage(creatorid,"Too many games in progress. Wait a while and try again.")
    else:
        games[gmid]=game(gmid,tiernum,creatorid)
        players[creatorid].currentGame=gmid
        sendMessage(creatorid,"New game created. Game will start in 10 minutes at most.")
        #START A TIMER

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
        
    botUpdate(numClear) #get rid of the last update queue


main()

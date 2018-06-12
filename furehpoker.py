import requests
import json
from random import shuffle

#TODO:
#Filter chat input so it follows UTF-8 (ASCII?)
#Make some of the information text more helpful please
#Introduce timers so that default options activate after a time limit
#Tell people how long they will wait (at most)
#Replace the invite system

BOT_TOKEN="598223102:AAGRkSBjoZV2KMKLtGAFB7xlMJnN1xShpTA"
ACCESS_WEBSITE="https://api.telegram.org/bot"+BOT_TOKEN+"/"
rankdict={1:"Ace",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"Jack",12:"Queen",13:"King"}
suitdict={1:"Spades",2:"Hearts",3:"Diamonds",4:"Clubs"}

TIER_CUTOFFS=[5, 1000, 2000, 3000, 4000] #The minimum required chips to be a member of each tier
TIER_BUYINS= [5,   10,   20,   30,   40] #The buyin cost for a game on that tier
ADMIN_IDS=[156638024,131331518] #Facade and Alexi
LEADERBOARD_NUM=10 #How many names to display in the leaderboard
MAX_SIMULTANEOUS_GAMES=40
STARTING_CHIPS=1000
MAX_PLAYERS_PER_GAME=3 #will change later; can't be more than 10 if only 1 deck is used
MAX_DRAWS=2
DRAW_COSTS=[10,20] #The price of drawing based on which turn, needs to be MAX_DRAWS long
CARDS_PER_HAND=5
CARD_DECKS=1 #Decks worth of cards used in each game
RESPONSE_TIME_LIMIT=120.0 #In seconds, float
GAME_START_LIMIT=300.0 #In seconds, float

cont=True
players={} #plid: player instance
games={} #gmid: game instance



class card:
    def __init__(self,rankid,suitid):
        self.rankid=rankid
        self.suitid=suitid
    def getName(self):
        return rankdict[self.rankid]+" of "+suitdict[self.suitid]

class player:
    def __init__(self,plid,username,chips):
        #SAVE STUFF
        self.id=plid
        self.username=username
        self.chips=chips
        self.online=True

        self.gameInit()
        
    def updateTier(self):
        for i in range(len(TIER_CUTOFFS)):
            if(TIER_CUTOFFS[i]>self.chips):
                self.currentTier=i
                return

    def getHand(self):
        retString=""
        for i in range(len(self.hand)):
            retString+="\n%d: %s" %(i+1,self.hand[i].getName())
        return retString

    def gameInit(self):
        #GAME STUFF
        self.updateTier()
        self.currentGame=0 #Player's current game id
        self.currentGameInvite=0 #Player's invite game id
        self.holding=False
        self.hand=[]
        self.timerRef=0
        self.awaitingInput="none" #Can be none, handturn, drawcards, betturn, raiseamt
            
    def acceptResponse(self,reqtext): #All user text is sent here when they are mid-game
        curGame=games[self.currentGame]
        reqtext=reqtext.upper() #Make it case insensitive
        
        if(self.awaitingInput=="handturn"):
            #Destroy the timer
            if(reqtext=="HOLD"):
                self.holding=True
                self.awaitingInput="none"
                sendMessage(self.id,"Waiting for the other players...")
                curGame.handTurn(self.id)
            elif(reqtext=="DRAW"):
                sendMessage(self.id,"Here's the format") #fix this please
                self.awaitingInput="drawcards"
            else:
                sendMessage(self.id,"Your options are:\nHOLD (free)\nDRAW (%d chips)" %DRAW_COSTS[curGame.currentHandRound])
        elif(self.awaitingInput=="drawcards"):
            reqtext=reqtext.replace(","," ")
            splitreq=[i for i in reqtext.split(" ")]
            numList=[]
            success=True
            for i in splitreq:
                try:
                    if(0<int(i)<=CARDS_PER_HAND):
                        numList.append(int(i)-1) #arrays start at 0
                    else:
                        success=False
                except ValueError: #ignore whatever isn't a number
                    continue
            if(not success):
                sendMessage(self.id,"Wrong format fucko") #this too
            else:
                self.awaitingInput="none"
                #Charge the player appropriately.
                self.chips-=DRAW_COSTS[curGame.currentHandRound]
                sendMessage(self.id,"%d chips removed.\nWaiting for the other players..."%DRAW_COSTS[curGame.currentHandRound])
                #Then swap the specified cards out
                for j in numList:
                    print("[DEBUG] Replacing %s with " %self.hand[j].getName(),end="")
                    curGame.deck.insert(0,self.hand[j])
                    self.hand.pop(j)
                    self.hand.insert(j,curGame.deck[-1])
                    print("%s" %curGame.deck[-1].getName())
                    curGame.deck.pop()
                curGame.handTurn(self.id)
        elif(self.awaitingInput=="betturn"):
            if(curGame.pPlayers[curGame.currentPlayerTurn]==self.id): #if it's your turn, check for event listeners
                print("UNIMPLEMENTED")

class game:
    def __init__(self,gmid,tiernum,creatorid):
        self.id=gmid
        self.tier=tiernum #the tier of players this game is open to
        self.entryCost=TIER_BUYINS[tiernum-1] #the amount it will cost to enter the game; arrays start at 0
        self.phase="wait" #can be wait, hand, or bet
        self.pPlaying=[creatorid] #list of all playing plid's
        self.currentPlayerTurn=0 #array index of which player's turn it is
        self.currentHandRound=0 #turn number of which round it is
        self.playersConfirmed={} #users who have finished their turn
        self.deck=[] #list of all cards remaining in the deck
        self.currentBet=0
        self.pot=0 #number of chips in the pot
        self.beginGame()
    def addPlayer(self,userid):
        players[userid].currentGame=self.id #set their current game
        players[userid].currentGameInvite=0 #clear invite
        self.pPlaying.append(userid) #add them to the list
        if(len(self.pPlaying)>=MAX_PLAYERS_PER_GAME): #start the game if the lobby is full
            self.startHand()
    def removePlayer(self,userid):
        if(userid in self.pPlaying):
            self.pPlaying.remove(userid)
        players[userid].currentGame=0
        players[userid].gameInit()
        if(len(self.pPlaying)==0):
            self.endGame()
    def beginGame(self):
        #Send invitations to everyone, and set a listener for their response
        for i in players.values():
            if(i.currentGame==0 and i.currentTier==self.tier): #if they're online, not in a game, and in the right tier
                i.currentGameInvite=self.id
    def startHand(self):
        self.phase="hand"
        #Revoke all remaining invites
        for i in players.values():
            if(i.currentGameInvite==self.id):
                i.currentGameInvite=0
        #Make deck(s), shuffle deck
        for k in range(CARD_DECKS):
            for i in rankdict.keys():
                for j in suitdict.keys():
                    self.deck.append(card(i,j))
        shuffle(self.deck)
        #Give everyone 5 cards, put entry cost into the piot, send everyone a message, listen for responses, and start a timer
        for i in self.pPlaying:
            #Give everyone 5 cards
            for j in range(CARDS_PER_HAND):
                players[i].hand.append(self.deck[-1])
                self.deck.pop()
            #Put entry cost into the pot
            players[i].chips-=self.entryCost
            self.pot+=self.entryCost
            players[i].awaitingInput="handturn" #An event listener answered by player.acceptResponse
            sendMessage(i,"Game start! %d of your chips have been placed into the pot."%self.entryCost+
                        "\nCards: "+players[i].getHand()+
                        ("\n\nOptions:\nHOLD - keep your hand, free\nDRAW - swap out any cards, %d chips"%DRAW_COSTS[self.currentHandRound])+
                        makeKeyboard(["HOLD","DRAW"]) )
    def handTurn(self,userid):
        self.playersConfirmed[userid]=True
        if(len(self.playersConfirmed)>=len(self.pPlaying)): #if everyone is confirmed trigger the next turn
            self.playersConfirmed={}
            self.currentHandRound+=1
            numHolding=0
            for i in self.pPlaying:
                players[i].awaitingInput="none" #for safety
                if(players[i].holding):
                    numHolding+=1
                    self.playersConfirmed[i]=True #auto-hold if they held last turn
            if(self.currentHandRound==MAX_DRAWS): #if people used up 2 draws or everyone is holding
                self.currentHandRound=0 #for safety
                self.endGame() #self.startBet()
            elif(numHolding==len(self.pPlaying)):
                self.currentHandRound=0 #for safety
                self.endGame() #self.startBet()
            else:
                for i in self.pPlaying:
                    if(not players[i].holding):
                        players[i].awaitingInput="handturn" #An event listener answered by player.acceptResponse
                        sendMessage(i,"Cards: "+players[i].getHand()+makeKeyboard(["HOLD","DRAW"]) )
    def startBet(self):
        self.currentTurn=0
        sendMessage(self.pPlaying[self.currentTurn],"The current bet is %d."%self.currentBet+"Cards: "+players[self.pPlaying[self.currentTurn]].getHand()+makeKeyboard(["FOLD","CALL","RAISE"]))
    def betTurn(self):
        #Let everyone bet one at a time
        #Setup the next turn, message the next person their query
        self.currentTurn=(self.currentTurn+1)%len(self.pPlaying)
        sendMessage(self.pPlaying[self.currentTurn],"The current bet is %d."%self.currentBet+"Cards: "+players[self.pPlaying[self.currentTurn]].getHand()+makeKeyboard(["FOLD","CALL","RAISE"]))
    def endGame(self):
        #Reset all the player's game vars
        for i in self.pPlaying:
            sendMessage(i,"End of the game. Type /join to join another one.")
            players[i].gameInit()
        #Delete from games list (and hopefully free instance?? python is weird so idk)
        del games[self.id]




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
    retString+="\""+btnList[0]+"\""
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
            sendMessage(userid,"Server shutdown.")
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
            sendMessage(userid,"Welcome to Fur-Eh poker. Type /rules to learn to play, or /join to join a game. Type /help for more commands. Your balance is %d chips." %players[userid].chips )

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

    elif(reqtext=="/getleaderboard"):
        leaderList=getLeaderboard()
        retText="%d players online.\nTop chips:" %findNumOnline()
        for i in leaderList:
            retText+="\n%s: %s" %(i[0],i[1])
        sendMessage(userid,retText)

    elif(not userid in players.keys() ): #if the player hasn't yet said /start
        sendMessage(userid,"Start the bot with /start.")
        return #don't let them do any other commands

    elif(players[userid].currentGame!=0): #if the player is in the middle of a game
        if(reqtext=="/leave"):
            games[players[userid].currentGame].removePlayer(userid)
            sendMessage(userid,"Removed from the game.")
        elif(reqtext[0]=="/"):
            sendMessage(userid,"You can't use bot commands in the middle of a game.")
        else:
            players[userid].acceptResponse(reqtext)

    elif(reqtext=="/join"):
        if(not players[userid].online):
            sendMessage(userid,"You are currently marked as offline. Type /online to get game invitations.")
        elif(players[userid].currentTier==0):
            sendMessage(userid,"Sorry, you don't have enough chips to continue playing. Have a fun Fur-Eh!")
        elif(players[userid].currentGameInvite==0):
            newGame(players[userid].currentTier,userid)
        else:
            retString="Joined game. Users at the table:"
            for i in games[players[userid].currentGameInvite].pPlaying:
                retString+=("\n@"+players[i].username) #print usernames of everyone in the game lobby
                sendMessage(i,"@%s has joined the table." %username) #also tell everyone in the lobby that you joined
            sendMessage(userid,retString)
            games[players[userid].currentGameInvite].addPlayer(userid) #join the game

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
        sendMessage(creatorid,"New game created. Game will start in 10 minutes at most. Waiting for players...")
        #START A TIMER

def main():
    #Load ffrom file
    for i in players.values():
        if(i.online):
            sendMessage(i.id,"Server restarted. Any previously ongoing games were terminated. Sorry for any inconvenience.")
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

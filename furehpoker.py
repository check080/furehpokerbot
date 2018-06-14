from globals import *
from game import game
from player import player

#TODO:
#Add rules and a list of poker hands
#Introduce timers so that default options activate after a time limit

#Global variables
cont=True
gamesFrozen=False

def findNumPlaying(): #Returns the number of people ingame
    totalPlaying=0
    for i in players.values():
        if(i.currentGame!=0):
            totalPlaying+=1
    return totalPlaying

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

def getGameList(): #Returns a list of the games currently running/waiting for players
    tieredGames={}
    for i in range(1,len(TIER_CUTOFFS)+1):
        tieredGames[i]=[]
    for j in games.values():
        retString="%d: " %j.id
        if(j.phase=="wait"):
            retString+="Waiting for players, "
        else:
            retString+="In progress, "
        retString+="%d players." %len(j.pPlaying)
        tieredGames[j.tier].append(retString)
    return tieredGames

def newGame(tiernum,creatorid):
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
        sendMessage(creatorid,"New game created for tier %d. Game will start in %2.0f minutes, or when %d players join. Waiting for players...\nSwitched to ingame chat." %(tiernum,GAME_START_TIME_LIMIT/60,MAX_PLAYERS_PER_GAME))
        #START A TIMER

		
		
def processCommand(usrReq):
    global cont
    global players
    global games
    global gamesFrozen

    userid=usrReq["from"]["id"]
    username=usrReq["from"]["username"]
    reqtext=usrReq["text"]

    #FILTER THE TEXT
    filter(lambda x: x in LEGAL_CHARS, reqtext)
    reqtext=(reqtext.encode('ascii', 'ignore')).decode("utf-8")
    for i in reqtext:
        if(ord(i)<32 or ord(i)>126):
            reqtext=reqtext.replace(i,"")
    if(len(reqtext)<1):
        return
    cmdList=reqtext.split(" ")
    
    print("FROM %d (%s): %s" %(userid,username,reqtext) ) #print it

    if(userid in ADMIN_IDS):
        #ADMIN COMMANDS
        if(cmdList[0]=="/quit"):
            print("[LOG] Admin called quit.")
            sendMessage(userid,"Server shutdown.")
            cont=False

        elif(cmdList[0]=="/help"):
            retString="ADMIN COMMANDS:\n" \
                      "/quit - Stop the server\n" \
                      "/startgame [tier] - Start a new game on the specified tier\n" \
                      "/gamestats - See all game stats\n" \
                      "/freeze - stop game events, stop sending invites\n" \
                      "/resume - continue game events and invites\n" \
                      "/setbalance [userid] [amount] - set a player's chip number\n" \
                      "/notify [text] - make an announcement to everyone on the user list"
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

        elif(cmdList[0]=="/freeze"):
            gamesFrozen=True
            sendMessage(userid,"Games frozen. Noone will be able to create a new game as long as this is on. Use /resume to unfreeze.")

        elif(cmdList[0]=="/resume"):
            gamesFrozen=False
            sendMessage(userid,"Games resumed. Players can start new games again.")

        elif(cmdList[0]=="/setbalance"): #UNTESTED
            try:
                targetID=int(cmdList[1])
                balanceAMT=int(cmdList[2])
                players[targetID].chips=balanceAMT
                players[targerID].updateTier()
                sendMessage(userid,"Chips of %d set to %d." %(targetID,players[targetID].chips) )
            except IndexError:
                sendMessage(userid,"Not enough arguments, expected 2: /setbalance [playerid] [amount]")
            except ValueError:
                sendMessage(userid,"Arguments are in the wrong type, expected integers: /setbalance [playerid] [amount]")
            except KeyError:
                sendMessage(userid,"User not found.")
                
        elif(cmdList[0]=="/notify"):
            try:
                retString="NOTICE: "
                retString+=" ".join(cmdList[1:])
                for i in players.keys():
                    sendMessage(i,retString)
            except IndexError:
                sendMessage(userid,"No text found in first argument.")

    #USER COMMANDS
    if(cmdList[0]=="/start"):
        if(userid in players.keys() ): #if the player is already registered
            sendMessage(userid,"Welcome back to Fur-Eh poker. Your balance is %d chips." %players[userid].chips )
        else: #if they aren't
            players[userid]=player(userid,username,STARTING_CHIPS) #add a dict entry with a new instance of the player class
            saveData()
            sendMessage(userid,"Welcome to Fur-Eh poker. Type /rules to learn to play, or /join to join a game." +
                               "Type /help for more commands. Your balance is %d chips." %players[userid].chips +
                               "\nOnce you run out of chips you will not be able to play for THE REST of fur-eh." +
                               "\nIf you have questions, message @check080"+
                               "\nJoined global chat.")

    elif(cmdList[0]=="/help"):
        retString="Bot Commands:\n" \
                  "/start - Start the bot\n" \
                  "/help - Get a list of commands\n" \
                  "/getleaderboard - Show the top players and their chips\n" \
                  "/join - Join the game you've been invited to\n" \
                  "/leave - Leave a game you're in\n" \
                  "/rules - See the rules of this version of 5-card poker\n" \
                  "/hands - See a list of poker hands\n" \
                  "/balance - See how many chips you have"
        sendMessage(userid,retString)

    elif(cmdList[0]=="/getleaderboard"):
        leaderList=getLeaderboard()
        retText="%d players waiting or ingame.\nTop chips:" %findNumPlaying()
        for i in leaderList:
            retText+="\n%s: %s" %(i[0],i[1])
        sendMessage(userid,retText)

    elif(cmdList[0]=="/rules"):
        sendMessage(userid,"POKER RULES GO HERE")

    elif(cmdList[0]=="/hands"):
        sendMessage(userid,"LIST OF POKER HANDS GOES HERE")

    elif(cmdList[0]=="/balance"):
        sendMessage(userid,"You currently have %d chips.\nYou are tier %d." %(players[userid].chips,players[userid].currentTier))

    elif(not userid in players.keys() ): #if the player hasn't yet said /start
        sendMessage(userid,"Start the bot with /start.")
        return #don't let them do any other commands

    elif(players[userid].currentGame!=0): #if the player is in the middle of a game
        if(cmdList[0]=="/leave"):
            games[players[userid].currentGame].removePlayer(userid)
            sendMessage(userid,"Removed from the game.\nRejoined global chat."+removeKeyboard())
        elif(reqtext[0]=="/join"):
            sendMessage(userid,"You can't use that command in the middle of a game. Use /leave to leave your current game.")
        else:
            players[userid].acceptResponse(reqtext)

    elif(cmdList[0]=="/join"):
        if(players[userid].currentTier==0):
            sendMessage(userid,"Sorry, you don't have enough chips to continue playing. Have a fun Fur-Eh!")
        else:
            success=False
            for g in games.values(): #see if there's one to join
                if(g.phase=="wait" and g.tier==players[userid].currentTier):
                    success=True
                    retString="Joined game. Users at the table:"
                    for i in g.pPlaying:
                        retString+=("\n@"+players[i].username) #get usernames of everyone in the game lobby
                        sendMessage(i,"@%s has joined the table." %username) #also tell everyone in the lobby that you joined
                    retString+="\nSwitched to ingame chat."
                    sendMessage(userid,retString)
                    g.addPlayer(userid) #join the game
            if(not success): #make a new game if there are none open
                if(gamesFrozen):
                    sendMessage(userid,"An admin has stopped the creation of new games. Your chip count is now final. Have a fun Fur-Eh!")
                else:
                    newGame(players[userid].currentTier,userid)
                    
    elif(reqtext[0]!="/"): #Send as global chat
        for plr in players.values():
            if(plr.currentGame==0 and plr.id!=userid):
                sendMessage(plr.id,"[TIER %d]@%s: %s" %(players[userid].currentTier,players[userid].username,reqtext))
    

def main():
    #Load from file
    if(loadData()):
        for plid,plarr in playerSaveArray.items():
            players[plid]=player(plid,plarr[0],plarr[1])
        for i in players.values():
            sendMessage(i.id,"Server restarted. Any previously ongoing games were terminated. Sorry for any inconvenience.")
    print("[LOG] Initialized.")

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

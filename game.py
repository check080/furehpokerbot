from random import shuffle
from globals import *

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
        self.pPlaying.append(userid) #add them to the list
        if(len(self.pPlaying)>=MAX_PLAYERS_PER_GAME): #start the game if the lobby is full
            self.startHand()
    def removePlayer(self,userid):
        if(userid in self.pPlaying):
            self.pPlaying.remove(userid)
        players[userid].currentGame=0
        players[userid].gameInit()
        if(len(self.pPlaying)==0):
            self.destroyGame()
    def beginGame(self):
        print("New game started")
    def startHand(self):
        self.phase="hand"
        #Make deck(s), shuffle deck
        for k in range(CARD_DECKS):
            for i in RANK_DICT.keys():
                for j in SUIT_DICT.keys():
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
        #Check which player(s) won, give them the pot
        winArray=getBestHand({i:players[i].hand for i in self.pPlaying}) #CHANGE THIS TO THE LIST OF PEOPLE THAT DIDN'T FOLD
        for plid in winArray[0]:
            players[plid].chips+=(self.pot/len(winArray[0]))
        self.destroyGame()
        for i in self.pPlaying:
            sendMessage(i,winArray[1]+"\nEach winner received %d chips.\n"%(self.pot/len(winArray[0]))+"End of the game. Type /join to join another one.")
    def destroyGame(self):
        #Reset all the player's game vars
        for i in self.pPlaying:
            players[i].gameInit()
        #Delete from games list (and hopefully free instance?? python is weird so idk)
        del games[self.id]

        
#input: {int plid: list hand}
#output: [[plid,...],wintext]
def getBestHand(handDict):
    highestRank=0
    scoreDict={} #{plid: [score,highcard]}
    
    for plid,hand in handDict.items():
        highestCard=2
        rankNumbers={i.rankid:0 for i in hand}
        suitNumbers={i.suitid:0 for i in hand}
        for i in hand:
            #find the highest card
            if(i.rankid>highestCard):
                highestCard=i.rankid
            #find how many of its rank
            rankNumbers[i.rankid]+=1
            #find out how many of its suit
            suitNumbers[i.suitid]+=1
        hasStraight=False
        hasRoyalStraight=False
        for i in hand:
            #find out of it's the lowest in a straight
            lowestOfStraight=True
            for j in range(1,5):
                if(not i.rankid+j in rankNumbers.keys()):
                    lowestOfStraight=False
            #if it is, the hand has a straight
            if(lowestOfStraight):
                hasStraight=True
                if(i.rankid==10):
                    hasRoyalStraight=True
                    
        #check all scores from greatest to least
        curScore=0
        #royal flush
        if(hasRoyalStraight and 5 in suitNumbers.values()):
            curScore=9
        #straight flush
        elif(hasStraight and 5 in suitNumbers.values()):
            curScore=8
        #4 of a kind
        elif(4 in rankNumbers.values()):
            curScore=7
        #full house
        elif(3 in rankNumbers.values() and 2 in rankNumbers.values()):
            curScore=6
        #flush
        elif(5 in suitNumbers.values()):
            curScore=5
        #straight
        elif(hasStraight):
            curScore=4
        #3 of a kind
        elif(3 in rankNumbers.values()):
            curScore=3
        #2 pairs
        elif(list(rankNumbers.values()).count(2)==2):
            curScore=2
        #1 pair
        elif(2 in rankNumbers.values()):
            curScore=1
        else:
            curScore=0
        scoreDict[plid]=[curScore,highestCard]
        
    #find the highest score
    highestScore=0
    winningPlayer=[]
    for plid,plscore in scoreDict.items():
        if(plscore[0]>highestScore):
            highestScore=plscore[0]
            winningPlayer=[plid]
        elif(plscore[0]==highestScore):
            winningPlayer.append(plid)
    retString=""
    #check for tie, if so, give to high card
    if(len(winningPlayer)>1):
        highestCard=2
        highestCardPlayer=[]
        for plid in winningPlayer:
            if(scoreDict[plid][1]>highestCard):
                highestCard=scoreDict[plid][1]
                highestCardPlayer=[plid]
            elif(scoreDict[plid][1]==highestCard):
                highestCardPlayer.append(plid)
        #Winner is the one with highest card
        winningPlayer=highestCardPlayer
        #If there are multiple
        if(len(winningPlayer)>1):
            retString+="Tie between %d" %winningPlayer[0]
            for plid in winningPlayer[1:]:
                retString+=" and %d" %plid
            retString+=" for %s with highest card %s" %(SCORE_DICT[highestScore],RANK_DICT[highestCard])
        else:
            retString+="%d wins for %s with highest card %s" %(winningPlayer[0],SCORE_DICT[highestScore],RANK_DICT[highestCard])
    else:
        retString+="%d wins for %s" %(winningPlayer[0],SCORE_DICT[highestScore])
    return [winningPlayer,retString]
from globals import *

class player:
    def __init__(self,plid,username,chips):
        #SAVE STUFF
        self.id=plid
        self.username=username
        self.chips=chips

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
                sendMessage(self.id,"Waiting for the other players... %2.0f minutes maximum" %(RESPONSE_TIME_LIMIT/60))
                for i in curGame.pPlaying:
                    if(i!=self.id):
                        sendMessage(i,"@%s is holding." %self.username)
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
                sendMessage(self.id,"%d chips removed.\nWaiting for the other players... %2.0f minutes maximum"%(DRAW_COSTS[curGame.currentHandRound],RESPONSE_TIME_LIMIT/60) )
                #Then swap the specified cards out
                for j in numList:
                    print("[DEBUG] Replacing %s with " %self.hand[j].getName(),end="")
                    curGame.deck.insert(0,self.hand[j])
                    self.hand.pop(j)
                    self.hand.insert(j,curGame.deck[-1])
                    print("%s" %curGame.deck[-1].getName())
                    curGame.deck.pop()
                #Tell everyone
                for i in curGame.pPlaying:
                    if(i!=self.id):
                        sendMessage(i,"@%s drew %d cards." %(self.username,len(numList)) )
                curGame.handTurn(self.id)
        elif(self.awaitingInput=="betturn" and curGame.pPlayers[curGame.currentPlayerTurn]==self.id):#if it's your turn, check for event listeners
            print("UNIMPLEMENTED")
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

    def updateData(self):
        playerSaveArray[self.id]=[self.username,self.chips]
        
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
        self.folded=False
        self.hand=[]
        self.swapcards=[]
        self.contributedBet=0
        self.awaitingInput="none" #Can be none, handturn, dealcards, betturn, raiseamt
        #NOW THAT YOU'RE OUT OF A GAME, SAVE
        self.updateData()
            
    def acceptResponse(self,reqtext): #All user text is sent here when they are mid-game
        curGame=games[self.currentGame]
        
        if(self.awaitingInput=="handturn"):
            #Destroy the timer
            if(reqtext=="HOLD"):
                self.holding=True
                self.awaitingInput="none"
                sendMessage(self.id,"Waiting for the other players... %2.0f minutes maximum" %(RESPONSE_TIME_LIMIT/60) +removeKeyboard())
                for i in curGame.pPlaying:
                    if(i!=self.id):
                        sendMessage(i,"@%s is holding." %self.username)
                curGame.handTurn(self.id)
            elif(reqtext=="DEAL"):
                if(self.chips<DEAL_COSTS[curGame.currentHandRound]):
                    sendMessage(self.id,"You don't have enough chips. Dealing costs %s." %DEAL_COSTS[curGame.currentHandRound])
                else:
                    sendMessage(self.id,"Type the number or the name of a card to swap it out. You can swap out as many cards as you'd like. Type DONE when you're done swapping cards out." +makeKeyboard([i.getName() for i in self.hand]+["DONE"]))
                    self.swapcards=[]
                    self.awaitingInput="dealcards"
                
            else:
                curGame.sendChat(self.id,reqtext)
        elif(self.awaitingInput=="dealcards"):
            success=False
            for i in range(len(self.hand)): #Try to interpret as string
                if(self.hand[i].getName()==reqtext and (not i in self.swapcards)):
                    success=True
                    self.swapcards.append(i)
                    cardsLeft=[self.hand[i].getName() for i in range(len(self.hand)) if (not i in self.swapcards)]
                    sendMessage(self.id,"Discarded the %s."%reqtext +makeKeyboard([i for i in cardsLeft]+["DONE"]))
                    break
            if(not success): #Try to interpret as number
                success=True
                try:
                    if(0<int(reqtext)<=CARDS_PER_HAND and (not i in self.swapcards)):
                        self.swapcards.append(int(i)-1)
                        cardsLeft=[self.hand[i].getName() for i in range(len(self.hand)) if (not i in self.swapcards)]
                        sendMessage(self.id,"Discarded the %s."%self.swapcards[-1] +makeKeyboard([i for i in cardsLeft]+["DONE"]))
                    else:
                        success=False
                except ValueError:
                    success=False
            if(reqtext=="DONE"):
                self.awaitingInput="none"
                if(len(self.swapcards)==0): #If they didn't actually swap out cards
                    self.holding=True
                    sendMessage(self.id,"Waiting for the other players... %2.0f minutes maximum" %(RESPONSE_TIME_LIMIT/60) +removeKeyboard())
                    for i in curGame.pPlaying:
                        if(i!=self.id):
                            sendMessage(i,"@%s is holding." %self.username)
                    curGame.handTurn(self.id)
                else:
                    #Charge the player appropriately.
                    self.chips-=DEAL_COSTS[curGame.currentHandRound]
                    curGame.pot+=DEAL_COSTS[curGame.currentHandRound]
                    sendMessage(self.id,"%d of your chips have been placed into the pot.\nWaiting for the other players... %2.0f minutes maximum"%(DEAL_COSTS[curGame.currentHandRound],RESPONSE_TIME_LIMIT/60) +removeKeyboard())
                    #Then swap the specified cards out
                    for j in self.swapcards:
                        curGame.deck.insert(0,self.hand[j])
                        self.hand.pop(j)
                        self.hand.insert(j,curGame.deck[-1])
                        curGame.deck.pop()
                    #Tell everyone
                    for i in curGame.pPlaying:
                        if(i!=self.id):
                            sendMessage(i,"@%s drew %d cards." %(self.username,len(self.swapcards)) )
                    self.swapcards=[]
                    curGame.handTurn(self.id)
            elif(not success):
                sendMessage(self.id,"Couldn't find an unswapped number or card name.\nType the number of each card you'd like to swap out, separated by spaces.\ne.g.: To swap out cards 1 and 3, type: 1 3")
        elif(self.awaitingInput=="betturn"):#if it's your turn, check for event listeners
            if(reqtext=="CALL"):
                if((curGame.currentBet-self.contributedBet)>self.chips):
                    sendMessage(self.id,"Not enough chips to call the bet, you only have %s chips." %self.chips)
                else:
                    moneyreq=curGame.currentBet-self.contributedBet
                    self.chips-=moneyreq
                    curGame.pot+=moneyreq
                    self.contributedBet+=moneyreq
                    self.awaitingInput="none"
                    sendMessage(self.id,"Placed %d chips into the pot. The pot is now at %d chips." %(moneyreq,curGame.pot) + removeKeyboard())
                    for i in curGame.pPlaying:
                        if(i!=self.id):
                            sendMessage(i,"@%s called the bet."%self.username)
                    curGame.consecutiveCalls+=1
                    curGame.betTurn()
            elif(reqtext=="RAISE"):
                if((curGame.currentBet-self.contributedBet)>=self.chips):
                    sendMessage(self.id,"Not enough chips to raise the bet, you only have %s chips." %self.chips)
                else:
                    sendMessage(self.id,"How many chips would you like to add to the bet? The current bet is %d." %curGame.currentBet + removeKeyboard())
                    self.awaitingInput="raiseamt"
                    #Maybe make a nice keyboard here?
            elif(reqtext=="FOLD"):
                self.folded=True
                sendMessage(self.id,"You have folded the game. Wait for the other players to finish betting, or use /leave to leave the game." +removeKeyboard())
                for i in curGame.pPlaying:
                    if(i!=self.id):
                         sendMessage(i,"@%s folded."%self.username)
                curGame.consecutiveCalls+=1
                if(len([i for i in curGame.pPlaying if not players[i].folded])<=1):
                    curGame.endGame()
                else:
                    curGame.betTurn()
            else:
                curGame.sendChat(self.id,reqtext)
        elif(self.awaitingInput=="raiseamt"):
            try:
                raiseAmount=int(reqtext)
                if(curGame.currentBet+raiseAmount-self.contributedBet>self.chips):
                    sendMessage(self.id,"You don't have enough chips to raise the bet by %d. You only have %d chips. Choose another amount to raise the bet by." %(raiseAmount,self.chips))
                else:
                    curGame.currentBet+=raiseAmount
                    moneyreq=curGame.currentBet-self.contributedBet
                    self.chips-=moneyreq
                    curGame.pot+=moneyreq
                    self.contributedBet+=moneyreq
                    self.awaitingInput="none"
                    sendMessage(self.id,"Bet raised to %d. Placed %d chips into the pot. The pot is now at %d chips." %(curGame.currentBet,moneyreq,curGame.pot))
                    for i in curGame.pPlaying:
                        if(i!=self.id):
                            sendMessage(i,"@%s raised the bet by %d."%(self.username,raiseAmount))
                    curGame.consecutiveCalls=0
                    curGame.betTurn()
            except ValueError:
                sendMessage(self.id,"Please send the number of chips you'd like to raise the bet by.")
            
        else:
            curGame.sendChat(self.id,reqtext)
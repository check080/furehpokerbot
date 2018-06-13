from globals import *

#input: {int plid: list hand}
#output: [[plid,...],wintext]
def getBestHand(handDict):
    highestRank=0
    scoreDict={} #{plid: [score,highcard]}
    
    for plid,hand in handDict.items():
        highestCard=2
        highestPair=2
        highestTriple=2
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
        for i,j in rankNumbers.items():
            if(j==2): #find the highest pair
                if(i>highestPair):
                    highestPair=i
            elif(j>=2): #find the highest triple
                if(i>highestTriple):
                    highestTriple=i
                    
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
        scoreDict[plid]=[curScore,highestCard,highestPair,highestTriple]
        
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
        cardCheckIndex=1
        cardCheckLUT={1:"card",2:"pair",3:"triple"}
        if(highestScore==1 or highestScore==2):
            cardCheckIndex=2
        elif(highestScore==3 or highestScore==6 or highestScore==7):
            cardCheckIndex=3
        else: #Winner is the one with highest card if it's not an of-a-kind
            cardCheckIndex=1
        highestSecondary=2
        highestSecondaryPlayer=[]
        for plid in winningPlayer:
            if(scoreDict[plid][cardCheckIndex]>highestSecondary):
                highestSecondary=scoreDict[plid][cardCheckIndex]
                highestSecondaryPlayer=[plid]
            elif(scoreDict[plid][cardCheckIndex]==highestSecondary):
                highestSecondaryPlayer.append(plid)
        winningPlayer=highestSecondaryPlayer
        #If there are multiple
        if(len(winningPlayer)>1):
            retString+="Tie between %d" %winningPlayer[0]
            for plid in winningPlayer[1:]:
                retString+=" and %d" %plid
            retString+=" for %s with highest %s %s" %(SCORE_DICT[highestScore],cardCheckLUT[cardCheckIndex],RANK_DICT[highestSecondary])
        else:
            retString+="%d wins for %s with highest %s %s" %(winningPlayer[0],SCORE_DICT[highestScore],cardCheckLUT[cardCheckIndex],RANK_DICT[highestSecondary])
    else:
        retString+="%d wins for %s" %(winningPlayer[0],SCORE_DICT[highestScore])
    return [winningPlayer,retString]

print(getBestHand({1:[card(2,2),card(2,1),card(3,0),card(4,0),card(6,0)],
                   2:[card(2,3),card(2,0),card(3,1),card(4,1),card(5,1)]}))

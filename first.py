# HOWTO : prepare text using pickletext.py, add worms, doallworms

import random
import math
import nltk
import matplotlib.pyplot as plt
import pickle

def recallpickle(where):
    out = open(where, 'rb')
    text=pickle.load(out) 
    out.close()
    return text

def randy(num):
    return random.randrange(0, num, 1)

def rrr(ranger):
    r= (random.uniform(ranger/-2, ranger/2),random.uniform(ranger/-2, ranger/2)) 
    return r;

def normalize(tup):
    x=tup[0]
    y=tup[1]
    mag=math.sqrt(x*x + y*y)
    if mag!=0:
        x=x/mag
        y=y/mag
    return (x,y)

def limit(tup,limit):
    x=tup[0]
    y=tup[1]
#   (magSq() > max*max) { normalize(); mult(max); 
    if math.sqrt(x*x + y*y) > limit*limit:
        (x,y)=normalize(tup)
        x=x*limit
        y=y*limit
    return (x,y)

def matcher(matchfunc, matchone, matchtwo):
    count=0
    pos= matchone()[0][1]
    otherpos=""
    while otherpos != pos and count<100: # redo with match function
        count+=1
        other=matchtwo()[0]
        otherpos=other[1]
#    print other
    return other

class worm():
    compost_stack = -1
    compost = []
    wormlist=[]

    def __init__(self, loc, speed, maxspeed, textpickle, wormtype):
        self.loc = loc
        self.speed = speed
        self.trail = 8 # set by type of worm
        self.acc=(0,0)
        self.vel=(0,0)
        self.ww = 24 # or this is based on text/pickle but per line so...
        self.maxspeed = maxspeed
        self.tail = []  
        self.counter = 0
        self.dir=(7,-4) # change this
        self.SW=1
        self.target=(0,0)
        # dict of worm types with functions, what else?
        self.wormdict =  { 
            'basicworm': self.wander,
            'bookworm':self.reader,
            'straightworm':self.straight,
            'seeker':self.seek,
            'squiggler':self.squiggler
        }

        self.function=self.wormdict[wormtype]
        # also need holes, targets and so on TODO maybe as dictionary or as part of text itself
        self.composter=0
        self.matchfunc=""
        for w in xrange(self.trail):
            self.tail.append((self.loc[0],self.loc[1]))

        worm.compost_stack += 1
        self.stack=worm.compost_stack
        worm.compost.append([])
        self.textpickle=textpickle
        worm.wormlist.append(self)    

    def checkdist(self):
        dis=(self.target[0]-self.loc[0],self.target[1]-self.loc[1]) 
        if dis[0]>self.ww/2: # need always to recalc this
            self.acc=(self.acc[0] * -1, self.acc[1])
        if dis[0]>self.wh/2:
            self.acc=(self.acc[0], self.acc[1]* -1)

    def do_tail(self):
        self.tail[self.trail-1]=(self.loc[0],self.loc[1])
        for w in xrange(trail-2):
            self.tail[w]=self.tail[w+1]
            
    def checky(self):
        self.wh = len(self.text)-1 # number of lines 
        if int(self.loc[1])>self.wh:
            self.loc=(self.loc[0],0)
        if self.loc[1]<0:
            self.loc=(self.loc[0],self.wh)

    def checkx(self):
        if int(self.loc[0])>self.ww:
            self.loc=(0,self.loc[1])
        if self.loc[0]<0:
            self.loc=(self.ww,self.loc[1])
    
    def doinit(self):
        # select compost stack number
        for worms in self.wormlist:
            if worms.textpickle == "COMPOST":
                worms.composter=randy(worm.compost_stack) # but only selected from added worms so far!!! ???
            else: 
                worms.text = recallpickle(worms.textpickle)
                # select partner worm
            worms.partner=randy(len(self.wormlist))

    def doallworms(self):
        for worms in self.wormlist:
            word=("","")
            if worms.textpickle=="COMPOST":
                worms.text=self.compost[self.composter] 
            if len(worms.text)>1:
                otherlist=[]
                while word[1]!="NL":
                    # match with otherother according to function eg. posmatch, rhyming 
                    word=matcher(worms.matchfunc, worms.function, self.wormlist[worms.partner].function)
                    #other=worms.function()[0]
                    #otherother=self.wormlist[worms.partner].function()[0]
                    otherlist.append(word)
                worm.compost[self.stack].append(otherlist)
                print " ".join([x[0] for x in otherlist]),

    def wander(self):
        self.acc = (self.acc[0] + random.uniform(-2,2), self.acc[1] + random.uniform(-2,2))
        self.acc=normalize(self.acc)
        self.acc = (self.acc[0] * self.speed, self.acc[1] * self.speed)
        self.vel = (self.vel[0] + self.acc[0], self.vel[1] + self.acc[1])
        self.vel=limit(self.vel,self.maxspeed)
        self.loc = (self.loc[0]+self.vel[0], self.loc[1]+self.vel[1])
        self.checky();
        line=self.text[int(self.loc[1])]
        self.ww=len(line)-1
        self.checkx()
        word=line[int(self.loc[0])]
        return (word,self.loc) # returns word, POS and location

    def reader(self): # walk text at speed, without any acceleration
        self.checky()
        self.loc=(self.loc[0]+self.speed, self.loc[1])
        if self.loc[0]>=len(self.text[int(self.loc[1])]):
            self.loc=(0, self.loc[1]+1)
            if self.loc[1]>=self.wh:
                self.loc=(0, 0) # circulate back to start
        line=self.text[int(self.loc[1])]
        word=line[int(self.loc[0])]
        return (word,self.loc) # returns word, POS and location

    def straight(self):
        self.acc = (self.dir[0],self.dir[1])
        rrrr=rrr(80)
        self.acc = (self.acc[0]+rrrr[0], self.acc[1]+rrrr[1])
        self.acc=normalize(self.acc)
        self.acc = (self.acc[0] * self.speed, self.acc[1] * self.speed)
        self.vel = (self.vel[0] + self.acc[0], self.vel[1] + self.acc[1])
        self.vel=limit(self.vel,self.maxspeed)
        self.loc = (self.loc[0]+self.vel[0], self.loc[1]+self.vel[1])
        self.checky();
        line=self.text[int(self.loc[1])]
        self.ww=len(line)-1
        self.checkx()
        word=line[int(self.loc[0])]
        return (word,self.loc) # returns word, POS and location

    def squiggler(self):
        self.counter = self.counter + 1;
        rot = math.sin(self.counter) * self.SW
        z = (self.acc[0] * math.cos(rot) - self.acc[1] * math.sin(rot), self.acc[0] * math.sin(rot) + self.acc[1] * math.cos(rot))
        self.acc = (self.dir[0],self.dir[1])
        self.acc = (self.acc[0] + z[0], self.acc[1] + z[1])
        self.vel = (self.vel[0] + self.acc[0], self.vel[1] + self.acc[1])
        self.vel=limit(self.vel,self.maxspeed)
        self.loc = (self.loc[0]+self.vel[0], self.loc[1]+self.vel[1])
        self.checky();
        line=self.text[int(self.loc[1])]
        self.ww=len(line)-1
        self.checkx()
        word=line[int(self.loc[0])]
        return (word,self.loc) # returns word, POS and location

    def seek(self):
        word=()
        if self.target == (0,0):
            word=self.wander()
            if word[0][0]=="worm" or word=="Worm" or word=="WORM" or word=="worms" or word=="Worms":
                self.target=word[1] 
#                print self.target
            return (word[0],word[1]) # returns word, POS and location
        else: # move towards target
            self.acc=(self.target[0]-self.loc[0], self.target[1]-self.loc[1])
            self.acc=normalize(self.acc)
            rrrr=rrr(2)
            self.acc = (self.acc[0]+rrrr[0], self.acc[1]+rrrr[1])
            self.acc=normalize(self.acc)
            line=self.text[int(self.loc[1])]
            self.ww=len(line)-1
            self.checkdist() ### ????
            self.acc = (self.acc[0] * self.speed, self.acc[1] * self.speed)
            self.vel = (self.vel[0] + self.acc[0], self.vel[1] + self.acc[1])
            self.vel=limit(self.vel,self.maxspeed)
            self.loc = (self.loc[0]+self.vel[0], self.loc[1]+self.vel[1])
            self.checky();
            line=self.text[int(self.loc[1])]
            self.ww=len(line)-1
            self.checkx()
            word=line[int(self.loc[0])]
            return (word,self.loc) # returns word, POS and location
 
# TODO diff movements -> move randomly then towards targetsDONE, move
# away from targets, up and then down=reflect, establish wormholes ->
# how these work - through to different worms, texts///stack of texts, compost buffer

# below example which rewrites straight read text with wormed POS
# how to make more generic - worm interaction?

random.seed()
loc=(randy(20),randy(20))
loc2=(randy(20),randy(20))
speed=1
maxspeed=4

# 'basicworm': self.wander,
# 'bookworm':self.reader,
# 'straightworm':self.straight,
# 'seeker':self.seek,
# 'squiggler':self.squiggler

firstworm=worm(loc,speed,maxspeed, "conqueror_pickle", 'straightworm')
secondworm=worm(loc2,1,maxspeed, "conqueror_pickle", 'squiggler')
thirdworm=worm(loc2,2,maxspeed, "COMPOST", 'squiggler')

firstworm.doinit()
for x in xrange(1000000):
    firstworm.doallworms()

# otherlist=[]
# for x in xrange(1000):
#     pos=secondworm.function()[0][1]
#     otherpos=""
#     count=0
#     while otherpos != pos and count<1000:
#         other = firstworm.function()[0]
#         otherpos=other[1]
#         count +=1
#         #    print other[0], 
#     otherlist.append(other)
#     if other[1]=="NL":
#         firstworm.compost[firstworm.stack].append(otherlist) ## but how do we make lines???    
#         otherlist=[]

# for x in xrange(1000):
#     word=thirdworm.function()[0][0]
#     print word,
# for lists in firstworm.compost[firstworm.stack]:
#     print lists
#     print "\n"

# print firstworm.compost

# [to resolve - spaces before punctuation]



####///////////////////////////////////////////////////////////////////

#glowworm.do_tail()
#for x in xrange(1000):
#    print glowworm.function()[0][0],

# testing plot of movements - seems okayyy...

# xx=[]
# yy=[]
# for x in xrange(100):
#     pp=firstworm.function()
#     xx.append(pp[1][0])
#     yy.append(pp[1][1])
# plt.plot(xx,yy)
# plt.show()
# print test

####///////////////////////////////////////////////////////////////////

# TODO: different types of worms - menagerie each with its emblem, to
# start to apply multiple worms to text and how we can deal with grid
# or flatten out 

# wormholes, wormholes on POS and words, reworking as text compost

# worm through source text (by words or by lines)?
# worm through substitutions tables for the POS?

# diff worms //vs// diff text gambits eg. worm thru same text to next/wormed equiv POS
# src worm//sub worm - and can be same worm/same text/diff texts... eg. same worm diff texts, diff worms, same texts
# how to organise this...

# worm ideas - rising up and descending, sine, worm-holes,
# glowing=what, segmented worms drag words, other worms make holes,

# attraction to words - so make text/pos grid (as what?), annotate
# with wormholes and targets/escapes, multiple worms,
# re-work/compost-also add holes etc. on each round

# emblems as part of text?

# ***compost class/functions with compost buffer all worms can access with wormholes!

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


# worm movement algorithm and how this is applied as needs to be across a grid (a grid of words but is normally long list)

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
    # limit magnitude to limit how????
    if math.sqrt(x*x + y*y) > limit:
        (x,y)=normalize(tup)
        x=x*limit
        y=y*limit
    return (x,y)

#   (magSq() > max*max) { normalize(); mult(max); 

class worm():
    def __init__(self, loc, speed, maxspeed, textpickle, wormtype):
        self.loc = loc
        self.speed = speed
        self.trail = 8 # set by type of worm
        self.acc=(0,0)
        self.vel=(0,0)
        self.ww = 24 # or this is based on text/pickle but per line so...
        self.maxspeed = maxspeed
        self.tail = []  # empty list of tuples 
        self.text = recallpickle(textpickle)
        self.wh = len(self.text)-1 # number of lines
        self.counter = 0
        self.dir=(7,-4)
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
        # also need holes, targets and so on TODO maybe as dictionary

        for w in xrange(self.trail):
            self.tail.append((self.loc[0],self.loc[1]))

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
        if int(self.loc[1])>self.wh:
            self.loc=(self.loc[0],0)
        if self.loc[1]<0:
            self.loc=(self.loc[0],self.wh)

    def checkx(self):
        if int(self.loc[0])>self.ww:
            self.loc=(0,self.loc[1])
        if self.loc[0]<0:
            self.loc=(self.ww,self.loc[1])

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
                print self.target
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
 
# TODO diff movements -> move randomly then towards targets, away from targets, up and then down, establish wormholes

# example which rewrites straight read text with wormed POS

loc=(randy(100),randy(100))
speed=2
maxspeed=4
firstworm=worm(loc,speed,maxspeed, "conqueror_pickle", 'squiggler')
secondworm=worm(loc,1,maxspeed, "conqueror_pickle", 'bookworm')

# for x in xrange(1000):
#     pos=secondworm.function()[0][1]
#     other = firstworm.function()[0]
#     otherpos=""
#     count=0
#     while otherpos != pos and count<1000:
#         other = firstworm.function()[0]
#         otherpos=other[1]
#         count +=1
#     print other[0], 

# to resolve - spaces before punctuation

####///////////////////////////////////////////////////////////////////

#glowworm.do_tail()
#for x in xrange(1000):
#    print glowworm.function()[0][0],

# testing plot of movements - seems okayyy...

xx=[]
yy=[]
for x in xrange(100):
    pp=firstworm.function()
    xx.append(pp[1][0])
    yy.append(pp[1][1])
plt.plot(xx,yy)
plt.show()
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

# TODO:
# first test with text-> clean text, annotate it and make grid of this (ww, wh noted for each//all texts, appended)
# and basic worm possibilities

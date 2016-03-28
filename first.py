import random
import math
import nltk
from textclean.textclean import textclean
import matplotlib.pyplot as plt

def randy(num):
    return random.randrange(0, num, 1)

# - worm movement algorithm and how this is applied as needs to be across a grid (a grid of words but is normally long list

# worm = 

#  PVector loc, vel, acc;//Standard particle variables
#  float speed, MAXspeed;
#  int trail, WW, WH;//Length of trail, world size
#  PVector[] tail;//Locations of tail segments

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
    def __init__(self, loc, speed, trail, ww, wh,maxspeed):
        self.loc = loc
        self.speed = speed
        self.trail = trail
        self.acc=(0,0)
        self.vel=(0,0)
        self.ww = ww
        self.wh = wh
        self.maxspeed= maxspeed
        self.tail = []  # empty list of tuples 

        for w in xrange(trail):
            self.tail.append((self.loc[0],self.loc[1]))

    def do_tail(self):
        self.tail[self.trail-1]=(self.loc[0],self.loc[1])
        for w in xrange(trail-1):
            self.tail[w]=self.tail[w+1]
            
    def check(self):
        if self.loc[0]>self.ww:
            self.loc=(0,self.loc[1])
        if self.loc[1]>self.wh:
            self.loc=(self.loc[0],0)
        if self.loc[0]<0:
            self.loc=(self.ww,self.loc[1])
        if self.loc[1]<0:
            self.loc=(self.loc[0],self.wh)

    def wander(self):
        self.acc = (self.acc[0] + random.uniform(-2,2), self.acc[1] + random.uniform(-2,2))
        self.acc=normalize(self.acc)
        self.acc = (self.acc[0] * self.speed, self.acc[1] * self.speed)
        self.vel = (self.vel[0] + self.acc[0], self.vel[1] + self.acc[1])
        self.vel=limit(self.vel,self.maxspeed)
        self.loc = (self.loc[0]+self.vel[0], self.loc[1]+self.vel[1])
        self.check();
        return (self.loc)

# diff movements



# menageries

loc=(randy(100),randy(100))
speed=1
trail=10
ww=100
wh=100
glowworm=worm(loc,speed,trail,ww,wh,2)
#glowworm.do_tail()

# testing plot of movements - seems okayyy...

xx=[]
yy=[]
for x in xrange(100):
    xx.append(glowworm.wander()[0])
    yy.append(glowworm.wander()[1])
plt.plot(xx,yy)
plt.show()
print test

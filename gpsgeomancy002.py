#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""gpsgeomancy.py
2015/02/05 14:29:53

Take an attached GPS (serial) and get the satellite positions and
data from the NMEA GSV sentences. Find four suitable data sets
(satellites) that correspond to the cardinal directions (North,
South, East, West) and return their data.

Geomantic divination information from Stephen Skinner "Terrestrial
Astronomy - Divination by Geomancy" (the asterisks are the
'reading' - they can be two dots or one):

      Earth    Water    Air     Fire
       IV       III     II       I
head   **        *      **       *
neck   **        *      **       *
body   *         *      *        **
feet   *         **     **       **
      West     North    East    South

Suggested correspondence between these categories and the GPS data
from the NMEA sentences. The satellites corresponding to the
cardinal points / elements are chosen by their closeness to the
azimuths (N=0, E=90, S=180, W=270) and then their signal to noise
(SNR) and then if necessary their elevation (closer to 45 wins?)

     West     North    East    South
prn    **        *      **       *
ele    **        *      **       *
azi    *         *      *        **
snr    *         **     **       **

Two stars could be even numbers, one star odd.

The default location of the GPS is /dev/ttyUSB0 but you can change
this with the -p (--port) option. The default baud rate for the GPS
is 4800 but you can change this with the -b (--baud) option. Garmin
etrex and similar tend to be on ttyUSB0 at 4800 but the dataloggers
can be on ttyACM0 and they are all 115200 baud.

Copyright 2015 Martin Howse m@1010.co.uk Daniel Belasco Rogers danbelasco@yahoo.co.uk

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301 USA.
"""

import sys
import argparse
from pprint import pprint
try:
    import serial
except ImportError:
    print """Please install pySerial:
sudo apt-get install python-serial"""
    sys.exit(2)

# dict for figures
figdict={'0010': ['Puer','Mars','Fire','Aries','+','Boy, yellow, beardless'], '0101': ['Amissio','Venus','Earth','Taurus','-','Loss, comprehended without'], '1101': ['Albus','Mercury','Air','Gemini','-','White, fair'], '1111': ['Populus','Moon','Water','Cancer','-','People, congregation'], '1100': ['Fortuna Major','Sun','Fire','Leo','+','Greater fortune, greater aid,safeguard entering'], '1001': ['Conjunctio','Mercury','Earth','Virgo','+','Conjunction, assembling'], '0100': ['Puella','Venus','Air','Libra','+','A girl, beautiful'], '1011': ['Rubeus','Mars','Water','Scorpio','-','Red, reddish'], '1010': ['Acquisitio','Jupiter','Fire','Sagitarrius','+','Obtaining, comprehending without'], '0110': ['Carcer','Saturn','Earth','Capricorn','+','A prison, bound'], '1110': ['Tristitia','Saturn','Air','Aquarius','-','Sadness, damned, cross'], '0111': ['Laetitia','Jupiter','Water','Pisces','-','Joy, laughing, healthy, bearded'], '0001': ['Cauda Draconis','Saturn & Mars','Fire','Scorpio','-','The threshold lower, or going out'], '1000': ['Caput Draconis',' Jupiter & Venus','Earth','Capricorn','+','The Head, the threshold entering, the upper threshold'], '0011': ['Fortuna Minor','Sun','Fire','Leo','-','Lesser Fortune, lesser aid, safeguard going out'], '0000': ['Via','Moon','Water','Cancer','+','Way, journey']}

roman=['0','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI']

#mapped to Crowley
crowley=['0','X','I','IV','VII','XI','II','V','VIII','XII','III','VI','IX','XIII','XIV','XV','XVI']

def parse_arguments():
    parser = argparse.ArgumentParser(description='Geomancy with GPS satellite positions')
    parser.add_argument('-v', '--verbose',
                        help="Print verbose outputs to screen (intermediate selections etc.)",
                        action='store_true',
                        default=False)
    parser.add_argument('-b', '--baud',
                        help="Set the baud rate for the GPS. Default is 4800",
                        default=4800)
    parser.add_argument('-p', '--port',
                        help="Address of the GPS. Default is /dev/ttyUSB0",
                        default="/dev/ttyUSB0")
    return (parser.parse_args())


def connectgps(port, baud):
    """
    Connects to a GPS at address passed by port at the rate defined
    by baud and handles simple exception

    """
    try:
        gps = serial.Serial(port, baud, timeout=1)
    except serial.SerialException:
        print """
Could not open port %s,
is the GPS plugged in and turned on?
""" % port
        sys.exit(2)
    return gps


def waitforfix(gps, verbose):
    """
    Examine the RMC sentence to see if the gps has a fix. This
    shows up as an 'A' in the second field after the header.

    $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A

    Where:
     RMC          Recommended Minimum sentence C
     123519       Fix taken at 12:35:19 UTC
     A            Status A=active or V=Void.
     4807.038,N   Latitude 48 deg 07.038' N
     01131.000,E  Longitude 11 deg 31.000' E
     022.4        Speed over the ground in knots
     084.4        Track angle in degrees True
     230394       Date - 23rd of March 1994
     003.1,W      Magnetic Variation
     *6A          The checksum data, always begins with *

    """
    alert_interval = 8  # number of seconds to wait between
                        # alerting the user there is no fix
    interval_count = 0
    while 1:
        try:
            line = gps.readline()
            if line.startswith('$GPRMC'):
                interval_count += 1
                line = formatline(line, verbose)

                # formatline performs checksum and returns None if
                # it fails
                if line is None:
                    continue

                if interval_count % alert_interval == 0:
                    print "No GPS fix yet..."

                if line[2] == 'A':
                    print "Fix found"
                    return

        except KeyboardInterrupt:
            # user sent ctrl-c to stop script
            gps.close()
            print """
user interrupt, shutting down"""
            sys.exit()


def checksum(data):
    """
    checksum(data) -> str Calculates the XOR checksum over the
    sentence (as a string, not including the leading '$' or the
    final 3 characters, the ',' and checksum itself).

    """
    checksum = 0
    for character in data:
        checksum = checksum ^ ord(character)
        hex_checksum = "%02x" % checksum
    return hex_checksum.upper()


def formatline(line, verbose):
    """
    Preformats NMEA sentences. Performs checksum to make sure the
    sentence has been recieved as it should. Returns a list of
    values without checksum and without carriage returns
    """
    line.strip()

    # lose carriage returns
    if line.endswith('\r\n'):
        line = line[:len(line) - 2]

    # validate
    star = line.rfind('*')
    if star >= 0:
        check = line[star + 1:]
        line = line[1:star]
        sum = checksum(line)
        if sum != check:
            if verbose:
                print "failed checksum"
            return None
    else:
        if verbose:
            print "no checksum"
        return None

    # lose checksum now we've validated it
    line = line[2:]

    # create a list of all elements in sentence
    line = line.split(',')
    return line


def parseGSV(line, gps, verbose):
    """
    The first part of decoding the GSV sentences. This function
    makes sure that all GSV sentences are fetched in one list of
    lists.

    GSV sentences:
    $GPGSV,3,1,12,01,80,283,20,32,77,227,18,11,72,175,19,20,42,247,25*79
    $GPGSV,3,2,12,14,35,055,15,19,23,174,28,17,19,318,26,28,15,281,15*7C
    $GPGSV,3,3,12,22,11,068,17,23,05,194,,31,04,113,,36,,,*4A

    Output:

    """
    gsvlist = [line]
    num_of_sentences = int(line[1])
    if verbose:
        print "sentences: %d\tsatellites: %s" % (num_of_sentences, line[3])

    # number of GSV sentences vary. Fetch them all before
    # parsing the values
    for sentence in range(num_of_sentences - 1):
        line = gps.readline()
        line = formatline(line, verbose)
        gsvlist.append(line)

    return gsvlist


def formatgsvlist(gsvlist):
    """
    """

    formattedgsv = []

    for sentence in gsvlist:

        # ignore first 4 items (This is the header, number of
        # sentences, sentence number and number of satellites and
        # so not necessary for us at this point)
        sentence = sentence[4:]

        # Replace empty fields with 0 if there is no data
        for item in sentence:
            if item in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": # if item is not an INT?
                item = 0
            if item == '':
                item = 0
#            print(item)
            formattedgsv.append(int(item))

    return formattedgsv


def makesatdict(gsvlist):
    """
    makes a dictionary with prn as a key and values as a list e.g.
    prn:[ele, azi, snr]
    """
    satdict = {}

    for item in range(0, len(gsvlist), 4):
        satdict[gsvlist[item]] = [gsvlist[item + 1],
                                  gsvlist[item + 2],
                                  gsvlist[item + 3]]

    return satdict


def directionclassify(satdict):
    """
    Appends compass direction onto end of list for each satellite.
    Also appends a 'score' of how near the satellite is to the
    cardinal point, which is the number of degrees away from the
    due cardinal points (N=0, E=90, S=180, W=270)

    Sample output
    {2: [7, 132, 16, 'East', 42],
     6: [19, 94, 27, 'East', 4],
     12: [70, 259, 29, 'West', 11],
     14: [28, 312, 31, 'West', 42],
     15: [16, 187, 32, 'South', 7],
     17: [24, 46, 25, 'East', 44],
     22: [4, 280, 0, 'West', 10],
     24: [77, 150, 50, 'South', 30],
     25: [29, 255, 32, 'West', 15],
     32: [4, 347, 0, 'North', 13],
     39: [28, 165, 46, 'South', 15]}
    """
    for prn in satdict:
        azi = satdict[prn][1]
        if azi >= 315 or azi <= 45: # fixed >=bug
            satdict[prn].append("North")
            if azi >= 180:
                azideviation = 360 - azi
            else:
                azideviation = azi
            satdict[prn].append(azideviation)
        if azi > 45 and azi <= 135:
            satdict[prn].append("East")
            azideviation = abs(azi - 90)
            satdict[prn].append(azideviation)
        if azi > 135 and azi <= 225:
            satdict[prn].append("South")
            azideviation = abs(azi - 180)
            satdict[prn].append(azideviation)
        if azi > 225 and azi < 315:
            satdict[prn].append("West")
            azideviation = abs(azi - 270)
            satdict[prn].append(azideviation)

    return satdict


def selectsats(satdict):
    """Choose four satellites to form the reading based on the
    following criteria, applied in order:

    1. Closeness of satellite to the azimuth of the direction based
    on azideviation score from directionclassify

    2. Signal to noise (highest number wins)

    """
    chosenfour = {}

    for prn in satdict:
#        print(prn)
 #       print(satdict[prn])
        direction = satdict[prn][3]
        aziscore = satdict[prn][4]
        if direction in chosenfour:  # if the key is already in the dict
            # select by lowest azi deviation
            if aziscore < chosenfour[direction][4]:
                chosenfour[direction] = [prn,
                                         satdict[prn][0],
                                         satdict[prn][1],
                                         satdict[prn][2],
                                         aziscore]
            # in the unlikely case that two satellites share the same azi
            elif aziscore == chosenfour[direction][4]:
                # select by highest snr
                if satdict[prn][2] > chosenfour[direction][3]: # fixed keyerror here
                    chosenfour[direction] = [prn,
                                             satdict[prn][0],
                                             satdict[prn][1],
                                             satdict[prn][2],
                                             aziscore]
        else:
            chosenfour[direction] = [prn,
                                     satdict[prn][0],
                                     satdict[prn][1],
                                     satdict[prn][2],
                                     aziscore]

    return chosenfour


def getsatellites(gps, verbose):
    """
    main reiterating loop which reads the incoming nmea sentences
    from the gps, sends to parser and catches user interrupt:
    ctrl-c
    """
    gsvlist = []
    while gsvlist == []:
        try:
            line = gps.readline()
            if line.startswith('$GPGSV'):
                line = formatline(line, verbose)

                # formatline performs checksum and returns None if
                # it fails
                if line is None:
                    break

                gsvlist = parseGSV(line, gps, verbose)
                gsvlist = formatgsvlist(gsvlist)

                return gsvlist

        except KeyboardInterrupt:
            # user sent ctrl-c to stop script
            gps.close()
            print """
user interrupt, shutting down"""
            sys.exit()


def inttodot(integer):
    """
    Convert an integer to divination dots, two dots if the integer
    is even, one if odd, two if zero

    Takes an integer argument, returns a string of two dotchars or
    one

    """
    dotchar = "*"
    if integer % 2 == 0:
        dot = dotchar * 2
    else:
        dot = dotchar + " "  # The addition of a space helps the
                             # final diagram line up

    return dot

def oddoreven(integer):
    if integer % 2 == 0:
        dot = 1
    else:
        dot = 0
    return dot
    
def domothers(chosenfour):
    """ Append binary representation 0 as O/odd, 1 as OO/even
    """
    motherlist=[]
    for elemental in ["South", "East", "North", "West"]:
        binrep=[]
        for body in range(4): 
            binrep.append(oddoreven(chosenfour[elemental][body]))
        motherlist.append(binrep)
    return motherlist

def dodaughters(motherlist):
    daughterlist=[]
    body=zip(*motherlist)
    for parts in body:
        daughterlist.append(parts)
    return daughterlist

def madd(x,y):
    return int(not(x ^ y))    

def donephews(mlist,dlist):
    nlist=[]
    nlist.append([madd(mlist[0][0],mlist[1][0]),madd(mlist[0][1],mlist[1][1]),madd(mlist[0][2],mlist[1][2]),madd(mlist[0][3],mlist[1][3])])
    nlist.append([madd(mlist[2][0],mlist[3][0]),madd(mlist[2][1],mlist[3][1]),madd(mlist[2][2],mlist[3][2]),madd(mlist[2][3],mlist[3][3])])
    nlist.append([madd(dlist[0][0],dlist[1][0]),madd(dlist[0][1],dlist[1][1]),madd(dlist[0][2],dlist[1][2]),madd(dlist[0][3],dlist[1][3])])
    nlist.append([madd(dlist[2][0],dlist[3][0]),madd(dlist[2][1],dlist[3][1]),madd(dlist[2][2],dlist[3][2]),madd(dlist[2][3],dlist[3][3])])
    return nlist

def dowitnesses(nlist):
    wlist=[]
    wlist.append([madd(nlist[0][0],nlist[1][0]),madd(nlist[0][1],nlist[1][1]),madd(nlist[0][2],nlist[1][2]),madd(nlist[0][3],nlist[1][3])])
    wlist.append([madd(nlist[2][0],nlist[3][0]),madd(nlist[2][1],nlist[3][1]),madd(nlist[2][2],nlist[3][2]),madd(nlist[2][3],nlist[3][3])])
    return wlist

def dojudge(wlist):
    jlist=[]
    jlist.append([madd(wlist[0][0],wlist[1][0]),madd(wlist[0][1],wlist[1][1]),madd(wlist[0][2],wlist[1][2]),madd(wlist[0][3],wlist[1][3])])
    return jlist

def dorec(jlist,mlist):
    rlist=[]
    rlist.append([madd(mlist[0][0],jlist[0][0]),madd(mlist[0][1],jlist[0][1]),madd(mlist[0][2],jlist[0][2]),madd(mlist[0][3],jlist[0][3])])
    return rlist

def preparemothers(chosenfour):
    """Turn the data from the four chosen satellites into the mothers
    diagram.

     West     North    East    South
prn    **        *      **       *
ele    **        *      **       *
azi    *         *      *        **
snr    *         **     **       **

    Earth    Water    Air     Fire
       IV       III     II       I
head   **        *      **       *
neck   **        *      **       *
body   *         *      *        **
feet   *         **     **       **
      West     North    East    South

    """
    spacer = "      "
    EOL = "\n"
    motherstring = """       Earth    Water    Air     Fire
        IV       III     II       I""" + EOL

    head = "head" + spacer
    neck = "neck" + spacer
    body = "body" + spacer
    feet = "feet" + spacer

    for d in ["West", "North", "East", "South"]:
        head += inttodot(chosenfour[d][0]) + spacer
        neck += inttodot(chosenfour[d][1]) + spacer
        body += inttodot(chosenfour[d][2]) + spacer
        feet += inttodot(chosenfour[d][3]) + spacer

    motherstring += head + EOL
    motherstring += neck + EOL
    motherstring += body + EOL
    motherstring += feet + EOL
    motherstring += "       West     North    East    South"

    return motherstring

def drawit(listere):
    """ run thru list and print whole list line by line"""
    # must reverse listy
    listy=list(listere)
    listy.reverse()
    body=zip(*listy)
    for parts in body:
        for part in parts:
            if part==1:
                print "O O   ",
            else:
                print " O    ",
        print

numeral=0

def lookfig(figure):
    # convert list to string
    global numeral
    key=''.join(str(e) for e in figure)
    numeral+=1
    return (' '.join((roman[numeral]+". GD:",crowley[numeral]+".",figdict[key][0],figdict[key][2],figdict[key][5])))

def main():
    """
    """
    satdict={}
    args = parse_arguments()
    gps = connectgps(args.port, args.baud)
    waitforfix(gps, args.verbose)
    # we need all directions
    #    while ("West" not in str(satdict.values()) and "East" not in str(satdict.values()) and "North" not in str(satdict.values()) and "South" not in str(satdict.values())):

    while (("West" not in str(satdict.values())) or ("East" not in str(satdict.values())) or ("North" not in str(satdict.values())) or ("South" not in str(satdict.values()))): 
        satellitepositions = getsatellites(gps, args.verbose)
        satdict = makesatdict(satellitepositions)
        satdict = directionclassify(satdict)
        print("WAITING FOR NSEW")
#        print(satdict)

    if args.verbose:
        print
        print "List of satellites found"
        print "prn: [elevation, azimuth, signal to noise,\
 direction, deviation from azi]"
        pprint(satdict)

    # choose four satellites (see function for criteria)
    chosenfour = selectsats(satdict)
    if args.verbose:
        print
        print "List of chosen satellites"
        print "direction: [prn, elevation, azimuth,\
 signal to noise, deviation from azi]"
        pprint(chosenfour)

    # need intermediate format/list of 0/1 to go from mothers/chosenfour as 1 or 2 dots/or binary0/1 [0-3] to daughters/4 // not xor
#    chosenfour={'East': [39, 65, 90, 0, 0], 'North': [4, 3, 24, 34, 24], 'South': [13, 52, 155, 23, 25], 'West': [24, 38, 278, 0, 8]}
    #but as list of lists so can index SENW -as 1,2,3,4
    mlist=domothers(chosenfour)
    if args.verbose:
        pprint(mlist)
    dlist=dodaughters(mlist)
    if args.verbose:
        pprint(dlist)
    nlist=donephews(mlist,dlist)
    if args.verbose:
        pprint(nlist)
    wlist=dowitnesses(nlist)
    if args.verbose:
        pprint(wlist)
    jlist=dojudge(wlist)
    if args.verbose:
        pprint(jlist)
    rlist=dorec(jlist,mlist)
    if args.verbose:
        pprint(rlist)

    # layout is right to left D M//nephews
    # witnesses// judge// reconciler

    print "VIII   VII    VI      V  |  IV     III    II      I"
    drawit(mlist+dlist)
    print "Daughters                  Mothers"
    print
    print "XII    XI      X     IX"
    drawit(nlist)
    print "Nephews"
    print
    print "XIV    XIII"
    drawit(wlist)
    print "Witnesses"
    print
    print "XV"
    drawit(jlist)
    print "Judge"
    print
    print "XVI"
    drawit(rlist)
    print "Reconciler"
    print
    # classify
    print "Mothers:"
    for figures in mlist:
        print(lookfig(figures))
    print
    print "Daughters:"
    for figures in dlist:
        print(lookfig(figures))
    print
    print "Nephews:"
    for figures in nlist:
        print(lookfig(figures))
    print
    print "Witnesses:"
    for figures in wlist:
        print(lookfig(figures))
    print
    print "Judge:"
    for figures in jlist:
        print(lookfig(figures))
    print
    print "Reconciler:"
    for figures in rlist:
        print(lookfig(figures))

if __name__ == '__main__':
    sys.exit(main())

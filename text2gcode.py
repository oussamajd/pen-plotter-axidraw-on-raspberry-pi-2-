#!/usr/bin/python
# coding: utf-8

import argparse
from math import *
import os
import re

parser = argparse.ArgumentParser(description="text2gcode")
group=parser
group.add_argument("-f", "--filepath", help="Path to txt file")
group.add_argument("-F", "--Fontfile", help="Path to font file")
group.add_argument("-xs", "--XStartVar",type=float, help="debut de x ")
group.add_argument("-ys", "--YStartVar",type=float, help="debut de y ")
group.add_argument("-a", "--AngleVar",type=float, help="Angle")
group.add_argument("-X", "--XScaleVar",type=float, help="XScaleVar")
group.add_argument("-Y", "--YScaleVar",type=float, help="YScaleVar")
group.add_argument("-s", "--CSpacePVar",type=float, help="CSpacePVar")
group.add_argument("-w", "--WSpacePVar",type=float, help="WSpacePVar")
group.add_argument("-m", "--MirrorVar",type=int, help="Mirror")
group.add_argument("-fl", "--FlipVar",type=int, help="FlipVar")
args = parser.parse_args()


fontfile = "/home/pi/Desktop/cnc/cxf-fonts/romant.cxf"
#fontfile="/home/oussama/Desktop/romanc.cxf"

def parse(file):
    font = {}
    key = None
    num_cmds = 0
    line_num = 0
    for text in file:
        #format for a typical letter (lowercase r):
        ##comment, with a blank line after it
        #
        #[r] 3
        #L 0,0,0,6
        #L 0,6,2,6
        #A 2,5,1,0,90
        #
        line_num += 1
        end_char = re.match('^$', text) #blank line
        if end_char and key: #save the character to our dictionary
            font[key] = Character(key)
            font[key].stroke_list = stroke_list
            font[key].xmax = xmax
            if (num_cmds != cmds_read):
                print "(warning: discrepancy in number of commands %s, line %s, %s != %s )" % (fontfile, line_num, num_cmds, cmds_read)

        new_cmd = re.match('^\[(.*)\]\s(\d+)', text)
        if new_cmd: #new character
            key = new_cmd.group(1)
            num_cmds = int(new_cmd.group(2)) #for debug
            cmds_read = 0
            stroke_list = []
            xmax, ymax = 0, 0

        line_cmd = re.match('^L (.*)', text)
        if line_cmd:
            cmds_read += 1
            coords = line_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            stroke_list += [Line(coords)]
            xmax = max(xmax, coords[0], coords[2])

        arc_cmd = re.match('^A (.*)', text)
        if arc_cmd:
            cmds_read += 1
            coords = arc_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            xcenter, ycenter, radius, start_angle, end_angle = coords
            # since font defn has arcs as ccw, we need some font foo
            if ( end_angle < start_angle ):
                start_angle -= 360.0
            # approximate arc with line seg every 20 degrees
            segs = int((end_angle - start_angle) / 20) + 1
            angleincr = (end_angle - start_angle)/segs
            xstart = cos(start_angle * pi/180) * radius + xcenter
            ystart = sin(start_angle * pi/180) * radius + ycenter
            angle = start_angle
            for i in range(segs):
                angle += angleincr
                xend = cos(angle * pi/180) * radius + xcenter
                yend = sin(angle * pi/180) * radius + ycenter
                coords = [xstart,ystart,xend,yend]
                stroke_list += [Line(coords)]
                xmax = max(xmax, coords[0], coords[2])
                ymax = max(ymax, coords[1], coords[3])
                xstart = xend
                ystart = yend
    return font
#=======================================================================
class Character:
    def __init__(self, key):
        self.key = key
        self.stroke_list = []

    def __repr__(self):
        return "%s" % (self.stroke_list)

    def get_xmax(self):
        try: return max([s.xmax for s in self.stroke_list[:]])
        except ValueError: return 0

    def get_ymax(self):
        try: return max([s.ymax for s in self.stroke_list[:]])
        except ValueError: return 0



#=======================================================================

class Line:

    def __init__(self, coords):
        self.xstart, self.ystart, self.xend, self.yend = coords
        self.xmax = max(self.xstart, self.xend)
        self.ymax = max(self.ystart, self.yend)

    def __repr__(self):
        return "Line([%s, %s, %s, %s])" % (self.xstart, self.ystart, self.xend, self.yend)




#=======================================================================
class app():
    def __init__(self):
        self.main()
        self.DoIt()
    def main(self):
        self.gcode = []
        self.PreambleVar='G17 G20 G90 G64 P0.003 M3 S3000 M7 F5'
       	self.Font=fontfile
       	self.textfile='/home/pi/Desktop/cnc/text.txt'
        self.TextVar=open(self.textfile,'r')

        self.XStartVar=1.0
        self.YStartVar=2.0
        self.AngleVar=1.0
        self.XScaleVar=0.04
        self.YScaleVar=0.04
        self.CSpacePVar=10.5
        self.WSpacePVar=50.0
        self.DepthVar=-0.010
        self.SafeZVar=0.100
        self.PostambleVar='M5 M9 M2'
        self.MirrorVar=0
        self.FlipVar=0
        self.DoIt
    def CopyClipboard(self):
	 self.fout=file("gcode.ngc",'w')
         for line in self.gcode:
            self.fout.write(line+'\n')
         self.fout.close()

#=======================================================================
    def WriteToAxis(self):
        for line in self.gcode:
            sys.stdout.write(line+'\n')
        self.quit()
#=======================================================================
    def sanitize(self,string):
        retval = ''
        good=' ~!@#$%^&*_+=-{}[]|\:;"<>,./?'
        for char in string:
            if char.isalnum() or good.find(char) != -1:
                retval += char
            else: retval += ( ' 0x%02X ' %ord(char))
        return retval
#=======================================================================
# routine takes an x and a y in raw internal format
# x and y scales are applied and then x,y pt is rotated by angle
# Returns new x,y tuple
    def Rotn(self,x,y,xscale,yscale,angle):
        Deg2Rad = 2.0 * pi / 360.0
        xx = x * xscale
        yy = y * yscale
        rad = sqrt(xx * xx + yy * yy)
        theta = atan2(yy,xx)
        newx=rad * cos(theta + angle*Deg2Rad)
        newy=rad * sin(theta + angle*Deg2Rad)
        return newx,newy
#=======================================================================
    def DoIt(self):
        # range check inputs for gross errors
        try:
               file = open(self.Font)
        except:
	       print"try to put font file"
               return
        Angle =float(self.AngleVar)
        if Angle <= -360.0 or Angle >= 360.0:
            print"chose the right angle"
            Angle=0.0
            return
        XScale =   float(self.XScaleVar)
        if XScale <= 0.0:
            print "chose the right XScale"
            XScale=0.04
            return
        YScale =   float(self.YScaleVar)
        if YScale <= 0.0:
            print"chose the right YScale"
            YScale=0.04
            return
        CSpaceP=   float(self.CSpacePVar)
        if CSpaceP <= 0.0:
            print"chose the right CSpaceP"
            CSpaceP=25.0
            return
        WSpaceP=   float(self.WSpacePVar)
        if WSpaceP <= 0.0:
            print"chose the right WSpaceP"
            WSpaceP=100.00
            return
        # erase old gcode as needed
        self.gcode = []
        # temps used for engraving calcs
        String =     self.TextVar.read()
        SafeZ =    float(self.SafeZVar)
        XStart =   float(self.XStartVar)
        YStart =   float(self.YStartVar)
        Depth =    float(self.DepthVar)
        XScale =   float(self.XScaleVar)
        YScale =   float(self.YScaleVar)
        CSpaceP=   float(self.CSpacePVar)
        oldx = oldy = -99990.0      # last engraver position
        font = parse(file)          # build stroke lists from font file
        file.close()
        font_line_height = max(font[key].get_ymax() for key in font)
        font_word_space =  max(font[key].get_xmax() for key in font) * (WSpaceP/100.0)
        font_char_space = font_word_space * (CSpaceP /100.0)
        xoffset = 0                 # distance along raw string in font units
        # calc a plot scale so we can show about first 15 chars of string
        # in the preview window
        PlotScale = 15 * font['A'].get_xmax() * XScale / 150
        for char in String:
            if char == ' ':
                xoffset += font_word_space
                continue
            try:
                self.gcode.append("(character '%s')" % self.sanitize(char))
                first_stroke = True
                for stroke in font[char].stroke_list:
#                    self.gcode.append("(%f,%f to %f,%f)" %(stroke.xstart,stroke.ystart,stroke.xend,stroke.yend ))
                    dx = oldx - stroke.xstart
                    dy = oldy - stroke.ystart
                    dist = sqrt(dx*dx + dy*dy)
                    x1 = stroke.xstart + xoffset
                    y1 = stroke.ystart
                    if self.MirrorVar == 1:
                        x1 = -x1
                    if self.FlipVar == 1:
                        y1 = -y1
                    # check and see if we need to move to a new discontinuous start point
                    if (dist > 0.001) or first_stroke:
                        first_stroke = False
                        #lift engraver, rapid to start of stroke, drop tool
                        self.gcode.append("G0 Z2")
                        self.gcode.append('G0 X%.4f Y%.4f' %(x1,y1))
                        self.gcode.append("G1 Z-1")
                    x2 = stroke.xend + xoffset
                    y2 = stroke.yend
                    if self.MirrorVar == 1:
                        x2 = -x2
                    if self.FlipVar == 1:
                        y2 = -y2
                    self.gcode.append('G1 X%.4f Y%.4f' %(x2,y2))
                    oldx, oldy = stroke.xend, stroke.yend
                    # since rotation and scaling is done in gcode, we need equivalent for plotting
                    # note that plot shows true shape and orientation of chrs, but starting x,y
                    # is always at the center of the preview window (offsets not displayed)
                    x1,y1 = self.Rotn(x1,y1,XScale,YScale,Angle)
                    x2,y2 = self.Rotn(x2,y2,XScale,YScale,Angle)
                # move over for next character
                char_width = font[char].get_xmax()
                xoffset += font_char_space + char_width
	    	self.CopyClipboard()
            except KeyError:
               self.gcode.append("(warning: character '0x%02X' not found in font defn)" % ord(char))
            self.gcode.append("")       # blank line after every char block
        self.gcode.append( 'G0 Z2')     # final engraver up
        # finish up with icing
        self.gcode.append(self.PostambleVar)


ab = app()
import cnc

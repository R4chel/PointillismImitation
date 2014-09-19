import random
import sys
from PIL import Image, ImageDraw
import segmentation

'''Assumptions made for Segment object:
- is a class 
- has property segment.pixels that returns a list of all Pixel objects that belongs to it
- has property size and num that are parameters for manipulation

Assumptions made for Pixel object:
- has properties x, y, r, g, b
'''

class Expressionist:

    def __init__(self, segments):
        self.segments = segments

    def manipulate(self, (width, height)):
        '''Perform the image manipulation
        width: width of the image
        height: height of the image'''

        def get_blocks(pixels, size):
            '''Divides each segment up into blocks with size size*size.
             Return list of (topleft, rgb) where topleft = the topleft x,y 
            point of block and rgb = the average color for the block.'''

            blocks_dict = {} #blocks_dict[(x,y)] = [count, tot r, tot g, tot b]
            for pixel in pixels:
                key = (pixel.x/size, pixel.y/size)
                if key in blocks_dict:
                    blocks_dict[key][0]+=1   #increment count
                    blocks_dict[key][1]+=pixel.r  #increment colors
                    blocks_dict[key][2]+=pixel.g 
                    blocks_dict[key][3]+=pixel.b 
                else:
                    blocks_dict[key] = [1, pixel.r, pixel.g, pixel.b]
            blocks = [] #list of (center x,y points and color)
            for (x,y), data in blocks_dict.items():
                #divide total color values by pixel count to get average color
                data[1:] = map(lambda x: x/data[0], data[1:])
                blocks.append(((x*size,y*size), tuple(data[1:])))
            return blocks

        def sort_segments(segments, n):
            #n = threshold number
            groups = {} #key is a 3-tuple consisting of 1 or 0
            #1 = above threshold, 0 = below threshold
            #floor = lambda x: 1 if x > threshold else 0
            def floor(c):
                thresholds = [i*(255/n) for i in range(1, n+1)]
                for i in range(0, n):
                    if thresholds[i] >= c:
                        return i
            for segment in segments:
                key = tuple(map(floor, segment.get_color()))
                if key in groups:
                    groups[key].append(segment)
                else:
                    groups[key] = [segment]
            return groups.values()
 

        new_image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(new_image)
        segment_groups = sort_segments(self.segments, 4)
        segment_groups.sort(key = lambda s: len(s))
        size = ((len(segment_groups))/2)+1
        i = 0 
        for group in segment_groups:
            for segment in group:
                for block in get_blocks(segment.pixels, size):
                    #paint circles, whatever shapes etc. etc.
                    x,y = block[0]
                    #u = BBOX_EXPAND
                    u = 0
                    s = size
                    draw.rectangle((x-u, y-u, x+s+u, y+s+u), fill="rgb"+str(block[1]))
            i+=1
            if (i%3 == 0):
                size-=1
        del draw
        return new_image                 

#GLOBALS
THRESHOLD = 500
MIN_SIZE = 10
#SIZE = 5
BBOX_EXPAND = 2

def start(image_name, output_name):
    image = Image.open(image_name)
    segments = segmentation.get_segments(image, THRESHOLD, MIN_SIZE)
    exp = Expressionist(segments)
    exp.manipulate(image.size).save(output_name)
    segments.sort(key = lambda s: s.size)
    l = len(segments)
    #paint.blur_segment(image, segments[2*l/3:], 3).save("output.png")

if len(sys.argv) != 3:
    print "usage: expressionist2.py [input_image_name] [output_name]"
else:
    start(sys.argv[1], sys.argv[2])

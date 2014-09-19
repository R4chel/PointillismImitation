from PIL import Image as I
from PIL import ImageStat

class Image_Segmentation:
    def __init__(self, name):
        self.name = name
        self.image = I.open(name)
        self.stat = ImageStat.Stat(self.image)
        (w,h) = self.image.size    
        self.pixels = []
        for i in range(h*w):    
            (x,y) = (i % w, int(i/w)) 
            self.pixels.append(Pixel(self.image.getpixel((x,y)), i ,x, y))
        self.forest = []
        self.root_dict = {}
        self.threshold = int(sum(self.stat.stddev))*2
        self.min_size = int(w*h/20)
        self.edges = image_segmentation(self.forest, self.root_dict, w,h,
                self.pixels, self.threshold, self.min_size)
        self.segments = []
        for k in self.root_dict:
            self.segments.append(self.root_dict[k])

    def get_center_segment(self):
        (w,h) = self.image.size
        i = int((h)/2)*w + int(w/2)
        root = self.forest[i].find()
        return self.root_dict[root.n]

# pixel
class Pixel:
    @property
    def r(self):
        return self.rgb[0]

    @property
    def g(self):
        return self.rgb[1]

    @property
    def b(self):
        return self.rgb[2]

    def __init__(self, rgb, n, x, y):
        self.rgb = rgb
        self.n = n
        self.x = x 
        self.y = y
        self.blur_rgb = None
# weighted edges
class Weighted_Edge:
    def __init__(self, u, v):
        self.u = u.n
        self.v = v.n
        self.w = calc_edge_weight(u,v)

# disjoint set
class Node:
    def __init__(self, value):
        self.parent = self
        self.n = value
    def find(self):
        if self.parent != self:
            self.parent = self.parent.find()
        return self.parent
    def merge(self, other, roots):
        root1 = self.find()
        root2 = other.find()
        del roots[root2.n]
        root2.parent = root1

# Segment
class Segment:
    def __init__(self, p):
        self.size = 1
        self.diff = 0.0
        self.rgb_sum = list(p.rgb)
        self.pixels = [p]
        self.blur = False
    def merge(self, other, edge_weight):
        self.size += other.size
        self.diff = max(self.diff, other.diff, edge_weight)
        for i in range(len(self.rgb_sum)):
            self.rgb_sum[i] += other.rgb_sum[i]
        self.pixels += other.pixels
    def get_color(self):
        colors = []
        for c in self.rgb_sum:
           colors.append(int(c/self.size))
        return tuple(colors)
    def find_center(self):
        x_sum = 0
        y_sum = 0
        for p in self.pixels:
            x_sum += p.x
            y_sum += p.y
        x = int(x_sum/self.size)
        y = int(y_sum/self.size)
        return (x,y)
    def get_data(self, mode):
        rgb_list = []
        for p in self.pixels:
            rgb_list.append(p.rgb)
        new_img = I.new(mode, (len(rgb_list),1))
        new_img.putdata(rgb_list)
        stat = ImageStat.Stat(new_img)
        return stat
    
    def get_value(self,threshold):
        return self.diff + threshold/self.size


def calc_edge_weight(u, v):
    w = 0
    for i in range(len(u.rgb)):
        w += (u.rgb[i]-v.rgb[i])**2
    w = w ** .5;
    return w


# image segmentation

def add_edges_to_list(p, w, h, pixels, edges):
    x = p.n % w
    y = int(p.n/w)
    if x + 1 < w :
        edges.append(Weighted_Edge(p, pixels[p.n+1]))
    if x > 0 and y + 1 < h:
        edges.append(Weighted_Edge(p, pixels[p.n+w-1]))
    if y + 1 < h :
        edges.append(Weighted_Edge(p, pixels[p.n+w]))
    if x + 1 < w and y + 1 < h:
        edges.append(Weighted_Edge(p, pixels[p.n+w+1]))



def image_segmentation(forest, root_dict, width, height, pixels, threshold, min_size):
    # create forest
    for i in range(width*height):
        forest.append(Node(i))
    
    weighted_edges = []
    for i in range(width*height):
        add_edges_to_list(pixels[i], width, height, pixels, weighted_edges)
        root_dict[i] = Segment(pixels[i])

    # sort weighted edge list by weight
    weighted_edges = sorted(weighted_edges, key=lambda edge: edge.w)

    for w in weighted_edges:
        r1 = forest[w.u].find()
        r2 = forest[w.v].find()
        if r1 != r2:
            s1 = root_dict[r1.n]
            s2 = root_dict[r2.n]
            if w.w <= min(s1.get_value(threshold), s2.get_value(threshold)):
                s1.merge(s2, w.w)
                r1.merge(r2, root_dict)
    print len(root_dict)
    #merge_segments(root_dict, forest, min_size)
    
        
    #merge small components 
    for w in weighted_edges:
        r1 = forest[w.u].find()
        r2 = forest[w.v].find()
        if r1 != r2:
            s1 = root_dict[r1.n]
            s2 = root_dict[r2.n]
            
            if min_size >= min(s1.size, s2.size):
                s1.merge(s2, w.w)
                r1.merge(r2, root_dict)
    
    print len(root_dict)
 
    return weighted_edges

def merge_segments(root_dict, forest, min_size):
    meta_pixel_forest = {}
    for k in root_dict:
        v = root_dict[k]
        
        meta_pixel_forest[k] = (Pixel(v.get_color(), k, -1, -1), Node(k))
    
    weighted_edges = []
    
    keys = meta_pixel_forest.keys()
    
    for k1 in meta_pixel_forest:
        (p1, n1) = meta_pixel_forest[k1]
        for k2 in meta_pixel_forest:
            if k1 != k2:
                (p2, n2) = meta_pixel_forest[k2]
                weighted_edges.append(Weighted_Edge(p1,p2))
    
    # sort weighted edge list by weight
    weighted_edges = sorted(weighted_edges, key=lambda edge: edge.w)
    
    for w in weighted_edges:
        (p1, n1) = meta_pixel_forest[w.u]
        (p2, n2) = meta_pixel_forest[w.v]
        r1 = n1.find()
        r2 = n2.find()
        s1 = root_dict[r1.n]
        s2 = root_dict[r2.n]
        if r1 != r2:
            if min_size >= min(s1.size, s2.size):
                s1.merge(s2, w.w)
                r1.merge(r2, root_dict)




def get_segments(image, threshold, min_size):
    img = image
    (w,h) = img.size    
    pixels = []
    for i in range(h*w):    
        (x,y) = (i % w, int(i/w)) 
        pixels.append(Pixel(img.getpixel((x,y)), i ,x, y))
    forest = []
    root_dict = {}
    edges = image_segmentation(forest, root_dict, w,h, pixels, threshold, min_size)
    segments = []
    for k in root_dict:
        segments.append(root_dict[k])
    return segments


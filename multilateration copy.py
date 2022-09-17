import json
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

class Packet():
    def __init__(self, packet_path):
        with open(packet_path, 'r') as packet_json:
            self.packet = json.load(packet_json)
        
        self.lat = self.packet['decoded']['payload']['latitude']
        self.long = self.packet['decoded']['payload']['longitude']
        self.alt = self.packet['decoded']['payload']['altitude']

        self.num_hotspots = len(self.packet['hotspots'])
    
    def list_hotspots(self):
        self.hotspots = []
        for hotspot in self.packet['hotspots']:
            self.hotspots.append({'id': hotspot['id'], 'lat': hotspot['lat'], 'long': hotspot['long'], 'rssi': hotspot['rssi'], 'snr': hotspot['snr']})

        return self.hotspots

    def get_best_hotspots(self):
        self.best_hotspots = []
        for hotspot in self.hotspots:
            if hotspot['rssi'] > -110:
                self.best_hotspots.append(hotspot)
        
        return self.best_hotspots


packet = Packet('packets/2022-07-10/Balloon Tracker/2022-07-10 09:46:33.737342.json')
packet.list_hotspots()
best_hotspots = packet.get_best_hotspots()

def circle_intersection(circle1, circle2):
    ''' Calculate intersection points of two circles.
    from https://gist.github.com/xaedes/974535e71009fa8f090e
    Args:
        circle1: tuple(x,y,radius)
        circle2: tuple(x,y,radius)
    Returns
        tuple of intersection points (which are (x,y) tuple)
    >>> circle_intersection((-0.5, 0, 1), (0.5, 0, 1))
    ((0.0, -0.8660254037844386), (0.0, 0.8660254037844386))
    >>> circle_intersection((-1, 0, 1), (1, 0, 1))
    ((0.0, 0.0), (0.0, 0.0))
    '''
    x1,y1,r1 = circle1
    x2,y2,r2 = circle2
    # http://stackoverflow.com/a/3349134/798588
    # d is euclidean distance between circle centres
    dx,dy = x2-x1,y2-y1
    d = math.sqrt(dx*dx+dy*dy)
    if d > r1+r2:
        # print('No solutions, the circles are separate.')
        return None # No solutions, the circles are separate.
    elif d < abs(r1-r2):
        # No solutions because one circle is contained within the other
        # print('No solutions because one circle is contained within the other')
        return None
    elif d == 0 and r1 == r2:
        # Circles are coincident - infinite number of solutions.
        # print('Circles are coincident - infinite number of solutions.')
        return None

    a = (r1*r1-r2*r2+d*d)/(2*d)
    h = math.sqrt(r1*r1-a*a)
    xm = x1 + a*dx/d
    ym = y1 + a*dy/d
    xs1 = xm + h*dy/d
    xs2 = xm - h*dy/d
    ys1 = ym - h*dx/d
    ys2 = ym + h*dx/d

    return ((xs1,ys1),(xs2,ys2))

def get_locus(hotspot_1, hotspot_2, delta_d, max_d):
    location_1 = (hotspot_1['lat'], hotspot_1['long'])
    location_2 = (hotspot_2['lat'], hotspot_2['long'])
    rssi_1 = hotspot_1['rssi']
    rssi_2 = hotspot_2['rssi']

    rssi_difference = abs(rssi_1 - rssi_2)

    # two lines, x0/y0 and x1/y1 corresponding to the two intersections of the
    # circles. These will be concateneated at the end to form a single line.
    x0 = []
    x1 = []
    y0 = []
    y1 = []

    # Which hotspot had the best signal
    if rssi_1 >= rssi_2:
        circle1 = (location_1[0], location_1[1], 0)
        circle2 = (location_2[0], location_2[1], rssi_difference)
    else:
        circle1 = (location_2[0], location_2[1], 0)
        circle2 = (location_1[0], location_1[1], rssi_difference)
    
    # Iterate over all potential radii.
    for _ in range(int(max_d)//int(delta_d)):
        intersect = circle_intersection(circle1, circle2)
        if(intersect is not None):
            x0.append(intersect[0][0])
            x1.append(intersect[1][0])
            y0.append(intersect[0][1])
            y1.append(intersect[1][1])

        circle1 = (circle1[0], circle1[1], circle1[2]+delta_d)
        circle2 = (circle2[0], circle2[1], circle2[2]+delta_d)
    
    # Reverse so the concatenated locus is continous. Could reverse only
    # x1/y1 instead if you wanted.
    x0 = list(reversed(x0))
    y0 = list(reversed(y0))

    # Concatenate
    x = x0 + x1
    y = y0 + y1

    return [x, y]

def get_loci(hotspots, delta_d, max_d):
    rec_rssi = []
    for hotspot in hotspots:
        rec_rssi.append(hotspot['rssi'])
    
    loci = []

    # Hotspot that receives the transmission with best RSSI.
    first_hotspot = int(np.argmax(rec_rssi))

    for j in [x for x in range(len(hotspots)) if x!= first_hotspot]:
        # print('hotspot', str(first_hotspot), 'to', str(j))
        locus = get_locus(hotspot_1=(hotspots[first_hotspot]),
                          hotspot_2=(hotspots[j]),
                          delta_d=delta_d, max_d=max_d)
        # Sometimes empty locus is produced depending on geometry of the
        # situation. Discard these.
        if(len(locus[0]) > 0):
            loci.append(locus)
    
    return loci

# How many hotspots. All hotspots recieve the transmission.
num_hotspots = 8

# Metre length of a square containing the transmitting
# device, centred around (x, y) = (0, 0). Device will be randomly placed
# in this area.
tx_square_side = 10

# Metre length of a square containing the hotspots,
# centred around (x, y) = (0, 0). hotspots will be randomly placed
# in this area.
rx_square_side = 200

# Metre increments to radii of circles when generating locus of
# circle intersection.
delta_d = int(100)

# Max distance a transmission will be from the hotspot that first
# received the transmission. This puts an upper bound on the radii of the
# circle, thus limiting the size of the locus to be near the hotspots.
max_d = int(20e3)

# location of transmitting device with tx[0] being x and tx[1] being y.
tx = (np.random.rand(2)-0.5) * tx_square_side
print('tx:', tx)

# Get the loci.
loci = get_loci(best_hotspots, 100, int(20e3))

print(loci)

# Plot hotspots and transmission location.
fig, ax = plt.subplots(figsize=(5,5))
max_width = max(tx_square_side, rx_square_side)/2
ax.set_ylim((max_width*-1, max_width))
ax.set_xlim((max_width*-1, max_width))
for i in range(len(best_hotspots)):
    x = best_hotspots[i]['lat']
    y = best_hotspots[i]['long']
    ax.scatter(x, y)
    ax.annotate('hotspot '+str(i), (x, y))
ax.scatter(tx[0], tx[1])
ax.annotate('Tx', (tx[0], tx[1]))

'''
# Iterate over every unique combination of hotspots and plot nifty stuff.
for i in range(num_hotspots):
    if(plot_trilateration_circles):
        # Circle from hotspot i to tx site
        circle1 = (hotspots[i][0], hotspots[i][1], distances[i])
        circle = plt.Circle((circle1[0], circle1[1]),
                            radius=circle1[2], fill=False)
        ax.add_artist(circle)
    for j in range(i+1, num_hotspots):
        if(plot_lines_between_hotspots):
            # Line between hotspots
            ax.plot((hotspots[i][0], hotspots[j][0]),
                    (hotspots[i][1], hotspots[j][1]))
'''

for locus in loci:
    ax.plot(locus[0], locus[1])
plt.show()
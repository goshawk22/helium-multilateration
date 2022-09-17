import json
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

class Packet():
    def __init__(self, packet_path):
        with open(packet_path, 'r') as packet_json:
            self.packet = json.load(packet_json)
        
        #self.lat = self.packet['decoded']['payload']['latitude']
        #self.long = self.packet['decoded']['payload']['longitude']
        #self.alt = self.packet['decoded']['payload']['altitude']

        self.num_hotspots = len(self.packet['hotspots'])
    
    def list_hotspots(self):
        self.hotspots = []
        for hotspot in self.packet['hotspots']:
            self.hotspots.append({'id': hotspot['id'], 'lat': hotspot['lat'], 'long': hotspot['long'], 'rssi': hotspot['rssi'], 'snr': hotspot['snr']})

        return self.hotspots

    def get_best_hotspots(self):
        self.best_hotspots = []
        for hotspot in self.hotspots:
            if hotspot['rssi'] > -130:
                self.best_hotspots.append(hotspot)
        
        return self.best_hotspots


#packet = Packet('packets/2022-07-10/Balloon Tracker/2022-07-10 09:46:33.737342.json')
#packet = Packet('packets/2022-07-17/Balloon Tracker/2022-07-17 10:57:36.507851.json')
#packet = Packet('packets/2022-07-17/Balloon Tracker/2022-07-17 10:54:06.484061.json')
packet = Packet('packets/2022-07-17/Balloon Tracker/2022-07-17 08:02:15.639708.json')

packet.list_hotspots()
best_hotspots = packet.get_best_hotspots()

def get_circle_intercection(circle_1, circle_2):
    # circle 1: (x0, y0, r0)
    # circle 2: (x1, y1, r1)
    x0, y0, r0 = circle_1
    x1, y1, r1 = circle_2

    d=math.sqrt((x1-x0)**2 + (y1-y0)**2)

    # non intersecting
    if d > r0 + r1 :
        return None
    # One circle within other
    if d < abs(r0-r1):
        return None
    # coincident circles
    if d == 0 and r0 == r1:
        return None
    else:
        a=(r0**2-r1**2+d**2)/(2*d)
        h=math.sqrt(r0**2-a**2)
        x2=x0+a*(x1-x0)/d   
        y2=y0+a*(y1-y0)/d   
        x3=x2+h*(y1-y0)/d     
        y3=y2-h*(x1-x0)/d 

        x4=x2-h*(y1-y0)/d
        y4=y2+h*(x1-x0)/d
        
        return (x3, y3, x4, y4)

def get_locus(hotspot_1, hotspot_2, increment, max_d):

    # There will be two lines, one for each point of intersection
    x0 = []
    x1 = []
    y0 = []
    y1 = []

    increment_dec = meters_to_decimal(increment, hotspot_1['lat'])

    # difference in RSSI
    d_rssi = abs(hotspot_1['rssi'] - hotspot_2['rssi'])

    # Which hotspot had the strongest signal?
    if hotspot_1['rssi'] > hotspot_2['rssi']:
        
        offset = hotspot_1['rssi'] / hotspot_2['rssi']

        circle_1 = (hotspot_1['lat'], hotspot_1['long'], 0)
        circle_2 = (hotspot_2['lat'], hotspot_2['long'], 0)

    else:

        offset = hotspot_2['rssi'] / hotspot_1['rssi']

        circle_1 = (hotspot_2['lat'], hotspot_2['long'], 0)
        circle_2 = (hotspot_1['lat'], hotspot_1['long'], 0)

    for _ in range(int(max_d)//int(increment)):
        intersection = get_circle_intercection(circle_1, circle_2)
        if intersection != None:
            x0.append(intersection[0])
            y0.append(intersection[1])
            x1.append(intersection[2])
            y1.append(intersection[3])

        circle_1 = (circle_1[0], circle_1[1], circle_1[2] + increment_dec*offset)
        circle_2 = (circle_2[0], circle_2[1], circle_2[2] + increment_dec)


    # Reverse so the concatenated locus is continous. Could reverse only
    # x1/y1 instead if you wanted.
    x0 = list(reversed(x0))
    y0 = list(reversed(y0))

    # Concatenate
    x = x0 + x1
    y = y0 + y1

    return [x,y]


def get_loci(hotspots, increment, max_d):
    loci = []
    num_hotspots = len(hotspots)
    for i in range(num_hotspots):
        for j in range(num_hotspots):
            if i != j:
                loci.append(get_locus(hotspots[i], hotspots[j], increment, max_d))
    
    return loci


def meters_to_decimal(meters, latitude):
    return meters / (111.32 * 1000 * math.cos(latitude * (math.pi / 180)))

loci = get_loci(best_hotspots, 100, 50000)

# Plot hotspots and transmission location.
fig, ax = plt.subplots(figsize=(5,5))
for i in range(len(best_hotspots)):
    h_x = best_hotspots[i]['lat']
    h_y = best_hotspots[i]['long']
    ax.scatter(h_x, h_y)
    ax.annotate('Hotspot '+str(i), (h_x, h_y))

x = []
y = []

for locus in loci:
    for point in locus[0]:
        x.append(point)
    
    for point in locus[1]:
        y.append(point)
        
    ax.plot(locus[0], locus[1])

for hotspot in best_hotspots:
    print(str(hotspot['lat']) + ', ' + str(hotspot['long']))

lat = sum(x)/len(x)
long = sum(y)/len(y)

print("Estimated Location: ")
print(lat, long)
plt.show()
import json
import os

def load_packet(path):
    with open(path, 'r') as packet_json:
        packet = json.load(packet_json)
    
    return packet

#test = load_packet('packets/2022-07-17/Balloon Tracker/2022-07-17 05:28:44.994135.json')
#print(test.keys())
#print(len(test['hotspots']))

most_hotspots = None
most_hotspots_count = 0

for date in os.listdir('packets'):
    tracker_path = 'packets/' + date + '/Balloon Tracker/'
    for packet_file in os.listdir(tracker_path):
        full_path = tracker_path + packet_file
        packet = load_packet(full_path)
        num_hotspots = len(packet['hotspots'])
        if 8 > num_hotspots > 4:
            most_hotspots = full_path
            most_hotspots_count = num_hotspots
            print(num_hotspots)

print(most_hotspots)
print(most_hotspots_count)
import json
from unicodedata import name
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
import ray

import os

if not os.path.exists("images"):
    os.mkdir("images")

class Packet():
    def __init__(self, packet_path):
        with open(packet_path, 'r') as packet_json:
            self.packet = json.load(packet_json)

        self.num_hotspots = len(self.packet['hotspots'])
    
    def list_hotspots(self):
        self.hotspots = []
        for hotspot in self.packet['hotspots']:
            self.hotspots.append({'name': hotspot['name'], 'lat': hotspot['lat'], 'long': hotspot['long'], 'rssi': hotspot['rssi'], 'snr': hotspot['snr']})

        return self.hotspots

list_of_packet_paths = os.listdir('../balloon-data/packets/')

@ray.remote
def create_images(paths):
    for packet_path in paths:
        name = packet_path
        full_packet_path = '../balloon-data/packets/' + name
        packet = Packet(full_packet_path)

        lat = []
        long = []
        text = []

        for hotspot in packet.list_hotspots():
            lat.append(hotspot['lat'])
            long.append(hotspot['long'])
            text.append(hotspot['name'])


        mapbox_access_token = open(".mapbox_token").read()

        fig = go.Figure(go.Scattermapbox(
                lat=lat,
                lon=long,
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=9
                ),
                text=text,
            ))

        fig.update_layout(
            autosize=True,
            height = 900,
            width = 1800,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=49.465,
                    lon=2.356,
                ),
                pitch=0,
                zoom=5
            ),
        )

        path = 'images/' + name[:-5] + '.png'
        fig.write_image(path)
    
    return paths

def split_list(list_to_split, n):
    # Split a Python List into Chunks using For Loops
    chunked_list = list()
    chunk_size = int(len(list_to_split)/n)

    for i in range(0, len(list_to_split), chunk_size):
        chunked_list.append(list_to_split[i:i+chunk_size])

    return chunked_list

#print(len(split_list(list_of_packet_paths, 11)))
#assert 1 == 2

'''
app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True)  # Turn off reloader if inside Jupyter
'''

# Launch 12 parallel tasks.

futures = [create_images.remote(i) for i in split_list(list_of_packet_paths,8)]

# Retrieve results.
print(ray.get(futures))
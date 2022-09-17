import requests

def get_hotspot_info(address):
    url = 'https://api.helium.io/v1/hotspots/' + address
    hotspot_info = requests.get(url)
    return hotspot_info.json()['data']

print(get_hotspot_info('11bg88bcWc3w96VhQGeyxqFwWm3UZzwXhpJgtdEMXypEDSjVCpq'))
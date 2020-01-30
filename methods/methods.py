import requests
import urllib3
from lxml.html import fromstring
from utils.utils import random_header
from random import choice

# Disable InsecureRequestWarning
urllib3.disable_warnings()

PROXIES = []

# def fetch(url):
#     try:
#         r = requests.get(url, headers=random_header(), verify=False)
#         r.raise_for_status()
#     except requests.exceptions.HTTPError as http:
#         return http.response.status_code
#     except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
#         return 500
#     return r.text

def fetch(url):
    try:
        req = requests.get(url, headers=random_header(), verify=False, allow_redirects=False)
        req.raise_for_status()
    except requests.exceptions.HTTPError as http:
        return http.response.status_code
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
        return 500
    if req.status_code != 200:
        return req.status_code
    return req.text

def fetch_file(page, eauctionsFileId, auctionId, f):
    proxy = choise(PROXIES) if len(PROXIES) > 0 else get_proxies()
    print(proxy[0])
    try:
        req = requests.post(page, { 'eauctionsFileId': eauctionsFileId, 'auctionId': auctionId}, verify=False, proxies={ 'http': 'http://'+proxy[0], 'https': 'http://'+proxy[0] }, allow_redirects=False)
        req.raise_for_status()
        print(req)
        # with open(f, 'wb') as file:
        #     file.write(req.content)
    except requests.exceptions.HTTPError as http:
        print(http)
        return http.response.status_code
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
        return 500
    return 200

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = []
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.append(proxy)
    PROXIES = proxies
    return proxies

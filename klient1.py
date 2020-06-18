from requests import *
import json
import datetime
import hashlib
import os

BASE = 'http://127.0.0.1:8080'

def httpdate(dt):
    """Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    The supplied date must be in UTC.

    """
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"][dt.month - 1]
    return bytes(json.dumps('%s, %02d %s %04d %02d:%02d:%02d GMT' % (weekday, dt.day, month,
        dt.year, dt.hour, dt.minute, dt.second)), 'utf-8')

# start session
ans = get(BASE+'/hello')

req = None

while not (ans.status_code==202 and ans.reason=='It works!'):
    if ans.text=='What time is it?':
        req = lambda: request('GIVE',BASE+'/time', data=httpdate(datetime.utctime()), stream=True)
    elif ans.status_code==500:
        req=req
    elif ans.status_code==303:
        req = lambda: get(BASE+'/hello', stream=True)
    elif ans.status_code==202:
        req = lambda: post(BASE+'/hello', stream=True)
    elif ans.text==None or ans.text=='':
        req = lambda: post(BASE+'/tell', data=b'Chill down, please!', stream=True)
    elif ans.status_code==418:
        req = lambda: patch(BASE+'/tea', data={'type':'mate','cups':1}, stream=True)
    elif ans.headers.get('content-type')=='application/octet-stream':
        if 'crypto-key' in ans.headers:
            key = int(ans.headers['crypto-key'])
            data = bytearray()
            resp = True
            while resp:
                resp = ans.raw.read(1)
                data.append(bytes([resp^key]))
            req = lambda: post(BASE+'/push', data=data, stream=True)
        else:
            hasher = hashlib.sha256()
            resp = True
            while resp:
                resp = ans.raw.read(1024)
                hasher.update(resp)
            req = lambda: post(BASE+'/push', data=hasher.digest(), stream=True)
    elif isinstance(ans.json(), list):
        l = ans.json()
        req = lambda: put(BASE+'/mean', data=bytes(json.dumps(sum(l)/len(l)), 'utf-8'), stream=True)
    elif ans.json()==None:
        req = lambda: delete(BASE+'/'+ans.headers['agent'], stream=True)
    elif 'type' in ans.json():
        if ans.json()['type']=='library':
            post(BASE+'/tell', data=open(ans.json()['name'], 'rb'), stream=True)
        elif ans.json()['type']=='tell_me':
            post(BASE+'/tell', data=bytes(os.environ['name'],'utf-8'), stream=True)
    ans = req()

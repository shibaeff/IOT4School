import fakeredis
import time
import json
import pygal
import datetime
from score import *

temp_scorer = TempScorer()
co2_scorer = Co2Scorer()
light_scorer = LightScorer()
humidity_scorer = HumidityScorer()


from werkzeug.wrappers import Response
from flask import Flask, request

# initialize app and our cache (it'll go away after the app stops running)
app = Flask(__name__)
app.config['DEBUG'] = True
redises = {
    "nfc": fakeredis.FakeStrictRedis(0),
    "temp": fakeredis.FakeStrictRedis(1),
    "light": fakeredis.FakeStrictRedis(3),
    "humidity": fakeredis.FakeStrictRedis(4),
    "co2": fakeredis.FakeStrictRedis(5)
}

scorers = {
    "temp": temp_scorer,
    "light": light_scorer,
    "humidity": humidity_scorer,
    "co2": co2_scorer
}

scores = {
    "nfc": 0,
    "temp": 0,
    "light": 0,
    "humidity": 0,
    "co2": 0
}
temps_redis_store = fakeredis.FakeStrictRedis(0)
nfc_redis_store = fakeredis.FakeStrictRedis(0)


# def get_temp():
#lala
#     temps = []
#     times = sorted([float(g.decode('utf-8')) for g in temps_redis_store.keys()])
#     for k in times:
#         temps.append(float(temps_redis_store.get(k).decode('utf-8')))
#     title = "Temperature History"
#     bar_chart = pygal.Bar(width=1200, height=600,
#                           explicit_size=True, title=title)
#     times = [datetime.datetime.fromtimestamp(g).strftime('%Y-%m-%d %H:%M:%S') for g in times]
#     bar_chart.x_labels = times
#     bar_chart.add('Temps in F', temps)
#     html = """
#         <html>
#              <head>
#                   <title>%s</title>
#              </head>
#               <body>
#                  %s
#              </body>
#         </html>
#         """ % (title, bar_chart.render())
#     return html

@app.route('/', methods=['GET'])
def get_temp():
    temps = [0]
    times = sorted([float(g.decode('utf-8')) for g in temps_redis_store.keys()])
    for k in times:
        temps.append(float(temps_redis_store.get(k).decode('utf-8')))
    return "Current temperature is %d" % (temps[-1]), 200

def generate():
        return "Принято"

@app.route('/api/dev/<device>', methods=['POST'])
def dev(device):
    
    return Response(generate(), mimetype='text/html')


@app.route('/api/score', methods=['GET'])
def get_score():
    return sum([s ** 2 for s in scores.values()]) ** 0.5

from math import log 

def temp_conv(thermoPin):
    voltage = float(thermoPin) * 5.0 / 1023.0
    r1 = voltage / (5.0 - voltage)
    return  1.0 / ( 1.0 / (4300.0) * log(r1) + 1.0 / (25.0 + 273.0) ) - 273.0



# curl -H "Content-Type: application/json" -X POST -d '{"temp":72}' http://127.0.0.1:5000/api/v1/temp
@app.route('/api/v1/<resource>', methods=['POST', 'GET'])
def post_temp(resource):
    redis = redises[resource]
    if request.method == 'POST':
        data = json.loads(request.data.decode())
       
        if resource in data.keys():
            value = 0
            if resource == 'temp':
                value = temp_conv(data[resource])
                assert (value < 100)
            else:
                value = float(data[resource])
            if resource in scorers:
                scores[resource] += scorers[resource].score(value)
                scores[resource] /= 2
        
            redis.set(time.time(), value)
            return Response(status=200)
        return Response(status=400)
    if request.method == 'GET':
        temps = [0]
        times = sorted([float(g.decode('utf-8')) for g in redis.keys()])
        for k in times:
            temps.append(redis.get(k).decode('utf-8'))
        if resource == 'temp' and float(temps[-1]) > 100.0:
            return (str(temp_conv(temps[-1])), 200)
        return (str(temps[-1]), 200)
        


if __name__ == '__main__':
    app.run()

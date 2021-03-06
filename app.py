import fakeredis
import time
import json
import pygal
import datetime
from score import *
import logging
from logging.handlers import RotatingFileHandler
import numpy as np

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
    "temp": 0,
    "light": 0,
    "humidity": 0,
    "co2": 0
}


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
        return "ok"

temp_const = None
@app.route('/api/dev')
def dev():
    app.logger.warn("Got request from the client")
    global temp_const
    temp_const = 22
    return generate(), 200

red_quants = 0
def manager():
    global red_quants
    if red_quants == 5:
        app.logger.warning("Encountered bad score. Toggling the parameters!")
        app.logger.warning("Parameters toggled!")
        red_quants = 0
    elif red_quants > 8:
        app.logger.error("Please, consider manual toggling")
        red_quants = 0

masses = {
    "temp": 1,
    "humidity": 0.5,
    "light":  0.7,
    "co2": 0.2
}

def check_score():
    global red_quants

    score = 0
    for item in scores.items():
        score += masses[item[0]] * item[1]
    score /= sum(list(masses.values()))
    score = int(score)

    if score <= 6:
        red_quants += 1
    manager()
    return score

@app.route('/api/score', methods=['GET'])
def get_score():
    score = check_score()
    return str(score), 200

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
            elif resource == 'light':
                # kostil
                rng = np.linspace(500, 600)
                value = rng[np.random.randint(0, len(rng))]
            else:
                value = float(data[resource])
            if resource in {"co2", "temp", "light", "humidity"}:
                scores[resource] = scorers[resource].score(value)
        
            redis.set(time.time(), value)
            score = check_score()
            return Response(status=200)
        return Response(status=400)
    if request.method == 'GET':
        score = check_score()
        temps = [0]
        times = sorted([float(g.decode('utf-8')) for g in redis.keys()])
        for k in times:
            temps.append(redis.get(k).decode('utf-8'))
        global temp_const
        if temp_const is not None and resource == 'temp':
            return ("%.1f" % (float(temp_const)), 200)
        if resource == 'temp' and float(temps[-1]) > 100.0:
            return (str(temp_conv(temps[-1])), 200)
        return ("%.1f" % (float(temps[-1])), 200)
        


if __name__ == '__main__':
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run()

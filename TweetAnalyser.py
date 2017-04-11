import json
from pprint import pprint
from sense_hat import SenseHat

sense = SenseHat()
blue = (0, 0, 255)
r = (255, 0, 0)

image = [
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r
]


normalstate = sense.show_message("HERMES", text_colour=r, scroll_speed=0.06, back_colour=[255, 255, 255])
badstate = image
thescores = []

with open('converted.json') as json_data:
    e = json.load(json_data)
    json_data.close()
    for x in e:
        actualtweets = {
            'scores': x['score']
        }
        thescores.append(actualtweets)

    for i in thescores:
        if i['score'] > 0.8:
            sense.set_pixel(badstate)
            print (i)
        else:
            sense.show_message("HERMES", text_colour=r, scroll_speed=0.06, back_colour=[255, 255, 255])





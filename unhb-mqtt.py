#!/usr/bin/python
import paho.mqtt.client as mqtt
import json
import time
import sys
import pyqrcode
from PIL import Image, ImageDraw, ImageFont
import cups
from matrix_client.client import MatrixClient

conn = cups.Connection()
printers = conn.getPrinters()


def padhexa(s):
    return '0x' + s[2:].zfill(4)


def create_qrcode(newcode,hexid):
    qrobj = pyqrcode.create(newcode)
    with open('test.png', 'wb') as f:
        qrobj.png(f, scale=10)
    bg = Image.open('bg.png')
    img = Image.open('test.png')
    width, height = img.size
    logo_size = 140
    logo = Image.open('unhb.png')
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))
    logo = logo.resize((xmax - xmin, ymax - ymin))
    img.paste(logo, (xmin, ymin, xmax, ymax))
    fnt = ImageFont.truetype('font.ttf', 28)
    d = ImageDraw.Draw(img)
    d.text((width / 2 - 55, height - 40), hexid, font=fnt)
    bg.paste(img, (205, 0, 615, 410))
    outimage = "./qrcodes/" + hexid + ".png"
    bg.save(outimage)
    print("qrcode erfolgreich generiert: " +newcode)
 #   conn.printFile("gk420d", outimage, "foo", {})


def get_lastkey():
    with open("/home/pi/lastkey.txt", "r") as lastkeyinfile:
        last_int = int(lastkeyinfile.read().rstrip(), 16)
    return lastkey


# Spaceapi definitions
space_status = "undefined"
# Test SilSon space_json = """{"api": "0.13","space": "UN-Hack-Bar","logo": "https://www.un-hack-bar.de/wp-content/uploads/2018/06/unhb_klein.png","url": "https://un-hack-bar.de","location": {"address": "Morgenstrasse 6, 59423 Unna, Germany","lon": 7.69172,"lat": 51.53575},"contact": {"email": "info@un-hack-bar.de","irc": "irc://irc.hackint.net/c3un","ml": "chaos-unna@lists.ctdo.de","twitter": "@un_hack_bar"},"state": {"open":  null,"lastchange": 23},"feeds":{"calendar":{"type":"ical","url":"https://www.un-hack-bar.de/events.ics"}},"issue_report_channels": ["email"],"ext_ccc": "chaostreff"}"""
space_json = """{"api": "0.13","space": "UN-Hack-Bar","logo": "https://www.un-hack-bar.de/wp-content/uploads/2018/06/unhb_klein.png","url": "https://un-hack-bar.de","location": {"address": "Morgenstrasse 6, 59423 Unna, Germany","lon": 7.69172,"lat": 51.53575},"contact": {"email": "info@un-hack-bar.de","irc": "irc://irc.hackint.net/c3un","ml": "chaos-unna@lists.ctdo.de","twitter": "@un_hack_bar"},"state": {"open":  null,"lastchange": 23},"feeds":{"calendar":{"type":"ical","url":"https://www.un-hack-bar.de/events.ics"}},"issue_report_channels": ["email"],"ext_ccc": "chaostreff", "state": { "icon": { "open": "https://matrix.un-hack-bar.de/_matrix/media/v1/download/matrix.un-hack-bar.de/AwzcZPKZlaFCiDjJGrbmhVqy", "closed": "https://matrix.un-hack-bar.de/_matrix/media/v1/download/matrix.un-hack-bar.de/rYahEOVyPMKJDQfLSnKLeHmn" } } }"""
space_obj = json.loads(space_json)

# Matrix-Bot definitions
matrix_bot_user = "DaneelOlivaw"  # Bot's username
matrix_bot_passwd = "StefanTest123"  # Bot's password
matrix_server = "https://matrix.un-hack-bar.de"
matrix_roomid = "!qxbQFatOwXtPBXegqg:matrix.un-hack-bar.de"
matrix_open_json = {"url": "mxc://matrix.un-hack-bar.de/AwzcZPKZlaFCiDjJGrbmhVqy"}
matrix_closed_json = {"url": "mxc://matrix.un-hack-bar.de/rYahEOVyPMKJDQfLSnKLeHmn"}
matrix_unk_json = {"url": "mxc://matrix.un-hack-bar.de/SXmvTOGHLXRsYDCBQncTBhGl"}


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/UHB/#")


def spaceapi():
    print("funktion spaceapi go!")
    json.dumps(space_json)
    print(y["api"])
    write_file = open("spaceapi.json", "w")
    json.dump(space_json, write_file)
    print("file written")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #    print(msg.topic+" "+str(msg.payload))
    print("Received message '" + str(msg.payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
    if msg.topic == '/UHB/public/status':
        if msg.payload == "0":
            #            space_obj["state"] = {u'open': True,u'lastchange': time.time()}
            space_obj["state"]["open"] = True
            space_obj["state"]["lastchange"] = time.time()
            print(json.dumps(space_obj, sort_keys=True, indent=4))
            with open("spaceapi.json", "w") as write_file:
                json.dump(space_obj, write_file, sort_keys=True)
            matrix_room.send_state_event("m.room.avatar", matrix_open_json)
        elif msg.payload == "1":
            #            space_obj["state"] = {b'open': False,u'lastchange': time.time()}
            space_obj["state"]["open"] = False
            space_obj["state"]["lastchange"] = time.time()
            with open("spaceapi.json", "w") as write_file:
                json.dump(space_obj, write_file, sort_keys=True)
            print(json.dumps(space_obj, sort_keys=True, indent=4))
            matrix_room.send_state_event("m.room.avatar", matrix_closed_json)
    if msg.topic == '/UHB/label/create':
        new_keys = int(msg.payload)
        print("anzahl neu zu generierender label: " + str(new_keys))

        with open("lastkey.txt", "r") as infile:
            last_label_key = int(infile.read().rstrip(), 16)

        print("bisher generierte labels: " + str(last_label_key))

        print("letzte gedruckte label id: " + padhexa(hex(last_label_key)))
        nextkey = last_label_key + 1
        print("naechste freie label id: " + padhexa(hex(nextkey)))
        for i in range(nextkey, nextkey + new_keys):
            hexkey = padhexa(hex(i))
            urldings = "https://inv.unhb.de/" + hexkey
            create_qrcode(urldings, hexkey)
        with open("lastkey.txt", "w") as outfile:
            outfile.write(hexkey)


# Prepare MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

# Prepare Matrix Client
matrix_client = MatrixClient(matrix_server)
matrix_client.login_with_password_no_sync(matrix_bot_user, matrix_bot_passwd)
matrix_room = matrix_client.join_room(matrix_roomid)
matrix_room.send_state_event("m.room.avatar", matrix_unk_json)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

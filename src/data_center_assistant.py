#!/usr/bin/env python3

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

The Google Assistant Library can be installed with:
    env/bin/pip install google-assistant-library==0.0.2

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import subprocess
import sys

import aiy.assistant.auth_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

from slackclient import SlackClient
import os
import socket
import traceback
from time import sleep

slack_api_token = "UPDATE ME" #Get it form https://api.slack.com/custom-integrations/legacy-tokens


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def power_off_pi():
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi():
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

def say_ping(text):
    hostname = text.strip("ping").replace(" ", "")
    HOST_UP  = True if os.system("ping -c 1 " + hostname) is 0 else False
    if (HOST_UP == True):
        aiy.audio.say(hostname + " is up" )
    else:
        aiy.audio.say(hostname + " is down" )


def say_nslookup(text):
    hostname = text.strip("ping").replace(" ", "")
    try:
        IP  = socket.gethostbyname(hostname)
        aiy.audio.say("The IP address for " + hostname + " is " + IP)
    except:
        aiy.audio.say("IP Lookup failed")
        
def say_ping(text):
    hostname = text.strip("ping").replace(" ", "")
    HOST_UP  = True if os.system("ping -c 1 " + hostname) is 0 else False
    if (HOST_UP == True):
        aiy.audio.say(hostname + " is up" )
    else:
        aiy.audio.say(hostname + " is up" )

sc = None

def get_sc():
    global sc
    global slack_api_token
    if sc == None:
        sc = SlackClient(slack_api_token)
    return sc
        

def send_message(text):
    try:
        sc = get_sc()

        message = text.strip("send message")
 
        sc.api_call(
            "chat.postMessage",
            channel="#general",
            text=message,
            username="Data Center Assistant"
            )
        aiy.audio.say("Message sent")

    except:
        aiy.audio.say("Could not send message to slack")
        traceback.print_exc()
    

keep_reading = True
def read_message():
    global keep_reading
    try:
        sc = get_sc()
        if sc.rtm_connect():
            aiy.audio.say("Reading messages from all channel")
            while keep_reading:
                event = sc.rtm_read()
                try:
                     if not event ==[]:
                         if event[0]["type"]=="message":
                             # prevents endless loop of replying to itself
                             user = event[0]["user"] # not good enough for speech
                             channel = event[0]["channel"] # not good enough for speech
                             message = event[0]["text"]

                             #TODO aiy.audio.say(user + channel + message)
                             
                             aiy.audio.say("Someone said " + message)
                except:
                    traceback.print_exc()
                    aiy.audio.say("Could not read messsage")
                sleep(.3)
    except:
        
        aiy.audio.say("Couldn't connect to slack")
        

def process_event(assistant, event):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')

    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        print('You said:', event.args['text'])
        text = event.args['text'].lower()
        if text == 'power off':
            assistant.stop_conversation()
            power_off_pi()
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()
        elif text.startswith('ping'):
            assistant.stop_conversation()
            say_ping(text)
        elif text.startswith('nslookup'):
            assistant.stop_conversation()
            say_nslookup(text)
        elif text.startswith('send message'):
            assistant.stop_conversation()
            send_message(text)
        elif text.startswith('read message'):
            assistant.stop_conversation()
            read_message()

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def main():
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        for event in assistant.start():
            process_event(assistant, event)


if __name__ == '__main__':
    main()

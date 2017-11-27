import smbus
import time
import os
import sys
import AWSIoTPythonSDK
sys.path.insert(0, os.path.dirname(AWSIoTPythonSDK.__file__))
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
from datetime import datetime

bus = smbus.SMBus(1)
address = 0x48

def getTemperature():
    temperature = bus.read_word_data(address, 0)
    integralCentigrade = temperature & 0xff
    fractionalCentigrade = (temperature & 0xff00) >> 12
    fullTemperature = integralCentigrade + 0.0625 * fractionalCentigrade
    print(fullTemperature)
    return fullTemperature



# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


# Read in command-line parameters
##parser = argparse.ArgumentParser()
##parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
##parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
##parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
##parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
##parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
##                    help="Use MQTT over WebSocket")
##parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
##                    help="Targeted client id")
##parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
##
##args = parser.parse_args()
##host = args.host
##rootCAPath = args.rootCAPath
##certificatePath = args.certificatePath
##privateKeyPath = args.privateKeyPath
##useWebsocket = args.useWebsocket
##clientId = args.clientId
##topic = args.topic

host = "a20v9qepl7xfji.iot.us-west-2.amazonaws.com"
rootCAPath = "/home/pi/IoT/samples/i2ctest/AWS/root-CA.crt"
certificatePath = "/home/pi/IoT/samples/i2ctest/AWS/btciot_rpi1.cert.pem"
privateKeyPath = "/home/pi/IoT/samples/i2ctest/AWS/btciot_rpi1.private.key"
useWebsocket = False
clientId = "btciot_rpi1"
topic = "temperature"

if useWebsocket and certificatePath and privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not useWebsocket and (not certificatePath or not privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, 443)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    strTemperature = str(getTemperature())
    myAWSIoTMQTTClient.publish(topic, '{"temperature": ' + strTemperature + "," +
                               '"date":' + '"' + str(datetime.now()) + '"' + 
                               "}", 1)
    myAWSIoTMQTTClient.publish("$aws/things/btciot_rpi1/shadow/update", '{"state" : {"reported" : {'
                               '"temperature" :' + strTemperature + ' } } }', 1)

    loopCount += 1
    time.sleep(5)

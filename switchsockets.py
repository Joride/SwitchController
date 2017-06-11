import socket
from Queue import Queue
from threading import Thread
import struct
import subprocess
import errno

kPortNumber = 82


 #             |   set/req     command  |
 # beginOfMes  |   0b0000      0000     |   endOfMessage
 # ------------|------------------------|-------------
 # 0b1000 0000 |   0b0001      1100     |   0b1100 0000  // set switch 4 to 1
 # 0b1000 0000 |   0b0001      0011     |   0b1100 0000  // set switch 3 to 0
 # 0b1000 0000 |   0b0001      1011     |   0b1100 0000  // set switch 3 to 1
 # 0b1000 0000 |   0b0001      1001     |   0b1100 0000  // set switch 1 to 1
 # 0b1000 0000 |   0b0001      1000     |   0b1100 0000  // set switch 0 to 1
 # 0b1000 0000 |   0b0011      0000     |   0b1100 0000  // request status

kBeginOfMessage  = 0b10000000
kEndOfMessage    = 0b11000000
kClientRequestStatusMessage = 0b00110000

# The least significant 4 bits indicate the
# values to be set on the switches:
# example: switch 1 on: 0b00010001
# example: switch 3 on: 0b00010100
# example: switch 2 and 4 on: 0b00011010
kClientModifyStatusMessage = 0b00010000

connections = []

def handleMessage(message, fileLikeObject):
    print "Message received:"

    for byte in message:
        print format(byte, '08b')

    messageByte = message[0]

    if (messageByte & kClientRequestStatusMessage) == kClientRequestStatusMessage:
        print "Client requested status"

        message = constructStatusMessage()
        sendMessage(connection, message)

    if (messageByte & kClientModifyStatusMessage) == kClientModifyStatusMessage:
        print "Client Requests Modification"

        valueMask = 0b00001000 # why? see the examples earlier in this file
        value = (valueMask & messageByte) >> 3
        valueString = "%s" % value

        indexMask = 0b00000111
        indexOfSwitch = messageByte & indexMask
        indexString = "%s" % indexOfSwitch

        print "index: %s; value: %s" % (indexString, valueString)
        subprocess.call(['gpio','write', indexString, valueString])

        sendStatusToAllConnections()

def constructStatusMessage():
    status = pinStatus()
    message = [kBeginOfMessage]
    message.append(status)
    message.append(kEndOfMessage)

    return message

def sendStatusToAllConnections():
    for aConnection in connections:
        bytes = constructStatusMessage()
        sendMessage(aConnection, bytes)

def sendMessage(connection = None, bytes = []):
    print "sendMessage: %s to: %s" % (bytes, connection)
    typeList = ''
    for index in range (0, len(bytes)):
        if index == 0:
            typeList += "B"
        else:
            typeList += " B"

    packer = struct.Struct(typeList)
    packed_data = packer.pack(*bytes)
    try:
        sent = connection.sendall(packed_data)
    except Exception as e:
        print "Exception while trying to send data: %s" % e
        closeAndRemoveConnection(connection)

def pinStatus():
    switchesValue = kClientRequestStatusMessage
    for index in range(0, 4):
        switchIndexStr = "%s" % index
        switchValue = subprocess.check_output(['gpio','read', switchIndexStr])
        bitShiftedValue = (int(switchValue) << index)
        switchesValue |=  bitShiftedValue

    return switchesValue

def closeAndRemoveConnection(connection):
    try:
        connection.shutdown(2)
        connection.close
        connections.remove(connection)
    except Exception as instance:
        # print type(instance)    # the exception instance
        # print instance.args     # arguments stored in .args
        # print instance          # __str__ logs args to be printed directly
        print "Unable to close a connection that returns not more data: %s" % (instance,)

def listenForBytes(connection, mock):
    fileLikeObject = connection.makefile('sb')

    while True:
        try:
            data = connection.recv(1024)
        except Exception as e:
            print "Exception while trying to receive data: %s" % e
            closeAndRemoveConnection(connection)
            break

        currentMessage = None

        if not data:
            print "%s has no more data, now considering it disconnected and closing the connection""" % (connection,)

            # maybe the connection did not actually disconnect
            # so we make sure it really is disconnected and in
            # this way the client knows we shut down
            closeAndRemoveConnection(connection)
            break

        else:
            # in this for loop, an array of bytes is build
            # that contains a message (by selecting out a pattern)
            currentMessage = []
            for byte in data:
                binaryByte  = ord(byte)
                if binaryByte == kBeginOfMessage:
                    # currentMessage = byte
                    print("")

                elif binaryByte == kEndOfMessage:
                    # currentMessage += byte
                    handleMessage(currentMessage, fileLikeObject)
                    currentMessage = []

                else:
                    if currentMessage !=  None:
                        currentMessage.append(binaryByte)
                    else:
                        print "Programming error: trying to appent a byte to the currentMessage, but there is no currentmessage yet."







##
##

## prepare the GPIO pins
subprocess.call(['gpio','mode', '0', 'out'])
subprocess.call(['gpio','mode', '1', 'out'])
subprocess.call(['gpio','mode', '2', 'out'])
subprocess.call(['gpio','mode', '3', 'out'])

# setup a socket to listen on port 82
try:
    socket = socket.socket()
    host = ""
    port = kPortNumber
    socket.bind((host, port))
    socket.listen(port)
    print "socket set up"
except Exception as instance:
    print "Unable to setup a listening socket: %s" % (instance,)
    exit("1")


# this will run forever until the the socket closes / client disconnects / error in socket occurs
while True:
    try:
        connection, addr = socket.accept()
        connections.append(connection)
        print "Got connection fom %s %s" % (connection, addr)
        worker = Thread(target=listenForBytes, args=(connection, None))
        worker.setDaemon(True)
        worker.start()

        message = constructStatusMessage()
        sendMessage(connection, message)

    except ValueError:
        print "ERROR IN MAIN WHILE-LOOP: ", ValueError
        print "Now shutting down socket and closing it."

        # The constants SHUT_RD, SHUT_WR, SHUT_RDWR have the values 0, 1, 2,
        # respectively, and are defined in <sys/socket.h> since glibc-2.1.91.
        socket.shutdown(2)
        socket.close
        break

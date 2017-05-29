import socket
from Queue import Queue
from threading import Thread
from subprocess import call
import struct

kBeginOfMessage  = 0b10000000
kEndOfMessage    = 0b11000000

def handleMessage(message, fileLikeObject):
    for byte in message:
        print "byte: ", ord(byte)

    if ord(message[1]) == 0b00000001:
        # turn on the lights
        print "LIGHTS ON"
        call(['gpio','write', '0', '1'])

    if ord(message[1]) == 0b00000000:
        # turn off the lights
        print "LIGHTS OFF"
        call(['gpio','write', 'X', '0'])

def listenForBytes(connection, mock):
    fileLikeObject = connection.makefile('sb')

    while True:
        data = connection.recv(1024)
        currentMessage = None

        if not data:
            print "%s has no more data, now considering it disconnected and closing the connection""" % (connection,)

            # maybe the connection did not actually disconnect
            # so we make sure it really is disconnected and in
            # this way the client knows we shut down
            try:
                connection.shutdown(2)
                connection.close
            except Exception as instance:
                # print type(instance)    # the exception instance
                # print instance.args     # arguments stored in .args
                # print instance          # __str__ logs args to be printed directly
                print "Unable to close a connection that returns not more data: %s" % (instance,)

            break

        else:
            # in this for loop, an array of bytes is build
            # that contains a message (by selecting out a pattern)
            for byte in data:
                binaryByte  = ord(byte)
                if binaryByte == kBeginOfMessage:
                    currentMessage = byte

                elif binaryByte == kEndOfMessage:
                    currentMessage += byte
                    handleMessage(currentMessage, fileLikeObject)
                    currentMessage = []

                else:
                    if currentMessage !=  None:
                        currentMessage += byte
                    else:
                        print "Programming error: trying to appent a byte to the currentMessage, but there is no currentmessage yet."







##
##

## prepare the GPIO pins
call(['gpio','mode', '0', 'out'])
call(['gpio','mode', '1', 'out'])
call(['gpio','mode', '2', 'out'])
call(['gpio','mode', '3', 'out'])

# setup a socket to listen on port 82
try:
    socket = socket.socket()
    host = ""
    port = 84
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
        worker = Thread(target=listenForBytes, args=(connection, None))
        worker.setDaemon(True)
        worker.start()

        pin0Value = call(['gpio','read', '0'])

        print "pin0Value %s" % pin0Value

        values = (kBeginOfMessage, pin0Value, kEndOfMessage)
        packer = struct.Struct('B B B')
        packed_data = packer.pack(*values)

        sent = connection.sendall(packed_data)

        print "Got connection fom %s %s" % (connection, addr)

    except ValueError:
        print "ERROR IN MAIN WHILE LOOP: ", ValueError
        print "Now shutting down socket and closing it."

        # The constants SHUT_RD, SHUT_WR, SHUT_RDWR have the values 0, 1, 2,
        # respectively, and are defined in <sys/socket.h> since glibc-2.1.91.
        socket.shutdown(2)
        socket.close
        break

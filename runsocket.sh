#!/bin/bash

sudo python switchsockets.py &

# save the PID in a file
echo $! > multisocketID.sockID

echo "processID = $!"

#!/bin/bash

SCRIPTPATH=`dirname "${BASH_SOURCE[0]}"`
cd $SCRIPTPATH

if hash python2 2>/dev/null; then
    sudo python2 launcher/start.py
else
    sudo python launcher/start.py
fi

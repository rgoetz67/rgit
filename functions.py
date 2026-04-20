#!/usr/bin/env python3
# File: functions.py
# Time-stamp: <>
# $Id: $
#
# Copyright (C) 2026 by LemnaTec GmbH
#
# Author: goetz
#
# Description: 
#
# cython: language_level=3

import sys
import os
import re
from math import *
# If started as program change stdout to liner buffering
if __name__ == '__main__':
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
import json


def configPath():
    if sys.platform == "win32":
        if "HOME" in os.environ:
            confPath = os.environ["HOME"]+"\\.rgit\\config"
            credPath = os.environ["HOME"]+"\\.rgit\\creds"
        elif "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
            confPath = os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]+"\\.rgit\\config"
            credPath = os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]+"\\.rgit\\creds"
        else:
            confPath = ".rgit\\config"
            credPath = ".rgit\\creds"
    else:
        confPath = os.environ["HOME"]+"/.rgit/config"
        credPath = os.environ["HOME"]+"/.rgit/creds"
    return confPath, credPath
        
def loadSettings():
    confPath, credPath = configPath()
    
    config = {}
    creds  = {}
    if os.path.exists(confPath):
        with open(confPath) as inp:
            config = json.load(inp)
    if os.path.exists(credPath):
        with open(credPath) as inp:
            creds = json.load(inp)
    return config, creds


def saveSettings(conf=None, creds=None):
    confPath, credPath = configPath()

    if not os.path.exists(os.path.dirname(confPath)):
        os.makedirs(os.path.dirname(confPath))

    if conf is not None:
        if os.path.exists(os.path.dirname(confPath)):
            with open(confPath, "w") as out:
                json.dump(conf, out, indent=4)
    if creds is not None:
        if os.path.exists(os.path.dirname(credPath)):
            with open(credPath, "w") as out:
                json.dump(creds, out, indent=4)
            



def centerWindow(win, bySizeHint=False, ref=None):
    if ref is None:
        ref = getMainWindow()

    if bySizeHint:
        ww = win.sizeHint().width()
        wh = win.sizeHint().height()
    else:
        ww   = win.width()
        wh   = win.height()
    print(" $$ CW:" , ref)
    if ref is not None:
        x = ref.pos().x() + (ref.width() >>1)  - (ww>>1)
        y = ref.pos().y() + (ref.height() >>1) - (wh>>1)
        print(" $$ CW:" , ref, ww, wh, x, y)
        win.move(x,y)



def getMainWindow():
    win = QApplication.activeWindow()
    if isinstance(win, QMainWindow):
        return win
    for w in QApplication.allWidgets():
        if "ExperimentAnalysisManger" in str(w) and isinstance(w, QMainWindow):
            return w
    return None



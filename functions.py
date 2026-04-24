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
baseDir       = re.sub(r"\\", "/", os.path.dirname(os.path.abspath(__file__)))
arrowImg      = "%s/icons/arrowDown.png" % baseDir
checkOnImg    = "%s/icons/checkBoxCheck.png" % baseDir
checkInterImg = "%s/icons/checkBoxInter.png" % baseDir
checkOffImg   = "%s/icons/checkBoxUncheck.png" % baseDir
# print("???", checkOnImg, os.path.exists(checkOnImg) )
baseStyle  = "QTreeWidget {font-size:14px;border: 1px solid black; font-size:14px}\n"
baseStyle += "QTreeView {selection-background-color:#3DAEE9; selection-color :white; background-color:white; border:1px solid #00AA00; border-radius:2px; font-size:14px}\n"
baseStyle += "QTreeView::item:selected {background-color: #88BBFF; color:#000000}\n"
baseStyle += "QTreeView::item:hover {background-color: #CCf8ff; color:#000000}\n"
baseStyle += "QListView::item:selected { background-color: #0088FF;}\n"
baseStyle += "QComboBox  { font-size:14px;background-color: white; border:1px solid #00AA00; border-radius:2px ; padding:2px; font-size:14px}\n"
baseStyle += "QComboBox::down-arrow { image: url('%s')}\n" %(arrowImg)
baseStyle += "QComboBox::drop-down {border:0px;}\n"
baseStyle += "QMenu  { font-size:16px}\n"
baseStyle += "QLabel { font-size:14px}\n"
baseStyle += "QHeaderView::section  {border: 0px solid white;border-right: 1px solid #cbe0c4; border-bottom: 1px solid #448800; background-color:#F9FFF7; font-size:14px; font-weight:bold; padding-left:8px; font-size:14px}\n"
baseStyle += "QToolButton {background-color:#FFFFFF; border:1px solid #00AA00; border-radius:2px}\n"
baseStyle += "QToolButton::disabled {border:1px solid #AABBAA; border-radius:2px}\n"
baseStyle += "QMainWindow {background-color:#FFFDFA;}\n"
baseStyle += "QPushButton {background-color:#FFFFFF; border:1px solid #00AA00; border-radius:2px; padding:2px 8px 2px 8px; font-size:14px}\n"
baseStyle += "QPlainTextEdit{background-color:#FFFFFF; border:1px solid #00AA00; border-radius:2px; font-size:14px}\n"
baseStyle += "QCheckBox{font-size:14px; background-color:white; font-weight:bold}\n"
baseStyle += "QCheckBox::indicator {border: 1px solid #000000; border-radius:2px; margin-left:1px;margin-bottom:1px;  height:15px; width:15px;}"
baseStyle += "QCheckBox::indicator:checked {  border: 1px solid black; image: url('%s'); height:15px; width:15px;}\n" %checkOnImg
baseStyle += "QCheckBox::indicator:indeterminate {  border: 1px solid black; image: url('%s'); height:15px; width:15px; }\n" %checkInterImg
baseStyle += "QMessageBox {font-weight:bold; font-size:16px; min-width:640px; width:640px; color:green}\n"
baseStyle += "\n"
baseStyle += "\n"
baseStyle += "\n"

splitterStyle  = "QSplitter:handle:horizontal { background-color:#CCE8AA; border:0px solid #CCE8AA;  margin:0 1px 0 1px; width:10px;}\n"
splitterStyle += "QSplitter:handle:vertical { background-color:#FFE8AA; border:0px solid #FFE8AA;  margin:0 1px 0 1px; }\n"
splitterStyle += "QSplitter:handle:pressed {background-color:#44AA00; border:0px solid #44AA00;}"
splitterStyle += "QSplitter:handle:hover {background-color:#44AA00; border:0px solid #44AA00;}"
# splitterStyle = "QSplitter:handle:horizontal { background-color:#00BB00; border:2px solid #00BB00; ); margin:0 4px 0 4px;}\n"
# splitterStyle += "QSplitter:handle:vertical { background-color:#00BB00; border:1px solid #0000FF; ); margin:0 4px 0 4px;}\n"
#splitterStyle +=  "QSplitter:handle:pressed {background-color:#00DD00; border:1px solid #00DD00;}"
#splitterStyle +=  "QSplitter:handle:hover {background-color:#88DD88; border:1px solid #88DD88;}"

# bsseStyle += splitterStyle
timFormat = "%Y-%m-%d %H:%M:%S"



def rgitBasePath():
    if sys.platform == "win32":
        if "HOME" in os.environ:
            rgitPath = os.environ["HOME"]+"\\.rgit"

        elif "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
            rgitPath = os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]+"\\.rgit"
        else:
            rgitPath = ".rgit"
    else:
        rgitPath = os.environ["HOME"]+"/.rgit"
    return rgitPath


def globalTmpPath():
    if sys.platform == "win32":
        rgitPath = rgitBasePath()
        tmpPath = rgitPath+"\\tmp"
        if not os.path.exists(tmpPath):
            os.makedirs(tmpPath)
    else:
        tmpPath = "/tmp"
    return tmpPath 
    

def configPath():
    
    if sys.platform == "win32":
        rgitPath = rgitBasePath()
        confPath = rgitPath+"\\config"
        credPath = rgitPath+"\\creds"
    else:
        rgitPath = rgitBasePath()
        confPath = rgitPath+"/config"
        credPath = rgitPath+"/creds"
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
    # print(" $$ CW:" , ref)
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



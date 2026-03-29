#!/usr/bin/env python3
# File: training.py
# Time-stamp: <23-Nov-2025 11:34:05 goetz>
# $Id: $
#
# Copyright (C) 2021 by LemnaTec GmbH
#
# Author: Ruediger Goetz
#
# Description: 
#
import sys
import os
import re
import time
from math import *
# If started as program change stdout to liner buffering
import psutil
if __name__ == '__main__' and not  psutil.WINDOWS:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
import time
import signal
from PySide2.QtWidgets import *
from PySide2.QtCore    import *


class MainWindow(QMainWindow):
    
    def __init__(self, arg1, arg2):
        super().__init__()

        self.initUI()
        QShortcut(QKeySequence("Alt+q"), self, self.done)


    def initUI(self):
        self.main = QFrame()               # Hauptframe im Mainwindow
        self.gbox = QGridLayout()          # grid layout
        self.main.setLayout(self.gbox)     # der Hauptframe verwendet das GriLayout
        self.gbox.setSpacing(4)            #   Platz zwischen den Elementen
        self.setContentsMargins(0,0,0,0)   # Platz aussen drumherrum
        
        self.setCentralWidget(self.main)   # set den Hauptframe ins MainWidnow

        self.navi = self.navigationFrame()
        self.hideBtn  = QPushButton("Hide")
        self.addBtn   = QPushButton("Add")
        self.buttonO3 = QPushButton("Button O3")
        self.checkBox = QCheckBox("ausgeblendet")

        
        self.gbox.addWidget(self.navi,   1, 1, 2, 1)
        self.gbox.addWidget(hideBtn,     1, 2, 1, 1)
        self.gbox.addWidget(addBtn,      1, 3, 1, 1)
        self.gbox.addWidget(buttonO3,    1, 4, 1, 1)
        self.gbox.addWidget(checkBox,    1, 5, 1, 1)

        self.gbox.setColumnStretch(1, 0)
        self.gbox.setColumnStretch(2, 0)
        self.gbox.setColumnStretch(3, 0)
        self.gbox.setColumnStretch(4, 0)
        self.gbox.setColumnStretch(5, 0)
        self.gbox.setColumnStretch(6,10)

        self.gbox.setRowStretch(1, 0)
        self.gbox.setRowStretch(2, 1)



        self.hideBtn.clicked.connect(self.hideObject)
        self.checkBox.checkStateChanged.connect(self.toogleHide)
        
        


    # Frame mit der linken Navigation
    def navigationFrame(self):
        f = QFrame()
        self.vbox = QHBoxLayout()
        f.setLayout(self.hbox)

        self.buttonN1 = QPushButton ("ButtonN1")
        self.buttonN2 = QPushButton ("ButtonN2")
        self.buttonN3 = QPushButton ("ButtonN3")
        self.buttonN4 = QPushButton ("ButtonN4")
        self.buttonN5 = QPushButton ("Exit")
        self.descr   = QLabel("")

        self.button1.setMinimumWidth(60)
        self.button2.setMinimumWidth(60)
        self.button3.setMinimumWidth(40)
        self.button4.setMinimumWidth(40)
        self.button5.setMinimumWidth(60)
        self.descr.setMinimumWidth(80)


        ##                                |- Stretch-factor (optional)
        ##                                V  V-- Alignment (optional)
        self.hbox.addWidget(self.buttonN1, 0, Qt.AlignLeft)
        self.hbox.addWidget(self.buttonN2, 0, Qt.AlignLeft)
        self.hbox.addWidget(self.buttonN3, 0, Qt.AlignRight)
        self.hbox.addWidget(self.buttonN4, 0, Qt.AlignHCenter)
        self.hbox.addWidget(self.buttonN5, 0, Qt.AlignLeft)
        self.hbox.addWidget(self.descr,   1)


        self.buttonN1.clicked.connect(self.actionN1)
        self.buttonN2.clicked.connect(self.actionN2)
        self.buttonN3.clicked.connect(self.actionN3)
        self.buttonN4.clicked.connect(self.actionN4)
        self.buttonN5.clicked.connect(self.actionN5)

        return f



    def actionN1(self, _state):
        self.descr("Button 1 wurde gedrückt.\n Und hier könnte stehen, was das bedeutet.")


    def actionN2(self, _state):
        self.descr("Button 2 wurde gedrückt.\n Und hier könnte stehen, was das bedeutet.\n Au-erdem, aktiviert er Button N3 und N4.")
        if self.buttonN3.isEnabled():
            self.self.buttonN3.setEnabled(False)
            self.self.buttonN4.setEnabled(False)
        else:
            self.self.buttonN3.setEnabled(True)
            self.self.buttonN4.setEnabled(True)


    def actionN3(self, _state):
        self.descr("Button 3 wurde gedrückt.\n Und hier könnte stehen, was der Unter button N3 macht.")


    def actionN4(self, _state):
        self.descr("Button 4 wurde gedrückt.\n Und hier könnte stehen, was der Unter button N4 beweirkt.")


    def actionN5(self, _state):
        ret = QMessageBox.question("icherheitsabfrage", "Wirklich beeenden?", ["Ja","Nein"])
        if ret == 0:
            self.close()




    def hideObject(self):
        pass

    def toogleHide(self):
        pass



 
if __name__ == '__main__':

    arg1 = "iregndwas"
    arg2 = "iregndwas"
    app  = QApplication(sys.argv)
    win  = MainWindow(arg1, arg2)
    win.setWindowTitle("Cluster Assignment")
    signal.signal(signal.SIGINT, win.done)



    
    ret = app.exec_()
    sys.exit(ret)

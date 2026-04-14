#!/usr/bin/env python3
# File: browser.py
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
    
import datetime

from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *
from PySide6.QtPrintSupport import QPrinter

from functions import centerWindow

class OpenRepositoryDialog(QFrame):
    openRepository = Signal(str, str)
    def __init__(self, pwin):
        super().__init__()
        self.pwin =pwin
        self.selectedRepo = None
        
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)
        
        self.tab = QTabWidget()
        self.tab.addTab(self.bookmarkFrame(),   "Bookmarks")
        self.tab.addTab(self.localRepoFrame(),  "Local Repository")
        self.tab.addTab(self.remoteRepoFrame(), "Remote Repository")

        self.cancelBtn = QPushButton("Cancel")
        self.openBtn   = QPushButton("Open Repository")
        self.gbox.addWidget( self.tab,       1, 1, 1, 3)
        self.gbox.addWidget( self.cancelBtn, 2, 1, 1, 1)
        self.gbox.addWidget( self.openBtn,   2, 3, 1, 1)
        self.gbox.setColumnStretch(1,0)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setColumnStretch(3,0)
           
        self.setMinimumSize(640, 400)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.openBtn.clicked.connect(self.openRepo)
        self.cancelBtn.clicked.connect(self.close)
        self.show()
        centerWindow(self, ref=self.pwin)


        
    def bookmarkFrame(self):
        f =QFrame()
        self.bbox  = QGridLayout()
        f.setLayout(self.bbox)

        return f


    def localRepoFrame(self):
        f =QFrame()
        self.lbox  = QGridLayout()
        f.setLayout(self.lbox)

        return f


    def remoteRepoFrame(self):
        f =QFrame()
        self.rbox  = QGridLayout()
        f.setLayout(self.rbox)

        l = QLabel ("URL of remote repository: ")
        self.repoUrl = QLineEdit("ssh://git@git.lemna.lemnatec.de:2222/goetz/LemnaGridNeXt.git")
        self.checkRepo = QPushButton("Check")
        self.checkRepo.setEnabled(False)

        self.rbox.addWidget(l,              2, 1, 1, 1)
        self.rbox.addWidget(self.repoUrl,   2, 2, 1, 1)
        self.rbox.addWidget(self.checkRepo, 2, 3, 1, 1)
        self.rbox.setColumnStretch(1,0)
        self.rbox.setColumnStretch(2,1)
        self.rbox.setColumnStretch(3,0)
        self.rbox.setRowStretch(1,1)
        self.rbox.setRowStretch(2,0)
        self.rbox.setRowStretch(3,99)
        return f


    def openRepo(self):
        print(self.tab.tabText(self.tab.currentIndex()), self.tab.currentIndex())
        if self.tab.currentIndex() == 2:
            self.openRepository.emit("remote", self.repoUrl.text())
        self.close()

    
    def quit(self):
        self.close()
        self.pwin.close()

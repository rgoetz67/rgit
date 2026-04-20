#!/usr/bin/env python3
# File: browser.py
# Time-stamp: <19-Apr-2026 17:39:25 goetz>
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


class EmbeddedFileDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        if sys.platform == "win32":
            self.setOptions(QFileDialog.DontUseNativeDialog)

        gbox = self.layout()
        for r in range( gbox.rowCount()):
            for c in range(gbox.columnCount()):
                item = gbox.itemAtPosition(r,c)
                idx  = gbox.indexOf(item)
                pos  = gbox.getItemPosition(idx)
                if isinstance(item.widget(), QDialogButtonBox):
                    item.widget().hide()
                    item2 = gbox.itemAtPosition(r,c-1)
                    idx  = gbox.indexOf(item2)
                    pos   = gbox.getItemPosition(idx)
                    # place it again update the UI
                    gbox.addWidget(item2.widget(), r, c, pos[2], pos[3])


class OpenRepositoryDialog(QFrame):
    openRepository = Signal(str, str )
    def __init__(self, pwin, creds):
        super().__init__()
        self.pwin  = pwin
        self.creds = creds
        self.selectedRepo = None
        
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)
        
        self.tab = QTabWidget()
        self.tab.addTab(self.bookmarkFrame(),   "Bookmarks")
        self.tab.addTab(self.localRepoFrame(),  "Local Repository")
        self.tab.addTab(self.remoteRepoFrame(), "Remote Repository")
        self.msg = QLabel("")
        self.msg.hide()
        self.msg.setStyleSheet("QLabel {font-size:14px; font-weight:bold}")
        self.cancelBtn = QPushButton("Cancel")
        self.openBtn   = QPushButton("Open Repository")
        self.gbox.addWidget( self.tab,       1, 1, 1, 3)
        self.gbox.addWidget( self.msg,       2, 1, 1, 3)
        self.gbox.addWidget( self.cancelBtn, 3, 1, 1, 1)
        self.gbox.addWidget( self.openBtn,   3, 3, 1, 1)
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

        self.bookmarks = QTreeWidget()
        self.bookmarks.setHeaderLabels(["Name", "Type", "Location"])
        for name, rp in self.pwin.config.get("bookmarks", {}).items():
            if isinstance(rp, dict):
                item = QTreeWidgetItem([name, "", ""])
                self.bookmarks.addTopLevelItem(item)
                self.__addBookmarks(item, rp)
            else:            
                item = QTreeWidgetItem([name, rp[0], rp[1]])
                self.bookmarks.addTopLevelItem(item)

        self.msgBM    = QLabel("")
        self.msgBM.setStyleSheet("QLabel {font-size:14px; font-weight:bold}")

        self.bbox.addWidget(self.bookmarks, 1,1,1,1)
        self.bbox.addWidget(self.msgBM,     2,1,1,1)
        self.bbox.setRowStretch(1,1)
        self.bbox.setRowStretch(2,0)
        self.bbox.setRowStretch(3,0)
        self.bookmarks.resizeColumnToContents(0)
        self.bookmarks.resizeColumnToContents(1)

        self.bookmarks.itemDoubleClicked.connect(self.openRepo)
        return f


    def __addBookmarks(self, parentItem, bookmarks):
        for name, rp in bookmarks.items():
            if isinstance(rp, dict):
                item = QTreeWidgetItem(parentItem, [name, "", ""])
                self.__addBookmarks(item, rp)
            else:            
                item = QTreeWidgetItem(parentItem,[name, rp[0], rp[1]])


    def localRepoFrame(self):
        f =QFrame()
        self.lbox  = QGridLayout()
        f.setLayout(self.lbox)


        self.select = EmbeddedFileDialog(self)
        self.select.setOption(QFileDialog.DontUseNativeDialog)
        self.select.setWindowFlags(Qt.Widget)
        self.select.setFileMode(QFileDialog.Directory)
        self.select.setAcceptMode(QFileDialog.AcceptOpen)
        self.lbox.addWidget(self.select, 1,1,1,1)
        
        return f


    def remoteRepoFrame(self):
        f =QFrame()
        self.rbox  = QGridLayout()
        f.setLayout(self.rbox)

        l = QLabel ("URL of remote repository: ")
        self.repoUrl = QLineEdit("")
        self.repoUrl.textChanged.connect(self.checkUrl1)
        self.lUser = QLabel("  Username : ")
        self.lPass = QLabel("  Password : ")
        self.user  = QLineEdit()
        self.pwd   = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.Password)
        iconPath = os.path.dirname(__file__) + "/icons/eye-solid-full.svg"
        self.pwdAction = self.pwd.addAction(QIcon(iconPath), QLineEdit.TrailingPosition)
        self.pwdAction.triggered.connect(self.showPassword)
        if "USER" in os.environ:
            self.user.setText(os.environ["USER"])
        
        self.remMsg = QLabel("")
        self.remMsg.setStyleSheet("QLabel {font-size:12px; font-weight:bold; color:red}")
        
        self.rbox.addWidget(l,              2, 1, 1, 1)
        self.rbox.addWidget(self.repoUrl,   2, 2, 1, 2)
        #   self.rbox.addWidget(self.checkRepo, 2, 3, 1, 1)
        self.rbox.addWidget(self.lUser,     3, 1, 1, 1)
        self.rbox.addWidget(self.user,      3, 2, 1, 2)
        self.rbox.addWidget(self.lPass,     4, 1, 1, 1)
        self.rbox.addWidget(self.pwd,       4, 2, 1, 2)

        self.rbox.addWidget(self.remMsg,    5, 1, 1, 3, Qt.AlignHCenter)
        self.rbox.setColumnStretch(1,0)
        self.rbox.setColumnStretch(2,1)
        self.rbox.setColumnStretch(3,0)
        self.rbox.setRowStretch(1,1)
        self.rbox.setRowStretch(2,0)
        self.rbox.setRowStretch(3, 0)
        self.rbox.setRowStretch(4, 0)
        self.rbox.setRowStretch(5, 0)
        self.rbox.setRowStretch(6,99)
        return f
    

    def checkUrl1(self, t):
        ml = []
        gitMsg =False
        if len(t)>4:
            if "@" in t:
                ml.append("Url looks like an ssh URL. This works only if you have a working ssh key at the remote side")
                gitMsg =True
        if len(t)>8:
            if not (t[:7] in ["https:/" , "http://"]) and not gitMsg:
                ml.append("Url looks like an ssh URL. This works only if you have a working ssh key at the remote side")
        if len(t)>16:
            if t[-4:] != ".git":
                ml.append("Url must end with '.git'")
        self.remMsg.clear()
        self.remMsg.setText("\n".join(ml))

        if t in self.creds:
            self.user.setText(self.creds[t][0])
            self.pwd.setText(self.creds[t][1])

            
    def showPassword(self):
        if self.pwd.echoMode() == QLineEdit.Password:
            self.pwd.setEchoMode(QLineEdit.Normal)
        else:
            self.pwd.setEchoMode(QLineEdit.Password)


    def setMessage4remoterepo(self, msg):
        self.remMsg.setText(msg)
        if self.tab.currentIndex() == 0:
            if self.newRepoType == "remote":
                self.repoUrl.setText(self.newRepoPath)
                if self.newRepoPath in self.creds:
                    auth = self.creds[self.newRepoPath]
                    self.user.setText(auth[0])
                    self.pwd.setText(auth[1])
                    self.tab.setCurrentIndex(2)
                    self.remMsg.setText(msg)
        

    def openRepo(self):
        #        print(self.tab.tabText(self.tab.currentIndex()), self.tab.currentIndex())
        if self.tab.currentIndex() == 2:
            self.msg.setText("Retrieve remote repository data")
            self.msg.show()
            self.creds[self.repoUrl.text()] =[self.user.text(), self.pwd.text()]
            QApplication.processEvents()
            self.openRepository.emit("remote", self.repoUrl.text())
        elif self.tab.currentIndex() == 1:
            sel =self.select.selectedFiles()
            if len(sel)>0:
                self.openRepository.emit("local",  sel[0])
            self.close()
        elif self.tab.currentIndex() == 0:
            selItems = self.bookmarks.selectedItems()
            if len(selItems)>0:
                self.newRepoType = selItems[0].text(1)
                self.newRepoPath = selItems[0].text(2)
                if self.newRepoType == "local":
                    os.chdir(self.newRepoPath)
                self.msgBM.setText("Retrieve remote repository data")
                QApplication.processEvents()
                self.openRepository.emit(self.newRepoType, self.newRepoPath)

    
    def quit(self):
        self.close()
        self.pwin.close()





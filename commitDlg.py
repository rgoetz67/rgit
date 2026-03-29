#!/usr/bin/env python3
# File: commitDlg.py
# Time-stamp: <29-Mar-2026 16:08:52 goetz>
# $Id: $
#
# Copyright (C) 2026 by LemnaTec GmbH
#
# Author: Ruediger Goetz
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




class CommitDialog(QFrame):

    def __init__(self, pwin, rgd, branch, files, push=True):
        super().__init__()
        self.pwin = pwin
        self.rgd  = rgd
        self.branch = branch
        self.diffBtn = {}
        self.revretBtn = {}
        self.revertBtn = {}
        self.initUI()
        self.fill(files)
        self.pushToRem.setChecked(push)
        print("      push = ", push)
        self.show()

    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)

        self.filesList = QTreeWidget()
        self.filesList.setMinimumSize(480,320)
        self.filesList.setColumnCount(3)
        self.filesList.setHeaderLabels(["FileName", "", ""])

        self.message = QPlainTextEdit()

        self.buttons   =self.buttonFrame()

        self.gbox.addWidget(self.message,   2,1,1, 2)
        self.gbox.addWidget(self.filesList, 1,1,1, 2)
        self.gbox.addWidget(self.buttons,   3,1,2, 2)

        self.gbox.setColumnStretch(1,1)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setRowStretch(1,1)
        self.gbox.setRowStretch(2,1)
        self.gbox.setRowStretch(3,0)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.setMinimumWidth(640)
        self.filesList.setMinimumHeight(320)
        self.message.setMinimumHeight(240)


    def buttonFrame(self):
        f = QFrame()
        self.hbox = QHBoxLayout()
        f.setLayout(self.hbox)

        self.cancelBtn = QPushButton("Cancel")
        self.commitBtn = QPushButton("Close")
        self.pushToRem = QCheckBox("Push To remote")
        self.cancelBtn.clicked.connect(self.close)
        self.hbox.addWidget(self.cancelBtn, 0, Qt.AlignLeft)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.pushToRem, 0, Qt.AlignLeft)
        self.hbox.addWidget(self.commitBtn, 0, Qt.AlignRight)
        return f

    
    def fill(self, files):
        print(">>>>>>", files)
        for f in files:
            item = QTreeWidgetItem([f, "", ""])
        #    item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        
            self.filesList.addTopLevelItem(item)
                
            self.diffBtn[f] = QPushButton("Diff Changes")
            self.diffBtn[f].clicked.connect(self.doDiff)
#            self.
            self.revertBtn[f] = QPushButton("Revert Changes")
            self.revertBtn[f].clicked.connect(self.doRevert)
            self.filesList.setItemWidget(item, 1, self.diffBtn[f])
            self.filesList.setItemWidget(item, 2, self.revertBtn[f])

        w = 0
        for c in range(1,3,1):
            self.filesList.resizeColumnToContents(c)
            w += self.filesList.columnWidth(c)
        self.filesList.setColumnWidth(0, self.width()-w-4)


    def doRevert(self):
        return


    def doDiff(self):
        for f in self.diffBtn:
            if self.diffBtn[f] == self.sender():
                print("diff prev:", f)
                e   = self.rgd.branchFiles[self.branch][f]
                eid = e["id"]
                commitId = self.rgd.blobPath[self.branch][eid]["firstCommit"][0]
                commit   = self.rgd.repo.get(commitId)
                prevBlobId = self.rgd.previousCommit(self.branch, f,
                                                     str(commit.id), commit.commit_time)
                self.rgd.doDiff(self.branch, eid, prevBlobId)
            
        return
        for eid in self.rb1:
            if self.rb1[eid].isChecked() :
                blobId1 = eid
                break
        for eid in self.rb2:
            if self.rb2[eid].isChecked():
                blobId2 = eid
                break
        if blobId1 != blobId2:
            self.rgd.doDiff(self.branch, blobId1, blobId2)


    def quit(self):
        self.close()
        self.pwin.close()

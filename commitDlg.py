#!/usr/bin/env python3
# File: commitDlg.py
# Time-stamp: <29-Mar-2026 16:52:23 goetz>
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


from data import GitCallbacks

class CommitDialog(QFrame):
    commitExecuted = Signal()
    
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
        self.commitBtn = QPushButton("Commit")
        self.pushToRem = QCheckBox("Push To remote")
        self.cancelBtn.clicked.connect(self.close)
        self.commitBtn.clicked.connect(self.doCommit)
        self.hbox.addWidget(self.cancelBtn, 0, Qt.AlignLeft)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.pushToRem, 0, Qt.AlignLeft)
        self.hbox.addWidget(self.commitBtn, 0, Qt.AlignRight)
        return f

    
    def fill(self, files):
        self.filesList.clear()
        self.diffBtn   = {}
        self.revertBtn = {}
        self.fileItems = {}
        for f in files:
            item = QTreeWidgetItem([f, "", ""])
        #    item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)
            print(">>>>>> ", item.flags())
#             item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            print(">>>>>> \t", item.flags(), Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
        
            self.filesList.addTopLevelItem(item)
                
            self.diffBtn[f] = QPushButton("Diff Changes")
            self.diffBtn[f].clicked.connect(self.doDiff)
            self.diffBtn[f].setMaximumWidth(100)
            self.revertBtn[f] = QPushButton("Revert Changes")
            self.revertBtn[f].clicked.connect(self.doRevert)
            self.revertBtn[f].setMaximumWidth(100)
            self.filesList.setItemWidget(item, 1, self.diffBtn[f])
            self.filesList.setItemWidget(item, 2, self.revertBtn[f])
            self.fileItems[f] = item
        self.filesList.setColumnWidth(1,100)
        self.filesList.setColumnWidth(2,100)
        self.filesList.setColumnWidth(0, self.width()-224)



    def doCommit(self):
        files = [ f for f in self.fileItems  if self.fileItems[f].checkState(0) == Qt.Checked]
        self.rgd.commitFiles(files, self.message.toPlainText(), self.pushToRem.isChecked())
        self.commitExecuted.emit()
        self.close()


    def doRevert(self):
        return


    def doDiff(self):
        for f in self.diffBtn:
            if self.diffBtn[f] == self.sender():
                print("diff prev:", f)
                e   = self.rgd.branchFiles[self.branch][f]
                eid = e["id"]
                commitId = self.rgd.getCommitOfBlob(self.branch, f, eid)
                commit   = self.rgd.repo.get(commitId)
                prevBlobId = self.rgd.previousCommit(self.branch, f,
                                                     str(commit.id), commit.commit_time)
                self.rgd.doDiff(self.branch, f, None, f, eid)
            
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

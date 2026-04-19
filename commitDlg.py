#!/usr/bin/env python3
# File: commitDlg.py
# Time-stamp: <19-Apr-2026 19:15:42 goetz>
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



import time
import datetime

from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *
from PySide6.QtPrintSupport import QPrinter


from data import GitCallbacks
from functions import centerWindow

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
        QApplication.processEvents()
        self.fill(files)
        self.pushToRem.setChecked(push)
        # print("      push = ", push)
        self.show()
        centerWindow(self, ref=self.pwin)


    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)

        self.lFiles    = QLabel("Files to be commited:")
        self.filesList = QTreeWidget()
        self.filesList.setMinimumSize(480,320)
        self.filesList.setColumnCount(3)
        self.filesList.setHeaderLabels(["FileName", "Status", "", ""])
        self.filesList.setSortingEnabled(True)


        self.lMessage  = QLabel("Commit Message:")
        self.message   = QPlainTextEdit()
        font = QFont("Liberation Mono")
        self.message.setFont(font)
        self.lMessage.setStyleSheet("QLabel {margin-top:4px}")
        self.comMsg    = QLabel("")
        self.comMsg.setStyleSheet("QLabel {font-weight:bold; font-size:16px}")
      # self.comMsg.hide()
        self.lPrev     = QLabel("Previous Messages:")
        self.prevMsg = QComboBox()
        self.prevMsg.addItem("", -1)
        for i, msg in enumerate(self.rgd.lastCommitMessages):
            line1 = msg.split("\n")[0]
            self.prevMsg.addItem(line1, i)
        self.prevMsg.currentIndexChanged.connect(self.copyMessage)
        self.buttons   = self.buttonFrame()

        self.gbox.addWidget(self.lFiles,    1,1,1, 3)
        self.gbox.addWidget(self.filesList, 2,1,1, 3)
        self.gbox.addWidget(self.comMsg ,   3,1,1, 3, Qt.AlignHCenter)
        self.gbox.addWidget(self.lMessage,  4,1,1, 3)
        self.gbox.addWidget(self.message,   5,1,1, 3)
        self.gbox.addWidget(self.lPrev  ,   6,1,1, 1)
        self.gbox.addWidget(self.prevMsg,   6,3,1, 1)
        self.gbox.addWidget(self.buttons,   7,1,1, 3)

        self.gbox.setColumnStretch(1,0)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setColumnStretch(3,0)
        self.gbox.setRowStretch(1,0)
        self.gbox.setRowStretch(2,1)
        self.gbox.setRowStretch(2,0)
        self.gbox.setRowStretch(4,0)
        self.gbox.setRowStretch(5,1)
        self.gbox.setRowStretch(6,0)
        self.gbox.setRowStretch(7,0)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.setMinimumWidth(640)
        self.filesList.setMinimumHeight(320)
        self.message.setMinimumHeight(240)
        self.message.setTabStopDistance( 56)  # 7 pixel per char seem to be corerct


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
            status = self.rgd.getFileStatus(self.branch, f)
            item   = QTreeWidgetItem([f, status, "", ""])
            item.setCheckState(0, Qt.Checked)
        
            self.filesList.addTopLevelItem(item)
                
            self.diffBtn[f] = QPushButton("Diff Changes")
            self.diffBtn[f].clicked.connect(self.doDiff)
            self.diffBtn[f].setMaximumWidth(100)
            self.revertBtn[f] = QPushButton("Revert Changes")
            self.revertBtn[f].clicked.connect(self.doRevert)
            self.revertBtn[f].setMaximumWidth(100)
            self.filesList.setItemWidget(item, 2, self.diffBtn[f])
            self.filesList.setItemWidget(item, 3, self.revertBtn[f])
            self.fileItems[f] = item
        self.filesList.setColumnWidth(1,100)
        self.filesList.setColumnWidth(2,100)
        self.filesList.setColumnWidth(3,100)
        self.filesList.setColumnWidth(0, self.width()-324)



    def copyMessage(self, idx):
        msgIndex = self.prevMsg.currentData()
        if msgIndex >=0:
            self.message.setPlainText(self.rgd.lastCommitMessages[msgIndex])
        else:
            self.message.clear()
#         print(" COPY ", msgIndex)
#         print(" COPY ", self.rgd.lastCommitMessages[msgIndex])

    def doCommit(self):
        files = []
        for f in self.fileItems:
            if self.fileItems[f].checkState(0) == Qt.Checked:
                files.append((f, self.fileItems[f].text(1)))
        if self.pushToRem.isChecked():
            self.comMsg.setText("Commit & Push in progress")
        else:
            self.comMsg.setText("Commit in progress")
        QApplication.processEvents()
        
        self.lFiles.setEnabled(False)  
        self.filesList.setEnabled(False)  
        self.lMessage.setEnabled(False)  
        self.message.setEnabled(False)   
        self.buttons.setEnabled(False)   

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
                commitId = self.rgd.getCommitOfBlob(eid, lastBefore=time.time())
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

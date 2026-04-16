#!/usr/bin/env python3
# File: training.py
# Time-stamp: <21-Mar-2026 17:38:30 goetz>
# $Id: $
#
# Copyright (C) 2021 by LemnaTec GmbH
#
# Author: Ruediger Goetz
#
# Description: 
#
# Implement self.showHistory UI
# Implement self.showBlame
# Implement self.doCommit
# Implement self.doRevert
#
# List of tags
#
# Context Menu of file and dir entries
# Branches List
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


import datetime

from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *
from PySide6.QtPrintSupport import QPrinter

from blame     import BlameDisplay
from functions import centerWindow


class CenteredRadioButton(QFrame):

    def __init__(self, text, buttonGroup=None):
        super().__init__()
        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)
        self.hbox.setContentsMargins(0,0,0,0)

        self.rb =QRadioButton(text)
        self.hbox.addWidget(self.rb, Qt.AlignHCenter)
        if buttonGroup is not None:
            buttonGroup.addButton(self.rb)


    def isChecked(self):
        return self.rb.isChecked()

    

class HistoryView(QFrame):

    def __init__(self, pwin):
        super().__init__()
        self.pwin =pwin
        self.rb1 = {}
        self.rb2 = {}
        self.bg1 = None
        self.bg2 = None
        self.diffBtn = {}
        self.blamBtn = {}
        self.initUI()
        centerWindow(self, ref=self.pwin)

    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)

        self.histList = QTreeWidget()
#        self.histList.setMinimumSize(1200,800)
        self.histList.setMinimumSize(960,640)
        self.histList.setColumnCount(10)
        self.histList.setHeaderLabels(["","", "Status", "Commit Hash", "Blob Hash", "Revision", "Author", "Last Change", "Branches", "Tags", "Commit Message"])

        self.message = QPlainTextEdit()


        self.filesList = QTreeWidget()
        self.filesList.setMinimumSize(480,320)
        self.filesList.setColumnCount(4)
        self.filesList.setHeaderLabels(["FileName", "Action", "", ""])

        self.buttons   =self.buttonFrame()

        self.gbox.addWidget(self.histList,  1,1,2, 1)
        self.gbox.addWidget(self.message,   1,2,1, 1)
        self.gbox.addWidget(self.filesList, 2,2,1, 1)
        self.gbox.addWidget(self.buttons,   3,1,2, 3)

        self.gbox.setColumnStretch(1,3)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setRowStretch(1,1)
        self.gbox.setRowStretch(2,1)
        self.gbox.setRowStretch(3,0)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.histList.itemClicked.connect(self.showCommit)
        self.diffPrvBtn.clicked.connect(self.doDiffPrev1)
        self.diffSelBtn.clicked.connect(self.doDiffSelected)
        self.blameCurBtn.clicked.connect(self.doBlameSelected)
        
    def sizeHint(self):
        return QSize(32,24)


    def buttonFrame(self):
        f = QFrame()
        self.hbox = QHBoxLayout()
        f.setLayout(self.hbox)

        self.diffSelBtn = QPushButton("Diff Selected")
        self.diffPrvBtn = QPushButton("Diff Previous")
        self.blameCurBtn = QPushButton("Blame")
        self.closeBtn   = QPushButton("Close")
        self.closeBtn.clicked.connect(self.close)
        self.hbox.addWidget(self.diffSelBtn,  0, Qt.AlignLeft)
        self.hbox.addWidget(self.diffPrvBtn,  0, Qt.AlignLeft)
        self.hbox.addWidget(self.blameCurBtn, 0, Qt.AlignLeft)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.closeBtn, 0, Qt.AlignRight)
        return f
    
        
    def fill(self, rgd,  filePath, branch):
        self.rgd      = rgd
        self.branch   = branch
        self.filePath = filePath
        self.histList.clear()
        self.message.clear()
        self.filesList.clear()
        self.rb1 = {}
        self.rb2 = {}
        self.bg1 = QButtonGroup()
        self.bg2 = QButtonGroup()
        self.blobHist = []
        self.blameWin = None
        self.commits  = sorted(rgd.repoFiles[filePath]["commits"], key = lambda c:-c[1])
        for commitId, commitTime, blobId, _ in self.commits:
            commit   = rgd.repo.get(commitId)
            entry    = rgd.repo.get(blobId)
            self.blobHist.append(blobId)
            timStr   = datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S")
            # status   = rgd.getFileStatus(blobId, filePath)
            #  status  = added, modifyied reanemd etc
            branches = rgd.getBranchesForPath(filePath)
            commitTime = datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S")
            cid  = str(commit.id)
            item = QTreeWidgetItem(["","", "updated", commit.short_id, entry.short_id,
                                    self.rgd.getVersionOfCommit(cid), commit.author.name ,
                                    commitTime, branches, ", ".join(self.rgd.getTagsForCommit(cid)),
                                    commit.message.split("\n")[0]])
            
            item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator);
            item.setData(0, Qt.UserRole , (commit, entry, filePath))
#            self.colorizeTreeItem(item, status)
            self.histList.addTopLevelItem(item)
            self.rb1[blobId] = CenteredRadioButton("", self.bg1)
            self.rb2[blobId] = CenteredRadioButton("", self.bg2)
            self.histList.setItemWidget(item, 0, self.rb1[blobId])
            self.histList.setItemWidget(item, 1, self.rb2[blobId])
        for c in range(2,10,1):
            self.histList.resizeColumnToContents(c)
        self.histList.setColumnWidth(0,36)   # extar space for the invisib;e expandion indicator
        self.histList.setColumnWidth(1,24)



    def showCommit(self,parentItem):
        commit = parentItem.data(0, Qt.UserRole)[0]
        entry  = parentItem.data(0, Qt.UserRole)[1]
        self.message.setPlainText(commit.message)

        self.currentCommitId = str(commit.id)
        self.prevCommit = {}
        self.diffBtn    = {}
        self.blamBtn    = {}
        self.fileItems  = {}
        
        newFiles = self.rgd.newFilesInCommit( str(commit.id))
        self.filesList.clear()
        for eid, path in newFiles:
            if not self.rgd.repoFiles[path]["isDir"]:
                item = QTreeWidgetItem([path, "updated"])
                item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator);
                prevBlobId = self.rgd.previousCommit(self.branch, self.filePath, str(commit.id),commit.commit_time)
#                 if prevBlobId is not None:
#                     item.setData(0, Qt.UserRole , (str(entry.id), prevBlobId))
                self.filesList.addTopLevelItem(item)
                
                self.diffBtn[eid] = QPushButton("Diff Previous")
                self.diffBtn[eid].clicked.connect(self.doDiffPrev2)
                self.diffBtn[eid].setMaximumWidth(100)
                self.blamBtn[eid] = QPushButton("Blame")
                self.blamBtn[eid].clicked.connect(self.doBlame)
                self.blamBtn[eid].setMaximumWidth(60)
                self.fileItems[eid] = item
                self.filesList.setItemWidget(item, 2, self.diffBtn[eid])
                self.filesList.setItemWidget(item, 3, self.blamBtn[eid])
                if prevBlobId is  None:
                    self.diffBtn[eid].setEnabled(False)
                else:
                    self.prevCommit[eid] = prevBlobId
        tw = 160
        self.filesList.resizeColumnToContents(1)
        tw += self.filesList.columnWidth(1)
        print("---->", self.filesList.width(), self.filesList.width() -24 -tw)
        self.filesList.setColumnWidth(0, self.filesList.width() -24 -tw)
        print("\t\t\t", 0, self.filesList.columnWidth(0))

    def countItems(self):
        count = 0
        iterator = QTreeWidgetItemIterator(self.histList) # pass your treewidget as arg
        while iterator.value():
            item = iterator.value()

            if item.parent():
                if item.parent().isExpanded():
                    count +=1
            else:
                # root item
                count += 1
            iterator += 1
        return count


    def doBlame(self):
        for eid in self.blamBtn:
            if self.blamBtn[eid] == self.sender():
                print("Blame ", eid, self.fileItems[eid].text(0))
                #  self.rgd.doDiff(self.branch, eid, self.prevCommit[eid] )
                if self.blameWin is None:
                    self.blameWin = BlameDisplay(self,self.rgd, self.branch,
                                                 self.fileItems[eid].text(0),
                                                 self.currentCommitId,
                                                 embedded=True)
                    self.gbox.addWidget(self.blameWin,   1,3,3, 1)
                else:
                    self.blameWin.reinit(self.branch, self.fileItems[eid].text(0), self.currentCommitId)

    def doBlameSelected(self):
        sel = self.histList.selectedItems()
        if len(sel) == 1:
            shortBlobHash   = sel[0].text(4)
            shortCommitHash = sel[0].text(3)
            commitTimeStr   = sel[0].text(7)
            commitTimeInt   = int(datetime.datetime.fromisoformat(commitTimeStr).timestamp())
            for i, (commitId, commitTime, blobId,_path) in enumerate(self.commits[:-1]):
                if blobId[:7] == shortBlobHash and commitId[:7] == shortCommitHash and  commitTimeInt == commitTime:
                    if self.blameWin is None:
                        self.blameWin = BlameDisplay(self,self.rgd, self.branch,
                                                     self.filePath,
                                                     commitId,
                                                     embedded=True)
                        self.gbox.addWidget(self.blameWin,   1,3,3, 1)
                    else:
                        self.blameWin.reinit(self.branch, self.filePath,  commitId)   


    def doDiffPrev1(self):
        sel = self.histList.selectedItems()
        if len(sel) == 1:
            shortBlobHash   = sel[0].text(4)
            shortCommitHash = sel[0].text(3)
            commitTimeStr   = sel[0].text(7)
            commitTimeInt   = int(datetime.datetime.fromisoformat(commitTimeStr).timestamp())
            for i, (commitId, commitTime, blobId, _path) in enumerate(self.commits[:-1]):
                if     blobId[:7]    == shortBlobHash   and \
                       commitId[:7]  == shortCommitHash and \
                       commitTimeInt == commitTime:
                    # FIXME copies?
                    self.rgd.doDiff(self.branch, self.filePath, blobId, self.filePath, self.commits[i+1][2])

    def doDiffPrev2(self):
        for eid in self.diffBtn:
            if self.diffBtn[eid] == self.sender():
                # FIXME copies?
                self.rgd.doDiff(self.branch, self.filePath, eid, self.filePath, self.prevCommit[eid] )
                

    def doDiffSelected(self):
        for eid in self.rb1:
            if self.rb1[eid].isChecked() :
                blobId1 = eid
                break
        for eid in self.rb2:
            if self.rb2[eid].isChecked():
                blobId2 = eid
                break
        if blobId1 != blobId2:
            # FIXME copies?
            self.rgd.doDiff(self.branch, self.filePath, blobId1, self.filePath, blobId2)


    def quit(self):
        self.close()
        self.pwin.close()

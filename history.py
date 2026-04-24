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
from functions import centerWindow, baseStyle, splitterStyle


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
        self.setStyleSheet(baseStyle + "HistoryView {background-color:#FFFDFA;}\n")
        self.initUI()
        QTimer.singleShot(100, self.delayedCenterWindow)

    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)
        self.gbox.setVerticalSpacing(4)
        self.gbox.setContentsMargins(4,4,4,4)


        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet(splitterStyle)
        self.splitter.setSizes([300,100,0])
        self.buttons   =self.buttonFrame()
        self.gbox.addWidget(self.splitter,  1,1,1, 1)
        self.gbox.addWidget(self.buttons,   2,1,1, 1)
        self.gbox.setRowStretch(1,1)
        self.gbox.setRowStretch(2,0)



        self.histList = QTreeWidget()
#         self.histList.setMinimumSize(1200,800)
#         self.histList.setMinimumSize(960,640)
        self.histList.setMinimumSize(960,480)
        self.histList.setColumnCount(10)
        self.histList.setHeaderLabels(["","", "Status", "Commit Hash", "Blob Hash", "Revision", "Author", "Last Change", "Branches", "Tags", "Commit Message"])


        self.selFrame = QFrame()
        self.vbox     = QVBoxLayout()
        self.selFrame.setLayout(self.vbox)
        self.vbox.setSpacing(4)
        self.vbox.setContentsMargins(0,0,0,0)

        self.message = QPlainTextEdit()


        self.filesList = QTreeWidget()
        self.filesList.setMinimumSize(480,320)
        self.filesList.setColumnCount(4)
        self.filesList.setHeaderLabels(["FileName", "Action", "", ""])

        self.vbox.addWidget(self.message,   1)
        self.vbox.addWidget(self.filesList, 1)

        self.filesList.setMinimumWidth(320)

        self.splitter.addWidget(self.histList)
        self.splitter.addWidget(self.selFrame)
#        self.splitter.addWidget(self.filesList,
#         self.buttons   =self.buttonFrame()

#         self.gbox.addWidget(self.histList,  1,1,2, 1)
#         self.gbox.addWidget(self.message,   1,2,1, 1)
#         self.gbox.addWidget(self.filesList, 2,2,1, 1)
#         self.gbox.addWidget(self.buttons,   3,1,2, 3)

        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.histList.itemClicked.connect(self.showCommit)
        self.diffPrvBtn.clicked.connect(self.doDiffPrev1)
        self.diffSelBtn.clicked.connect(self.doDiffSelected)
        self.blameCurBtn.clicked.connect(self.doBlameSelected)
        self.setMaximumWidth(1640)
        
    def sizeHint(self):
        return QSize(32,24)


    def delayedCenterWindow(self):
        s =self.size()
        s.setWidth(1440)
        self.resize(s)
        centerWindow(self, ref=self.pwin)
        
            

    def buttonFrame(self):
        f = QFrame()
        self.hbox = QHBoxLayout()
        f.setLayout(self.hbox)
        self.hbox.setSpacing(10)
        self.hbox.setContentsMargins(0,0,0,0)

        self.diffSelBtn   = QPushButton("Diff Selected")
        self.diffPrvBtn   = QPushButton("Diff Previous")
        self.blameCurBtn  = QPushButton("Blame")
        self.hideBlameBtn = QPushButton("Hide Blame")
        self.closeBtn     = QPushButton("Close")
        self.closeBtn.clicked.connect(self.close)
        self.hideBlameBtn.clicked.connect(self.hideBlame)
        self.hbox.addWidget(self.diffSelBtn,  0, Qt.AlignLeft)
        self.hbox.addWidget(self.diffPrvBtn,  0, Qt.AlignLeft)
        self.hbox.addWidget(self.blameCurBtn, 0, Qt.AlignLeft)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.hideBlameBtn, 0, Qt.AlignRight)
        self.hbox.addWidget(self.closeBtn, 0, Qt.AlignRight)
        self.hideBlameBtn.hide()
        return f
    
        
    def fill(self, rgd,  filePath, branch):
        self.setWindowTitle("RGit: History of '%s'"% filePath)
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
        if sys.platform =="win32":
            self.histList.setColumnWidth(0,54)   # extra space for the invisib;e expandion indicator
        else:
            self.histList.setColumnWidth(0,36)   # extra space for the invisib;e expandion indicator
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
        # print("---->", self.filesList.width(), self.filesList.width() -24 -tw)
        self.filesList.setColumnWidth(0, self.filesList.width() -24 -tw)
        # print("\t\t\t", 0, self.filesList.columnWidth(0))


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
                self.prevSize   = self.size()
                self.prevSizes  = self.splitter.sizes() 
                if self.blameWin is None:
                    self.blameWin = BlameDisplay(self,self.rgd, self.branch,
                                                 self.fileItems[eid].text(0),
                                                 self.currentCommitId,
                                                 embedded=True)
                    self.splitter.addWidget(self.blameWin)
                    self.prevSizes  += [0]
                else:
                    self.blameWin.reinit(self.branch, self.fileItems[eid].text(0), self.currentCommitId)
                self.blameWin.setMinimumWidth(660)
                self.histList.setMinimumSize(600,480)
                self.setMaximumWidth(1640)
                s1, s2, _ = self.prevSizes
                # 880 is minimum size for histList and selFrame (600+280)
                # 660 is minium widt for blame
                # 1640 is now total width
                extra = s1+s2 -920
                print([600+int(floor( (s1-600)/920 * 180)),
                       280+int(floor( (s2-280)/920 * 180)),
                       660])
                self.splitter.setSizes([600 +int(floor( (s1-600)/920 * 100)),
                                        280 +int(floor( (s2-280)/920 * 100)),
                                        660])
                self.hideBlameBtn.show()
                centerWindow(self, ref=self.pwin)
                break


    def doBlameSelected(self):
        sel = self.histList.selectedItems()
        if len(sel) == 0:
            sel = [self.histList.topLevelItem(0)]
        if len(sel) == 1:
            shortBlobHash   = sel[0].text(4)
            shortCommitHash = sel[0].text(3)
            commitTimeStr   = sel[0].text(7)
            commitTimeInt   = int(datetime.datetime.fromisoformat(commitTimeStr).timestamp())
            
            self.prevSize   = self.size()
            self.prevSizes  = self.splitter.sizes() 
            for i, (commitId, commitTime, blobId,_path) in enumerate(self.commits[:-1]):
                if blobId[:7] == shortBlobHash and commitId[:7] == shortCommitHash and  commitTimeInt == commitTime:
                    print("\t open blame")
                    if self.blameWin is None:
                        self.blameWin = BlameDisplay(self,self.rgd, self.branch,
                                                     self.filePath,
                                                     commitId,
                                                     embedded=True)
                        self.splitter.addWidget(self.blameWin)
                        self.prevSizes  += [0]

                    else:
                        self.blameWin.reinit(self.branch, self.filePath,  commitId)
                    self.blameWin.setMinimumWidth(660)
                    self.histList.setMinimumSize(600,480)
                    self.setMaximumWidth(1640)
                    s1, s2, _ = self.prevSizes
                    # 880 is minimum size for histList and selFrame (600+280)
                    # 660 is minium widt for blame
                    # 1640 is now total width
                    extra = s1+s2 -920
                    print([600+int(floor( (s1-600)/920 * 180)),
                           280+int(floor( (s2-280)/920 * 180)),
                                            660])
                    self.splitter.setSizes([600 +int(floor( (s1-600)/920 * 100)),
                                            280 +int(floor( (s2-280)/920 * 100)),
                                            660])
                    self.hideBlameBtn.show()
                    centerWindow(self, ref=self.pwin)
                    break


    def hideBlame(self):
        self.splitter.setSizes(self.prevSizes)
        self.histList.setMinimumSize(960,480)
        self.blameWin.setMinimumWidth(1)
        self.setMaximumWidth(1640)
        self.hideBlameBtn.hide()
        QApplication.processEvents()
        self.resize(self.prevSize)
        

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
                    self.rgd.doDiff(self.branch,
                                    self.filePath, self.commits[i+1][2],    # prev blob
                                    self.filePath, blobId)                  # current blob

    def doDiffPrev2(self):
        for eid in self.diffBtn:
            if self.diffBtn[eid] == self.sender():
                self.rgd.doDiff(self.branch,
                                self.filePath, self.prevCommit[eid],
                                self.filePath, eid)
                

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
            self.rgd.doDiff(self.branch,
                            self.filePath, blobId1,
                            self.filePath, blobId2)


    def quit(self):
        self.close()
        self.pwin.close()

#!/usr/bin/env python3
# File: training.py
# Time-stamp: <29-Mar-2026 16:13:41 goetz>
# $Id: $
#
# Copyright (C) 2021 by LemnaTec GmbH
#
# Author: Ruediger Goetz
#
# Description: 
#
# Implement self.doRevert
# Implement List local files (so we can add them)
# FIX: added files must be listed in commit dialog
#
#
# Context Menu of file and dir entries
#
#  b1 = repo.blame("css/activity.css")
#  bhl = [ l for l in b1]
#  bhl[1] -> final_commit_id  , lines_in_hunk , ...
#  
#  b2 = repo.blame("css/activity.css", newest_commit="644c64aa4b79eecb2034b3ae79a80320a04694e2")
#  bhl2 = [ l for l in b2]
#  
#
# What is status INDEX_MODIFIED


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
import glob
import datetime
import json
import subprocess
from collections import defaultdict
import numpy as np
from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *


from data import RGitData
from history import HistoryView
from commitDlg import CommitDialog
from blame     import BlameDisplay

from collections import defaultdict
import pygit2


class RToolButton(QToolButton):

    def __init(self, text, icon):
        super().__init__(text, icon)
        




class RGitVersions(QMainWindow):

    
    def __init__(self, argv):
        super().__init__()


        self.statusColor = {"CURRENT" : "#FF0000",
                            "WT_MODIFIED"   : "#FF8888",
                            "Remote Update" : "#AAFFAA",
                            "CONFLICT"      : "#FFCC88",
                            "Not Commited"  : "#CC88FF",
#                             "" : "",
#                             "" : "",
#                             "" : "",
                            "Unknown"       : "#FF88FF",
                            "No Status"     : "#EEDDDD",
                            "WT_MODIFIED ++"   : "#FF4444",
                            "Remote Update ++" : "#AAFF66",
                            "CONFLICT ++ "     : "#FFDD44",
                            "Not Commited ++"  : "#CC88FF",
                            "Unknown ++": "#FF44FF ++ ",
                           }
        self.statusOrder = ["Unknown", "CONFLICT", "Remote Update", "WT_MODIFIED", "Not Comitted", "CURRENT"]
        self.curBranch   = "main"
        self.primaryBranches = ["main", "origin"]
        self.rgd         = RGitData(self.curBranch, self.primaryBranches)
        self.initUI()
        for b in self.rgd.branches["local"] +self.rgd.branches["remote"] :
            self.branchSelect.addItem(b)
        self.branchSelect.setCurrentText("main")
        QShortcut(QKeySequence("Alt+q"), self, self.closeApp)
        self.show()


    def initUI(self):
        f = QFrame()
        self.setCentralWidget(f)
        self.gbox = QGridLayout()
        f.setLayout(self.gbox)

        progPath = os.path.dirname(__file__)
        

        self.tools = self.toolFrame()
        self.toolBtn= {
            "history":  self.addToolButton("History",    progPath+"/icons/hist.png",
                                           self.showHistory, "History of selected file"),
            "diff"   :  self.addToolButton("Diff",       progPath+"/icons/diffLocal.png",
                                           self.diffWithPrev, "Diff local changes"),
            "diffHead": self.addToolButton("Diff Head",  progPath+"/icons/diffRemote.png",
                                           self.diffWithHead, "Diff remote changes"),
            "revert" :  self.addToolButton("Revert",     progPath+"/icons/revert.png",
                                           self.doRevert, "Revert local changes"),
            "blame"  :  self.addToolButton("Blame",      progPath+"/icons/blame.png",
                                           self.showBlame, "Blame"),
            "commitL":  self.addToolButton("Commit Locally", progPath+"/icons/commitLocal.png",
                                           self.doLocalCommit, "Commit to local repo"),
            "commit" :  self.addToolButton("Commit & Push", progPath+"/icons/commit.png",
                                           self.doCommit, "Commit to remote repo"),
            "push" :    self.addToolButton("Push \nLocal Commits \nto master", progPath+"/icons/push.png",
                                           self.doPush, "Commit to remote repo"),
            "info"   :  self.addToolButton("Info",       progPath+"/icons/info.png",
                                           None, " Repo Info"),
            "Update" :  self.addToolButton("Update",     progPath+"/icons/update.png",
                                           None, "Update / Pull Changes"),
            "clone"  :  self.addToolButton("Clone",      progPath+"/icons/checkout.png",
                                           None, "Checkout / Clone"),
            "branch" :  self.addToolButton("Branch",     progPath+"/icons/branch.png",
                                           None, "Branch"),
            "merge"  :  self.addToolButton("Merge",      progPath+"/icons/merge.png",
                                           None, "Merge"),
            "Delete" :  self.addToolButton("Delete",     progPath+"/icons/delete.png",
                                           None, "Delete Files from repo"),
            "refrsh" :  self.addToolButton("Refresh",    progPath+"/icons/refresh.png",
                                           self.refreshTrees, "Refresh"),
            }
        self.tools.layout().addWidget(QLabel(""), 100)

        self.branchSelect = QComboBox()
        self.branchSelect.currentTextChanged.connect(self.switchBranch)

        self.dirTree  = QTreeWidget()
        self.fileTree = QTreeWidget()
        self.dirTree.setMinimumSize(400,800)
        self.fileTree.setMinimumSize(1200,800)
        self.fileTree.setColumnCount(8)
        self.fileTree.setHeaderLabels(["File","Status", "Commit Hash", "Blob Hash", "Revision", "Author", "Last Change", "Branches", "Tags"])
        self.dirTree.setHeaderLabels(["Directory","Status"])
        self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
        self.dirTree.addTopLevelItem(self.rootItem)

        self.gbox.addWidget(self.tools,         1, 1, 1, 2)
        self.gbox.addWidget(self.branchSelect,  2, 1, 1, 1)
        self.gbox.addWidget(self.dirTree,       3, 1, 7, 1)
        self.gbox.addWidget(self.fileTree,      2, 2, 8, 1)

        self.gbox.setRowStretch(1,0)
        self.gbox.setRowStretch(2,0)
        self.gbox.setRowStretch(3,0)
        self.gbox.setRowStretch(4,0)
        self.gbox.setRowStretch(5,1)
        self.gbox.setRowStretch(6,0)
        self.gbox.setRowStretch(7,0)
        self.gbox.setRowStretch(8,0)
        self.fill(self.curBranch)
        self.rootItem.setExpanded(True)

        self.dirTree.itemClicked.connect(self.showFiles)
        self.dirTree.expanded.connect(self.resizeDirTree)
        self.dirTree.collapsed.connect(self.resizeDirTree)
        self.fileTree.setStyleSheet("QTreeWidget::item {margin-right:0.5em;margin-left:0.5em}")
        self.fileTree.setSelectionMode(QAbstractItemView.ExtendedSelection)

        QShortcut(QKeySequence("Ctrl+l"), self.fileTree, self.showHistory)
        QShortcut(QKeySequence("Ctrl+b"), self.fileTree, self.showBlame)
        QShortcut(QKeySequence("Ctrl+c"), self.fileTree, self.doCommit)
        QShortcut(QKeySequence("Ctrl+r"), self.fileTree, self.doRevert)
        QShortcut(QKeySequence("Ctrl+d"), self.fileTree, self.diffWithPrev)
        QShortcut(QKeySequence("Ctrl+Shift+d"),  self.fileTree, self.diffWithHead)
        # FIXME contxt menu


    def toolFrame(self):
        f=QFrame()
        self.tbox =QHBoxLayout()
        f.setLayout(self.tbox)
        return f

    def addToolButton(self, text, iconFile, func, tooltip):
        toolButton = QToolButton()
        toolButton.setMinimumHeight(64)
        toolButton.setMinimumWidth(48)
        toolButton.setIcon( QIcon(iconFile))
        toolButton.setIconSize(QSize(48,48))
        toolButton.setText(text)
        print(">>toolButton>>", text)
        toolButton.setStyleSheet("QToolButton {font-size:10px;}")
        if func is None:
            toolButton.setToolTip(tooltip + "\n (disabled)")
        else:
            toolButton.setToolTip(tooltip)
        if func is not None:
            toolButton.clicked.connect(func)
        else:
            toolButton.setEnabled(False)
        toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);
        self.tools.layout().addWidget(toolButton)
        return  toolButton


    def switchBranch(self, branch):
        self.rgd.getBranchData(branch)
        print(" FIXME: switch branch on file system")
        


    def resizeDirTree(self):
        for c in range(2):
            self.dirTree.resizeColumnToContents(c)


    def resizeFileTree(self):
        for c in range(self.fileTree.columnCount()):
            self.fileTree.resizeColumnToContents(c)




    def fill(self, branch=None):
        self.rootItem.setData(0, Qt.UserRole , (self.rgd.branchFiles[branch]["."], "."))
        status = self.rgd.getDirStatus(branch,  ".")
        self.rootItem.setText(1, status)
        self.colorizeTreeItem(self.rootItem, status)
        if branch is not None:
            for f in self.rgd.branchFiles[branch]["."]["files"]:
                e = self.rgd.branchFiles[branch][f]
                if len(e["files"])>0:
                    status = self.rgd.getDirStatus(branch,  f)
                    item = QTreeWidgetItem(self.rootItem, [e["name"],status])
                    item.setData(0, Qt.UserRole , (e, f))
                    self.colorizeTreeItem(item, status)
                    self.__fill(branch, e,  f, item)
        QTimer.singleShot(500, self.resizeDirTree)
    

    def __fill(self, branch, parentElem, parentPath, parentItem):
        for f in parentElem["files"]:
            e = self.rgd.branchFiles[branch][f]
            if len(e["files"])>0:
                item = QTreeWidgetItem(parentItem, [e["name"], ""])
                item.setData(0, Qt.UserRole , (e, f))
                self.__fill(branch, e,  f, item)


    def fillFileList(self, parentItem):
        # FIXME merge local files
        #    print(">>>>", parentItem, parentItem.data(0, Qt.UserRole))
        self.fileTree.clear()
        files  = parentItem.data(0, Qt.UserRole)[0]["files"]
        branch = parentItem.data(0, Qt.UserRole)[0]["branch"]
        for f in files:
            e   = self.rgd.branchFiles[branch][f]
            eid = e["id"]
            entry = self.rgd.repo.get(eid)

            if len(e["files"])>0:
                fname = os.path.basename(f) +"/"
                status = self.rgd.getDirStatus(branch, f)
                obj = self.rgd.repo.get(e["id"])

            else:
                fname = os.path.basename(f)
                status = self.rgd.getFileStatus(eid, f)
            commitId = self.rgd.getCommitOfBlob(branch, f, eid)
            commit   = self.rgd.repo.get(commitId)

            
               
            branches = self.rgd.getBranchesForPath(f)
            cid  = str(commit.id)
            item = QTreeWidgetItem([fname , status, commit.short_id, entry.short_id,
                                    self.rgd.getVersionOfCommit(cid),
                                    commit.author.name ,
                                    datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S"),
                                    branches, ", ".join(self.rgd.getTagsForCommit(cid))])
            item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator);
            item.setData(0, Qt.UserRole , (f, branch, eid))
            self.colorizeTreeItem(item, status)
            self.fileTree.addTopLevelItem(item)
        self.resizeFileTree()

    def refreshTrees(self):
        sel = self.dirTree.selectedItems()
        dirName = sel[0].text(0)

        self.dirTree.clear()
        # self.fileTree.clear()
        self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
        self.dirTree.addTopLevelItem(self.rootItem)
        self.fill(self.curBranch)
        self.rootItem.setExpanded(True)
        items = self.dirTree.findItems(dirName, Qt.MatchExactly, 0)

        for item in items:
            if item.text(0) == dirName:
                self.dirTree.setCurrentItem(item)
                self.showFiles(item)
                break
        
        

    def colorizeTreeItem(self, item, status):
        if status != "CURRENT":
            if status in self.statusColor:
                self.setFileTreeItemColor(item, self.statusColor[status])
            else:
                self.setFileTreeItemColor(item, self.statusColor["Unknown"])


    def setFileTreeItemColor(self, item, color):
        for c  in range(self.fileTree.columnCount()):
            item.setBackground(c, QBrush(color))
                        

    def showFiles(self, e):
        self.fillFileList(e)





    def __collectModifiedFiles4Commit(self, branch, path):
        files = []
        fl = self.rgd.collectFilesFromPath(self.curBranch, path)
        for f in fl:
            if self.rgd.isModified(f):
                files.append(f)
        return files


    def doLocalCommit(self):
        print("doCommit")
        self.__doPush(push=False)
    
    def doPush(self):
        pass
    
    def doCommit(self):
        print("doPush")
        self.__doPush(push=True)
        
    def __doPush(self, push=True):
        print("doPush push= ", push)
        files = []
        sel1 = self.dirTree.selectedItems()
        sel2 = self.fileTree.selectedItems()
        print(" ::::" , sel1)
        print(" ::::" , sel2)
        for item in sel1:
            path   = item.data(0, Qt.UserRole)[1]
            entry  = item.data(0, Qt.UserRole)[0]
            branch = item.data(0, Qt.UserRole)[0]["branch"]
            if len(entry["files"])>0:
                for f2 in self.__collectModifiedFiles4Commit( branch, path):
                    if f2 not in files:
                        files.append(f2)

        for item in sel2:
            
            f = item.data(0, Qt.UserRole)[0]
            branch = item.data(0, Qt.UserRole)[1]
            e   = self.rgd.branchFiles[branch][f]
            if len(e["files"])>0:
                for f2 in self.__collectModifiedFiles4Commit( branch, f):
                    if f2 not in files:
                        files.append(f2)
            elif self.rgd.isModified(f):
                if f not in files:
                    files.append(f)
        print("---->", files)
        if len(files) >0 :
            self.commitDlg = CommitDialog(self, self.rgd, branch, files, push=push)
            self.commitDlg.commitExecuted.connect(self.refreshTrees)

    def doRevert(self):
        sel = self.fileTree.selectedItems()
        for i,e in enumerate(sel):
            if e == 0:
                print("Revert  ",e.data(0, Qt.UserRole)[0])
            else:
                print("        ",e.data(0, Qt.UserRole)[0])


    def diffWithPrev(self):
        sel = self.fileTree.selectedItems()
        if len(sel) == 1:
            filePath, branch, entryId = sel[0].data(0, Qt.UserRole)
            self.rgd.doDiff(branch, filePath, None, filePath, entryId) 

    def diffWithHead(self):
        sel = self.fileTree.selectedItems()
        if len(sel) == 1:
            filePath, branch, entryId = sel[0].data(0, Qt.UserRole)
            if filePath in self.rgd.repoFiles:
                commitId, commitTime, blobId, _ = self.rgd.repoFiles[filePath]["commits"][-1]
                self.rgd.doDiff(branch, filePath, None, filePath, blobId)


                
    def showBlame(self):
        sel = self.fileTree.selectedItems()
        print(">>>", sel)
        if len(sel) == 1:
            fileName = sel[0].text(0)
            filePath = sel[0].data(0, Qt.UserRole)[0]
            branch   = sel[0].data(0, Qt.UserRole)[1]
            entryId  = sel[0].data(0, Qt.UserRole)[2]
            commitId = self.rgd.getCommitOfBlob(branch, filePath, entryId)
            print ("BLAME : ", branch, entryId, commitId)
            print ("BLAME : ", filePath)
            self.blameDisplay = BlameDisplay(self, self.rgd, branch, filePath, commitId, blobId=entryId)
            
    def showHistory(self):
        sel = self.fileTree.selectedItems()
        if len(sel) == 1:
            fileName = sel[0].text(0)
            filePath = sel[0].data(0, Qt.UserRole)[0]
            branch   = sel[0].data(0, Qt.UserRole)[1]
            entryId  = sel[0].data(0, Qt.UserRole)[2]
            print("History for " , filePath, filePath in self.rgd.repoFiles)
            if filePath in self.rgd.repoFiles:
                for commitId, commitTime, blobId, _ in self.rgd.repoFiles[filePath]["commits"]:
                    commit   = self.rgd.repo.get(commitId)
                    entry    = self.rgd.repo.get(blobId)
                    timStr   =  datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S")
                    print("%-8s  %-8s  %-20s  %s" % (commit.short_id, entry.short_id,  timStr, commit.author.name) )
            self.histDialog = HistoryView(self)
            self.histDialog.fill(self.rgd, filePath, self.curBranch)
            self.histDialog.show()
        

    def closeApp(self):
        super().close()


 
if __name__ == '__main__':

    app  = QApplication(sys.argv)
    win  = RGitVersions(sys.argv)
    win.setWindowTitle("RGit")
    signal.signal(signal.SIGINT, win.closeApp)



    
    ret = app.exec_()
    sys.exit(ret)

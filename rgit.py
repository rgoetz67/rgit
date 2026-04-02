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
from blame     import BlameDisplay, CodeDisplay
from selectionMenu import SelectionMenu
from collections import defaultdict
import pygit2


timFormat = "%Y-%m-%d %H:%M:%S"

class RToolButton(QToolButton):

    def __init(self, text, icon):
        super().__init__(text, icon)
        




class RGitVersions(QMainWindow):

    
    def __init__(self, argv):
        super().__init__()


        self.statusColor = {"CURRENT"       : "#FFFFFF",
                            "MODIFIED"      : "#FF8888",
                            "ADDED"         : "#FFBB88",
                            "DELETED"       : "#EE7777",
                            "Remote Update" : "#AAFFAA",
                            "CONFLICT"      : "#FFCC88",
                            "Not Commited"  : "#CC88FF",
                            "not versioned" : "#F4F0F0",
                            "removed from Repo" : "#F8ECEC",
#                             "" : "",
#                             "" : "",
                            "Unknown"       : "#FF88FF",
                            "No Status"     : "#EEDDDD",
                            "MODIFIED ++"   : "#FF4444",
                            "ADDED ++"      : "#FFCC44",
                            "DELETED ++"    : "#DD4444",
                            "Remote Update ++" : "#AAFF66",
                            "CONFLICT ++ "     : "#FFDD44",
                            "Not Commited ++"  : "#CC88FF",
                            "Unknown ++": "#FF44FF ++ ",
                           }
        # self.statusOrder = ["Unknown", "CONFLICT", "Remote Update", "MODIFIED", "ADDED", "Not Comitted", "CURRENT"]
        self.curBranch   = "main"
        self.rgd         = RGitData(self.curBranch)
        self.curBranch   = self.rgd.curBranch
        self.dirItems    = []
        self.fileItems   = []
        self.statusCache = {}
        self.dirStatusRefreshPointer = 0
        self.updateIndex = 0
        self.initUI()
        self.initMenus()
        for b in self.rgd.branches["local"] +self.rgd.branches["remote"] :
            self.branchSelect.addItem(b)
        self.branchSelect.setCurrentText("main")
        QShortcut(QKeySequence("Alt+q"), self, self.closeApp)
        self.show()
        self.updTimer = QTimer()
        self.updTimer.timeout.connect(self.refreshStatus)
        self.updTimer.setInterval(5000)
        self.updTimer.start()
        self.resizeDirTree()
        self.resizeFileTree()

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
                                           self.doCommitAndPush, "Commit to remote repo"),
            "push" :    self.addToolButton("Push Local\nto master", progPath+"/icons/push.png",
                                           self.doPush, "Commit to remote repo"),
            "info"   :  self.addToolButton("Info",       progPath+"/icons/info.png",
                                           None, " Repo Info"),
            "Update" :  self.addToolButton("Update",     progPath+"/icons/update.png",
                                           self.doPull, "Update / Pull Changes"),
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
        self.fileTree.setContextMenuPolicy(Qt.CustomContextMenu);
        self.dirTree.setHeaderLabels(["Directory","Status"])
        self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
        self.dirTree.addTopLevelItem(self.rootItem)

        self.showLocal = QCheckBox("Show Local Files")
        self.lFileType = QLabel("File Types: ")
        self.fileTypes = SelectionMenu(maxStrLen=40)
        self.fileTypes.addItems([["C /C++ Files", [".c", ".cc", ".cpp", ".h", ".hpp", ".hh"]],
                                 ["Python Files", [".py"]],
                                 ["C# Files", [".cs"]],
                                 ["Batch Files", [".bat"]],
                                 ["Shell Scripts", [".sh", ".csh", ".ksh", ".zsh"]],
                                 ["AWK Files", [".awk", ".gawk"]],
                                 ["Text Files", [".txt", ".md"]],
                                 ["Image Files", [".png", ".jpeg", ".jpg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]],
                                 ["Video Files", [".mp4", ".wmv", ".avi", ".webm"]],
                                 ["Java Script Files", [".js"]],
                                 ["Java Files", [".java", ".class"]],
                                 ["HTML / CSS Files", [".html", ".htm", ".css"]],
#                                 ["Python Files", [".py"]],
#                                 ["Python Files", [".py"]],
                                 ["Other Files", ["."]]])

        self.gbox.addWidget(self.tools,         1, 1, 1, 2)
        self.gbox.addWidget(self.branchSelect,  2, 1, 1, 1)
        self.gbox.addWidget(self.dirTree,       3, 1, 2, 1)
        self.gbox.addWidget(self.fileTree,      2, 2, 2, 4)
        self.gbox.addWidget(self.showLocal,     4, 3, 1, 1)
        self.gbox.addWidget(self.lFileType,     4, 4, 1, 1)
        self.gbox.addWidget(self.fileTypes,     4, 5, 1, 1)

        self.gbox.setColumnStretch(1,1)
        self.gbox.setColumnStretch(2,4)
        self.gbox.setColumnStretch(3,0)
        self.gbox.setColumnStretch(4,0)
        self.gbox.setColumnStretch(5,0)
        self.gbox.setRowStretch(1,0)
        self.gbox.setRowStretch(2,0)
        self.gbox.setRowStretch(3,1)
        self.gbox.setRowStretch(4,0)
        self.fill(self.curBranch)
        self.rootItem.setExpanded(True)
        self.fillFileList(self.rootItem)

        self.dirTree.itemClicked.connect(self.showFiles)
        self.dirTree.expanded.connect(self.resizeDirTree)
        self.dirTree.collapsed.connect(self.resizeDirTree)
        self.showLocal.stateChanged.connect(self.refreshTrees)
        self.fileTypes.selectionChanged.connect(self.refreshTrees)

        self.fileTree.setStyleSheet("QTreeWidget::item {margin-right:0.5em;margin-left:0.5em}")
        self.fileTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fileTree.customContextMenuRequested.connect(self.showFileContextMenu)
        
        QShortcut(QKeySequence("Ctrl+l"), self.fileTree, self.showHistory)
        QShortcut(QKeySequence("Ctrl+b"), self.fileTree, self.showBlame)
        QShortcut(QKeySequence("Ctrl+c"), self.fileTree, self.doCommitAndPush)
        QShortcut(QKeySequence("Ctrl+r"), self.fileTree, self.doRevert)
        QShortcut(QKeySequence("Ctrl+d"), self.fileTree, self.diffWithPrev)
        QShortcut(QKeySequence("Ctrl+Shift+d"),  self.fileTree, self.diffWithHead)
        # FIXME contxt menu


    def initMenus(self):
        self.menu = {"addOnly"  : QMenu(),
                     "commited" : QMenu(),
                     "modified" : QMenu(),
                     "remoteUp" : QMenu()
                     }
        self.menuActions = {"add"     : self.menu["addOnly"].addAction("Add File"),
                            "showN"   : self.menu["addOnly"].addAction("Show Content"),
                            
                            "commit"  : self.menu["modified"].addAction("Commit && Push"),
                            "commitL" : self.menu["modified"].addAction("Commit Locally"),
                            "revert"  : self.menu["modified"].addAction("Revert local changes"),
                            "restore" : self.menu["modified"].addAction("Restore from Origin"),
                            "remove"  : self.menu["modified"].addAction("Remove from Repo"),
                            "show"    : self.menu["modified"].addAction("Show Content"),
                            "move"    : self.menu["modified"].addAction("Move File"),
                            
                            "removeC" : self.menu["commited"].addAction("Remove from Repo"),
#                            "restoreC": self.menu["commited"].addAction("Restore from Origin"),
                            "showC"   : self.menu["commited"].addAction("Show Content"),
                            "moveC"   : self.menu["commited"].addAction("Move File"),

                            "update"  : self.menu["remoteUp"].addAction("Update to origin"),

                            }

        self.menuActions["add"].triggered.connect(self.doAddFile)
        self.menuActions["showN"].triggered.connect(self.showFileContent)
        
        self.menuActions["remove"].triggered.connect(self.doDeleteFile)
        self.menuActions["revert"].triggered.connect(self.doDummy)
        self.menuActions["restore"].triggered.connect(self.doDummy)
        self.menuActions["commit"].triggered.connect(self.doCommitAndPushFromContext)
        self.menuActions["commitL"].triggered.connect(self.doLocalCommitFromContext)
        self.menuActions["show"].triggered.connect(self.showFileContent)
        self.menuActions["move"].triggered.connect(self.doDummy)

        self.menuActions["removeC"].triggered.connect(self.doDeleteFile)
#        self.menuActions["restoreC"].triggered.connect(self.doDummy)
        self.menuActions["showC"].triggered.connect(self.showFileContent)
        self.menuActions["moveC"].triggered.connect(self.doDummy)

        self.menuActions["update"].triggered.connect(self.doDummy)


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
        # print(">>toolButton>>", text)
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
        for c in range(self.fileTree.columnCount()-1):
            self.fileTree.resizeColumnToContents(c)




    def fill(self, branch=None):
        self.dirItems = []
        self.rootItem.setData(0, Qt.UserRole , (self.rgd.branchFiles[branch]["."], "."))
        status = self.rgd.getDirStatus(branch,  ".")
        self.statusCache["."] = status
        self.rootItem.setText(1, status)
        self.colorizeTreeItem(self.rootItem, status)
        if branch is not None:
            for f in self.rgd.branchFiles[branch]["."]["files"]:
                e = self.rgd.branchFiles[branch][f]
                if len(e["files"])>0:
                    status = self.rgd.getDirStatus(branch,  f)
                    self.statusCache[f] = status
                    item = QTreeWidgetItem(self.rootItem, [e["name"],status])
                    item.setData(0, Qt.UserRole , (e, f))
                    self.colorizeTreeItem(item, status)
                    self.__fill(branch, e,  f, item, 2)
                    self.dirItems.append((item,1))
        self.sortedDirItems = list(sorted(self.dirItems + [(self.rootItem, 0)], key=lambda x: -x[1]))
        self.dirStatusRefreshPointer = 0
        QTimer.singleShot(500, self.resizeDirTree)



    def __acceptedExtensions(self):
        allSel = self.fileTypes.getAllItems(returnData = True)
        curSel = self.fileTypes.currentSelection(returnData = True)
        extFilter = {}
        for extList in allSel:
            for ext in extList:
                extFilter[ext] = False
        for extList in curSel:
            for ext in extList:
                extFilter[ext] = True
        return extFilter
                
                
            

    def __fill(self, branch, parentElem, parentPath, parentItem, lvl):
        for f in parentElem["files"]:
            e = self.rgd.branchFiles[branch][f]
            if len(e["files"])>0:
                item = QTreeWidgetItem(parentItem, [e["name"], ""])
                item.setData(0, Qt.UserRole , (e, f))
                self.dirItems.append((item, lvl))
                self.__fill(branch, e,  f, item, lvl+1)



    def fillFileList(self, parentItem):
        # FIXME merge local files
  #     print(">>>>", parentItem, parentItem.data(0, Qt.UserRole))
        self.fileItems = []
        self.fileTree.clear()
        files  = parentItem.data(0, Qt.UserRole)[0]["files"]
        branch = parentItem.data(0, Qt.UserRole)[0]["branch"]
        folder = parentItem.data(0, Qt.UserRole)[1]

        localFiles = []
        if self.showLocal.isChecked():
            extFilter  = self.__acceptedExtensions()
            for f in glob.glob(folder + "/*"):
                if f not in files:
                    if os.path.isdir(f):
                        localFiles.append(f+"/")
                    else:
                        ext = os.path.splitext(f)[1]
                        if ext in extFilter:
                            if extFilter[ext]:
                                localFiles.append(f)
                        else:
                            if extFilter["."]:  # aka other files
                                localFiles.append(f)
        allFiles = files + localFiles


        # print("::::::::::", branch, "\t", self.rgd.branchFiles[branch].keys())
        for f in sorted(allFiles):
            print("\t add ", branch, f, f in files, f in  self.rgd.branchFiles[branch])
            if f in files:
                e   = self.rgd.branchFiles[branch][f]
                eid = e["id"]
                entry = self.rgd.repo.get(eid)

                if len(e["files"])>0:
                    fname  = os.path.basename(f) +"/"
                    status = self.rgd.getDirStatus(branch, f)
                    self.statusCache[f] = status
                    obj    = self.rgd.repo.get(e["id"])

                else:
                    fname = os.path.basename(f)
                    status = self.rgd.getFileStatus(eid, f)

                branches = self.rgd.getBranchesForPath(f)

                commitId = self.rgd.getCommitOfBlob(eid, lastBefore=time.time())
                if commitId is not None:
                    commit   = self.rgd.repo.get(commitId)
                    cid  = str(commit.id)
                    cts  = datetime.datetime.fromtimestamp(commit.commit_time).strftime(timFormat)
                else:
                    cid  = ""
                    cts  = ""
                item = QTreeWidgetItem([fname , status, commit.short_id, entry.short_id,
                                        self.rgd.getVersionOfCommit(cid),
                                        commit.author.name , cts,
                                        branches, ", ".join(self.rgd.getTagsForCommit(cid))])
                item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator);
                item.setData(0, Qt.UserRole , (f, branch, eid))
                self.colorizeTreeItem(item, status)
                self.fileTree.addTopLevelItem(item)
                self.fileItems.append(item)
            else:
                status = "not versioned"
                item = QTreeWidgetItem([f, status, "", "", "", "", "", "", ""])
                item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator);
                item.setData(0, Qt.UserRole , (f, branch, None))
                self.colorizeTreeItem(item, status)
                self.fileTree.addTopLevelItem(item)
                self.fileItems.append(item)
                print("\t\t ==>", item)
            self.statusCache[f] = status
        self.resizeFileTree()


    def showFileContextMenu(self, p):
        item = self.fileTree.itemAt(p)
        print("custom menu at ",p, item, item.text(0), item.text(1))
        status = item.text(1)
        if status == "not versioned":
            self.curContextItem = item
            self.menu["addOnly"].popup(self.cursor().pos())
        elif status in ["MODIFIED"]:
            self.curContextItem = item
            self.menu["modified"].popup(self.cursor().pos())
        elif status in ["CURRENT"]:
            self.curContextItem = item
            self.menu["commited"].popup(self.cursor().pos())
        elif status in ["Remote Update"]:
            self.curContextItem = item
            self.menu["remoteUp"].popup(self.cursor().pos())


    def refreshTrees(self):
        sel = self.dirTree.selectedItems()
        if len(sel)>0:
            dirName = sel[0].text(0)
        else:
            dirName = None
        self.dirTree.clear()
        # self.fileTree.clear()
        self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
        self.dirTree.addTopLevelItem(self.rootItem)
        self.fill(self.curBranch)
        self.rootItem.setExpanded(True)
        if dirName is not None:
            items = self.dirTree.findItems(dirName, Qt.MatchExactly, 0)
            for item in items:
                if item.text(0) == dirName:
                    self.dirTree.setCurrentItem(item)
                    self.showFiles(item)
                    break
        else:
            self.dirTree.setCurrentItem(self.rootItem)
            self.showFiles(self.rootItem)
        

    def refreshStatus(self, allCommits = False):
        t0 =time.time()
        print("  refreshStatus  ")
        # FIXME tree like dir state update
        p = self.dirStatusRefreshPointer
        if not allCommits:
            commits = self.sortedDirItems[ p:p+20]
        else:
            commits = self.sortedDirItems
            
        for item, lvl in commits:
            _, f = item.data(0, Qt.UserRole)
            status = self.rgd.getDirStatus(self.curBranch,  f, verbose=False, useDirStatusCache = True)
            if status != self.statusCache.get(f, ""):
                item.setText(1, status)
                self.colorizeTreeItem(item, status)
                self.statusCache[f] = status
        if not allCommits:
            self.dirStatusRefreshPointer +=20
            if self.dirStatusRefreshPointer > len(self.sortedDirItems):
                self.dirStatusRefreshPointer = 0
                self.rgd.resetDirStatusCache()

        else:
            self.dirStatusRefreshPointer = 0
            self.rgd.resetDirStatusCache()
            
        t1 =time.time()
        for item in self.fileItems:
            f, branch, eid = item.data(0, Qt.UserRole)
            if f in self.rgd.branchFiles[branch]:
                if len(self.rgd.branchFiles[branch][f]["files"])>0:
                    status = self.rgd.getDirStatus(branch, f, verbose=False, useDirStatusCache = True)
                else:
                    status = self.rgd.getFileStatus(eid, f)
            else:
                status = "not versioned"
            if status != self.statusCache.get(f, ""):
                item.setText(1, status)
                self.colorizeTreeItem(item, status)
                self.statusCache[f] = status
        print("  refreshStatus   done after %7.2fs %7.2fs" %(t1-t0, time.time() -t0),
              self.dirStatusRefreshPointer, len(self.sortedDirItems) )

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





    def doAddFile(self):
        print("add  ", self.curContextItem.text(0))
        f = self.curContextItem.text(0)
        self.rgd.addFile(f)
        self.refreshTrees()


    def doDeleteFile(self):
        print("delete  ", self.curContextItem.text(0))
        f = self.curContextItem.text(0)
        self.rgd.deleteFile(f)
        self.refreshTrees()


    def __collectModifiedFiles4Commit(self, branch, path):
        files = []
        fl = self.rgd.collectFilesFromPath(self.curBranch, path)
        for f in fl:
            if self.rgd.isModified(f):
                files.append(f)
        return files



    def doLocalCommitFromContext(self, item):
        if len(self.fileTree.selectedItems())>0:
            files = self.__getCommitFiles()
            self.__doCommit(files, push=False)
        else:
            self.__doCommit(self.__getCommitFilesFromFileItem(item), push=False)

    def doCommitAndPushFromContext(self, item):
        if len(self.fileTree.selectedItems())>0:
            files = self.__getCommitFiles()
            self.__doCommit(files, push=True)
        else:
            self.__doCommit(self.__getCommitFilesFromFileItem(item), push=True)
            

    def doLocalCommit(self):
        files = self.__getCommitFiles()
        self.__doCommit(files, push=False)
    
    def doPush(self):
        self.rgd.push()
        self.refreshTrees()
        
    
    def doCommitAndPush(self):
        files = self.__getCommitFiles()
        print(">>>>>>", files)
        self.__doCommit(files, push=True)
        
    def __getCommitFiles(self):
        files = []
        sel1 = self.dirTree.selectedItems()
        sel2 = self.fileTree.selectedItems()
        if len(sel2) == 0:
            for item in sel1:
                path   = item.data(0, Qt.UserRole)[1]
                entry  = item.data(0, Qt.UserRole)[0]
                branch = item.data(0, Qt.UserRole)[0]["branch"]
                if len(entry["files"])>0:
                    for f2 in self.__collectModifiedFiles4Commit( branch, path):
                        if f2 not in files:
                            files.append(f2)
        else:
            for item in sel2:
                for f in self.__getCommitFilesFromFileItem(item):
                    if f not in files:
                        files.append(f)
        return files
#                 f = item.data(0, Qt.UserRole)[0]
#                 branch = item.data(0, Qt.UserRole)[1]
#                 e   = self.rgd.branchFiles[branch][f]
#                 if len(e["files"])>0:
#                     for f2 in self.__collectModifiedFiles4Commit( branch, f):
#                         if f2 not in files:
#                             files.append(f2)
#                 elif self.rgd.isModified(f):
#                     if f not in files:
#                         files.append(f)


    def __getCommitFilesFromFileItem(self, item):
        f = item.data(0, Qt.UserRole)[0]
        branch = item.data(0, Qt.UserRole)[1]
        e   = self.rgd.branchFiles[branch][f]
        if len(e["files"])>0:
            for f2 in self.__collectModifiedFiles4Commit( branch, f):
                if f2 not in files:
                    return f2
        elif self.rgd.isModified(f):
            return [f]
        return []


    def __doCommit(self, files, push=True):
        self.commitDlg = CommitDialog(self, self.rgd, self.curBranch, files, push=push)
        self.commitDlg.commitExecuted.connect(self.refreshTrees)
        self.refreshStatus(allCommits=True)



    def doPull(self):
        print(" DO PULL")
        self.rgd.pull()
        self.refreshTrees()



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
            print(" DIFF ", filePath, entryId)
            self.rgd.doDiff(branch, filePath, entryId, filePath, None) 

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
            commitId = self.rgd.getCommitOfBlob(entryId, lastBefore=time.time())
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


    def showFileContent(self):
        filePath = self.curContextItem.text(0)
        if not os.path.isdir(filePath):
            blobId   = self.curContextItem.data(0, Qt.UserRole)[2]
            self.codeDisplay = CodeDisplay(self, self.rgd,  filePath, blobId)
        

    
    def doDummy(self):
        print("DUMMY ACTION")
        pass
    
    def closeApp(self):
        self.updTimer.stop()
        super().close()


 
if __name__ == '__main__':

    app  = QApplication(sys.argv)
    win  = RGitVersions(sys.argv)
    win.setWindowTitle("RGit")
    signal.signal(signal.SIGINT, win.closeApp)



    
    ret = app.exec_()
    sys.exit(ret)

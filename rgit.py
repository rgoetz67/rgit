#!/usr/bin/env python3
# File: training.py
# Time-stamp: <19-Apr-2026 18:53:01 goetz>
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
import shutil
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
from browser   import OpenRepositoryDialog
from blame     import BlameDisplay, CodeDisplay
from selectionMenu import SelectionMenu
from collections import defaultdict
from functions import loadSettings, saveSettings, baseStyle, timFormat, splitterStyle
import pygit2


class RTMessageBox(QMessageBox):
    def __init__(self, icon, title, msg, btn, pwin):
        super().__init__(icon, "RT"+title, msg, btn, pwin)
        self.ll = max( [len(l)   for l in msg.split("\n")])
        
    def resizeEvent(self, ev):
        print("!! resizeEvent",ev.size())
        self.setFixedWidth(int(self.ll * 7.5+32))
        return super().resizeEvent(ev)


class RToolButton(QToolButton):

    def __init(self, text, icon):
        super().__init__(text, icon)
        


class RGitVersions(QMainWindow):

    
    def __init__(self, argv):
        super().__init__()

        self.config, self.creds = loadSettings()
        self.statusColor = {"CURRENT"           : "#FFFFFF",
                            "MODIFIED"          : "#FF8888",
                            "ADDED"             : "#FFBB88",
                            "DELETED"           : "#EE7777",
                            "Deleted on Remote" : "#CCEE66",
                            "Remote Update"     : "#AAFFAA",
                            "Only On Remote"    : "#AAFF99",
                            "CONFLICT"          : "#FFCC88",
                            "Not Commited"      : "#CC88FF",
                            "not versioned"     : "#F4F0F0",
                            "removed from Repo" : "#F8ECEC",
#                             "" : "",
#                             "" : "",
                            "Unknown"       : "#FF88FF",
                            "No Status"     : "#EEDDDD",
                            "MODIFIED ++"   : "#FF4444",
                            "ADDED ++"      : "#FFCC44",
                            "DELETED ++"    : "#DD4444",
                            "Deleted on Remote ++" : "#CCEE44",
                            "Remote Update ++"     : "#AAFF66",
                            "Only On Remote ++"    : "#AAFF55",
                            "CONFLICT ++ "         : "#FFDD44",
                            "Not Commited ++"      : "#CC88FF",
                            "Unknown ++": "#FF44FF ++ ",
                           }
        # self.statusOrder = ["Unknown", "CONFLICT", "Remote Update", "MODIFIED", "ADDED", "Not Comitted", "CURRENT"]
        if os.path.exists(".git"):
            self.rgd         = RGitData(self.config, self.creds, ".", "main")
            self.curBranch   = self.rgd.curBranch
        else:
            self.rgd         = None
            self.curBranch   = None
        self.dirItems    = []
        self.fileItems   = []
        self.statusCache = {}
        self.dirStatusRefreshPointer = 0
        self.updateIndex = 0
        self.blockRefresh = False
        self.initUI()
        self.initMenus()
        if self.rgd is not None:
            for b in self.rgd.branches["local"] +self.rgd.branches["remote"] :
                self.branchSelect.addItem(b)
            self.branchSelect.setCurrentText(self.curBranch)
        self.updateButtonStates()
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

        self.setStyleSheet(baseStyle)


        self.tools = self.toolFrame()
        self.toolFunc = {}
        self.toolBtn= {
            "open":     self.addToolButton("Open",    progPath+"/icons/open.png",
                                           self.openRepo, "Open Repository"),
            "history":  self.addToolButton("History",    progPath+"/icons/hist.png",
                                           self.showHistory, "History of selected file"),
            "diff"   :  self.addToolButton("Diff",       progPath+"/icons/diffLocal.png",
                                           self.diffWithPrev, "Diff local changes"),
            "diffHead": self.addToolButton("Diff Head",  progPath+"/icons/diffRemote.png",
                                           self.diffWithHead, "Diff remote changes"),
            "revert" :  self.addToolButton("Restore",     progPath+"/icons/revert.png",
                                           self.doRestore, "Revert local changes"),
            "blame"  :  self.addToolButton("Blame",      progPath+"/icons/blame.png",
                                           self.showBlame, "Blame"),
            "commitL":  self.addToolButton("Commit\nLocally", progPath+"/icons/commitLocal.png",
                                           self.doLocalCommit, "Commit to local repo"),
            "commit" :  self.addToolButton("Commit\n&& Push", progPath+"/icons/commit.png",
                                           self.doCommitAndPush, "Commit to remote repo"),
            "push" :    self.addToolButton("Push Local\nto Remote", progPath+"/icons/push.png",
                                           self.doPush, "Commit to remote repo"),
            "info"   :  self.addToolButton("Info",       progPath+"/icons/info.png",
                                           None, " Repo Info"),
            "Update" :  self.addToolButton("Update\n or Pull",     progPath+"/icons/update.png",
                                           self.doPull, "Update / Pull Changes"),
            "clone"  :  self.addToolButton("Clone",      progPath+"/icons/checkout.png",
                                           self.doClone, "Checkout / Clone"),
            "branch" :  self.addToolButton("Branch",     progPath+"/icons/branch.png",
                                           None, "Branch"),
            "merge"  :  self.addToolButton("Merge",      progPath+"/icons/merge.png",
                                           None, "Merge"),
            "Delete" :  self.addToolButton("Delete",     progPath+"/icons/delete.png",
                                           self.doDeleteFile, "Delete Files from repo"),
            "refrsh" :  self.addToolButton("Refresh",    progPath+"/icons/refresh.png",
                                           self.refreshTrees, "Refresh"),
            "rebuild" :  self.addToolButton("Rebuild\nCaches",    progPath+"/icons/rebuild.png",
                                           self.rebuildRGD, "Rebuild internal caches"),
            "reset" :  self.addToolButton("Reset\nIndex",    progPath+"/icons/resetIndex.png",
                                           self.resetIndex, "Reset the local indexu"),
            }
        self.tools.layout().addWidget(QLabel(""), 100)
        self.infos = self.infoFrameFrame()


        self.splitter   = QSplitter()
        self.splitter.setStyleSheet(splitterStyle)
        self.dirFrame   = self.dirTreeFrame()
        self.filesFrame = self.fileTreeFrame()
        self.splitter.addWidget(self.dirFrame)
        self.splitter.addWidget(self.filesFrame)
        

        self.gbox.addWidget(self.tools,         1, 1, 1, 1)
        self.gbox.addWidget(self.infos,         2, 1, 1, 1)
        self.gbox.addWidget(self.splitter,      3, 1, 1, 1)

        self.gbox.setRowStretch(1,0)
        self.gbox.setRowStretch(2,0)
        self.gbox.setRowStretch(3,1)
        if self.rgd is not None:
            self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
            self.dirTree.addTopLevelItem(self.rootItem)
            self.fill(self.curBranch)
            self.rootItem.setExpanded(True)
            self.fillFileList(self.rootItem)
            self.isFilled = True
        else:
            self.rootItem = None
            self.isFilled = False
            
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
        QShortcut(QKeySequence("Ctrl+r"), self.fileTree, self.doRestore)
        QShortcut(QKeySequence("Ctrl+d"), self.fileTree, self.diffWithPrev)
        QShortcut(QKeySequence("Ctrl+Shift+d"),  self.fileTree, self.diffWithHead)
#        self.dirTree.setMaximumWidth(1200)
        self.resize(1670,960)
        self.setMinimumSize(1280,640)
        self.splitter.setSizes([280,1200])

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
                            "sep1"    : self.menu["modified"].addSeparator(),
#                             "revert"  : self.menu["modified"].addAction("Revert local changes"),
#                             "restore" : self.menu["modified"].addAction("Restore from Origin"),
                            "restore" : self.menu["modified"].addAction("Restore from Local"),
                            "sep1"    : self.menu["modified"].addSeparator(),
                            "remove"  : self.menu["modified"].addAction("Remove from Repo"),
                            "move"    : self.menu["modified"].addAction("Move File"),
                            "sep1"    : self.menu["modified"].addSeparator(),
                            "blame"   : self.menu["modified"].addAction("Blame"),
                            "show"    : self.menu["modified"].addAction("Show Content"),
                            
                            "removeC" : self.menu["commited"].addAction("Remove from Repo"),
#                            "restoreC": self.menu["commited"].addAction("Restore from Origin"),
                            "showC"   : self.menu["commited"].addAction("Show Content"),
                            "blameC"  : self.menu["commited"].addAction("Blame"),
                            "moveC"   : self.menu["commited"].addAction("Move File"),

                            "update"  : self.menu["remoteUp"].addAction("Update to origin"),

                            }

        self.menuActions["add"].triggered.connect(self.doAddFile)
        self.menuActions["showN"].triggered.connect(self.showFileContent)
        
        self.menuActions["remove"].triggered.connect(self.doDeleteFile)
    #    self.menuActions["revert"].triggered.connect(self.doDummy)
        self.menuActions["restore"].triggered.connect(self.doRestoreFile)
        self.menuActions["commit"].triggered.connect(self.doCommitAndPushFromContext)
        self.menuActions["commitL"].triggered.connect(self.doLocalCommitFromContext)
        self.menuActions["show"].triggered.connect(self.showFileContent)
        self.menuActions["blame"].triggered.connect(self.showBlameFromContext)
        self.menuActions["move"].triggered.connect(self.doDummy)

        self.menuActions["removeC"].triggered.connect(self.doDeleteFile)
#        self.menuActions["restoreC"].triggered.connect(self.doDummy)
        self.menuActions["showC"].triggered.connect(self.showFileContent)
        self.menuActions["blameC"].triggered.connect(self.showBlameFromContext)
        self.menuActions["moveC"].triggered.connect(self.doDummy)

        self.menuActions["update"].triggered.connect(self.doDummy)



    def toolFrame(self):
        f=QFrame()
        self.tbox =QHBoxLayout()
        f.setLayout(self.tbox)
        return f


    def infoFrameFrame(self):
        f=QFrame()
        self.ibox =QHBoxLayout()
        f.setLayout(self.ibox)
        self.ibox.setSpacing(0)
        self.ibox.setContentsMargins(2,8,2,8)

        self.infoLocalRepo  = QLabel("Local Repository: ")
        self.infoCurBranch  = QLabel("Current branch = ")
        self.infoRemoteRepo = QLabel("Remote repo branch = ")
        self.infoRemoteURL  = QLabel(" @  ")
        self.infoLocalRepo.setStyleSheet("QLabel { font-size:14px; font-weight:bold; margin-right:3em}")
        self.infoCurBranch.setStyleSheet("QLabel { font-size:14px; font-weight:bold; margin-right:3em}")
        self.infoRemoteRepo.setStyleSheet("QLabel { font-size:14px; font-weight:bold;}")
        self.infoRemoteURL.setStyleSheet("QLabel { font-size:14px; font-weight:bold; }")
        self.infoCurBranch.setMinimumWidth(200)
        self.infoRemoteRepo.setMinimumWidth(240)

        icon = QIcon(os.path.dirname(__file__)+"/icons/plus-solid-full.svg")
        self.bookmarkBtn = QPushButton(icon, "")
        self.bookmarkBtn.setMinimumHeight(24)
        self.bookmarkBtn.setMaximumHeight(24)
        self.bookmarkBtn.setMinimumWidth(24)
        self.bookmarkBtn.setMaximumWidth(24)
        self.bookmarkBtn.clicked.connect(self.addBookmark)
        self.bookmarkBtn.setToolTip("Bookmark current Repository/branch")
        self.ibox.addWidget(self.infoLocalRepo, 0)
        self.ibox.addWidget(self.infoCurBranch, 0)
        self.ibox.addWidget(self.infoRemoteRepo, 0)
        self.ibox.addWidget(self.infoRemoteURL, 0)
        self.ibox.addWidget(QLabel(" "), 1)
        self.ibox.addWidget(self.bookmarkBtn, 0, Qt.AlignRight)
        return f


    def dirTreeFrame(self):
        f = QFrame()
        self.vdbox = QVBoxLayout()
        f.setLayout(self.vdbox)
        self.vdbox.setSpacing(4)
        self.vdbox.setContentsMargins(1,1,1,1)

        self.branchSelect = QComboBox()
        self.branchSelect.currentTextChanged.connect(self.switchBranch)
        self.branchSelect.hide()
        self.dirTree  = QTreeWidget()
        self.dirTree.setMinimumSize(400,800)
        self.dirTree.setHeaderLabels(["Directory","Status"])

#        self.vdbox.addWidget(self.branchSelect,0)
        self.vdbox.addWidget(self.dirTree,1)
        self.dirTree.setMinimumWidth(180)
        f.setMinimumWidth(180)

        return f


    def fileTreeFrame(self):
        f = QFrame()
        self.gfbox = QGridLayout()
        f.setLayout(self.gfbox)
        self.gfbox.setSpacing(4)
        self.gfbox.setContentsMargins(1,1,1,1)

        self.fileTree = QTreeWidget()
        self.fileTree.setMinimumSize(1200,800)
        self.fileTree.setColumnCount(8)
        self.fileTree.setHeaderLabels(["File","Status", "Commit Hash", "Blob Hash", "Revision", "Author", "Last Change", "Branches", "Tags"])
        self.fileTree.setContextMenuPolicy(Qt.CustomContextMenu);
        self.fileTree.setSortingEnabled(True)

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

        self.gfbox.addWidget(self.fileTree,  1, 1, 1, 3)
        self.gfbox.addWidget(self.showLocal, 2, 2, 1, 1)
        self.gfbox.addWidget(self.lFileType, 2, 3, 1, 1)
        self.gfbox.addWidget(self.fileTypes, 2, 4, 1, 1)
        self.gfbox.setColumnStretch(1,1)
        self.gfbox.setColumnStretch(2,0)
        self.gfbox.setColumnStretch(3,0)
        self.gfbox.setColumnStretch(4,0)
        self.gfbox.setRowStretch(1,1)
        self.gfbox.setRowStretch(2,0)
        self.fileTree.setMinimumHeight(480)
        self.fileTree.setMinimumWidth(640)
        self.fileTree.setMaximumWidth(9640)
        f.setMinimumWidth(640)

        return f



    def addToolButton(self, text, iconFile, func, tooltip):
        toolButton = QToolButton()
        toolButton.setMinimumHeight(80)
        toolButton.setMinimumWidth(48)
        toolButton.setIcon( QIcon(iconFile))
        toolButton.setIconSize(QSize(48,48))
        toolButton.setText(text)
        # print(">>toolButton>>", text)
        toolButton.setStyleSheet("QToolButton {font-size:9px; padding:2px}")
        if func is None:
            toolButton.setToolTip(tooltip + "\n (disabled)")
        else:
            toolButton.setToolTip(tooltip)
        if func is not None:
            toolButton.clicked.connect(func)
#         else:
#             toolButton.setEnabled(False)
        self.toolFunc[toolButton] = func
        toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);
        self.tools.layout().addWidget(toolButton)
        return  toolButton



    def updateButtonStates(self):
        if self.rgd is None:
            self.__updateButtonStates(["open"])
        elif self.rgd.isRemoteOnly():
            self.__updateButtonStates(["open", "history", "diffHead", "info", "blame", "clone", "refrsh"])
        else:
            self.__updateButtonStates(["open",   "history",  "diff",    "diffHead", "revert", "info",
                                       "blame",  "commityL", "commit",  "push",     "Update", 
                                       "clone",  "branch",   "merge",   "Delete",   "refrsh", "rebuild", "reset"])
            
    def __updateButtonStates(self, enabledButtons):
        # print("   __updateButtonStates :", enabledButtons)
        for name, btn in self.toolBtn.items():
            if name in enabledButtons and self.toolFunc[btn] is not None:
                # print("\t\t", name, self.toolFunc[btn] )
                btn.setEnabled(True)
            else:
                # print("\t\t diasable", name)
                btn.setEnabled(False)


    def switchBranch(self, branch):
        self.rgd.getBranchData(branch)
        # print(" FIXME: switch branch on file system")
        


    def switchRepo(self, repoType, repoPath):
        self.isFilled    = False
        self.rgd         = RGitData(self.config, self.creds, repoPath)
        if self.repoDlg.isVisible():
            if self.rgd.failedToOpen:
                self.repoDlg.setMessage4remoterepo(self.rgd.failMessage)
                return
            else:
                self.repoDlg.close()
        if self.rgd.failedToOpen:
            #FIXME Dialog
            pass
            
        self.curBranch   = self.rgd.curBranch
        self.branchSelect.blockSignals(True)
        self.branchSelect.clear()
        for b in self.rgd.branches["local"] +self.rgd.branches["remote"] :
            self.branchSelect.addItem(b)
        self.branchSelect.setCurrentText(self.curBranch)
        self.branchSelect.blockSignals(False)

        if self.rootItem is None :
            self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
            self.dirTree.addTopLevelItem(self.rootItem)
        self.fill(self.curBranch)
        self.fillFileList(self.rootItem)
        self.updateButtonStates()
        self.isFilled =  True
#         if self.repoType == "remote":
#             self.toolBtn["clone"].setEnabled(True)
#         else:
#             self.toolBtn["clone"].setEnabled(False)



    def resizeDirTree(self):
        for c in range(2):
            self.dirTree.resizeColumnToContents(c)


    def resizeFileTree(self):
        for c in range(self.fileTree.columnCount()-1):
            self.fileTree.resizeColumnToContents(c)


        

    def fill(self, branch=None):
        if self.rgd.localRepoPath is not None:
            self.infoLocalRepo.setText("Local Repository: "+self.rgd.localRepoPath)
        else:
            self.infoLocalRepo.setText("Local Repository: none")
        self.infoCurBranch.setText("Current branch = "+self.rgd.curBranch)
        self.infoRemoteRepo.setText("Remote repo branch = "+self.rgd.curRemoteBranch)
        self.infoRemoteURL.setText("  @    " + self.rgd.curRemoteUrl)
        self.dirItems = []
        # print("######", branch, self.rgd.branchFiles[branch].keys())
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
        # print(">>>>", parentItem, parentItem.data(0, Qt.UserRole))
        self.fileItems = []
        self.fileTree.clear()
        files  = parentItem.data(0, Qt.UserRole)[0]["files"]
        branch = parentItem.data(0, Qt.UserRole)[0]["branch"]
        folder = parentItem.data(0, Qt.UserRole)[1]

        localFiles = []
        remoteOnlyFiles = []
        extFilter  = self.__acceptedExtensions()
        for f in glob.glob(folder + "/*"):
            if not os.path.isdir(f) and  self.rgd.isAdded(f):
                print("   local file is ADDED", f)
                localFiles.append(f)
            elif self.showLocal.isChecked():
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

        
#         if self.showLocal.isChecked():
#             extFilter  = self.__acceptedExtensions()
#             for f in glob.glob(folder + "/*"):
#                 if f not in files:
#                     if os.path.isdir(f):
#                         localFiles.append(f+"/")
#                     else:
#                         ext = os.path.splitext(f)[1]
#                         if ext in extFilter:
#                             if extFilter[ext]:
#                                 localFiles.append(f)
#                         else:
#                             if extFilter["."]:  # aka other files
#                                 localFiles.append(f)
#         elif len(self.rgd.addedFiles)>0:
#             for f in self.rgd.addedFiles:
#                 if  f[:len(folder)] == folder:
#                     if "/" not in f[len(folder)+1:] and f != folder:
#                         localFiles.append(f)
        for f in self.rgd.remoteOnlyFiles:
            if  f[:len(folder)] == folder:
                if f not in files:
                    if "/" not in f[len(folder)+1:] and f != folder:
                        remoteOnlyFiles.append(f)
        # print(">>>  files      ", files)
        # print(">>>  remote only", remoteOnlyFiles)
        print(">>>  local  only", localFiles)
        allFiles = files + localFiles + remoteOnlyFiles

        for f in sorted(allFiles):
           #  print("\t add ", branch, f, f in files, f in  self.rgd.branchFiles[branch])
            if f in files or f in remoteOnlyFiles:
                if f in remoteOnlyFiles:
                    e = self.rgd.branchFiles[self.rgd.curRemoteBranch][f]
                else:
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
                # print("\t\t ==>", item)
            self.statusCache[f] = status
        self.resizeFileTree()


    def showFileContextMenu(self, p):
        item = self.fileTree.itemAt(p)
        print("custom menu at ",p, item, item.text(0), item.text(1))
        status = item.text(1)
        if status == "not versioned":
            self.curContextItem = item
            self.menu["addOnly"].popup(self.cursor().pos())
        elif status in ["MODIFIED"] or "MODIFIED" in status:
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
            if dirName == self.rgd.projectName():
                self.dirTree.setCurrentItem(self.rootItem)
                self.showFiles(self.rootItem)
            else:
                for item, _ in self.dirItems:
                    if item.text(0) == dirName:
                        self.dirTree.setCurrentItem(item)
                        self.showFiles(item)
                        break
        else:
            print("\t\t-> show files of ROOT")
            self.dirTree.setCurrentItem(self.rootItem)
            self.showFiles(self.rootItem)
        self.resizeDirTree()
        self.resizeFileTree()
        

    def refreshStatus(self, allCommits = False):
        if self.rgd is None or not self.isFilled or self.blockRefresh:
            return
        self.rgd.fetch()
        t0 =time.time()
        print("  refreshStatus  ", self.blockRefresh)
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
            elif f in self.rgd.remoteOnlyFiles:
                status = self.rgd.getFileStatus(eid, f)
            else:
                status = "not versioned"
            if status != self.statusCache.get(f, ""):
                item.setText(1, status)
                self.colorizeTreeItem(item, status)
                self.statusCache[f] = status
        self.resizeFileTree()
#        print("  refreshStatus   done after %7.2fs %7.2fs" %(t1-t0, time.time() -t0))

    def colorizeTreeItem(self, item, status):
        if status != "CURRENT":
            if status in self.statusColor:
                self.setFileTreeItemColor(item, self.statusColor[status])
            else:
                self.setFileTreeItemColor(item, self.statusColor["Unknown"])
        else:
            self.setFileTreeItemColor(item, "#FFFFFF")

    def setFileTreeItemColor(self, item, color):
        for c  in range(self.fileTree.columnCount()):
            item.setBackground(c, QBrush(color))
                        

    def showFiles(self, e):
        self.fillFileList(e)





    def doAddFile(self):
        # print("add  ", seilf.curContextItem.text(0))
        f = self.curContextItem.text(0)
        self.rgd.addFile(f)
        self.refreshStatus()
        self.refreshTrees()


    def doDeleteFile(self):
        sel = self.fileTree.selectedItems()
        print(" :::: doDeleteFile", sel)
        if len(sel) ==1 :
            fileName = sel[0].text(0)
            ret = QMessageBox.question(self, "Delete File from Repository?",
                                       "Do you want to delete\n'%s'\nfrom the repository" % fileName)
        elif len(sel) > 1:
            ret = QMessageBox.question(self, "Delete File from Repository?",
                                       "Do you want to delete\n %d files \nfrom the repository" % len(sel))
        else:
            return
        print(ret == QMessageBox.Yes)
        for item in sel:
            fileName = item.text(0)
            self.rgd.deleteFile(fileName)
        self.refreshStatus()
        self.refreshTrees()

        
    def doDeleteFileFromContext(self):
        print("delete  ", self.curContextItem.text(0))
        f = self.curContextItem.text(0)
        self.rgd.deleteFile(f)
        self.refreshStatus()
        self.refreshTrees()


    def doRestoreFile(self, f = None):
        if f is None or not isinstance(f, str):
            print("restore  ", self.curContextItem.text(0))
            f = self.curContextItem.text(0)
        self.rgd.restoreFile(f)
        self.refreshStatus()
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
        self.blockRefresh = True
        self.rgd.push()
        self.blockRefresh = False
        self.refreshTrees()
        
    
    def doCommitAndPush(self):
        files = self.__getCommitFiles()
        # print(">>>>>>", files)
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
            for f in self.rgd.addedFiles:
                files.append(f)
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
        self.blockRefresh = True
        sucess, msg = self.rgd.pull()
        if not sucess:
            msg = RTMessageBox(QMessageBox.Critical, msg[0], msg[1], QMessageBox.Ok, self)
            msg.setStyleSheet("RTMessageBox {font-weight:bold; font-size:16px; min-width:640px; width:640px; color:green}\n")
            ret =msg.exec()
        self.blockRefresh = False
        self.refreshTrees()



    def doRestore(self):
        sel = self.fileTree.selectedItems()
        files = []
        for i,e in enumerate(sel):
            f = e.data(0, Qt.UserRole)[0]
            if self.rgd.isModified(f):
                files.append(f)
        for f in files:
            self.doRestoreFile(f)


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


    def showBlameFromContext(self):
        filePath = self.curContextItem.text(0)
        if not os.path.isdir(filePath):
            self.__showBlame(self.curContextItem)

                
    def showBlame(self):
        sel = self.fileTree.selectedItems()
        # print(">>>", sel)
        if len(sel) == 1:
            self.__showBlame(sel[0])

    def __showBlame(self, item):
        print("---->", item)
        print("---->", item.text(0))
        print("---->", item.data(0, Qt.UserRole))
        fileName = item.text(0)
        filePath = item.data(0, Qt.UserRole)[0]
        branch   = item.data(0, Qt.UserRole)[1]
        entryId  = item.data(0, Qt.UserRole)[2]
        commitId = self.rgd.getCommitOfBlob(entryId, lastBefore=time.time())
        # print ("BLAME : ", branch, entryId, commitId)
        # print ("BLAME : ", filePath)
        self.blameDisplay = BlameDisplay(self, self.rgd, branch, filePath, commitId, blobId=entryId)


    def openRepo(self):
        self.repoDlg = OpenRepositoryDialog(self, self.creds)
        self.repoDlg.openRepository.connect(self.switchRepo)
        

    def doClone(self):
        dirPath = QFileDialog.getExistingDirectory(self, "Directory for  local repository")
        if os.path.exists(dirPath) and dirPath != "":
            print("move ", self.rgd.tmpRepoPath, " to ", dirPath)
            shutil.move(self.rgd.tmpRepoPath, dirPath)
            newRepoPath = dirPath + "/" + os.path.basename(self.rgd.tmpRepoPath)
            self.switchRepo("local", newRepoPath)

        
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
        

    def resetIndex(self):
        self.rgd.resetIndex()


    def rebuildRGD(self):
        self.isFilled    = False
        curRepoPath      = self.rgd.repoPath
        self.rgd         = RGitData(self.config, self.creds, curRepoPath, forcedRebuild=True)
        self.curBranch   = self.rgd.curBranch
        self.branchSelect.blockSignals(True)
        self.branchSelect.clear()
        for b in self.rgd.branches["local"] +self.rgd.branches["remote"] :
            self.branchSelect.addItem(b)
        self.branchSelect.setCurrentText(self.curBranch)
        self.branchSelect.blockSignals(False)

        if self.rootItem is None :
            self.rootItem = QTreeWidgetItem([self.rgd.projectName()])
            self.dirTree.addTopLevelItem(self.rootItem)
        self.fill(self.curBranch)
        self.fillFileList(self.rootItem)
        self.updateButtonStates()
        self.isFilled =  True


    def getNameOfBookmarkedRepo(self, repoPath, bookmarks):
        repoName = None
        for rn, rp in bookmarks.items():
            if isinstance(rp, dict):
                return self. getNameOfBookmarkedRepo(repoPath, rp)
            
            if rp[0]  == repoPath[0] and rp[1] == repoPath[1]:
                repoName = rn
                break
        return repoName


    def addBookmark(self):
        if self.rgd.localRepoPath is not None:
            repoPath = ("local", self.rgd.localRepoPath)
            repoName = os.path.basename(self.rgd.localRepoPath)
        else:
            repoPath = ("remote", self.rgd.repoPath)
            repoName = os.path.basename(self.rgd.repoPath)[:-4]
        oldName = self. getNameOfBookmarkedRepo(repoPath,  self.config.get("bookmarks", {}))

        if oldName is not None:
            msg = "The %s repository at %s\n has already been bookmarks\n by the name '%s'"%\
                  (repoPath[0], repoPath[1], oldName)
            dlg = QMessageBox.warning(self, "Repository alreday bookmarked", msg)
            dlg.exec()
            return

        if "bookmarks" not in self.config:
             self.config["bookmarks"] = {}
        repoName1 = repoName
        if  repoName in self.config["bookmarks"]:
            repoName = repoName1 + " (%s)" % repoPath[0]

        n=1
        while repoName in self.config["bookmarks"]:
            n+=1
            repoName = repoName1 + " (%s) #%d" % (repoPath[0] , n)
            
        self.config["bookmarks"][repoName] = repoPath
        saveSettings(self.config, self.creds)
        
            
    
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



    
    ret = app.exec()
    sys.exit(ret)

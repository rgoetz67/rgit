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

# repo.status("README.md")  -> return locally changed files


# def __scanDir(p):
#     prev = os.getcwd()
#     os.chdir(p)
#     tree = {}
#     fl = glob.glob("*") + glob.glob(".??*")
#     fl2 = glob.glob(".??*")
#     for f in fl:
#         if os.path.isdir(f):
#             if f not in [".git", "github", ".devcontainer"]:
#                 tree[f] = __scanDir(f)
#         else:
#             tree[f] = None
#     os.chdir(prev)
#     return tree

            

# def filesInLocalRepo(localRepoPath):
#     return __scanDir(localRepoPath)



# def __scanGitTree(repo, tree, path):
#     et = {}
#     for entry in tree:
#         name = entry.name
#         if entry.filemode == pygit2.GIT_FILEMODE_TREE:
#             nextTree = repo.get(entry.id)
#             et[name] = (entry,
#                         __scanGitTree(repo, nextTree, path+"/"+entry.name),
#                         path+"/"+entry.name)
#         else:
#             et[name] = (entry, None, path+"/"+entry.name)
#     return et


# def lsTree(repo, branch):
#     tree = repo.revparse_single(branch).tree
#     return __scanGitTree(repo, tree, ".")



# def __scanGitTreeFP(repoFiles, repo, tree, path):
#     for entry in tree:
#         name = path+"/"+entry.name
#         if entry.filemode == pygit2.GIT_FILEMODE_TREE:
#             nextTree = repo.get(entry.id)
#             repoFiles[name] = (entry, True, entry.name)
#             __scanGitTreeFP(repoFiles, repo, nextTree, path+"/"+entry.name),
#         else:
#             repoFiles[name] = (entry, False, entry.name)
#     return repoFiles


# def lsTreeFP(repo, branch, indexByFullPath=False):
#     repoFiles = {}
#     tree = repo.revparse_single(branch).tree
#     return __scanGitTreeFP(repoFiles, repo, tree, ".")



from collections import defaultdict


# def collectCommitsFromTree(tree, commit):
#     global commitByObj, allCommits
#     for e in tree:
#         allCommits[e.id].append( commit)

#         if e.filemode == pygit2.GIT_FILEMODE_TREE:
#             nextTree = repo.get(e.id)
#             collectCommitsFromTree(nextTree, commit)
#         else:
#             if e.id in commitByObj:
#                 if commitByObj[e.id].commit_time > commit.commit_time:
#                     commitByObj[e.id] = commit
#             else:
#                 commitByObj[e.id] = commit



# def collectCommits(repo):
#     global commitByObj, allCommits
#     commitByObj = {}
#     allCommits  = defaultdict(list)
#   #  commitByName = {}
#     walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)
#     commitList = list(reversed([c  for c in walker]))
#     for commit in commitList:
#         for e in commit.tree:
#             allCommits[e.id].append( commit)
#             if e.filemode == pygit2.GIT_FILEMODE_TREE:
#                 nextTree = repo.get(e.id)
#                 collectCommitsFromTree(nextTree, commit)
#             else:
#                 if e.id in commitByObj:
#                     if commitByObj[e.id].commit_time > commit.commit_time:
#                         commitByObj[e.id] = commit
#                 else:
#                     commitByObj[e.id] = commit
# #            commitByName[e.name] = commit
# #    return commitByObj, commitByName
#     return commitByObj

# # collectCommits(repo)


class RToolButton(QToolButton):

    def __init(self, text, icon):
        super().__init__(text, icon)
        



import pygit2

# FUNCTIONS:
#    UPDATE
#    COMMIT
#    COMMIT & PUSH
#    HISTORY
#    DIFF
#    BLAME
#    REVERT
#    REVERT FROM REMOTE
#
#    BRANCH
#    SWITCH BRANCH
class RGitVersions(QMainWindow):




    # self.blobPath[branch][blob.id] = {"Path":path, "lastCommit": (lastCommit.id, lastCommitTime, blob.id)}   ->cached
    # self.allCommitIds [branch]     = set( commitId)     -> cached
    # ### self.branchPath[branch] = [path]
    # self.branchPath[path] = [branches]
    # self.repoFiles[path] = { "name":name, 
    #                          "isDir":  bool
    #                          "lastCommit" : (commit.id, commitTime) 
    #                          "commits" : [(commit.id, commitTime, blob.id/tree.id) ....]
    #                          "files" : [ path, ....]}   -> cached and updated on start
    # global cache: repoFiles
    # branchCache : blobPath allCommitIds  
    

    
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
#         self.repo       =  pygit2.Repository(".")
#         self.remotes    = list(self.repo.remotes)
        
#         for rem in self.remotes:
#             print("REMOTE: ", rem.name, rem.url, type(rem))
#             self.repo[rem.name] = pygit2.Repository(rem.url)
#         self.branches   = {"local": list(self.repo.branches.local),
#                            "remote" : list(self.repo.branches.remote)}

#         self.localFiles = filesInLocalRepo(".")

#         self.allCommits   = {"local" : defaultdict(dict)}
#         self.allObjects   = {"local" : defaultdict(dict)}
#         self.commitByObj  = {"local" : defaultdict(dict)}
#         self.repoFiles    = {}
#         self.lastObj      = {"local" : defaultdict(dict)}
#         self.treeSet      = {"local" : defaultdict(dict)}
#         self.blobSet      = {"local" : defaultdict(dict)}
#         self.blobPath     = defaultdict(dict)
#         self.branchFiles  = defaultdict(dict)
#         self.allCommitIds = defaultdict(set)
#         self.branchPath   = defaultdict(set)
#         self.collectedBranched = set()

#         self.primaryBranches = ["main", "origin/HEAD"]
#         self.loadCaches(self.primaryBranches)
        #         self.repoFiles["local"]  = lsTree(self.repo, self.curBranch)
        #         self.repoFiles["remote"] = lsTreeFP(self.repo, "origin")
#         t0 = time.time()
#         print("------")
#         self.getBranchFiles(self.curBranch)
# #        self.getFileList(self.curBranch)
#         print("------")
#         self.getBranchFiles("origin/HEAD")
#         self.branches = {"local" : list(self.repo.branches.local),
#                          "remote": list(self.repo.branches.remote)}
        
# #        self.getFileList("origin")
#         print("------> %7.2fs" %(time.time()-t0))
        
#         self.collectCommits("main")
#         print("------------> %7.2fs" %(time.time()-t0))
#         self.collectCommits("origin/HEAD")
#         print("-----------------> %7.2fs" %(time.time()-t0))
# #         for b in self.branches["local"] +self.branches["remote"] :
# #             if b not in self.collectedBranched:
# #                 t1 =time.time()
# #                 self.collectCommits(b)
# #                 print("-----------------> %7.2fs   (%7.2fs)" %(time.time()-t0, time.time()-t1))
                
#         self.postProcess()
#         self.saveCaches(self.primaryBranches, repoFiles=True)
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
        toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);
        self.tools.layout().addWidget(toolButton)
        return  toolButton


    
#     def __getFileList(self, branch, tree, parentPath):
#         files = []
#         for entry in tree:
#             seid =str(entry.id)
#             path = parentPath+entry.name
#             files.append(path)
#             if entry.filemode == pygit2.GIT_FILEMODE_TREE:
#                 path    += "/"
#                 nextTree = self.repo.get(entry.id)
#                 self.repoFiles[path] = self.__newRepoFile(entry.name, isDir=True, branch=branch,
#                                                           files= self.__getFileList(branch, nextTree, path))
#                 self.treeSet[branch][entry.id]  = entry
#                 self.blobPath[branch][seid] = {"path": path,  "lastCommit":["", 0]}
#             else:
#                 self.repoFiles[path] = self.__newRepoFile(entry.name, branch=branch)
#                 self.blobSet[branch][entry.id]  = entry
#                 self.blobPath[branch][seid] = {"path":path,  "lastCommit":["", 0]}
#         return files



#     def __scanBranchTree(self, branch, tree, parentPath):
#         files = []
#         for entry in tree:
#             path = parentPath+"/"+entry.name
#             self.branchFiles[branch][parentPath]["files"].append(path)
#             self.branchFiles[branch][path] = {"id":str(entry.id), "name":entry.name, "branch":branch, "files":[]}
#             if entry.filemode == pygit2.GIT_FILEMODE_TREE:
#                 nextTree = self.repo.get(entry.id)
#                 self.__scanBranchTree(branch, nextTree, path)

    

#     def getBranchFiles(self, branch):
#         self.branchFiles[branch] = {"." :{"id":None, "name":"", "branch":branch, "files":[]} }
#         tree = self.repo.revparse_single(branch).tree
#         self.__scanBranchTree(branch, tree, ".")
# #        print(">>>>>", self.branchFiles.keys())
# #         self.blobPath[branch]  = {}
# #         self.treeSet[branch]   = {}
# #         self.blobSet[branch]   = {}
        
# #         if "./" not in self.repoFiles:
# #             self.repoFiles["./"] = self.__newRepoFile("./", isDir=True, branch=branch,
# #                                                      files= self.__getFileList(branch, tree, "./"))


#     def __newRepoFile( self, name, isDir=False,  files = None):
#         commits = []
#         return  { "name":name,
#                   "isDir":isDir,
#                   "commits": commits ,
#                   "files" :files or []
#                   }


#     def collectBlobsFromTree(self, branchName, tree, commit, parentPath):
#         repo   = self.repo
#         for e in tree:
#             path = parentPath+"/"+ e.name
# #             if e.name == "command-rebase.yml":
# #                 print("\t\t found ", e.name, branchName)
#             if e.filemode == pygit2.GIT_FILEMODE_TREE:
#                 isDir = True
#             else:
#                 isDir = False

#             if path not in  self.repoFiles:
#                 print("\t * add path to repoFiles:", path)
#                 self.repoFiles[path] = self.__newRepoFile(e.name, isDir=isDir)
#             else:
#                 self.branchPath[path].add(branchName)

#             if path not in self.repoFiles[parentPath]["files"]:
#                 self.repoFiles[parentPath]["files"].append(path)

                
#             if isDir:
#                 nextTree = repo.get(e.id)
#                 self.collectBlobsFromTree(branchName,nextTree, commit,path)
#             esid = str(e.id)
#             com  = [str(commit.id), commit.commit_time, str(e.id)]
#             if esid in self.blobPath:
#                 if commit.commit_time < self.blobPath[branchName][esid]["lastCommit"][1]:
#                     self.blobPath[branchName][esid]["lastCommit"] = com
#             else:
#                 self.blobPath[branchName][esid] = {"path":path, "lastCommit":com}


#     def addBranchToCommits(self, branchName, tree, commit, parentPath):
#         repo   = self.repo
#         for e in tree:
#             path = parentPath+"/"+ e.name
#             self.branchPath[path].add(branchName)


#     def collectCommits(self, branchName):
#         print("collectCommits", branchName)
#         self.collectedBranched.add(branchName)
#         if branchName not in self.allCommitIds:
#             self.allCommitIds[branchName] = set()
#         if branchName not in self.blobPath:
#             self.blobPath[branchName] = {}
        
#         repo   = self.repo
#         walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME )
#         commitList = list([c  for c in walker])
#         if "." not in self.repoFiles:
#             self.repoFiles["."] = self.__newRepoFile(".", isDir=True)
#         prevTime = commitList[0].commit_time +10
#         for commit in commitList:
#             if commit.id in self.allCommitIds[branchName]:
#                 self.addBranchToCommits(branchName, commit.tree, commit, ".")
#             if str(commit.id) not in self.allCommitIds[branchName]:
#                 self.allCommitIds[branchName].add(str(commit.id))
#                 self.collectBlobsFromTree( branchName, commit.tree, commit, ".")

#         for eid in self.blobPath[branchName]:
#             path       = self.blobPath[branchName][eid]["path"]
#             lastCommit = self.blobPath[branchName][eid]["lastCommit"]
#             if path not in  self.repoFiles:
#                 self.repoFiles[path] = self.__newRepoFile(os.path.basename(path), isDir=path[-1]=="/")
#             if len(lastCommit) != 3:
#                 print(">>lastC>>>", lastCommit)
#             if lastCommit[1] >0:
#                 self.repoFiles[path]["commits"].append(lastCommit )

            

#     def postProcess(self):
#         for p in self.repoFiles:
#             tmp = list(set([ tuple(e)   for e in self.repoFiles[p]["commits"]]))
#             self.repoFiles[p]["commits"] = [list(e)  for e in tmp]
#         for path in self.repoFiles:
#             self.repoFiles[path]["commits"] = list(sorted(self.repoFiles[path]["commits"],  key=lambda x:x[1]))
#             if len(self.repoFiles[path]["commits"] )>0:
#                 self.repoFiles[path]["lastCommit"] = self.repoFiles[path]["commits"][-1]
#             else:
#                 if not self.repoFiles[path]["isDir"]:
#                     print("No commits for ", path, "\t", self.repoFiles[path]["isDir"])
#                     #                print("No commits for ", path, "\t", self.repoFiles[path]["isDir"])


    def switchBranch(self, branch):
        self.rgd.getBranchData(branch)
        print(" FIXME: switch branch on file system")
        

#     def loadCaches(self, branches):
#         if not os.path.exists(".rgc"):
#             os.makedirs(".rgc")
#         if os.path.exists(".rgc/__rf__"):
#             with open(".rgc/__rf__") as inp:
#                 print("LOAD RF CACHE")
#                 self.repoFiles = json.load(inp)
#         for branch in branches:
#             self.loadBranchCache(branch)

            
#     def loadBranchCache(self, branch):
#         cf = ".rgc/"+branch
#         if not os.path.exists(os.path.dirname(cf)):
#             os.makedirs(os.path.dirname(cf))
#         if os.path.exists(cf):
#             with open(cf) as inp:
#                 print("LOAD  %s CACHE"% branch)
#                 conf =json.load(inp)
#                 self.blobPath[branch] = conf["blobs"]
#                 self.allCommitIds[branch] = set(conf["commits"])
#             for e in self.blobPath[branch].values():
#                 self.branchPath[e["path"]].add(branch)
                

#     def saveCaches(self, branches, repoFiles=False):
#         if not os.path.exists(".rgc"):
#             os.makedirs(".rgc")
#         if repoFiles:
#             with open(".rgc/__rf__", "w") as out:
#                 print("SAVE RF CACHE")
#                 json.dump(self.repoFiles, out , indent=4)
#         for branch in branches:
#             cf = ".rgc/"+branch
#             if not os.path.exists(os.path.dirname(cf)):
#                 os.makedirs(os.path.dirname(cf))

#             with open(cf, "w") as out:
#                 print("SAVE %s CACHE" % branch)
#                 cache = {"blobs"     : self.blobPath[branch],
#                          "commits"   : list(self.allCommitIds[branch])
#                          }
#                 json.dump(cache, out , indent=4)


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
    
#         for c in range(2):
#             self.dirTree.resizeColumnToContents(c)

        #        print(">>>>>>", self.repoFiles.keys())
        # print(">>>>>>>>>>", self.repoFiles["."]["files"])
#         for f in self.repoFiles["."]["files"]:
#             p =self.__activePath(f)
#             if p is None:
#                 continue
                
#             if self.curBranch in  self.repoFiles[p]["branches"]:
#                 e = self.repoFiles[p]
#                 if e["isDir"]:
#                     item = QTreeWidgetItem(self.rootItem, [e["name"]])
#                     item.setData(0, Qt.UserRole , e)
#                     self.__fill(e,  item)
                

    def __fill(self, branch, parentElem, parentPath, parentItem):
        for f in parentElem["files"]:
#           for f in self.branchFiles[branch][parentPath]["files"]:
                e = self.rgd.branchFiles[branch][f]
                if len(e["files"])>0:
                    item = QTreeWidgetItem(parentItem, [e["name"], ""])
                    item.setData(0, Qt.UserRole , (e, f))
                    self.__fill(branch, e,  f, item)
                    if f == "./.github/workflows":
                        print(" >>", f, "->", e["files"])


#              if self.curBranch in  self.repoFiles[p]["branches"]:
#                 e = self.repoFiles[p]
#                 if e["isDir"]:
#                     item = QTreeWidgetItem(parentItem, [e["name"]])
#                     item.setData(0, Qt.UserRole , e)
#                     self.__fill(e, item)


#     def scanStatus(self, treeItem):
#         files  = treeItem.data(0, Qt.UserRole)["files"]
#         branch = treeItem.data(0, Qt.UserRole)["branch"]
#         for f in parentItem.data(0, Qt.UserRole)["files"]:
#             e   = self.branchFiles[branch][f]
#             eid = e["id"]
#             entry  = self.repo.get(eid)
#             status = RGitVersions.getFileStatus(self.repo, self.repoFiles, e, eid, f)



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
#             print(f, e["files"])
            #   print(">>>>>", entry)
#             if f == "./.github/workflows":
#                 print(" >lf>", f, "->", e["files"])

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
        
        
#        QTimer.singleShot(200, self.resizeFileTree)

#     def __activePath(self, f):
#         d = f+"/"
#         if f in self.rgd.repoFiles:
#             p = f
#         elif d in self.repoFiles:
#             p = d
#         else:
#             print("??????????",f )
#             return None
#         return p
 


#     def getFileStatus(self, eid, path):
#         if path[:2] == "./":
#             status = self.rgd.repo.status_file(path[2:]).name
#         else:
#             status = self.rgd.repo.status_file(path).name
#         if path in self.rgd.repoFiles:
#             if "lastCommit" not in self.rgd.repoFiles[path] :
#                 status = "Not Commited"
#             elif self.rgd.repoFiles[path]["lastCommit"][2] != eid:
#                 if status == "CURRENT":
#                     status="Remote Update"
#                 elif status ==  "WT_MODIFIED":
#                     status="CONFLICT"
#                 else:
#                     status+=" and Remote Update"
#                     print("  \t\t ", path, " updated  but local says = ", status)
#         return status

#     def getDirStatus(self, branch, files, path):
#         statusDict = self.__getDirStatus(branch, files, path)
#         nStat      =  np.sum(np.array(list(statusDict.values())))
#         if nStat == 0:
#             return "No Status"
            
#         if nStat == 1:   # only a single status
#             status = [s  for s,v in statusDict.items() if v][0]
#             print(" ** getDirStatus :", status, path)
#             return status

#         # Check for only a single status + CURRENT
#         del(statusDict["CURRENT"])
#         nStat      =  np.sum(np.array(list(statusDict.values())))
#         if nStat == 1:
#             status = [s  for s,v in statusDict.items() if v][0]
#             print(" ** getDirStatus :", status, path)
#             return status

#         # Check status from most important to least
#         for s in self.statusOrder:
#             if s in statusDict:
#                 if statusDict[s]:
#                     return s+" ++"
#         return "Unknown"
            

#     def __getDirStatus(self, branch, files, path):
#         mergedStatus = {"Not Commited": False,
#                         "CURRENT"     : False,
#                         "WT_MODIFIED" : False,
#                         "CONFLICT"    : False,
#                         "Unknown"     : False
#                         }
#         for f in files:
#             # print("\t getDirStatus ", path , "->", f)
#             if f in self.rgd.branchFiles[branch]:
#                 if len(self.rgd.branchFiles[branch][f]["files"])>0:
#                     dirStatus = self.__getDirStatus( branch, self.rgd.branchFiles[branch][f]["files"], f)
#                     for k in dirStatus:
#                         if dirStatus[k]:
#                             mergedStatus[k] = True
                        
#                 else:
#                     fileStatus = self.rgd.getFileStatus(branch, f)
#                     mergedStatus[fileStatus] = True
# #                     if f in self.rgd.branchFiles[branch]:
# #                         fileStatus = self.getFileStatus( self.rgd.branchFiles[branch][f]["id"], f)
# #                         mergedStatus[fileStatus] = True
# #                     else:
# #                         print("\t ..getDirStatus ", path , "->", f)
                        
# #                         fileStatus = "Unknown"
#         # print("\t getDirStatus", path, ":", mergedStatus)
#         return mergedStatus


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
                commitId, commitTime, blobId = self.rgd.repoFiles[filePath]["commits"][-1]
                self.rgd.doDiff(branch, filePath, None, filePath, blobId)

#             fileName  = sel[0].text(0)
#             filePath  = sel[0].data(0, Qt.UserRole)[0]
#             filePath1 = self.rgd.repo.workdir + "/" +sel[0].data(0, Qt.UserRole)[0]

#             if filePath in self.rgd.repoFiles:
#                 commitId, commitTime, blobId = self.rgd.repoFiles[filePath]["commits"][-1]
#                 entry     = self.rgd.repo.get(blobId)
#                 bf, ext   = os.path.splitext(fileName)
#                 filePath2 = "/tmp/" + bf+"."+ commitId + ext
#                 if not entry.is_binary:
#                     with open(filePath2, "wb") as out:
#                         out.write(entry.data)
#                     cmd = re.sub("%2", filePath2, re.sub("%1", filePath1, self.rgd.diffCommand))
#                     p = subprocess.Popen(cmd, shell = True)
#                     p.wait()
#                     print("compare done")
#                     os.unlink(filePath2)

                
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
                for commitId, commitTime, blobId in self.rgd.repoFiles[filePath]["commits"]:
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

#!/usr/bin/env python3
# File: training.py
# Time-stamp: <29-Mar-2026 16:02:09 goetz>
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

import time
import signal
import glob
import datetime
import json
import subprocess
from collections import defaultdict
import pygit2
import numpy as np

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
    


preferedPrimaryBranchNames = ["trunk", "main", "HEAD", "head", "master"]
preferedRemotePrefixes     = ["origin", "master"]
class RGitData():

    def __init__(self, curBranch, primaryBranches):
        self.curBranch       = curBranch
        self.repo            = pygit2.Repository(".")
        self.remotes         = list(self.repo.remotes)
        self.branches        = {"local": list(self.repo.branches.local),
                                "remote" : list(self.repo.branches.remote)}
        self.branches["all"] = self.branches["local"] + self.branches["remote"]
        self.repoFiles    = {}
        self.blobPath     = defaultdict(dict)
        self.branchFiles  = defaultdict(dict)
        self.allCommitIds = defaultdict(set)
        self.branchPath   = defaultdict(set)
        self.tags         = {}
        self.updated      = {"rf" : False,"tags": False}

        self.statusOrder = ["Unknown", "CONFLICT", "Remote Update", "WT_MODIFIED", "Not Comitted", "CURRENT"]
        self.diffCommand = "tkdiff %1 %2"

        self.primaryBranches = []
        localPrim = ""
        if len(self.branches["local"]) == 1:
            localPrim = self.branches["local"][0]
        else:
            for name in preferedPrimaryBranchNames:
                if name in self.branches["local"]:
                    localPrim = name
                    break
        remotePrim = ""
        if len(self.branches["remote"]) == 1:
            remotePrim = self.branches["remote"][0]
        else:
            for prefix in preferedRemotePrefixes:
                for name in preferedPrimaryBranchNames:
                    if prefix + "/" + name in self.branches["remote"]:
                        remotePrim = prefix + "/" + name
                        break
        self.primaryBranches = [localPrim, remotePrim]
        print(">>>>>", self.primaryBranches)


        t0 = time.time()
        self.loadCaches(self.primaryBranches)
        self.getBranchFiles(self.curBranch)
        for branch in self.primaryBranches:
            if branch != self.curBranch:
                self.getBranchFiles(branch)
        print("------> %7.2fs" %(time.time()-t0))
        for branch in self.primaryBranches:
            self.collectCommits(branch)
            print("------> %7.2fs" %(time.time()-t0))
        self.collectTags()
        self.postProcess()
        self.saveCaches(self.primaryBranches, repoFiles=True)
           
        

    def __scanBranchTree(self, branch, tree, parentPath):
        files = []
        for entry in tree:
            path = parentPath+"/"+entry.name
            self.branchFiles[branch][parentPath]["files"].append(path)
            self.branchFiles[branch][path] = {"id":str(entry.id), "name":entry.name, "branch":branch, "files":[]}
            if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                nextTree = self.repo.get(entry.id)
                self.__scanBranchTree(branch, nextTree, path)

    

    def getBranchFiles(self, branch):
        self.branchFiles[branch] = {"." :{"id":None, "name":"", "branch":branch, "files":[]} }
        tree = self.repo.revparse_single(branch).tree
        self.__scanBranchTree(branch, tree, ".")


    def __newRepoFile( self, name, isDir=False,  files = None):
        commits = []
        return  { "name":name,
                  "isDir":isDir,
                  "commits": commits ,
                  "files" :files or []
                  }
       
    def collectBlobsFromTree(self, branchName, tree, commit, parentPath):
        repo   = self.repo
        for e in tree:
            path = parentPath+"/"+ e.name
            if e.filemode == pygit2.GIT_FILEMODE_TREE:
                isDir = True
            else:
                isDir = False

            if path not in  self.repoFiles:
                print("\t * add path to repoFiles:", path)
                self.repoFiles[path] = self.__newRepoFile(e.name, isDir=isDir)
                self.updated["rf"] = True
            else:
                self.branchPath[path].add(branchName)

            if path not in self.repoFiles[parentPath]["files"]:
                self.repoFiles[parentPath]["files"].append(path)
                self.updated["rf"] = True

                
            if isDir:
                nextTree = repo.get(e.id)
                self.collectBlobsFromTree(branchName,nextTree, commit,path)
            esid = str(e.id)
            com  = [str(commit.id), commit.commit_time, str(e.id)]
            if esid in self.blobPath:
                if commit.commit_time < self.blobPath[branchName][esid]["firstCommit"][1]:
                    self.blobPath[branchName][esid]["firstCommit"] = com
                    self.updated[branchName]= True
            else:
                self.blobPath[branchName][esid] = {"path":path, "firstCommit":com}
                self.updated[branchName]= True


    def addBranchToCommits(self, branchName, tree, commit, parentPath):
        repo   = self.repo
        for e in tree:
            path = parentPath+"/"+ e.name
            self.branchPath[path].add(branchName)


    def collectCommits(self, branchName):
        print("collectCommits", branchName)
        self.updated[branchName]= False
        if branchName not in self.allCommitIds:
            self.allCommitIds[branchName] = set()
            self.updated[branchName]= True
        if branchName not in self.blobPath:
            self.blobPath[branchName] = {}
            self.updated[branchName]= True
        
        repo   = self.repo
        walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME )
        commitList = list([c  for c in walker])
        if "." not in self.repoFiles:
            self.repoFiles["."] = self.__newRepoFile(".", isDir=True)
            self.updated["rf"] = True
        prevTime = commitList[0].commit_time +10
        for commit in commitList:
            if commit.id in self.allCommitIds[branchName]:
                self.addBranchToCommits(branchName, commit.tree, commit, ".")
            if str(commit.id) not in self.allCommitIds[branchName]:
                self.allCommitIds[branchName].add(str(commit.id))
                self.collectBlobsFromTree( branchName, commit.tree, commit, ".")
                self.updated[branchName]= True

        for eid in self.blobPath[branchName]:
            path        = self.blobPath[branchName][eid]["path"]
            firstCommit = self.blobPath[branchName][eid]["firstCommit"]
            if path not in  self.repoFiles:
                self.repoFiles[path] = self.__newRepoFile(os.path.basename(path), isDir=path[-1]=="/")
                self.updated["rf"] = True
            if len(firstCommit) != 3:
                print(">>lastC>>>", firstCommit)
            if firstCommit[1] >0:
                self.repoFiles[path]["commits"].append(firstCommit )
                self.updated["rf"] = True

            

    def postProcess(self):
        if self.updated["rf"]:
            for p in self.repoFiles:
                tmp = list(set([ tuple(e)   for e in self.repoFiles[p]["commits"]]))
                self.repoFiles[p]["commits"] = [list(e)  for e in tmp]
            for path in self.repoFiles:
                self.repoFiles[path]["commits"] = list(sorted(self.repoFiles[path]["commits"],  key=lambda x:x[1]))
                if len(self.repoFiles[path]["commits"] )>0:
                    self.repoFiles[path]["lastCommit"] = self.repoFiles[path]["commits"][-1]
                else:
                    if not self.repoFiles[path]["isDir"]:
                        print("No commits for ", path, "\t", self.repoFiles[path]["isDir"])


    def collectTags(self):
        self.tags = {}
        for ref in self.repo.references:
            if ref.startswith('refs/tags/'):
                commit = self.repo.lookup_reference(ref).peel(pygit2.Commit)
                cid = str(commit.id)
                if cid not in self.tags or ref[10:] not in self.tags:
                    self.tags[ref[10:]] = cid
                    if cid not in self.tags:
                        self.tags[cid] = []
                    self.tags[cid].append(ref[10:])
                    self.updated["tags"] = True
              

    def getTagsForCommit(self, cid):
        return self.tags.get(cid, [])

    def getVersionOfCommit(self, cid):
        rVersion = ""
        dVersion = ""
        sVersion = ""
        for tag in self.tags.get(cid, []):
            if tag[0] == "v":
                if "+dev" in tag:
                    if tag > dVersion:
                        dVersion = tag
                else:
                    if tag > rVersion:
                        rVersion = tag
        commit = self.repo.get(cid)
        p = commit.message.find("git=svn=id")
        verStr = (dVersion + " " + rVersion).strip()
        if p>0:
            p2 = commit.message[p:].find("@") +p
            p3 = commit.message[p2:].find(" ") +p2
            if p2 >=0 and p3 >p2:
                if len(verStr) >0:
                    return "rev"+commit.message[p2:p3] + " / " +verStr
                else:
                    return "rev"+commit.message[p2:p3]             
        return (dVersion + " " + rVersion).strip()

    

    def getBranchData(self, branch):
        t0 =time.time()
        saveCache = False
        if branch not in self.allCommitIds:
            self.loadBranchCache(branch)
            saveCache = True
        self.getBranchFiles(branch)
        self.collectCommits(branch)
        self.postProcess()
        if saveCache:
            self.saveCaches([branch])
        print(" branch %s colelcted after %7.2fs" %(branch, time.time()-t0))

    



    def loadCaches(self, branches):
        if not os.path.exists(".rgc"):
            os.makedirs(".rgc")
        if os.path.exists(".rgc/__rf__"):
            with open(".rgc/__rf__") as inp:
                print("LOAD RF CACHE")
                self.repoFiles = json.load(inp)
        if os.path.exists(".rgc/__tags__"):
            with open(".rgc/__rf__") as inp:
                print("LOAD TAGS CACHE")
                self.tags = json.load(inp)
        for branch in branches:
            self.loadBranchCache(branch)

            
    def loadBranchCache(self, branch):
        if "/" in branch:
            cf = ".rgc/"+branch
        else:
            cf = ".rgc/"+branch+"/__base__"
        if not os.path.exists(os.path.dirname(cf)):
            os.makedirs(os.path.dirname(cf))
        if os.path.exists(cf):
            with open(cf) as inp:
                print("LOAD  %s CACHE"% branch)
                conf =json.load(inp)
                self.blobPath[branch] = conf["blobs"]
                self.allCommitIds[branch] = set(conf["commits"])
            for e in self.blobPath[branch].values():
                self.branchPath[e["path"]].add(branch)
                

    def saveCaches(self, branches, repoFiles=False):
        if not os.path.exists(".rgc"):
            os.makedirs(".rgc")
        if repoFiles:
            if self.updated["rf"]:
                with open(".rgc/__rf__", "w") as out:
                    print("SAVE RF CACHE")
                    json.dump(self.repoFiles, out , indent=4)
                self.updated["rf"] = False
            if self.updated["tags"]:
                with open(".rgc/__tags__", "w") as out:
                    print("SAVE TAGS CACHE")
                    json.dump(self.tags, out , indent=4)
                self.updated["tags"] = False
        for branch in branches:
            if "/" in branch:
                cf = ".rgc/"+branch
            else:
                cf = ".rgc/"+branch+"/__base__"
            if not os.path.exists(os.path.dirname(cf)):
                os.makedirs(os.path.dirname(cf))

            if self.updated[branch]:
                with open(cf, "w") as out:
                    print("SAVE %s CACHE" % branch)
                    cache = {"blobs"     : self.blobPath[branch],
                             "commits"   : list(self.allCommitIds[branch])
                             }
                    json.dump(cache, out , indent=4)
                    self.updated[branch] = False


    def getBranchesForPath(self, f):
        prim  = [b   for b in self.branchPath[f]  if b in self.primaryBranches]
        other = [b   for b in self.branchPath[f]  if b not in self.primaryBranches]
        if len(prim)>0  and len(other)>0:
            branches = ", ".join(prim) + ", ".join(other)
            if len(branches)> 32:
                branches = ", ".join(prim) + " + %d other" % len(other)
                if len(branches)> 32:
                    if self.curBranch in prim:
                        branches = self.curBranch + " + %d other" % (len(other+prim)-1)
                        if len(branches)> 32:
                            branches = " %d branches" % (len(other+prim))
                    else:
                        branches = " %d other branches" % (len(other+prim))
        elif len(prim)>0:
            branches = ", ".join(prim) 
            if len(branches)> 32:
                if self.curBranch in prim:
                    branches = self.curBranch + " + %d other" % (len(other+prim)-1)
                    if len(branches)> 32:
                        branches = " %d branches" % (len(other+prim))
                else:
                    branches = " %d other branches" % (len(other+prim))

        elif len(other)>0:
            branches = ", ".join(other)
            if len(branches)> 32:
                branches = " %d other branches" % (len(other+prim))
        else:
            branches = ""
        return branches



    def collectFilesFromPath(self, branch, path):
#        print(" COLLECT", branch, path)
        files = []
        for f in self.branchFiles[branch][path]["files"]:
            if len(self.branchFiles[branch][f]["files"])>0:
                files += self.collectFilesFromPath(branch, f)
            else:
                files.append(f)
        return files
    

    def isModified(self, path):
        if path[:2] == "./":
            status = self.repo.status_file(path[2:]).name
        else:
            status = self.repo.status_file(path).name
        if status in ["WT_MODIFIED"]:
            return True
        return False
    
    def getFileStatus(self, branchOrId, path):
        if branchOrId in self.branches["all"]:
            eid    = self.branchFiles[branchOrId][path]["id"]
        else:
            eid    = branchOrId
        
        if path[:2] == "./":
            status = self.repo.status_file(path[2:]).name
        else:
            status = self.repo.status_file(path).name
        if path in self.repoFiles:
            if "lastCommit" not in self.repoFiles[path] :
                status = "Not Commited"
            elif self.repoFiles[path]["lastCommit"][2] != eid:
                if status == "CURRENT":
                    status="Remote Update"
                elif status ==  "WT_MODIFIED":
                    status="CONFLICT"
                else:
                    status+=" and Remote Update"
                    print("  \t\t ", path, " updated  but local says = ", status)
        return status



    def getDirStatus(self, branch, path):
        statusDict = self.__getDirStatus(branch,  path)
        nStat      =  np.sum(np.array(list(statusDict.values())))
        if nStat == 0:
            return "No Status"
            
        if nStat == 1:   # only a single status
            status = [s  for s,v in statusDict.items() if v][0]
            print(" ** getDirStatus :", status, path)
            return status

        # Check for only a single status + CURRENT
        del(statusDict["CURRENT"])
        nStat      =  np.sum(np.array(list(statusDict.values())))
        if nStat == 1:
            status = [s  for s,v in statusDict.items() if v][0]
            print(" ** getDirStatus :", status, path)
            return status

        # Check status from most important to least
        for s in self.statusOrder:
            if s in statusDict:
                if statusDict[s]:
                    return s+" ++"
        return "Unknown"



    def __getDirStatus(self, branch,  path):
        files = self.branchFiles[branch][path]["files"]
        mergedStatus = {"Not Commited": False,
                        "CURRENT"     : False,
                        "WT_MODIFIED" : False,
                        "CONFLICT"    : False,
                        "Unknown"     : False
                        }
        for f in files:
            if f in self.branchFiles[branch]:
                if len(self.branchFiles[branch][f]["files"])>0:
                    dirStatus = self.__getDirStatus( branch,  f)
                    for k in dirStatus:
                        if dirStatus[k]:
                            mergedStatus[k] = True
                        
                else:
                    fileStatus = self.getFileStatus(branch, f)
                    mergedStatus[fileStatus] = True
        return mergedStatus



    def newFilesInCommit(self, branch, commitId):
        newFiles = []
        for eid,v in self.blobPath[branch].items():
            if v["firstCommit"][0] == commitId:
                newFiles.append((eid, v["path"]))
        return newFiles


    def previousCommit(self, branch, path, commitId, commitTime):
        # get all commits before commitTime and sort them newest to oldest
        commits = sorted( [ c  for c in self.repoFiles[path]["commits"]    if c[1] < commitTime],
                          key = lambda c: -c[1])
        print("commits:", commits)
        for commitId, commitTime, entryId in commits:
            if commitId in self.allCommitIds[branch]:
                return entryId
        return None



    def nameOfEntry(self, branch, entryId):
        for eid,v in self.blobPath[branch].items():
            if eid == entryId:
                return v["path"]
        return None


    def getDifFile(self, branch, fileOrId):
        if fileOrId in self.repoFiles:
            return self.repo.workdir + "/"  + fileOrId
        
        entry    = self.repo.get(fileOrId)
        commitId = self.blobPath[branch][fileOrId]["firstCommit"][0]
        entryFilePath = self.nameOfEntry(branch, fileOrId)
        if entryFilePath is None:
            return None
        e
        bf, ext  = os.path.splitext(os.path.basename(entryFilePath))
        filePath = "/tmp/" + bf+"."+ commitId + ext
        with open(filePath, "wb") as out:
            out.write(entry.data)
        return filePath

    def doDiff(self, branch, fileOrId1, fileOrId2):
        filePath1 = self.getDifFile(branch, fileOrId1)
        filePath2 = self.getDifFile(branch, fileOrId2)
        cmd = re.sub("%2", filePath2, re.sub("%1", filePath1, self.diffCommand))
        p = subprocess.Popen(cmd, shell = True)
        p.wait()
        print("compare done")
        l = len(self.repo.workdir)
        if filePath1[:l] != self.repo.workdir:
            print(" DELETE ", filePath1)
            os.unlink(filePath1)
        if filePath2[:l] != self.repo.workdir:
            print(" DELETE ", filePath2)
            os.unlink(filePath2)


    def getCommitOfBlob(self, branch, blobId):
        if branch in self.blobPath:
            if blobId in self.blobPath[branch]:
                print( self.blobPath[branch][blobId])
                return self.blobPath[branch][blobId]["firstCommit"][0]
        return None


    def getBlobIdInCommit(self, branch, commitId, path):
        for blobId in self.blobPath[branch]:
            if self.blobPath[branch][blobId]["firstCommit"][0] == commitId:
                if self.blobPath[branch][blobId]["path"] == path:
                    return blobId
        return None
                                             
    def commitForPath(self, branch, path):
        cl= []
        for commitId, commitTime, _ in self.repoFiles[path]["commits"]:
            if commitId in self.allCommitIds[branch]:
                cl.append((commitId, commitTime))
        return [e[0]  for e in sorted(cl, key=lambda x:-x[1]) ]


                    
    def projectName(self):
        p =self.repo.path.rstrip("/\\")
        print(">>>>>", p)
        print(">>>>>", os.path.dirname(p))
        print(">>>>>", os.path.basename(os.path.dirname(p)) )
        return os.path.basename(os.path.dirname(p))
                                             

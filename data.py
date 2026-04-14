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
import copy
import subprocess
from collections import defaultdict
import pygit2
import numpy as np
from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *


class GitCallbacks(pygit2.RemoteCallbacks):
    def __init__(self, user=None, token=None, pub_key=None, priv_key=None, passphrase=None):
        self.user = user
        self.token = token
        self.pub_key = pub_key
        self.priv_key = priv_key
        self.passphrase = passphrase

    def credentials(self, url, username_from_url, allowed_types):
        if allowed_types & pygit2.enums.CredentialType.USERNAME:
            return pygit2.Username(self.user)
        elif allowed_types & pygit2.enums.CredentialType.USERPASS_PLAINTEXT:
            return pygit2.UserPass(self.user, self.token)
        elif allowed_types & pygit2.enums.CredentialType.SSH_KEY:
            return pygit2.Keypair(username_from_url, self.pub_key, self.priv_key, self.passphrase)
        else:
            return None

    def push_update_reference(self, refname, message):
        if message is not None:
            raise GitError("Push of {} failed - error message is: {}".format(refname, message))

    def certificate_check(self, certificate, valid, host):
        return True


    def transfer_progress(self, stats):
        print("Retrieved objects: {}/{}".format(stats.indexed_objects, stats.total_objects), end="\r")


    # self.commitsByPath[path] = [ [commitId, commitTime, blobId], ...]
    # self.newFilesInCommit[commitId] = [ path, ...]
    # self.allCommitIds [branch][path] = set( commitId)     -> cached
    # ### self.branchPath[branch] = [path]
    # self.branchPath[path] = [branches]
    # self.repoFiles[path] = { "name":name, 
    #                          "isDir":  bool
    #                          "lastCommit" : (commit.id, commitTime) 
    #                          "commits" : [(commit.id, commitTime, blob.id/tree.id, path) ....]
    #                          "files" : [ path, ....]}   -> cached and updated on start
    # global cache: repoFiles
    # branchCache : firstCommitOfBlob allCommitIds  
    


preferedPrimaryBranchNames = ["trunk", "main", "HEAD", "head", "master"]
preferedRemotePrefixes     = ["origin", "master"]

statusNameMap = {"WT_MODIFIED"   : "MODIFIED",
                 "INDEX_NEW"     : "ADDED",
                 "INDEX_DELETED" : "DELETED",
                 "INDEX_DELETED|WT_NEW" : "DELETED",
                 "WT_NEW"        : "removed from Repo",
                 }
                 



class RGitData():

    def __init__(self, repoPath, curBranch):
        self.curBranch       = curBranch
        #         self.globalConfig    = {c.name:c.value for c in pygit2.Config.get_global_config()}
        
        # FXIME better detection of available ssh keys
        if sys.platform == "win32":
            if "HOME" in os.environ:
                sshPath = os.environ["HOME"]+"\\.ssh"
            elif "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
                sshPath = os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]+"\\.ssh"
            if os.path.exists(sshPath):
                self.privKeyFile = sshPath+"\\id_rsa"
                self.publKeyFile = sshPath+"\\id_rsa.pub"
        else:
            self.privKeyFile = os.environ["HOME"]+"/.ssh/id_rsa"
            self.publKeyFile = os.environ["HOME"]+"/.ssh/id_rsa.pub"

        if isinstance(repoPath, str):
            if os.path.exists(repoPath):
                self.repo        = pygit2.Repository(repoPath)
                self.tmpRepoPath = None
            else:
                self.cloneTempRepo(repoPath)
                self.repo        = self.cloneTempRepo(repoPath)
                
        self.remotes         = list(self.repo.remotes)
        self.branches        = {"local": list(self.repo.branches.local),
                                "remote" : list(self.repo.branches.remote)}
        self.branches["all"] = self.branches["local"] + self.branches["remote"]
        self.repoFiles    = {}
        self.branchFiles  = defaultdict(dict)
        self.indexFiles   = defaultdict(dict)
        self.allCommitIds = defaultdict(set)
        self.branchPath   = defaultdict(set)
        self.commitsByPath  = defaultdict( list)
        self.newFilesInCommit = defaultdict(set)
        self.commitByBlob = defaultdict(list)
        self.copies       = {}
        self.tags         = {}
        self.dirStatusCache = {}
        self.currentCommit  = {}  # list fort each branch the last commit registered
        self.updated      = {"rf" : False,"tags": False, "cbp": False}

        self.statusOrder = ["Unknown", "CONFLICT", "Remote Update", "MODIFIED", "ADDED", "DELETED", "CURRENT", "Not Comitted", "removed from Repo"]
        self.diffCommand = "tkdiff %1 %2"

        self.primaryBranches = []
        localPrim = ""
        if len(self.branches["local"]) == 1:
            localPrim = self.branches["local"][0]
        else:
            for name in [curBranch] + preferedPrimaryBranchNames:
                if name in self.branches["local"]:
                    localPrim = name
                    break
        self.curBranch = localPrim

        remotePrim = ""
        if len(self.branches["remote"]) == 1:
            remotePrim = self.branches["remote"][0]
            self.curRemote = remotePrim.wplit("/")[0]
            self.curRemoteBranch = remotePrim
        else:
            for prefix in preferedRemotePrefixes:
                for name in ["HEAD", curBranch] + preferedPrimaryBranchNames:
                    if prefix + "/" + name in self.branches["remote"]:
                        remotePrim = prefix + "/" + name
                        self.curRemote = prefix
                        self.curRemoteBranch = remotePrim
                        break

        self.curRemoteUrl    = self.repo.remotes[self.curRemote].url
        self.primaryBranches = [localPrim, remotePrim]

        t0 = time.time()
        self.loadCaches(self.primaryBranches)
        self.getBranchFiles(self.curBranch)
        for branch in self.primaryBranches:
            if branch != self.curBranch:
                print("\n scan ", branch)
                self.getBranchFiles(branch)
        print("------> %7.2fs" %(time.time()-t0))
        for branch in self.primaryBranches:
            self.collectCommits(branch)
            print("------> %7.2fs" %(time.time()-t0))
        self.collectTags()
        self.postProcess()
        self.saveCaches(self.primaryBranches, repoFiles=True)
           

    def cloneTempRepo(self, repoUrl):
        self.repoUrl = repoUrl
        # FIXME use tyemp dir
        tmpDir = "/home/goetz/tmp/.rgit/Rgit.tmp.%d" % os.getpid()
     #   repoPath ="ssh://git@git.lemna.lemnatec.de:2222/goetz/LemnaGridNeXt.git"
        localName = re.sub(r".git$","", os.path.basename(repoUrl))
        self.tmpRepoPath = tmpDir + "/" +localName
        return pygit2.clone_repository(self.repoUrl, self.tmpRepoPath, bare=True,
                                        callbacks=GitCallbacks(user="git",
                                                               priv_key=privKeyFile,
                                                               pub_key=publKeyFile))

        


    def __scanBranchTree(self, branch, tree, parentPath, commitId, commitTime):
        files = []
        for entry in tree:
            path = parentPath+"/"+entry.name
            self.branchFiles[branch][parentPath]["files"].append(path)
            self.branchFiles[branch][path] = {"id":str(entry.id), "name":entry.name, "branch":branch, "files":[]}
            if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                nextTree = self.repo.get(entry.id)
                self.__scanBranchTree(branch, nextTree, path, commitId, commitTime)

    def __scanIndexTree(self, branch, tree, parentPath):
        files = []
        for entry in tree:
            path = parentPath+"/"+entry.name
            self.indexFiles[branch][parentPath]["files"].append(path)
            self.indexFiles[branch][path] = {"id":str(entry.id), "name":entry.name, "branch":branch, "files":[]}
            if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                nextTree = self.repo.get(entry.id)
                self.__scanIndexTree(branch, nextTree, path)

    

    def getBranchFiles(self, branch):
        self.branchFiles[branch] = {"." :{"id":None, "name":"", "branch":branch, "files":[]} }
        if branch in self.branches["local"]:
            local = True
            self.indexFiles[branch] = {"." :{"id":None, "name":"", "branch":branch, "files":[]} }
            tid = self.repo.index.write_tree()
            tree = self.repo.get(self.repo.index.write_tree())
            self.__scanIndexTree(branch, tree, ".")
        else:
            local = False
        commit = self.repo.revparse_single(branch)
        tree   = commit.tree
        self.__scanBranchTree(branch, tree, ".", str(commit.id), commit.commit_time)
        if local:
            # copy over new files from indexFiles to branchFiles
            for f in self.indexFiles[branch]:
                if f not in self.branchFiles[branch]:
                    self.branchFiles[branch][f] = self.indexFiles[branch][f]
                    
        self.currentCommit[branch] = str(self.repo.revparse_single(branch).id)
        print(" !! LAST COMMIT : ", branch, self.currentCommit[branch] )

    def __newRepoFile( self, name, isDir=False,  files = None):
        commits = []
        return  { "name":name,
                  "isDir":isDir,
                  "commits": commits ,
 #                 "files" :files or [],
                  "copiedFrom":""
                  }


    def detectCopiesInCommit(self,commit):
        cts = datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S")
        svn = commit.message_trailers.get("git-svn-id", "").split(" ")[0].split("/")[-1]
        print(" DETECT COPIES %s @ %s [%s]:" %(str(commit.id), cts, svn))
        t0 =time.time()
        for parentCommitId in commit.parent_ids:
            t1 =time.time()
            differ = self.repo.diff(parentCommitId, commit.id)
            n1 = len([d for d in differ])
            differ.find_similar()
            t2 =time.time()
            n2 = len([d for d in differ])
            diffList = [ d for d in list(differ.deltas)]
            for diff in diffList:
                if isinstance(diff, pygit2.DiffDelta):
                    if diff.new_file.path != diff.old_file.path:
                        print("     Commit %s @ %s :  MOVED " %(str(commit.id), cts), diff.old_file.path)
                        print("%*s   TO "%(78, ""), diff.new_file.path)
                        # copies[origPath] = curPath
                        # since we work from new to old, if the newPath is already stored as copies source then use this information:
                        if diff.new_file.path in self.copies:
                            self.copies[diff.old_file.path] = self.copies[diff.new_file.path]
                        else:
                            self.copies[diff.old_file.path] = diff.new_file.path

#            print("\t\t\t\t\t\t\t\t\t\tdone for %s after %7.2fs / %7.2fs" %(parentCommitId, t2-t1, time.time()-t2), n1, n2)
#        print("\t\t\t\t\t\t\t\t\t\t\t\t done after %7.2fs" %(time.time()-t0))
        return self.copies



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

            if isDir:
                nextTree = repo.get(e.id)
                self.collectBlobsFromTree(branchName,nextTree, commit,path)
            esid = str(e.id)
            com  = [str(commit.id), commit.commit_time, str(e.id), path]

            self.commitsByPath[path]. append(com)
            self.updated["cbp"] = True


    def addBranchToCommits(self, branchName, tree, commit, parentPath):
        repo   = self.repo
        for e in tree:
            path = parentPath+"/"+ e.name
            self.branchPath[path].add(branchName)


    def collectCommits(self, branchName, stopCommitId = None):
        print("collectCommits", branchName) 
        self.updated[branchName]= False
        if branchName not in self.allCommitIds:
            self.allCommitIds[branchName] = set()
            self.updated[branchName]= True
            
        repo   = self.repo
        walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME )
        commitList = list([c  for c in walker])
        if "." not in self.repoFiles:
            self.repoFiles["."] = self.__newRepoFile(".", isDir=True)
            self.updated["rf"] = True
        prevTime = commitList[0].commit_time +10
        for commit in commitList:
            # print("   WALK :", commit.id, commit.commit_time)
            if str(commit.id) ==  stopCommitId:
                break
            # copies = self.detectCopiesInCommit(commit)
            if commit.id in self.allCommitIds[branchName]:
                self.addBranchToCommits(branchName, commit.tree, commit, ".")
            if str(commit.id) not in self.allCommitIds[branchName]:
                self.allCommitIds[branchName].add(str(commit.id))
                self.collectBlobsFromTree( branchName, commit.tree, commit, ".")
                self.updated[branchName]= True
                

#        self.postProcess2(branchName)
            

    def postProcess(self):
        # print(" --- postProcess",  self.updated["rf"],  len(self.repoFiles["./justfile"]["commits"]))
        if self.updated["cbp"]:
            for path, commits in self.commitsByPath.items():
                if path in self.branches["all"]:
                    continue
                
                if path not in  self.repoFiles:
                    self.repoFiles[path] = self.__newRepoFile(os.path.basename(path),
                                                              isDir=path[-1]=="/")
                    self.updated["rf"] = True
                commits = list(sorted(commits,  key = lambda x : -x[1]))
                if len(commits) >0 :
                    activeCommits = []
                    for i in range(len(commits[:-1])):
                        if commits[i][2] != commits[i+1][2]:
                            activeCommits.append(commits[i])
                    activeCommits.append(commits[-1])
                    self.repoFiles[path]["commits"] = list(reversed(activeCommits))
                else:
                    print("no commits for", path)
                    self.repoFiles[path]["commits"] = []

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
        # print(" --- postProcess update cbb: ",  len(self.repoFiles["./justfile"]["commits"]))
        for path in self.repoFiles:
            for cid, cts, eid, _ in self.repoFiles[path]["commits"]:
#                 if path == "./justfile":
#                     print("\t postProcess : add ", eid,"::", cid, cts)
                self.commitByBlob[eid].append([cid, cts])
        for eid in self.commitByBlob:
            self.commitByBlob[eid] = list(sorted(self.commitByBlob[eid], key =lambda x:x[1]))
            



    def updateLocal(self, stopCommitId, indexOnly=False):
        print("----- updateLocal", stopCommitId, indexOnly)
        stopCommitId = copy.copy(self.currentCommit[self.curBranch])
        self.getBranchFiles(self.curBranch)
        if not indexOnly:
            self.collectCommits(self.curBranch, stopCommitId=stopCommitId)
        self.postProcess()


        
    def updateRemote(self, stopCommitId):
        stopCommitId = copy.copy(self.currentCommit[curRemoteBranch])
        self.getBranchFiles(self.curRemoteBranch)
        self.collectCommits(self.curRemoteBranch, stopCommitId=stopCommitId)
        self.postProcess()
        

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
        if cid == "":  # not yet coimmitedL
            return ""
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
        p = commit.message.find("git-svn-id")
        verStr = (dVersion + " " + rVersion).strip()
        if p>0:
            p2 = commit.message[p:].find("@") +p
            p3 = commit.message[p2:].find(" ") +p2
            if p2 >=0 and p3 >p2:
                if len(verStr) >0:
                    return "rev"+commit.message[p2+1:p3] + " / " +verStr
                else:
                    return "rev"+commit.message[p2+1:p3]             
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
        print(" branch %s collected after %7.2fs" %(branch, time.time()-t0))

    



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
#         if os.path.exists(".rgc/__cbb__"):
#             with open(".rgc/__rf__") as inp:
#                 print("LOAD CBB CACHE")
#                 self.commitByBlob = json.load(inp)
        for branch in branches:
            self.loadBranchCache(branch)
            # self.postProcess2(branch)
            
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
                self.commitsByPath[branch] = conf["commitsByPath"]
                self.allCommitIds[branch]  = set(conf["commits"])
                

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
            with open(".rgc/__cbb__", "w") as out:
                print("SAVE CBB CACHE")
                json.dump(self.commitByBlob, out , indent=4)
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
                    cache = {"commitsByPath" : self.commitsByPath[branch],
                             "commits"       : list(self.allCommitIds[branch])
                             }
                    json.dump(cache, out , indent=4)
                    self.updated[branch] = False
            # for debugging purposes only:
            cf += ".bf"
            if not os.path.exists(os.path.dirname(cf)):
                os.makedirs(os.path.dirname(cf))

            with open(cf, "w") as out:
                print("SAVE %s BF" % branch)
                json.dump(self.branchFiles[branch], out , indent=4)
            cf = cf[:-3] + ".cb"
            if not os.path.exists(os.path.dirname(cf)):
                os.makedirs(os.path.dirname(cf))


                
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
        if status in ["WT_MODIFIED", "INDEX_NEW", "INDEX_DELETED|WT_NEW", "INDEX_DELETED"]:
            return True
        return False
    
    def getFileStatus(self, branchOrId, path):
        global statusNameMap
        if branchOrId in self.branches["all"]:
            eid    = self.branchFiles[branchOrId][path]["id"]
        else:
            eid    = branchOrId
        
        if path[:2] == "./":
            status = self.repo.status_file(path[2:]).name
        else:
            status = self.repo.status_file(path).name
        status = statusNameMap.get(status, status)
        # print(":::::::", path, status)
        
        updateAvailable = False
        if path in self.branchFiles[self.curRemoteBranch]:
            
            if     self.branchFiles[self.curRemoteBranch][path]["id"] != \
                   self.branchFiles[self.curBranch][path]["id"]:
                updateAvailable = True
            
        if path in self.repoFiles:
            if "lastCommit" not in self.repoFiles[path] :
                status = "Not Commited"
            elif updateAvailable:
                if status == "CURRENT":
                    status="Remote Update"
                elif status ==  "WT_MODIFIED":
                    status="CONFLICT"
                else:
                    status+=" and Remote Update"
                    print("  \t\t ", path, " updated  but local says = ", status)
        return status


    def resetDirStatusCache(self):
        self.dirStatusCache = {}
    

    def getDirStatus(self, branch, path, verbose=False, useDirStatusCache=False):
        statusDict = self.__getDirStatus(branch,  path, useDirStatusCache=useDirStatusCache)
        nStat      =  np.sum(np.array(list(statusDict.values())))

        if nStat == 0:
            return "No Status"
            
        if nStat == 1:   # only a single status
            status = [s  for s,v in statusDict.items() if v][0]
            if verbose:
                print(" ** getDirStatus :", status, path)
            return status

        # Check for only a single status + CURRENT
        del(statusDict["CURRENT"])
        nStat      =  np.sum(np.array(list(statusDict.values())))
        if nStat == 1:
            status = [s  for s,v in statusDict.items() if v][0]
            if verbose:
                print(" ** getDirStatus :", status, path)
            return status

        # Check status from most important to least
        for s in self.statusOrder:
            if s in statusDict:
                if statusDict[s]:
                    return s+" ++"
        return "Unknown"



    def __getDirStatus(self, branch,  path, useDirStatusCache=None):
        files = self.branchFiles[branch][path]["files"]
        mergedStatus = {"Not Commited": False,
                        "CURRENT"     : False,
                        "MODIFIED"    : False,
                        "ADDED"       : False,
                        "CONFLICT"    : False,
                        "Unknown"     : False
                        }
        for f in files:
            if f in self.branchFiles[branch]:
                if len(self.branchFiles[branch][f]["files"])>0:
                    if useDirStatusCache and f in self.dirStatusCache:
                        dirStatus = self.dirStatusCache[f]
                    else:
                        dirStatus = self.__getDirStatus( branch,  f)
                    for k in dirStatus:
                        if dirStatus[k]:
                            mergedStatus[k] = True
                        
                else:
                    fileStatus = self.getFileStatus(branch, f)
                    mergedStatus[fileStatus] = True
        self.dirStatusCache[path] = mergedStatus
        return mergedStatus



    def newFilesInCommit(self, branch, commitId):
        return self.newFilesInCommit[branch][commitId]
#         newFiles = []
#         for eid in self.firstCommitOfBlob[branch]:
#             for path,v in self.firstCommitOfBlob[branch][eid].items():
#                 if v[0] == commitId:
#                     newFiles.append((eid, path))
#         return newFiles


    def previousCommit(self, branch, path, commitId, commitTime):
        # get all commits before commitTime and sort them newest to oldest
        commits = sorted( [ c  for c in self.repoFiles[path]["commits"]    if c[1] < commitTime],
                          key = lambda c: -c[1])
        print("commits:", commits)
        for commitId, commitTime, entryId, _path in commits:
            if commitId in self.allCommitIds[branch]:
                return entryId
        return None



    def getLastCommit(self, path):
        if path in self.repoFiles:
            for commitId, _, blobId, p in reversed(self.repoFiles[path]["commits"]):
                if p==path:
                    return commitId
        return ""

    

    def getDifFile(self, branch, filePath , blobId):
        if self.repo.workdir[-1] in ["/","\\"]:
            wd = self.repo.workdir[:-1]
        else:
            wd = self.repo.workdir
        if blobId is None:
            if os.path.exists(filePath):
                if filePath[:2] == "./":
                    return wd + "/"  + filePath[2:]
                else:
                    return wd + "/"  + filePath
            return None
        
        entry    = self.repo.get(blobId)
        # FIXME
        commitId = self.getLastCommit(filePath)
        bf, ext  = os.path.splitext(os.path.basename(filePath))
        tmpFilePath = "/tmp/" + bf+"."+ commitId + ext
        with open(tmpFilePath, "wb") as out:
            out.write(entry.data)
        return tmpFilePath


    def doDiff(self, branch, file1, blobId1, file2, blobId2):
        self.diffFilePath1 = self.getDifFile(branch, file1, blobId1)
        self.diffFilePath2 = self.getDifFile(branch, file2, blobId2)
        print("DIFF  ", self.diffFilePath1, blobId1)
        print("  vs  ", self.diffFilePath2, blobId2)
        cmd = re.sub("%2", self.diffFilePath2, re.sub("%1", self.diffFilePath1, self.diffCommand))
        self.diffProc = subprocess.Popen(cmd, shell = True)
        QTimer.singleShot(500, self.__checkDiffStatus)

    def __checkDiffStatus(self):
        if self.diffProc.poll() is None:
            QTimer.singleShot(500, self.__checkDiffStatus)
            return
        self.diffProc.wait()
        l = len(self.repo.workdir)
        if self.diffFilePath1[:l] != self.repo.workdir:
            print(" DELETE ", self.diffFilePath1)
            os.unlink(self.diffFilePath1)
        if self.diffFilePath2[:l] != self.repo.workdir:
            print(" DELETE ", self.diffFilePath2)
            os.unlink(self.diffFilePath2)
        self.diffProc = None
        self.diffFilePath1 = None
        self.diffFilePath2 = None

            
    def getCommitOfBlob(self, blobId, after=None, lastBefore=None):
        if blobId in self.commitByBlob:
            if after is not None:
                commits = [ c[0]   for c in self.commitByBlob[blobId]   if c[1]>=after]
                if len(commits)>0:
                    return commits[0]  # first after
            elif lastBefore is not None:
                commits = [ c[0]   for c in self.commitByBlob[blobId]   if c[1]<=lastBefore]
                if len(commits)>0:
                    return commits[-1]  # lasy before
            return self.commitByBlob[blobId][-1][0]
        print("  NO COMMIT FOR ",  blobId)
        return None


    def getBlobIdInCommit(self, branch, commitId, path):
        for blobId, p in self.newFilesInCommit[commitId]:
            if path == p:
                return blobId

                                             
    def commitForPath(self, branch, path):
        cl= []
        for commitId, commitTime, _, _ in self.repoFiles[path]["commits"]:
            if commitId in self.allCommitIds[branch]:
                cl.append((commitId, commitTime))
        return [e[0]  for e in sorted(cl, key=lambda x:-x[1]) ]


                    
    def projectName(self):
        p =self.repo.path.rstrip("/\\")
        print(">>>>>", p)
        print(">>>>>", os.path.dirname(p))
        print(">>>>>", os.path.basename(os.path.dirname(p)) )
        return os.path.basename(os.path.dirname(p))
                                             


    def commitFiles(self, files, message, pushToRemote):
        ref     = self.repo.head.name  
        parents = [self.repo.head.target]
                    
        index     = self.repo.index
        for f, status in files:
            fname = f
            if f[:2] == "./":
                fname = f[2:]
            if status in ["MODIFIED", "ADDED"]:
                index.add(fname)
            elif status in ["DELETED"]:
                try:
                    index.remove(fname)
                except:
                    pass
        index.write()
        user = self.repo.default_signature
        tree      = index.write_tree()
        self.repo.create_commit(ref, user, user, message, tree, parents)
        if pushToRemote:
            self.push()
        return True



    def push(self, remote_name='origin', branch="main"):
        for remote in self.repo.remotes:
            if remote.name == remote_name:
                remote.push(['refs/heads/'+branch],
                            callbacks=GitCallbacks(priv_key=self.privKeyFile, pub_key=self.publKeyFile))



    def pull(self, remote_name=None, branch=None):
        print("PULL")
        branch = branch or self.curBranch
        remote_name = remote_name or self.curRemote
        
        for remote in self.repo.remotes:
            if remote.name == remote_name:
                remote.fetch( callbacks=GitCallbacks(priv_key=self.privKeyFile, pub_key=self.publKeyFile))
                remote_master_id = self.repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target
                merge_result, _ = self.repo.merge_analysis(remote_master_id)
                print("PULL: merge_result=",merge_result, merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE, merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD, merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL)
                # Up to date, do nothing
                if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                    return
                
                # We can just fastforward
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                    self.repo.checkout_tree(self.repo.get(remote_master_id))
                    try:
                        master_ref = self.repo.lookup_reference('refs/heads/%s' % (branch))
                        master_ref.set_target(remote_master_id)
                    except KeyError:
                        print("WARRNING: Local BTRANCH not exists")
                        self.repo.create_branch(branch, self.repo.get(remote_master_id))
                    self.repo.head.set_target(remote_master_id)
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                    self.repo.merge(remote_master_id)
                    
                    if self.repo.index.conflicts is not None:
                        for conflict in self.repo.index.conflicts:
                            print('Conflicts found in:', conflict[0].path)
                        raise AssertionError('Conflicts, ahhhhh!!')

                    user = self.repo.default_signature
                    tree = self.repo.index.write_tree()
                    commit = self.repo.create_commit('HEAD',
                                                user,
                                                user,
                                                'Merge!',
                                                tree,
                                                [self.repo.head.target, remote_master_id])
                    # We need to do this or git CLI will think we are still merging.
                    self.repo.state_cleanup()
                else:
                    raise AssertionError('Unknown merge analysis result')
        self.updateLocal(None)


    def addFile(self, f):
        if f[-1] in ["/","\\"]:
            # FIXME message
            return
        if f[:2] == "./":
            self.repo.index.add(f[2:])
        else:
            self.repo.index.add(f)
        self.repo.index.write()
        self.updateLocal(None)  # stopCommitId is not usaed if indexOnly=True

        
    def deleteFile(self, f):
        if f[-1] in ["/","\\"]:
            # FIXME message
            return
        if f[:2] == "./":
            self.repo.index.remove(f[2:])
        else:
            self.repo.index.remove(f)
        self.repo.index.write()
        self.updateLocal(None)  # stopCommitId is not usaed if indexOnly=True


    def restoreFile(self, f):
        if f[-1] in ["/","\\"]:
            # FIXME message
            return 
        fname = f
        if f[:2] == "./":
            fname = f[2:]
            
        self.repo.index.remove(fname)
        blob = self.repo.revparse_single('HEAD').tree[f]
        self.repo.index.add(pygit2.IndexEntry(f, blob.id, blob.filemode))
        with open(f, "wb") as out:
            out.write(blob.data)
        self.repo.index.write()
        self.updateLocal(None)  # stopCommitId is not usaed if indexOnly=True


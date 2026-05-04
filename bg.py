#!/usr/bin/env python3
# File: bg.py
# Time-stamp: <>
# $Id: $
#
# Copyright (C) 2026 by LemnaTec GmbH
#
# Author: goetz
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

from data import RGitData
import multiprocessing
from multiprocessing       import Process, Manager

from PySide6.QtCore import *
from PySide6.QtGui  import *
from PySide6.QtWidgets import *
from PySide6.QtCore import QRunnable, QObject,QEventLoop
import pygit2

from functions import loadSettings


class BackgroundTasks(QRunnable, QObject):
    refetched = Signal()

    def __init__(self):
        QObject.__init__(self)
        QRunnable.__init__(self)

        self.lastTask   = None
        self.manager1   = Manager()
        self.manager2   = Manager()
        self.manager3   = Manager()
        self.exchange   = self.manager1.dict()
        self.tasks      = self.manager1.Queue()
        self.status     = self.manager1.Queue()
        self.initExchange()
        self.proc       = Process(target=runBG, args=(self.tasks, self.status, self.exchange))
        self.proc.start()
        self.terminated = False

    def initExchange(self):
        self.pending = {"fetch" : False,
                        "stop"    : False,
                        "update"  : False,
                        "updateFull" :False,
                        "updateCreds" :False,
                        "stop" : False,
                        "dummy" : 0}
        self.exchange["repoPath"]   = ""
        self.exchange["remoteName"] = ""
        self.exchange["remoteUrl"]  = ""
        self.exchange["terminated"] = False
        self.exchange["task"]  = ""


    def update(self, rgd, mode="rgd"):
        if  rgd is None:
            return
        if mode in [ "update", "updateFull"]:
            self.exchange["repoPath"]   = rgd.repoPath
            self.exchange["remoteName"] = rgd.curRemote
            self.exchange["remoteUrl"]  = rgd.curRemoteUrl
            #  self.exchange[""] = rgd.
            #  self.exchange[""] = rgd.
        self.tasks.put(mode)
        self.lastTask = mode


    def refetch(self):
        if not self.pending["fetch"] :
            self.pending["fetch"]  =True
            self.tasks.put("fetch")
            

    def stop(self):
        self.tasks.put("stop")


    def run(self):
        # print("start Monitor",  self.exchange)
        while True:
            stat = self.status.get()
            if stat == "fetched":
                self.pending["fetch"] = False
                self.refetched.emit()
            if stat == "stop":
                break
        #  print("End Monitor", self.exchange["terminated"] )
        self.terminated = True



def runBG(tasks, status, exchange):
    repoPath      = exchange.get("repoPath", None)
    remoteName    = exchange.get("remoteName", None)
    remoteUrl     = exchange.get("remoteUrl", None)
    if repoPath is not None and len(repoPath)>0:
        repo = pygit2.Repository(repoPath)
    else:
        repo = None
    config, creds = loadSettings()
    sshKeys       = RGitData.getSSHkeys()
    authCallBack  = RGitData.getAuthCallBack(creds, sshKeys, remoteUrl)
    config, creds = loadSettings()

    while True:
        task = tasks.get()
        # print("\t\t\t\t @bg : ", task, "//", tasks)
        
        if task == "fetch" and repo is not None and remoteName is not None and authCallBack is not None:
            fetchRemote(repo, remoteName , authCallBack)
            #status["fetch"] = "done"
            status.put("fetched")
        if task == "update":
            repoPath      = exchange.get("repoPath", None)
            remoteName    = exchange.get("remoteName", None)
            authCallBack  = RGitData.getAuthCallBack(creds, sshKeys, remoteUrl)
            if repoPath is not None and len(repoPath)>0:
                repo = pygit2.Repository(repoPath)
            else:
                repo = None
        if task =="updateFull":
            config, creds = loadSettings()
            repoPath      = exchange.get("repoPath", None)
            remoteName    = exchange.get("remoteName", None)
            remoteUrl     = exchange.get("remoteUrl", None)
            authCallBack  = RGitData.getAuthCallBack(creds, sshKeys, remoteUrl)
            if repoPath is not None and len(repoPath)>0:
                repo = pygit2.Repository(repoPath)
            else:
                repo = None
        if task == "updateCreds":
            config, creds = loadSettings()
            tasks["updateCreds"] = False
        if task == "stop":
            status.put("stop")
            break
        time.sleep(01.2)

    print("\t\t\t\t @bg : Terminated")
    exchange["terminated"] = True



def fetchRemote(repo, remoteName , authCallBack):
    t0 =time.time()
    for remote in repo.remotes:
        if remote.name == remoteName:
            remote.fetch( callbacks=authCallBack)
    print("fetch remote done after %7.2fs" %(time.time() -t0))
  

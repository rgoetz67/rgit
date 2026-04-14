#!/usr/bin/env python3
# File: blame.py
# Time-stamp: <>
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


import json
import pygit2
import datetime

from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *
from PySide6.QtPrintSupport import QPrinter


colors = [QBrush("#FFDDDD"),
          QBrush("#DDFFDD"),
          QBrush("#DDDDFF"),
          QBrush("#FFFFCC"),
          QBrush("#FFCCFF"),
          QBrush("#CCFFFF"),
          QBrush("#DCDCDC")]
                 

class BlameDisplay(QFrame):

    def __init__(self, pwin, rgd, branch, path, commitId, blobId = None, embedded=False):
        super().__init__()
        self.pwin = pwin
        self.rgd  = rgd
        self.branch = branch
        self.path   = path
        self.embedded = embedded
        self.initUI()
        for cid in self.rgd.commitForPath(self.branch, self.path):
            self.commitSelect.addItem(cid)
            
        self.fill(commitId, blobId)
        self.show()
        centerWindow(self, ref=self.pwin)


    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)

        self.commitSelect = QComboBox()
        self.codeDisplay  = QTreeWidget()
        self.codeDisplay.setMinimumSize(920,480)
        self.codeDisplay.setColumnCount(4)
        self.codeDisplay.setHeaderLabels(["Line", "Last\nVersion", "Change\nCommit", "Conetnt"])


        self.messageCB = QCheckBox("Show Commit Message")
        self.message = QPlainTextEdit()
        self.message.setMinimumSize(480,40)
        self.message.setMinimumHeight(80)
        self.message.hide()

        self.buttons   =self.buttonFrame()

        self.gbox.addWidget(self.commitSelect, 1, 1, 1, 1, Qt.AlignTop | Qt.AlignLeft)
        self.gbox.addWidget(self.messageCB,    1, 3, 1, 1, Qt.AlignTop | Qt.AlignRight)
        self.gbox.addWidget(self.message,      1, 4, 1, 1)
        self.gbox.addWidget(self.codeDisplay,  2, 1, 1, 4)
        self.gbox.addWidget(self.buttons,      3, 1, 1, 4)

        self.gbox.setColumnStretch(1,0)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setColumnStretch(3,0)
        self.gbox.setColumnStretch(4,0)
        self.gbox.setRowStretch(1,0)
        self.gbox.setRowStretch(2,1)
        self.gbox.setRowStretch(3,0)
        self.gbox.setColumnMinimumWidth (3, 480)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.setMinimumWidth(920)
        self.commitSelect.currentTextChanged.connect(self.refill)
        self.messageCB.stateChanged.connect(self.showMessage)

    def buttonFrame(self):
        f = QFrame()
        self.hbox = QHBoxLayout()
        f.setLayout(self.hbox)

        if self.embedded:
            self.closeBtn = QPushButton("Hide")
        else:
            self.closeBtn = QPushButton("Close")
        self.closeBtn.clicked.connect(self.close)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.closeBtn, 0, Qt.AlignRight)
        return f


    def reinit(self, branch, path, commitId):
        self.branch = branch
        self.path   = path
        self.commitSelect.blockSignals(True)
        self.commitSelect.clear()
        for cid in self.rgd.commitForPath(self.branch, self.path):
            self.commitSelect.addItem(cid)
        self.commitSelect.blockSignals(False)
        self.refill(commitId)
        

    def refill(self, commitId):
        self.codeDisplay.clear()
        self.fill(commitId)



    def fill(self, commitId, blobId=None):
        print("fill \t >  ", blobId, blobId is None, commitId, self.branch, self.path)
        if blobId is None:
            blobId = self.rgd.getBlobIdInCommit(self.branch, commitId, self.path)
        print("fill \t >> ", blobId)
        if blobId is None:
            return False

        commit = self.rgd.repo.get(commitId)
        self.message.setPlainText(commit.message)

        blob = self.rgd.repo.get(blobId)
        if blob.is_binary:
            return False
        lines = blob.data.decode().split("\n")

        if self.path[:2] == "./":
            bo = self.rgd.repo.blame(self.path[2:], newest_commit=commitId)
        else:
            bo = self.rgd.repo.blame(self.path, newest_commit=commitId)


        lc = 0
        ci = 0
        for bh in bo:
            cid    = str(bh.final_commit_id)
            for i in range(bh.lines_in_hunk):
                if lc+i >= len(lines):
                    break
                if i ==0:
                    verStr = "  "+ self.rgd.getVersionOfCommit(cid)+"  "
                    comStr = "  "+ cid[:7]+"  "
                    item   = QTreeWidgetItem([str(lc+i+1)+"  ", verStr, comStr, lines[lc+i]])
                else:
                    item   = QTreeWidgetItem([str(lc+i+1)+"  ","", "", lines[lc+i]])
                item.setBackground(3, colors[ ci] )
                self.codeDisplay.addTopLevelItem(item)
            lc += bh.lines_in_hunk
            ci  = (ci +1)  % len(colors)

        tw =0
        for c in range(3):
            self.codeDisplay.resizeColumnToContents(c)
            tw += self.codeDisplay.columnWidth(c)
        w = self.width() - tw -4
        self.codeDisplay.setColumnWidth(3,w)


    def showMessage(self):
        if self.messageCB.isChecked():
            self.message.show()
        else:
            self.message.hide()



    def close(self):
        if self.embedded:
            self.hide()
        else:
            super().close()

            
    def quit(self):
        self.close()
        self.pwin.close()


class PythonCodeHighligher(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)

        self.rules = {}
        self.fmt = {}
        self.ruleSets = {}
        rf = os.path.dirname(__file__)+"/syntaxRules.json"
        print(":::", rf, os.path.exists(rf), __file__)
        if os.path.exists(rf):
            with open(rf) as inp:
                self.ruleSets =json.load(inp)

        self.bf = QTextCharFormat()
        self.bf.setForeground(Qt.red)
        self.bf.setFontWeight(QFont.Bold)
        
#         self.rules = { "self": QRegularExpression("self"),
#                   "def": QRegularExpression("def .*?\("),
#                   "com": QRegularExpression("#.*"),
#                   }
#         self.fmt   = { k : QTextCharFormat()  for k in self.rules}
#         self.fmt["self"].setForeground(Qt.darkBlue)
#         self.fmt["self"].setFontWeight(QFont.Bold)
#         self.fmt["def"].setForeground(Qt.darkRed)
#         self.fmt["def"].setFontWeight(QFont.Bold)
#         self.fmt["def"].setForeground(Qt.green)
#         self.fmt["def"].setFontWeight(QFont.Bold)

    def activate(self, ext):
        self.rules = {}
        self.fmt = {}
        if ext in self.ruleSets:
            for i,rule in enumerate(self.ruleSets[ext]):
                self.rules[i] = QRegularExpression(rule["rex"])
                self.fmt[i] = QTextCharFormat()
                if "color" in rule:
                    print("set fg", rule["color"])
                    self.fmt[i].setForeground(QBrush(QColor(rule["color"])))
                if "bg" in rule:
                    self.fmt[i].setForeground(QColor(rule["bg"]))
                if "weight" in rule:
                    if rule["weight"] == "bold":
                        self.fmt[i].setFontWeight(QFont.Bold)
                if "italic" in rule:
                        self.fmt[i].setFontItalic(rule["italic"])
        print(" %d syntax rtules activates", len(self.rules))
        for i in self.rules:
            print("\t", i, self.rules[i].pattern(), "\t\t",
                  self.fmt[i].foreground().color().name(),
                  self.fmt[i].background() .color().name(),
                  self.fmt[i].fontWeight(),
                  self.fmt[i].fontItalic() 
                  )
                        
    def highlightBlock(self, txt):
        for key in self.rules:
            matchIterator = self.rules[key].globalMatch(txt)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.fmt[key])

class CodeDisplay(QFrame):

    def __init__(self, pwin, rgd, path,  blobId , embedded=False):
        super().__init__()
        self.pwin     = pwin
        self.rgd      = rgd
        self.path     = path
        self.embedded = embedded
        self.initUI()
            
        self.fill( blobId)
        self.show()


    def initUI(self):
        self.gbox = QGridLayout()
        self.setLayout(self.gbox)

        self.codeDisplay  = QTextEdit()
        self.codeDisplay.setMinimumSize(920,480)
        font = QFont("Liberation Mono",12)
        self.codeDisplay.setCurrentFont(font)
        self.highlighter = PythonCodeHighligher(self.codeDisplay.document())
        self.highlighter.activate(self.path.split(".")[-1])



        self.buttons   =self.buttonFrame()

        self.gbox.addWidget(self.codeDisplay,  1, 1, 1, 4)
        self.gbox.addWidget(self.buttons,      2, 1, 1, 4)

        self.gbox.setColumnStretch(1,0)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setColumnStretch(3,0)
        self.gbox.setColumnStretch(4,0)
        self.gbox.setRowStretch(1,1)
        self.gbox.setRowStretch(2,0)
        self.gbox.setColumnMinimumWidth (3, 480)
        QShortcut(QKeySequence("Escape"),  self, self.close)
        QShortcut(QKeySequence("Alt+q"),  self, self.quit)
        self.setMinimumWidth(920)


    def buttonFrame(self):
        f = QFrame()
        self.hbox = QHBoxLayout()
        f.setLayout(self.hbox)

        if self.embedded:
            self.closeBtn = QPushButton("Hide")
        else:
            self.closeBtn = QPushButton("Close")
        self.closeBtn.clicked.connect(self.close)
        self.hbox.addWidget(QLabel(""), 10)
        self.hbox.addWidget(self.closeBtn, 0, Qt.AlignRight)
        return f





    def fill(self, blobId):
        if blobId is None:
            return False

        blob = self.rgd.repo.get(blobId)
        if not isinstance(blob, pygit2.Blob):
            return
        if blob.is_binary:
            return False
        code = blob.data.decode()
        self.codeDisplay.setPlainText(code)
        self.codeDisplay.setReadOnly(True)


    def close(self):
        if self.embedded:
            self.hide()
        else:
            super().close()

            
    def quit(self):
        self.close()
        self.pwin.close()

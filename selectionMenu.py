#!/usr/bin/env python3
# File: selectionMenu.py
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

from PySide6.QtWidgets import *
from PySide6.QtGui     import *
from PySide6.QtCore    import *



class MyMenu(QMenu):
    selectionChanged = Signal()
    titleUpdate      = Signal(str)

    def __init__(self, maxStrLen = 20, ellipseInTitle=True, menuButton=None):
        super().__init__()
        self.maxStrLen      = maxStrLen
        self.ellipseInTitle = ellipseInTitle
        self.menuButton     = menuButton

        self.items = []
        self.nCheckables = 0
        self.addItemList()


    def sendSelectionChanged(self, x):
        self.selectionChanged.emit()

    def addItemList(self):
        self.itemList = QListWidget()
        self.itemList.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listAct = QWidgetAction(self)
        self.listAct.setDefaultWidget(self.itemList)
        self.addAction(self.listAct)
        self.itemList.itemClicked.connect(self.sendSelectionChanged)

    def clear(self):
        self.itemList.clear()
        self.items = []
        self.nCheckables = 0

    def addItems(self, items,  checked= True):
        self.itemList.blockSignals(True)
        for itemText, itemData in items:
            self.addItem(itemText, itemData, checked=checked, updateTitle=False)
        self.itemList.blockSignals(False)
        self.updateTitle()
  
    
    def addItem(self, itemText, itemData=None, checked = False, updateTitle=True):
        item = QListWidgetItem(itemText)
        self.items.append( (itemText, itemData, item))
        item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        if checked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
        self.nCheckables += 1
        self.itemList.addItem(item)

        if updateTitle:
            self.updateTitle()


    
    
    def addSeparator(self):
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        self.itemList.addItem(item)
        hl   = QFrame()
        hl.setStyleSheet("QFrame {background-color:#0080C9; margin-top:8px;}")
        hl.setMaximumHeight(10)
        self.itemList.setItemWidget(item, hl)



    def getTitleString(self):
        selected = self.currentSelection()
        if len(selected) == self.nCheckables:
            return"      All       "
        elif len(selected) >1:
            selStr = ", ".join(selected)
            if self.maxStrLen <0 and self.menuButton is not None:
                maxStrLen = int(floor(self.menuButton.width()/7))
            else:
                maxStrLen = self.maxStrLen
            if len(selStr)> maxStrLen-10:
                if  self.ellipseInTitle:
                    return "%d values: (%s ...)" % ( len(selected), selStr[:maxStrLen-15])
                else:
                    return "%d values:" % ( len(selected))
            else:
                return "%d values: (%s)" % ( len(selected),selStr)
        elif len(selected) == 1:
            return selected[0]
        else:
            if len(self.items) == 0:
                return  "      None      "            
        return "?"


    def updateTitle(self):
        self.titleUpdate.emit(self.getTitleString())
       

    def getAllItems(self, returnData=False):
        l = []
        for idx, (itemText, data, _) in enumerate(self.items):
            if returnData:
                l.append(data)
            else:
                l.append(itemText)
        return l


    def currentSelection(self, returnData=False, forced=False):
        if not self.isEnabled() and not forced:
            return []
        l = []
        for idx, (itemText, data,item) in enumerate(self.items):
            if item.checkState() == Qt.Checked and Qt.ItemIsEnabled in item.flags():
                if returnData:
                    l.append(data)
                else:
                    l.append(itemText)
        return l


    def selectAll(self, noSignal = None , state=Qt.Checked):
        self.blockSignals(True)
        self.itemList.blockSignals(True)
        for _, _,item in self.items:
            if item not in self.exclusiveItems:
                if not item.isHidden():
                    item.setCheckState(state)
        self.itemList.blockSignals(False)
        self.blockSignals(False)
        self.updateTitle()
        if not noSignal:
            self.selectionChanged.emit()
                

    def selectNone(self, noSignal = None):
        self.selectAll(noSignal = noSignal, state = Qt.Unchecked)


    def setSelection(self, selList):
        if isinstance(selList, str):
            if selList == "  All  ":
                self.selectAll()
            elif selList == "  None  ":
                self.selectNone()
        for itemText, _,item in self.items:
            if itemText in selList:
                if len(selList) == 1 or item not in self.exclusiveItems:
                    item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self.updateTitle()



    
class SelectionMenu(QPushButton):
    selectionChanged = Signal()
    
    def __init__(self, maxStrLen = 20, ellipseInTitle=True):
        super().__init__()
        
        self.menu = MyMenu( maxStrLen      = maxStrLen,
                            ellipseInTitle = ellipseInTitle,
                            menuButton     = self)

        self.setMenu(self.menu)
        self.menu.titleUpdate.connect(self.updateTitle)
        self.menu.selectionChanged.connect(self.selectionChanged.emit)


    def clear(self):
        self.menu.clear()


    def updateTitle(self, titleStr= None):
        titleStr = titleStr or self.menu.getTitleString()
        self.setText(titleStr)


    def addItems(self, items):
        self.menu.addItems(items)
        

    def addItem(self, itemText, data=None, checkBox = True, checked= True, updateTitle=True, exclusive=False):
        self.menu.addItem( itemText,   data=data, checkBox = checkBox,
                          checked= checked, updateTitle=updateTitle, exclusive=exclusive)


    def addSeparator(self):
        self.menu.addSeparator()


    def getAllItems(self, returnData=False):
        return self.menu.getAllItems( returnData=returnData)

    def currentSelection(self, returnData=False, forced=False):
        return self.menu.currentSelection(returnData=returnData, forced=forced )

    def setSelection(self, sel):
        self.menu.setSelection(sel)

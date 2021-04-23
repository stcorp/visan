# Copyright (C) 2002-2021 S[&]T, The Netherlands.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import wx
import wx.grid

import coda
import re
import os
import sys
import math
import struct
import weakref

from . import model
from . import renderers


# CONSTANTS
_maxLineLength = 256


# EXCEPTION HIERARCHY
class ProductBrowserError(Exception):
    """Generalization of all ProductBrowser errors"""
    pass


class PathError(ProductBrowserError):

    def __init__(self, str):
        ProductBrowserError.__init__(self)
        self.str = str

    def __str__(self):
        return "PathError: " + self.str


# CUSTOM EVENTS
wxEVT_ITEM_SELECTED = wx.NewEventType()
EVT_ITEM_SELECTED = wx.PyEventBinder(wxEVT_ITEM_SELECTED)
wxEVT_ITEM_DESELECTED = wx.NewEventType()
EVT_ITEM_DESELECTED = wx.PyEventBinder(wxEVT_ITEM_DESELECTED)
wxEVT_CHILD_FOCUS = wx.NewEventType()
EVT_CHILD_FOCUS = wx.PyEventBinder(wxEVT_CHILD_FOCUS)


class ItemSelectedEvent(wx.PyCommandEvent):

    eventType = wxEVT_ITEM_SELECTED

    def __init__(self, id, index):
        wx.PyCommandEvent.__init__(self, ItemSelectedEvent.eventType, id)
        self.index = index

    def Clone(self):
        tmp = self.__class__(self.GetId(), self.index)
        tmp.SetEventObject(self.GetEvenObject())
        return tmp


class ItemDeselectedEvent(wx.PyCommandEvent):

    eventType = wxEVT_ITEM_DESELECTED

    def __init__(self, id, index):
        wx.PyCommandEvent.__init__(self, ItemDeselectedEvent.eventType, id)
        self.index = index

    def Clone(self):
        tmp = self.__class__(self.GetId(), self.index)
        tmp.SetEventObject(self.GetEvenObject())
        return tmp


class ChildFocusEvent(wx.PyCommandEvent):
    eventType = wxEVT_CHILD_FOCUS

    def __init__(self, id):
        wx.PyCommandEvent.__init__(self, ChildFocusEvent.eventType, id)

    def Clone(self):
        tmp = self.__class__(self.GetId())
        tmp.SetEventObject(self.GetEvenObject())
        return tmp


class Observable(object):

    def __init__(self):
        self.observers = []

    def register(self, observer):
        assert hasattr(observer, "notify"), "Observer should have a callable attribute \"notify\""
        assert callable(observer.notify), "Observer should have a callable attribute \"notify\""
        self.observers.append(observer)

    def unregister(self, observer):
        self.observers.remove(observer)

    def notifyObservers(self):
        for observer in self.observers:
            observer.notify(self)


class ButtonGroup(object):

    def __init__(self):
        self.map = {}
        self.buttons = []
        self.selected = -1

    def AppendButton(self, button):
        self.map[button.GetId()] = len(self.buttons)
        self.buttons.append(button)

        if self.selected == -1:
            self.selected = 0
            button.SetValue(True)

    def GetSelected(self):
        return self.selected

    def SetSelected(self, index):
        assert (index >= 0) and (index < len(self.buttons)), "Button index out of range"
        if self.selected != -1:
            self.buttons[self.selected].SetValue(False)
            self.selected = index
            self.buttons[self.selected].SetValue(True)

    def ProcessToggleEvent(self, button):
        try:
            index = self.map[button.GetId()]
        except KeyError:
            return False

        if index == self.selected:
            button.SetValue(True)
            return False
        else:
            self.buttons[self.selected].SetValue(False)
            self.selected = index
            return True


class NavigationController(Observable):

    def __init__(self, frame):
        Observable.__init__(self)

        self.frame = frame
        self.view = None
        self.rootNode = None
        self.productRootNode = None
        self.selectedNode = None

        self.autoExpanding = False
        self.autoPath = None
        self.autoIndex = -1

        self.ignoreFocus = False

    def Initialize(self, view, cursor):
        self.view = view

        try:
            self.productRootNode = model.NodeFactory(cursor)
            self.productRootNode.cursor = cursor
            self.productRootNode.name = "|product|"
            self.productRootNode.initialize()

        except coda.CodacError as ex:
            self.productRootNode = None
            message = wx.MessageDialog(self.frame, "Error reading product root node.\nPlease check product sanity, "
                                       "e.g. using codacheck.\n\nCODA error message: \"[CODA] %s\"" % str(ex),
                                       "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()
            self.view.LayoutAndRefresh()
        else:
            self.rootNode = model.RecordNode()
            self.rootNode.name = "|root|"
            self.rootNode._count = 1
            self.rootNode._fields = [self.productRootNode]

            # set parent of productRootNode
            self.productRootNode.parent = weakref.proxy(self.rootNode)

            rootView = self.view.ViewFactory(self.rootNode)
            self.view.PushView(rootView)
            self.view.LayoutAndRefresh()

            rootView.SelectItem(0)

    def AutoExpand(self, node):
        assert (self.autoIndex >= 0) and (self.autoIndex <= len(self.autoPath) - 1), "AutoIndex out of range"

        if self.autoIndex == len(self.autoPath) - 1:
            # reached the end of the path.
            return False
        elif node.name != self.autoPath[self.autoIndex]:
            # mismatch, can occur when a user clicks a node during auto-expansion
            return False
        else:
            # try to find next path element.
            view = self.view.GetView(self.autoIndex + 1)
            index = view.Find(self.autoPath[self.autoIndex + 1])

            if index < 0:
                return False
            else:
                # found it.
                self.autoIndex += 1
                wx.CallAfter(view.SelectItem, index)
                return True

    def OnItemDeselected(self, view, parent, index):
        # pop all views to the right of this view
        self.view.PopUntil(view)

        # unfortunately, this notifyObservers() call is necessary because
        # it is impossible to tell if a user is deselecting a node or changing
        # a selection. in the first case, no subsequent select event will be send
        # which would leave the interface in an inconsistent state without the calls
        # below.
        self.selectedNode = parent

        # ensure a path length of either 0 or at least 2 on win32.
        if self.selectedNode == self.rootNode:
            self.selectedNode = None

        self.ignoreFocus = True
        self.notifyObservers()

        # give focus to parent view.
        index = self.view.GetViewIndex(view)
        if index >= 1:
            parentView = self.view.GetView(index - 1)
            parentView.SetFocus()

        self.ignoreFocus = False

    def OnItemSelected(self, view, parent, index):
        self.ignoreFocus = True

        # try to access the selected node.
        try:
            node = parent[index]
        except model.CorruptProductError as ex:
            message = wx.MessageDialog(self.frame, "Error reading array element.\nPlease check product sanity, "
                                       "e.g. using codacheck.\n\nCODA error message: \"%s\"" % str(ex),
                                       "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()

            if sys.platform != "win32":
                self.view.PopUntil(view)

            self.autoExpanding = False
            self.selectedNode = parent
            self.notifyObservers()
            if sys.platform in ["darwin", "win32"]:
                view.SetFocus()
            self.view.ScrollToEnd()
            self.ignoreFocus = False
            return

        # ignore the selection if the node is already selected.
        if node == self.selectedNode and not self.autoExpanding:
            self.ignoreFocus = False
            return

        # pop all the views to the right of the current view. on win32 this has already
        # happened due to the deselect event.
        if sys.platform != "win32":
            self.view.PopUntil(view)

        # if the selected node is a record, try to retrieve information
        # about its fields.
        if node.type == model.TYPE_RECORD and node.dirty():
            try:
                model.RetrieveFieldInfo(node)
            except model.CorruptProductError as ex:
                message = wx.MessageDialog(self.frame, "Error reading record field information.\nPlease check product "
                                           "sanity, e.g. using codacheck.\n\nCODA error message: \"%s\"" % str(ex),
                                           "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                message.ShowModal()

                self.autoExpanding = False
                self.selectedNode = node
                self.notifyObservers()
                if sys.platform in ["darwin", "win32"]:
                    view.SetFocus()
                self.view.ScrollToEnd()
                self.ignoreFocus = False
                return

        # create a new view for the selected node.
        self.view.PushView(self.view.ViewFactory(node))
        self.view.LayoutAndRefresh()

        # if needed, try to auto expanded the next node on the path.
        # NB. AutoExpand() may change the value of autoExpanding.
        if self.autoExpanding:
            self.autoExpanding = self.AutoExpand(node)

        if not self.autoExpanding:
            # the end of the path was reached, the next path element could
            # not be found, or the user manually selected a node.
            self.selectedNode = node
            self.notifyObservers()
            if sys.platform in ["darwin", "win32"]:
                view.SetFocus()
            self.view.ScrollToEnd()
            self.ignoreFocus = False

    def OnChildFocus(self, view, parent):
        if not self.ignoreFocus:
            self.ignoreFocus = True

            index = view.GetSelectedIndex()
            if index >= 0:
                try:
                    selectedNode = parent[index]
                except model.CorruptProductError:
                    selectedNode = parent
            else:
                selectedNode = None

            if selectedNode and self.selectedNode and selectedNode != self.selectedNode:
                self.selectedNode = selectedNode
                self.notifyObservers()
                if sys.platform in ["darwin", "win32"]:
                    view.SetFocus()

            self.ignoreFocus = False

    def Back(self):
        if self.autoExpanding:
            return

        if not self.selectedNode:
            return

        self.ignoreFocus = True

        index = len(self.selectedNode.path()) - 2
        view = self.view.GetView(index)

        if index > 0:
            previousView = self.view.GetView(index - 1)
            parent = previousView.GetNode()
            selectedIndex = previousView.GetSelectedIndex()
            if selectedIndex >= 0:
                try:
                    node = parent[selectedIndex]
                except model.CorruptProductError:
                    view.SetFocus()
                    self.ignoreFocus = False
                    return

                if node and self.selectedNode and node != self.selectedNode:
                    self.selectedNode = node
                    self.notifyObservers()

            previousView.SetFocus()
            self.ignoreFocus = False
        else:
            view.SetFocus()
            self.ignoreFocus = False

    def Forward(self):
        if self.autoExpanding:
            return

        if not self.selectedNode:
            return

        self.ignoreFocus = True

        index = len(self.selectedNode.path()) - 2
        view = self.view.GetView(index)

        if index < self.view.GetViewCount() - 1:
            nextView = self.view.GetView(index + 1)
            parent = nextView.GetNode()
            selectedIndex = nextView.GetSelectedIndex()
            if selectedIndex >= 0:
                try:
                    node = parent[selectedIndex]
                except model.CorruptProductError:
                    view.SetFocus()
                    self.ignoreFocus = False
                    return

                if node and self.selectedNode and node != self.selectedNode:
                    self.selectedNode = node
                    self.notifyObservers()

            nextView.SetFocus()
            self.ignoreFocus = False
        else:
            view.SetFocus()
            self.ignoreFocus = False

    def ParsePath(self, pathString):
        if pathString.endswith('['):
            raise PathError("path cannot end with \"[\"")

        fieldRegEx = re.compile(r"([^\\[\\]/]+)")
        dimensionRegEx = re.compile(r"([\s0-9\s]+)")

        path = []
        index = 0
        if pathString[0] == '/':
            # consume starting /
            index += 1
        while index < len(pathString):
            fieldDescriptor = fieldRegEx.match(pathString, index)
            if not (fieldDescriptor is None):
                (fieldName,) = fieldDescriptor.groups()

                if fieldName is None:
                    raise PathError("invalid field name")

                path.append(fieldName)

                index = fieldDescriptor.end()
                if (index < len(pathString)) and (pathString[index] == '/'):
                    # consume '/'
                    index += 1

            elif pathString[index] == '[':
                # consume '['
                index += 1

                dimensions = []
                dimensionCount = 0
                while dimensionCount < coda.CODA_MAX_NUM_DIMS:
                    dimensionDescriptor = dimensionRegEx.match(pathString, index)
                    if dimensionDescriptor is not None:
                        (idx,) = dimensionDescriptor.groups()

                        if idx is None:
                            raise PathError("invalid index")

                        idx = idx.strip()
                        if len(idx) == 0:
                            raise PathError("invalid index")

                        dimensions.append(int(idx))

                        index = dimensionDescriptor.end()
                        if index < len(pathString):
                            if pathString[index] == ',':
                                # consume ','
                                index += 1
                            elif pathString[index] == ']':
                                # consume ']'
                                index += 1
                                break
                            else:
                                raise PathError("invalid index")
                    else:
                        raise PathError("invalid index")

                    dimensionCount += 1

                # check for a period after the dimension specification
                if index < len(pathString):
                    if pathString[index] == '/':
                        # consume '/'
                        index += 1
                    elif pathString[index] != '[':
                        raise PathError("'/' or '[' expected")

                path.append(dimensions)
            else:
                raise PathError("extra characters in path")

        return path

    def GetSelectedNode(self):
        return self.selectedNode

    def notify(self, obj):
        if not self.productRootNode or self.autoExpanding:
            return

        pathString = obj.GetValue()
        try:
            path = self.ParsePath(pathString)
        except PathError as ex:
            message = wx.MessageDialog(self.frame, "Unable to parse path specification:\n%s" % (str(ex),),
                                       "Parse Error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()
            return

        self.autoExpanding = True
        self.autoPath = path
        self.autoIndex = 0

        path.insert(0, self.productRootNode.name)
        self.view.ExpandPath(path)


class NavigationView(wx.ScrolledWindow):

    defaultTreeStyle = wx.TR_HAS_BUTTONS | wx.TR_NO_LINES | wx.NO_BORDER | wx.FULL_REPAINT_ON_RESIZE

    def __init__(self, parent, id, controller):
        wx.ScrolledWindow.__init__(self, parent, id, size=(100, 100), style=wx.NO_BORDER)

        # weakref to avoid garbage cycle.
        self.controller = weakref.proxy(controller)

        self.viewIndex = {}
        self.viewStack = []
        self.separatorStack = []

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.Bind(EVT_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(EVT_CHILD_FOCUS, self.OnChildFocus)

        if sys.platform == "win32":
            self.Bind(EVT_ITEM_DESELECTED, self.OnItemDeselected)

    def ViewFactory(self, node):
        if node.type == model.TYPE_RECORD and not node.dirty() and len(node) > 0:
            view = RecordView(self, wx.NewId())
            view.Initialize(node)
            return view

        elif node.type == model.TYPE_ARRAY and node.isObjectArray() and len(node) > 0:
            if sys.platform == "win32":
                return NonVirtualIndexView(self, wx.NewId(), node)
            else:
                return IndexView(self, wx.NewId(), node)
        else:
            return None

    def PushView(self, view):
        if view is None:
            return

        self.viewIndex[view.GetId()] = len(self.viewStack)
        self.viewStack.append(view)

        # horizontal sizer
        self.sizer.Add(view, 0, wx.EXPAND, 0)
        separator = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        self.separatorStack.append(separator)
        # horizontal sizer
        self.sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

    def PopView(self):
        # cannot pop the root view.
        assert len(self.viewStack) > 1, "Cannot pop root view"

        view = self.viewStack.pop()
        del self.viewIndex[view.GetId()]

        separator = self.separatorStack.pop()
        self.sizer.Detach(separator)
        separator.Destroy()

        self.sizer.Detach(view)
        view.Destroy()

    def PopUntil(self, view):
        while len(self.viewStack) > 0 and not self.viewStack[-1] == view:
            self.PopView()

    def ExpandPath(self, path):
        self.viewStack[0].SelectItem(0)

    def LayoutAndRefresh(self):
        self.Layout()
        # takes care of displaying horizontal scrollbar after
        # selection change...
        self.FitInside()

    def ScrollToEnd(self):
        vx, vy = self.GetVirtualSize()
        cx, cy = self.GetClientSize()
        xUnit, yUnit = self.GetScrollPixelsPerUnit()

        if vx > cx:
            scrollAmount = ((vx - cx) / xUnit) + 1
            self.Scroll(scrollAmount, -1)

    def ValidEvent(self, event):
        if (event.GetId() in self.viewIndex):
            return True
        else:
            return False

    def GetViewCount(self):
        return len(self.viewStack)

    def GetView(self, index):
        assert (index >= 0) and (index < len(self.viewStack)), "view index out of range"
        return self.viewStack[index]

    def GetViewIndex(self, view):
        try:
            return self.viewIndex[view.GetId()]
        except KeyError:
            return -1

    def OnItemDeselected(self, event):
        if self.ValidEvent(event):
            view = event.GetEventObject()
            self.controller.OnItemDeselected(view, view.GetNode(), event.index)
            self.LayoutAndRefresh()

    def OnItemSelected(self, event):
        if self.ValidEvent(event):
            view = event.GetEventObject()
            self.controller.OnItemSelected(view, view.GetNode(), event.index)

    def OnChildFocus(self, event):
        if self.ValidEvent(event):
            view = event.GetEventObject()
            self.controller.OnChildFocus(view, view.GetNode())


class RecordView(wx.ListCtrl):

    def __init__(self, parent, id):
        style = wx.LC_REPORT | wx.LC_NO_HEADER | wx.BORDER_NONE | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, id, style=style)

        self.SetImageList(model.iconImageList, wx.IMAGE_LIST_SMALL)
        self.InsertColumn(0, "Name")
        self.node = None
        self.index = -1

    def Initialize(self, node):
        assert not node.dirty(), "cannot create view for dirty record nodes"
        self.node = node

        for i in range(0, len(node)):
            field = node[i]
            if not (coda.get_option_filter_record_fields() and (field.hidden or not field.available)):
                self.InsertItem(model.GetNodeAsListItem(self.GetItemCount(), field, i))

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetMinSize(wx.Size(self.GetColumnWidth(0) + 25, 0))

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

    def GetNode(self):
        return self.node

    def GetSelectedIndex(self):
        if self.index >= 0:
            item = self.GetItem(self.index)
            return item.GetData()
        else:
            return -1

    def SelectItem(self, index):
        # programmatically selecting an item only causes an EVT_LIST_ITEM_SELECTED
        # event when the item is not currently selected.
        self.SetItemState(index, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        self.SetItemState(index, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                          wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

    def Find(self, destination):
        if not isinstance(destination, str):
            return -1
        else:
            return self.FindItem(-1, destination)

    def OnItemSelected(self, event):
        if event.GetIndex() != self.index:
            self.index = event.GetIndex()
            newEvent = ItemSelectedEvent(self.GetId(), event.GetItem().GetData())
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnItemDeselected(self, event):
        self.index = -1
        if sys.platform == "win32":
            newEvent = ItemDeselectedEvent(self.GetId(), event.GetItem().GetData())
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnFocus(self, event):
        newEvent = ChildFocusEvent(self.GetId())
        newEvent.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(newEvent)
        event.Skip()


class NonVirtualIndexView(wx.ListCtrl):
    # This class was created because with the current version of wxPython
    # a virtual ListCtrl and a non-virtual ListCtrl differ in the events
    # they send and/or do not send on Windows platforms.
    #
    # On Windows, contrary to GTK, a ListCtrl with the LC_SINGLE_SEL style
    # allows the user to deselect the selected item by clicking under or
    # next to the list of items. On GTK, there always is a selected item.
    # When the user deselects the selected item (on Windows), then the native
    # control reflects this (the item is no longer highlighted). Therefore, some
    # reaction of the user interface required. Otherwise it would be possible to
    # deselect any node on the current path.
    #
    # On Windows, an EVT_LIST_ITEM_DESELECTED event is sent when an item is deselected.
    # NB. this implies the event is also sent when the user selects a different item,
    # in which case it is immediately followed by an EVT_LIST_ITEM_SELECTED event.
    #
    # The problem is that if the ListCtrl also has the LC_VIRTUAL style, _NO_ deselect
    # events are sent. So, the item looks deselected on screen, but there is no way for the
    # code to know this has happened! Therefore, on Windows a non-virtual version of the
    # IndexView class is used to prevent this situation (non-virtual controls _do_ sent
    # deselect events).
    #
    # If this issue is resolved in future versions of wxPython it would be wise to remove
    # this class and use the virtual IndexView class. A list of array indices may be very long
    # and a non-virtual ListCtrl has to add an item for each array index to the list in its
    # constructor. A virtual control will only request data for items that are visible,
    # through the OnGetItemText(), OnGetItemImage(), and OnGetItemAttr() methods. This is much
    # more efficient and therefore a virtual ListCtrl should be used whenever possible.
    #
    # NB. When removing this class, do not forget to check the whole event system. Look
    # for lines like 'if sys.platform ==/!= "win32"'.

    def __init__(self, parent, id, node):
        style = wx.LC_REPORT | wx.LC_NO_HEADER | wx.BORDER_NONE | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, id, style=style)
        assert len(node) > 0, "Number of elements should always be larger than zero"

        self.node = node

        if node.isRankZero():
            self.InsertColumn(0, "0", wx.LIST_FORMAT_RIGHT)
            self.InsertItem(0, "0")
            self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.SetSizeHints(self.GetColumnWidth(0) + 25, 0)
        else:
            rank = len(node.dimensions)

            # add columns.
            for i in range(0, rank):
                self.InsertColumn(i, str(i), wx.LIST_FORMAT_RIGHT)

            # add rows.
            multiDimensionalIndex = [0] * rank
            for row in range(0, len(node)):
                if rank == 1:
                    self.InsertItem(row, str(multiDimensionalIndex[0]))
                else:
                    item = self.InsertItem(row, str(multiDimensionalIndex[0]) + ",")

                    # insert item into list
                    for col in range(1, rank - 1):
                        self.SetItem(item, col, str(multiDimensionalIndex[col]) + ",")
                    self.SetItem(item, rank - 1, str(multiDimensionalIndex[-1]))

                # update dimensions
                for col in reversed(list(range(0, rank))):
                    multiDimensionalIndex[col] += 1
                    if multiDimensionalIndex[col] < node.dimensions[col]:
                        break
                    multiDimensionalIndex[col] = 0

            # compute total width
            width = 0
            for i in range(0, rank):
                self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
                width += self.GetColumnWidth(i)
            self.SetSizeHints(width + 25, 0)

        self.index = -1

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

    def GetNode(self):
        return self.node

    def GetSelectedIndex(self):
        return self.index

    def SelectItem(self, index):
        # programmatically selecting an item only causes an EVT_LIST_ITEM_SELECTED
        # event when the item is not currently selected.
        self.SetItemState(index, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        self.SetItemState(index, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                          wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

    def Find(self, destination):
        if not isinstance(destination, list):
            return -1

        if self.node.isRankZero():
            if len(destination) != 1:
                return -1

            index = destination[0]
        else:
            if len(destination) != len(self.node.dimensions):
                return -1

            # compute flat index via Horner's rule.
            index = 0
            for i in range(1, len(self.node.dimensions)):
                index = (index + destination[i - 1]) * self.node.dimensions[i]
            index += destination[-1]

        if (index < 0) or (index > self.GetItemCount() - 1):
            return -1
        else:
            return index

    def OnItemSelected(self, event):
        if event.GetIndex() != self.index:
            self.index = event.GetIndex()
            newEvent = ItemSelectedEvent(self.GetId(), self.index)
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnItemDeselected(self, event):
        self.index = -1
        if sys.platform == "win32":
            newEvent = ItemDeselectedEvent(self.GetId(), event.GetIndex())
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnFocus(self, event):
        newEvent = ChildFocusEvent(self.GetId())
        newEvent.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(newEvent)
        event.Skip()


class IndexView(wx.ListCtrl):

    def __init__(self, parent, id, node):
        style = wx.LC_REPORT | wx.LC_NO_HEADER | wx.BORDER_NONE | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | \
            wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, id, style=style)

        assert len(node) > 0, "Number of elements should always be larger than zero"

        self.node = node

        if node.isRankZero():
            self.InsertColumn(0, "0", wx.LIST_FORMAT_RIGHT)

            # Alas! GTK1.2's implementation of GetTextExtent() does not
            # seem to be very accurate.
            if sys.platform != "win32":
                columnString = "9" * (1 + 2)
            else:
                columnString = "9"
            width, height = self.GetTextExtent(columnString)

            self.SetColumnWidth(0, width)
            self.SetSizeHints(width + 25, 0)
        else:
            width = 0
            for i in range(0, len(node.dimensions)):
                self.InsertColumn(i, str(i), wx.LIST_FORMAT_RIGHT)

                if node.dimensions[i] == 1:
                    digitCount = 1
                else:
                    digitCount = int(math.log10(node.dimensions[i] - 1)) + 1

                # Alas! GTK1.2's implementation of GetTextExtent() does not
                # seem to be very accurate.
                if sys.platform != "win32":
                    digitCount += 2

                columnString = "9" * digitCount
                if i < len(node.dimensions) - 1:
                    columnString += ","
                columnWidth, rowHeight = self.GetTextExtent(columnString)

                self.SetColumnWidth(i, columnWidth)
                width += columnWidth

            self.SetSizeHints(width + 25, 0)

        self.SetItemCount(len(node))

        self.index = -1

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

    def GetNode(self):
        return self.node

    def GetSelectedIndex(self):
        return self.index

    def SelectItem(self, index):
        # programmatically selecting an item only causes an EVT_LIST_ITEM_SELECTED
        # event when the item is not currently selected.
        self.SetItemState(index, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        self.SetItemState(index, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                          wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

    def Find(self, destination):
        if not isinstance(destination, list):
            return -1

        if self.node.isRankZero():
            if len(destination) != 1:
                return -1

            index = destination[0]
        else:
            if len(destination) != len(self.node.dimensions):
                return -1

            # compute flat index via Horner's rule.
            index = 0
            for i in range(1, len(self.node.dimensions)):
                index = (index + destination[i - 1]) * self.node.dimensions[i]
            index += destination[-1]

        if (index < 0) or (index > self.GetItemCount() - 1):
            return -1
        else:
            return index

    def OnItemSelected(self, event):
        if event.GetIndex() != self.index:
            self.index = event.GetIndex()
            newEvent = ItemSelectedEvent(self.GetId(), self.index)
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnItemDeselected(self, event):
        self.index = -1
        if sys.platform == "win32":
            newEvent = ItemDeselectedEvent(self.GetId(), event.GetIndex())
            newEvent.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(newEvent)

    def OnFocus(self, event):
        newEvent = ChildFocusEvent(self.GetId())
        newEvent.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(newEvent)
        event.Skip()

    def OnGetItemText(self, item, col):
        multiDimensionalIndex = model.GetMultiDimensionalIndex(self.node, item)

        if self.node.isRankZero():
            return str(multiDimensionalIndex[0])
        elif col < len(self.node.dimensions) - 1:
            return str(multiDimensionalIndex[col]) + ","
        else:
            return str(multiDimensionalIndex[col])

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        return None


class AttributeView(wx.ListCtrl):

    def __init__(self, parent, id):
        style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_VRULES | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, id, style=style)

        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Value")

    def Initialize(self, frame, node):
        self._AppendItem(("Type", model.GetTypeAsString(node.type)))

        if node.type == model.TYPE_ARRAY:
            self._AppendItem(("Elements", "%u" % (len(node),)))

            if node.isRankZero():
                self._AppendItem(("Dimensions", ""))
            else:
                dimensionString = ""
                for dim in node.dimensions[:-1]:
                    dimensionString += "%u x " % (dim,)
                dimensionString += "%u" % (node.dimensions[-1],)
                self._AppendItem(("Dimensions", dimensionString))

            self._AppendItem(("Base type", model.GetTypeAsString(node.base)))
        elif node.type == model.TYPE_RECORD:
            self._AppendItem(("Fields", "%u" % (len(node),)))
        elif node.type == model.TYPE_STRING:
            self._AppendItem(("Length", "%u" % (len(node),)))

        # save the number of succesfully inserted attributes
        safeCount = self.GetItemCount()

        try:
            if wx.Config.Get().ReadBool('ProductBrowser/ShowByteSize', False):
                # size in bytes:bits.
                bitSize = node.getBitSize()
                if bitSize != -1:
                    bitFraction = bitSize & 7
                    if bitFraction == 0:
                        self._AppendItem(("Size", "%u" % (bitSize / 8,)))
                    else:
                        self._AppendItem(("Size", "%u:%u" % (bitSize / 8, bitFraction)))

            # get node type.
            nodeCodaType = coda.cursor_get_type(node.cursor)

            # description.
            description = coda.type_get_description(nodeCodaType)
            if description is not None:
                self._AppendItem(("Description", description))

            # unit of measurement.
            unit = coda.type_get_unit(nodeCodaType)
            if unit is not None:
                self._AppendItem(("Unit", unit))

            # check for fixed value.
            nodeCodaClass = coda.type_get_class(nodeCodaType)
            if (nodeCodaClass == coda.coda_text_class) or (nodeCodaClass == coda.coda_raw_class):
                type = model.TranslateCodaType(nodeCodaClass, nodeCodaType)
                fixedValue = coda.type_get_fixed_value(nodeCodaType)
                if fixedValue is not None:
                    # a maximum size of _maxLineLength characters is specified, because
                    # GDK may crash if the length of a string item gets too long.
                    # also, if the line is really long the user will probably not want
                    # to view it as a single line in a ListCtrl anyway.
                    self._AppendItem(("Fixed value", model.GetDataAsString(type, fixedValue, _maxLineLength)))

        except coda.CodacError as ex:
            for i in range(safeCount, self.GetItemCount()):
                self.DeleteItem(i)

            message = wx.MessageDialog(frame, "Error retrieving attribute information.\n\n"
                                       "CODA error message: \"%s\"" % str(ex), "CODA error",
                                       style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()

        # auto-size the list
        self._AutoSize((0, 1))

    def _AppendItem(self, descriptor):
        index = self.InsertItem(self.GetItemCount(), descriptor[0])
        self.SetItem(index, 1, descriptor[1])

    def _AutoSize(self, columns):
        for col in columns:
            header = self.GetColumn(col)
            if header:
                self.SetColumnWidth(col, wx.LIST_AUTOSIZE)
                columnWidth = self.GetColumnWidth(col)
                headerWidth, headerHeight = self.GetTextExtent(header.GetText())
                self.SetColumnWidth(col, max(columnWidth, headerWidth + 15))


class ProductAttributeView(wx.ListCtrl):

    def __init__(self, parent, id):
        style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_VRULES | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, id, style=style)

        self.InsertColumn(0, "Fieldname")
        self.InsertColumn(1, "Real name")
        self.InsertColumn(2, "Value")
        self.InsertColumn(3, "Type")
        self.InsertColumn(4, "Array Dimensions")

    def Initialize(self, frame, attributes):
        try:
            data = coda.fetch(attributes.cursor)
        except (coda.CodaError, coda.CodacError) as ex:
            message = wx.MessageDialog(frame, "Error reading attribute information from product.\nPlease check product "
                                       "sanity, e.g. using codacheck.\n\nCODA error message: \"%s\"" % str(ex),
                                       "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()
        else:
            for i in range(0, len(attributes)):
                attr = attributes[i]

                if attr.available:
                    if attr.type == model.TYPE_ARRAY:
                        valueString = ""
                        if data[i].size > 0:
                            value = data[i].flat
                            for val in value[:-1]:
                                valueString += "%s, " % (model.GetDataAsString(attr.base, val),)
                            valueString += "%s" % (model.GetDataAsString(attr.base, value[-1]),)

                        if len(valueString) > _maxLineLength:
                            valueString = "<array>"

                        dimensionString = ""
                        if not attr.isRankZero():
                            dimensionString = ""
                            for dim in attr.dimensions[:-1]:
                                dimensionString += "%u x " % (dim,)
                            dimensionString += "%u" % (attr.dimensions[-1],)

                        index = self.InsertItem(i, attr.name)
                        self.SetItem(index, 1, attr.real_name)
                        self.SetItem(index, 2, valueString)
                        self.SetItem(index, 3, model.GetTypeAsString(attr.base))
                        self.SetItem(index, 4, dimensionString)
                    else:
                        index = self.InsertItem(i, attr.name)
                        # a maximum size of _maxLineLength characters is specified, because
                        # GDK may crash if the length of a string item gets too long.
                        # also, if the line is really long the user will probably not want
                        # to view as a single line in a ListCtrl anyway.
                        self.SetItem(index, 1, attr.real_name)
                        self.SetItem(index, 2, model.GetDataAsString(attr.type, data[i], _maxLineLength))
                        self.SetItem(index, 3, model.GetTypeAsString(attr.type))
                        self.SetItem(index, 4, "-")
                else:
                    index = self.InsertItem(i, attr.name)
                    self.SetItemTextColour(index, "light grey")

        self.SetColumnWidth(2, 150)
        self._AutoSize((0, 1, 3, 4))

    def _AutoSize(self, columns):
        for col in columns:
            header = self.GetColumn(col)
            if header:
                self.SetColumnWidth(col, wx.LIST_AUTOSIZE)
                columnWidth = self.GetColumnWidth(col)
                headerWidth, headerHeight = self.GetTextExtent(header.GetText())
                self.SetColumnWidth(col, max(columnWidth, headerWidth + 15))


class NodeAttributeView(wx.Panel):

    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey).
        self.SetBackgroundColour(self.GetBackgroundColour())

    def Initialize(self, frame, node):
        sizer = wx.BoxSizer(wx.VERTICAL)

        view = AttributeView(self, -1)
        view.Initialize(frame, node)
        sizer.Add(wx.StaticText(self, -1, "Attributes from Product Format Definition"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        sizer.Add(view, 1, wx.EXPAND | wx.ALL, 5)

        try:
            attributes = model.RetrieveAttributes(node)
            model.RetrieveFieldInfo(attributes)
        except (coda.CodaError, coda.CodacError) as ex:
            message = wx.MessageDialog(frame, "Error reading attribute information from product.\nPlease check product "
                                       "sanity, e.g. using codacheck.\n\nCODA error message: \"%s\"" % str(ex),
                                       "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            message.ShowModal()
        else:
            if len(attributes) > 0:
                view = ProductAttributeView(self, -1)
                view.Initialize(frame, attributes)
                sizer.Add(wx.StaticText(self, -1, "Attributes from Product"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
                sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
                sizer.Add(view, 2, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()


class NodeDataView(wx.Panel):
    # a mapping from type to renderers

    renderers = {}

    def RegisterRenderer(cls, type, renderer):
        try:
            list = cls.renderers[type]
        except KeyError:
            list = []
            cls.renderers[type] = list

        if renderer not in list:
            list.append(renderer)

    RegisterRenderer = classmethod(RegisterRenderer)

    def __init__(self, parent, id, frame, node):
        wx.Panel.__init__(self, parent, id)
        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey).
        self.SetBackgroundColour(self.GetBackgroundColour())

        self.frame = weakref.ref(frame)
        self.node = node

        # get a list of renderers capable of rendering
        # the specified node.
        try:
            availableRenderers = NodeDataView.renderers[node.type]

            # purge renderers from the list that cannot render
            # the specific node given. for instance, a PlotRenderer
            # is able to render nodes of TYPE_ARRAY but only with
            # a specific base type (e.g. uint32, but not string or char).
            self.qualifiedRenderers = [x for x in availableRenderers if x.CanRender(node)]

        except KeyError:
            self.qualifiedRenderers = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add((5, 5), 0, 0)

        if len(self.qualifiedRenderers) == 0:
            view = renderers.UnavailableRenderer(self)
        else:
            view = self.qualifiedRenderers[0](self)
            try:
                view.Initialize(self.node)
            except renderers.RenderError as ex:
                view.Destroy()
                view = renderers.UnavailableRenderer(self)

                message = wx.MessageDialog(self.frame(), "Could not instantiate renderer.\nPlease check product "
                                           "sanity, e.g. using codacheck.\n\nError message: \"%s\"" % (str(ex),),
                                           "Render error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                message.ShowModal()

            # if multiple renderers are qualified, create a toggle
            # button for each renderer and cache the views.
            if len(self.qualifiedRenderers) > 1:
                self.buttonGroup = ButtonGroup()
                buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
                buttonSizer.Add(wx.StaticText(self, -1, "View data as:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
                for renderer in self.qualifiedRenderers:
                    button = wx.ToggleButton(self, -1, renderer.name)
                    buttonSizer.Add(button, 0, wx.ALL, 5)
                    self.buttonGroup.AppendButton(button)

                self.sizer.Add(buttonSizer, 0, wx.EXPAND, 0)
                self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
                self.sizer.Add((5, 5), 0, 0)

                self.views = {}
                self.views[0] = view

                self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleButton)

        # add view to sizer
        self.sizer.Add(view, 1, wx.EXPAND, 0)
        self.SetSizer(self.sizer)
        self.Layout()

    def OnToggleButton(self, event):
        currentView = self.buttonGroup.GetSelected()
        if self.buttonGroup.ProcessToggleEvent(event.GetEventObject()):
            nextView = self.buttonGroup.GetSelected()

            try:
                view = self.views[nextView]
            except KeyError:
                # view not in cache, so create it.
                view = self.qualifiedRenderers[nextView](self)

                try:
                    view.Initialize(self.node)

                except renderers.RenderError as ex:
                    view.Destroy()
                    view = renderers.UnavailableRenderer(self)

                    message = wx.MessageDialog(self.frame(), "Could not instantiate renderer.\nPlease check product "
                                               "sanity, e.g. using codacheck.\n\nError message: \"%s\"" % (str(ex),),
                                               "Render error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                    message.ShowModal()

                # add view to cache.
                self.views[nextView] = view
                self.sizer.Add(view, 1, wx.EXPAND, 0)

            # hide current view
            self.sizer.Show(self.views[currentView], False, True)

            # show next view, if creation was succesful.
            self.sizer.Show(view, True, True)
            self.sizer.Layout()


class NodeView(wx.Notebook):

    def __init__(self, parent, id, frame):
        wx.Notebook.__init__(self, parent, id, style=wx.CLIP_CHILDREN | wx.NB_BOTTOM)
        self.frame = weakref.ref(frame)

    def notify(self, obj):
        self.DeleteAllPages()
        if obj.GetSelectedNode() is not None:
            view = NodeDataView(self, -1, self.frame(), obj.GetSelectedNode())
            self.AddPage(view, "Data", True)

            view = NodeAttributeView(self, -1)
            view.Initialize(self.frame(), obj.GetSelectedNode())
            self.AddPage(view, "Attributes", False)


class PathView(wx.TextCtrl, Observable):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1, "", style=wx.TE_PROCESS_ENTER)
        Observable.__init__(self)

        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)

    def OnTextEnter(self, event):
        wx.CallAfter(self.notifyObservers)
        event.Skip()

    def notify(self, obj):
        if obj.GetSelectedNode() is not None:
            path = obj.GetSelectedNode().path()
            # strip rootNode and productRootNode
            self.SetValue(model.GetPathAsString(path[2:]))
        else:
            self.SetValue("")


class PathDropTarget(wx.TextDropTarget, Observable):

    def __init__(self):
        wx.TextDropTarget.__init__(self)
        Observable.__init__(self)
        self.path = None

    def OnDropText(self, x, y, data):
        self.path = data
        wx.CallAfter(self.notifyObservers)

    def GetValue(self):
        return self.path


class ProductBrowser(wx.Frame):

    initialised = False

    def __init__(self, parent, filename):
        wx.Frame.__init__(self, parent, -1, os.path.basename(str(filename)), size=(800, 600))

        if not ProductBrowser.initialised:
            model.InitIcons()
            ProductBrowser.initialised = True

        if 8 * struct.calcsize("P") == 32:
            # On a 32-bit platform we open a product without using mmap.
            # This allows us to have multiple large product files open without
            # having the risk of running out of memory address space.
            prev_opt = coda.get_option_use_mmap()
            coda.set_option_use_mmap(0)
            try:
                self.product = coda.open(str(filename))
            finally:
                coda.set_option_use_mmap(prev_opt)
        else:
            self.product = coda.open(str(filename))

        try:
            self.cursor = coda.Cursor()
            coda.cursor_set_product(self.cursor, self.product)

            self.closing = False

            # register node renderers
            self.RegisterRenderers()

            # create GUI
            self.CreateMenuBar()
            self.CreateControls(self.product, self.cursor)

            # Other Event Listeneres
            self.Bind(wx.EVT_CLOSE, self.OnClose)
        except Exception:
            coda.close(self.product)
            raise

    def CreateMenuBar(self):
        menuBar = wx.MenuBar()

        filemenu = wx.Menu()

        item = filemenu.Append(wx.ID_CLOSE, "&Close\tCtrl+W", "Close the Product Browser")
        self.Bind(wx.EVT_MENU, self.OnClose, item)

        menuBar.Append(filemenu, "&File")

        self.SetMenuBar(menuBar)

    def CreateControls(self, product, cursor):
        # this panel seems to be required for win32, because the default
        # background color of a frame is dark grey, and the trick to correct
        # the default background color of a panel (see below) does not seem
        # to work for frames.
        panel = wx.Panel(self, -1, style=wx.NO_BORDER)

        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey).
        panel.SetBackgroundColour(panel.GetBackgroundColour())

        self.pathView = PathView(panel)

        backButton = wx.BitmapButton(panel, -1, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (16, 16)),
                                     size=(23, 23))
        backButton.Bind(wx.EVT_BUTTON, self.OnBack)

        forwardButton = wx.BitmapButton(panel, -1, wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_OTHER, (16, 16)),
                                        size=(23, 23))
        forwardButton.Bind(wx.EVT_BUTTON, self.OnForward)

        copyCmdButton = wx.BitmapButton(panel, -1, wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_OTHER, (16, 16)),
                                        size=(23, 23))
        copyCmdButton.Bind(wx.EVT_BUTTON, self.OnCopyCmd)

        pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        pathSizer.Add(backButton, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)
        pathSizer.Add(forwardButton, 0, wx.ALIGN_CENTER | wx.RIGHT, 5)
        pathSizer.Add(self.pathView, 1, wx.RIGHT, 5)
        pathSizer.Add(copyCmdButton, 0, wx.ALIGN_CENTER | wx.RIGHT, 5)

        splitterstyle = wx.SP_LIVE_UPDATE | wx.SIMPLE_BORDER
        if wx.Platform == "__WXMAC__":
            splitterstyle |= wx.SP_3DSASH
        splitter = wx.SplitterWindow(panel, -1, style=splitterstyle)
        # this corrects the colour of the splitter in win32 (without this
        # line it defaults to dark grey, instead of light grey).
        splitter.SetBackgroundColour(splitter.GetBackgroundColour())
        splitter.SetMinimumPaneSize(50)

        self.navigationController = NavigationController(self)
        self.navigationController.register(self.pathView)
        self.pathView.register(self.navigationController)
        self.pathDropTarget = PathDropTarget()
        self.pathDropTarget.register(self.navigationController)
        self.SetDropTarget(self.pathDropTarget)

        navigationView = NavigationView(splitter, -1, self.navigationController)
        navigationView.SetScrollRate(5, 0)
        navigationView.SetBackgroundColour("white")

        self.nodeView = NodeView(splitter, -1, self)
        self.navigationController.register(self.nodeView)

        # the position of this line of code is important: Initialize() will cause
        # a call to notifyObservers(). therefore, all observers that want to be
        # notified of this initial event should register before this line.
        self.navigationController.Initialize(navigationView, cursor)

        splitter.SplitHorizontally(navigationView, self.nodeView, -300)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(pathSizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.BOTTOM, 3)
        sizer.Add(splitter, 1, wx.EXPAND, 0)

        panel.SetSizer(sizer)
        self.SetSizeHints(400, 300)

    def RegisterRenderers(self):
        NodeDataView.RegisterRenderer(model.TYPE_RECORD, renderers.RecordRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_ARRAY, renderers.ArrayRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_ARRAY, renderers.PlotRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_INT8, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_UINT8, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_INT16, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_UINT16, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_INT32, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_UINT32, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_INT64, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_UINT64, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_VSF_INTEGER, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_FLOAT32, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_FLOAT64, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_CHAR, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_STRING, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_BYTES, renderers.BytesRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_TIME, renderers.ScalarRenderer)
        NodeDataView.RegisterRenderer(model.TYPE_COMPLEX, renderers.ScalarRenderer)

    def OnBack(self, event):
        self.navigationController.Back()

    def OnForward(self, event):
        self.navigationController.Forward()

    def OnCopyCmd(self, event):
        selectedNode = self.navigationController.GetSelectedNode()
        if selectedNode:
            path = selectedNode.path()

            pathSpecification = ""
            for node in path[2:]:
                if isinstance(node.name, list):
                    if len(node.name) == 1:
                        pathSpecification += str(node.name[0])
                    else:
                        pathSpecification += str(node.name)
                else:
                    pathSpecification += "\"%s\"" % (node.name,)

                pathSpecification += ", "

            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(pathSpecification[:-2]))
                wx.TheClipboard.Close()

    def OnClose(self, event):
        if self.closing:
            return

        self.closing = True

        # unregister observers
        self.navigationController.unregister(self.pathView)
        self.pathView.unregister(self.navigationController)
        self.pathDropTarget.unregister(self.navigationController)
        self.navigationController.unregister(self.nodeView)

        # close product
        coda.close(self.product)

        if self.GetParent():
            self.GetParent().SetFocus()
        self.Destroy()

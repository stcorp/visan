# Copyright (C) 2002-2022 S[&]T, The Netherlands.
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

import os

import wx

from .preferences import PreferencesDialog
from .shell import VisanShell


class VisanFrame(wx.Frame):

    def __init__(self, app, title, pos, size):
        wx.Frame.__init__(self, None, -1, title, pos, size)

        self.app = app
        self.closingdown = False

        if wx.Config.Get().Read("IconFile"):
            self.SetIcon(wx.Icon(wx.Config.Get().Read("IconFile")))

        # Create and configure all widgets
        self.CreateMenuBar()
        self.CreateStatusBar()
        self.shell = VisanShell(self)
        self.shell.SetFocus()

        # Other Event Listeneres
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def CreateMenuBar(self):
        menuBar = wx.MenuBar()

        filemenu = wx.Menu()

        item = filemenu.Append(wx.ID_OPEN, "&Load and Execute Script...\tCtrl+O",
                               "Load and execute a VISAN script from a file")
        self.Bind(wx.EVT_MENU, self.OnExecuteScript, item)

        recentmenu = wx.Menu()

        self.recentMenuItem = filemenu.Append(wx.ID_ANY, "&Recent Scripts", recentmenu)
        self.recentMenuItem.Enable(False)
        self.app.filehistory.UseMenu(recentmenu)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_ANY, "&Browse Product...\tCtrl+B", "Browse the contents of a product file")
        self.Bind(wx.EVT_MENU, self.OnBrowseProduct, item)

        item = filemenu.Append(wx.ID_ANY, "&Harp Import...\tCtrl+I", "Import a product file using HARP")
        self.Bind(wx.EVT_MENU, self.OnHarpImport, item)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_ANY, "&Show Log", "Show the contents of the console log")
        self.Bind(wx.EVT_MENU, self.OnShowLog, item)

        item = filemenu.Append(wx.ID_ANY, "&Clear Log", "Clear the console log")
        self.Bind(wx.EVT_MENU, self.OnClearLog, item)

        item = filemenu.Append(wx.ID_SAVE, "S&ave Log to script...\tCtrl+S", "Save the console log as a VISAN script")
        self.Bind(wx.EVT_MENU, self.OnSaveLog, item)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_PREFERENCES, "&Preferences...", "Edit Preferences")
        self.Bind(wx.EVT_MENU, self.OnPrefs, item)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close this Window (and terminate the application)")
        self.Bind(wx.EVT_MENU, self.OnExit, item)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_EXIT, "E&xit VISAN\tCtrl+Q", "Terminate the application")
        self.Bind(wx.EVT_MENU, self.OnExit, item)

        menuBar.Append(filemenu, "&File")

        editmenu = wx.Menu()

        item = editmenu.Append(wx.ID_UNDO, "&Undo \tCtrl+Z", "Undo the last action")
        self.Bind(wx.EVT_MENU, self.OnUndo, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_UNDO)

        item = editmenu.Append(wx.ID_REDO, "&Redo \tCtrl+Y", "Redo the last undone action")
        self.Bind(wx.EVT_MENU, self.OnRedo, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_REDO)

        editmenu.AppendSeparator()

        item = editmenu.Append(wx.ID_CUT, "Cu&t \tCtrl+X", "Cut the selection")
        self.Bind(wx.EVT_MENU, self.OnCut, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_CUT)

        item = editmenu.Append(wx.ID_COPY, "&Copy \tCtrl+C", "Copy the selection")
        self.Bind(wx.EVT_MENU, self.OnCopy, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_COPY)

        item = editmenu.Append(wx.ID_PASTE, "&Paste \tCtrl+V", "Paste from clipboard")
        self.Bind(wx.EVT_MENU, self.OnPaste, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_PASTE)

        item = editmenu.Append(wx.ID_CLEAR, "&Delete", "Delete the selection")
        self.Bind(wx.EVT_MENU, self.OnDelete, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_CLEAR)

        editmenu.AppendSeparator()

        item = editmenu.Append(wx.ID_SELECTALL, "Select A&ll \tCtrl+A", "Select all text")
        self.Bind(wx.EVT_MENU, self.OnSelectAll, item)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateMenu, id=wx.ID_SELECTALL)

        menuBar.Append(editmenu, "&Edit")

        helpmenu = wx.Menu()

        item = helpmenu.Append(wx.ID_HELP, "&VISAN Documentation\tF1", "Display VISAN Documentation")
        self.Bind(wx.EVT_MENU, self.OnVisanHelp, item)

        item = helpmenu.Append(wx.ID_ANY, "&CODA Documentation", "Display CODA Documentation")
        self.Bind(wx.EVT_MENU, self.OnCodaHelp, item)

        item = helpmenu.Append(wx.ID_ANY, "&HARP Documentation", "Display HARP Documentation")
        self.Bind(wx.EVT_MENU, self.OnHarpHelp, item)

        helpmenu.AppendSeparator()

        item = helpmenu.Append(wx.ID_ANY, "&CODA Product Format Definitions\tCtrl-F1",
                               "Display Product Format Specification Documentation for products supported by CODA")
        self.Bind(wx.EVT_MENU, self.OnCodaDefHelp, item)

        helpmenu.AppendSeparator()

        item = helpmenu.Append(wx.ID_ANY, "&Python Documentation", "Display Python Documentation")
        self.Bind(wx.EVT_MENU, self.OnPythonHelp, item)

        item = helpmenu.Append(wx.ID_ANY, "&Numpy Documentation", "Display Numpy Documentation")
        self.Bind(wx.EVT_MENU, self.OnNumpyHelp, item)

        helpmenu.AppendSeparator()

        item = helpmenu.Append(wx.ID_ANY, "&Getting Started with VISAN", "Display a short VISAN introduction")
        self.Bind(wx.EVT_MENU, self.OnIntro, item)

        item = helpmenu.Append(wx.ID_ABOUT, "&About VISAN",
                               "Display the VISAN splash screen, version number and credits")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)

        menuBar.Append(helpmenu, "&Help")

        self.SetMenuBar(menuBar)

        if wx.Config.Get().Read('UserMode') == "Developer":

            developmenu = wx.Menu()

            item = developmenu.Append(wx.ID_ANY, "Open VISAN &Shell", "Open a VISAN/Python command line shell")
            self.Bind(wx.EVT_MENU, self.OnShell, item)

            item = developmenu.Append(wx.ID_ANY, "Open VISAN &Crust", "Open a VISAN/Python enhanced command line shell")
            self.Bind(wx.EVT_MENU, self.OnCrust, item)

            menuBar.Append(developmenu, "[&Develop]")

    def OnPrefs(self, event):
        PreferencesDialog(self).ShowModal()

    def OnExit(self, event):
        if self.closingdown:
            return

        self.closingdown = True
        for i in self.GetChildren():
            if isinstance(i, wx.Frame):
                i.Close(True)

        self.Destroy()
        self.app.Exit()

    def OnShowLog(self, event):
        self.app.ShowLog()

    def OnClearLog(self, event):
        self.app.ClearLog()

    def OnSaveLog(self, event):
        self.app.SaveLog()

    def OnExecuteScript(self, event):
        self.app.ExecuteScript()

    def OnBrowseProduct(self, event):
        self.app.BrowseProduct()

    def OnHarpImport(self, event):
        self.app.HarpImport()

    def OnFileHistory(self, event):
        filenum = event.GetId() - wx.ID_FILE1
        self.app.FileHistory(filenum)

    def OnShowOzone(self, event):
        self.app.ShowOzone()

    def OnIntro(self, event):
        self.app.ShowIntro()

    def OnAbout(self, event):
        self.app.ShowAbout()

    def OnVisanHelp(self, event):
        self.app.ShowHelp(mode="mainindex")

    def OnCodaHelp(self, event):
        self.app.ShowHelp(mode="coda")

    def OnHarpHelp(self, event):
        self.app.ShowHelp(mode="harp")

    def OnCodaDefHelp(self, event):
        self.app.ShowHelp(mode="codadef")

    def OnPythonHelp(self, event):
        self.app.ShowHelp(mode="python")

    def OnNumpyHelp(self, event):
        self.app.ShowHelp(mode="numpy")

    def OnShell(self, event):
        self.app.OpenShell()

    def OnCrust(self, event):
        self.app.OpenCrust()

    def OnUndo(self, event):
        win = wx.Window.FindFocus()
        win.Undo()

    def OnRedo(self, event):
        win = wx.Window.FindFocus()
        win.Redo()

    def OnCut(self, event):
        win = wx.Window.FindFocus()
        win.Cut()

    def OnCopy(self, event):
        win = wx.Window.FindFocus()
        win.Copy()

    def OnPaste(self, event):
        win = wx.Window.FindFocus()
        win.Paste()

    def OnDelete(self, event):
        win = wx.Window.FindFocus()
        win.Clear()

    def OnSelectAll(self, event):
        win = wx.Window.FindFocus()
        win.SelectAll()

    def OnUpdateMenu(self, event):
        win = wx.Window.FindFocus()
        eventid = event.GetId()
        event.Enable(True)
        try:
            if eventid == wx.ID_UNDO:
                event.Enable(win.CanUndo())
            elif eventid == wx.ID_REDO:
                event.Enable(win.CanRedo())
            elif eventid == wx.ID_CUT:
                event.Enable(win.CanCut())
            elif eventid == wx.ID_COPY:
                event.Enable(win.CanCopy())
            elif eventid == wx.ID_PASTE:
                event.Enable(win.CanPaste())
            elif eventid == wx.ID_CLEAR:
                event.Enable(win.CanCut())
            elif eventid == wx.ID_SELECTALL:
                event.Enable(hasattr(win, 'SelectAll'))
            else:
                event.Enable(False)
        except AttributeError:
            # This menu option is not supported in the current context.
            event.Enable(False)

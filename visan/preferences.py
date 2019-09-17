# Copyright (C) 2002-2019 S[&]T, The Netherlands.
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
import coda


class PreferencesDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Preferences")
        self.config = wx.Config.Get()

        self.currentdir = self.config.Read('DirectoryLocation/Products')

        self.CreateControls()
        self.CreateLayout()
        self.InstallToolTips()
        self.InstallEventListeners()

    def CreateControls(self):
        self.locLabel = wx.StaticText(self, -1, "&Location of your product-file directory:",
                                      size=wx.DLG_UNIT(self, -1, -1), style=wx.ALIGN_RIGHT)
        self.locField = wx.TextCtrl(self, -1, size=wx.DLG_UNIT(self, 150, -1), style=wx.TE_PROCESS_ENTER)
        self.browseButton = wx.Button(self, -1, "Browse...")

        self.filterRecordFields = wx.CheckBox(self, -1, "Show hidden and unavailable record fields")
        self.filterRecordFields.SetValue(not coda.get_option_filter_record_fields())

        self.performConversions = wx.CheckBox(self, -1, "Perform conversions")
        self.performConversions.SetValue(coda.get_option_perform_conversions())

        self.showByteSize = wx.CheckBox(self, -1, "Show byte sizes")
        self.showByteSize.SetValue(self.config.ReadBool('ProductBrowser/ShowByteSize'))

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.saveButton = wx.Button(self, wx.ID_OK, "Save")

        self.saveButton.Enable(len(self.currentdir) > 0)

        locdefault = self.currentdir
        if locdefault != "" and locdefault[-1] != os.sep:
            locdefault += os.sep

        self.locField.SetValue(locdefault)
        self.locField.SetInsertionPointEnd()
        self.SetDefaultItem(self.locField)
        self.locField.SetFocus()

    def CreateLayout(self):
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(self.locField, 1, wx.EXPAND | wx.RIGHT, border=10)
        hsizer1.Add(self.browseButton, 0, wx.EXPAND)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add((0, 0), 1, wx.EXPAND)
        hsizer2.Add(self.cancelButton, 0, wx.EXPAND | wx.RIGHT, border=10)
        hsizer2.Add(self.saveButton, 0, wx.EXPAND)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.locLabel, 0, wx.LEFT | wx.TOP | wx.RIGHT, border=10)
        vsizer.Add(hsizer1, 0, wx.EXPAND | wx.ALL, border=10)
        vsizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, 10)
        vsizer.Add(self.filterRecordFields, 0, wx.LEFT | wx.BOTTOM | wx.RIGHT, 10)
        vsizer.Add(self.performConversions, 0, wx.LEFT | wx.BOTTOM | wx.RIGHT, 10)
        vsizer.Add(self.showByteSize, 0, wx.LEFT | wx.BOTTOM | wx.RIGHT, 10)
        vsizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, 10)
        vsizer.Add(hsizer2, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
        vsizer.Fit(self)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(vsizer)
        self.CentreOnParent()

    def InstallToolTips(self):
        self.locField.SetToolTip(wx.ToolTip("The path to the directory where product files are located."))
        self.browseButton.SetToolTip(wx.ToolTip("Open a path selector dialog box."))
        self.filterRecordFields.SetToolTip(wx.ToolTip("If checked, hidden and unavailable record fields "
                                                      "will be shown in the product browser."))
        self.performConversions.SetToolTip(wx.ToolTip("If checked, units and values are converted as specified "
                                                      "in the data dictionary."))
        self.showByteSize.SetToolTip(wx.ToolTip("If checked, byte sizes will be shown in the product browser. "
                                                "Determining byte sizes may take much time, so the default is not "
                                                "to show them."))

    def InstallEventListeners(self):
        self.cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.saveButton.Bind(wx.EVT_BUTTON, self.OnSave)
        self.browseButton.Bind(wx.EVT_BUTTON, self.OnBrowse)
        self.locField.Bind(wx.EVT_TEXT_ENTER, self.OnLocFieldEnter)
        self.locField.Bind(wx.EVT_TEXT, self.OnLocFieldChar)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnSave(self, event):
        self.pathname = self.locField.GetValue()

        self.pathname = os.path.abspath(os.path.expanduser(os.path.expandvars(self.pathname)))

        if not os.path.isdir(self.pathname):
            wx.MessageBox(parent=self, message="Product-file directory location is not a valid directory.",
                          caption="Error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
            return

        coda.set_option_filter_record_fields(not self.filterRecordFields.GetValue())
        coda.set_option_perform_conversions(self.performConversions.GetValue())

        self.config.Write('DirectoryLocation/Products', self.pathname)
        self.config.WriteBool('ProductBrowser/ShowByteSize', self.showByteSize.GetValue())
        self.config.WriteBool('CODA/PerformConversions', coda.get_option_perform_conversions())
        self.config.WriteBool('CODA/FilterRecordFields', coda.get_option_filter_record_fields())
        self.config.Flush()

        self.EndModal(wx.ID_OK)

    def OnLocFieldChar(self, event):
        self.saveButton.Enable(self.locField.GetValue() != "")

    def OnLocFieldEnter(self, event):
        self.OnSave(None)

    def OnBrowse(self, event):
        directory = os.path.dirname(self.locField.GetValue())
        if not directory:
            directory = self.currentdir

        directory = os.path.abspath(os.path.expanduser(os.path.expandvars(directory)))

        pathname = wx.DirSelector("Select Path", directory, wx.FD_SAVE, parent=self)
        if pathname:
            self.locField.SetValue(pathname)
            self.locField.SetInsertionPointEnd()
            self.saveButton.SetFocus()
            self.currentdir = os.path.dirname(pathname)

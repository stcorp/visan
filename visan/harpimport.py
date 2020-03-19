# Copyright (C) 2002-2020 S[&]T, The Netherlands.
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


class HarpImportDialog(wx.Dialog):

    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.InitUI()
        self.SetTitle("Import product using Harp")

    def InitUI(self):
        panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)

        self.fileLabel = wx.StaticText(self, label="file path :")
        grid.Add(self.fileLabel, flag=wx.ALIGN_RIGHT | wx.ALL, pos=(0, 0))
        self.filePicker = wx.FilePickerCtrl(self, size=(500, -1), style=wx.FLP_USE_TEXTCTRL)
        grid.Add(self.filePicker, pos=(0, 1))

        self.operationsLabel = wx.StaticText(self, label="operations :")
        grid.Add(self.operationsLabel, flag=wx.ALIGN_RIGHT | wx.ALL, pos=(1, 0))
        self.operationsText = wx.TextCtrl(self, size=(500, -1))
        self.operationsText.SetToolTip(wx.ToolTip("semi-colon separated string of operations to apply as part of "
                                                  "the import (see HARP documentation for further details)"))
        grid.Add(self.operationsText, pos=(1, 1))

        self.ingestionOptionsLabel = wx.StaticText(self, label="ingestion options :")
        grid.Add(self.ingestionOptionsLabel, flag=wx.ALIGN_RIGHT | wx.ALL, pos=(2, 0))
        self.ingestionOptionsText = wx.TextCtrl(self, size=(500, -1))
        self.ingestionOptionsText.SetToolTip(wx.ToolTip("semi-colon separated string of key=value pairs to use as "
                                                        "ingestion options when importing from a product that is not "
                                                        "in HARP format (see HARP 'ingestion definitions' "
                                                        "documentation for further details)"))
        grid.Add(self.ingestionOptionsText, pos=(2, 1))

        self.variableLabel = wx.StaticText(self, label="variable name :")
        grid.Add(self.variableLabel, flag=wx.ALIGN_RIGHT | wx.ALL, pos=(3, 0))
        self.variableText = wx.TextCtrl(self, value="product", size=(200, -1))
        self.variableText.SetToolTip(wx.ToolTip("the name of the variable as it will end up in the VISAN Python shell"))
        grid.Add(self.variableText, pos=(3, 1))

        mainSizer.Add(grid, 0, wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, label='Import')
        cancelButton = wx.Button(self, wx.ID_CANCEL, label='Cancel')
        hbox.Add(okButton)
        hbox.Add(cancelButton, flag=wx.LEFT, border=5)
        mainSizer.Add(hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def OnHarpFormat(self, event):
        self.ingestionOptionsLabel.Enable(not self.harpformatCtrl.IsChecked())
        self.ingestionOptionsText.Enable(not self.harpformatCtrl.IsChecked())

    def GetFilename(self):
        return self.filePicker.GetPath()

    def GetIsHarpFormat(self):
        return self.harpformatCtrl.IsChecked()

    def GetOperations(self):
        return self.operationsText.GetValue()

    def GetIngestionOptions(self):
        return self.ingestionOptionsText.GetValue()

    def GetVariableName(self):
        return self.variableText.GetValue()

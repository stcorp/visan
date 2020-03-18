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

"""
Custom dialog for allowing the user to easily specify a filename
of a certain type, that is: a name with a verified extension.

The use provides the TypedSaveFileDialog upon creation with a
list of (description, extension) tuples representing the allowed
file types.

The Dialog will only successfully exit if the user specifies a
filename that is of an allowed type, either by specifying a
filename that ends in one of the supplied extensions, or by
explicitly connecting one of the supplied types to an arbitrary
filename by choosing a type from a pop-up menu.

Sample usage (e.g. from within a wx.Frame OnSave handler):

    imageExtensions = [('TIFF', 'tif'),
                       ('Windows Bitmap', 'bmp'),
                       ('JPEG', 'jpg'),
                       ('PNG', 'png'),
                       ('PNM', 'pnm')
                       ]

    dlg = TypedSaveFileDialog(parent=self,
                              title='Save Image',
                              initialdir='$HOME',
                              typeinfo=imageExtensions)

    if dlg.ShowModal() == wx.ID_OK:
       print '  chosen file name: ', dlg.filename
       print '  chosen type extension: ', dlg.ext


Note that the chosen type extension is not always deducible from
the filename. If the user first chooses an explicit filetype from
the pop-up box, but then manually changes the resulting filename,
it can be possible for the dialog to have exit values of e.g.
dlg.filename == 'image.png', but dlg.ext == 'jpg'.

"""
import wx
import os


class TypedSaveFileDialog(wx.Dialog):

    def __init__(self, parent, title, initialdir, typeinfo):
        wx.Dialog.__init__(self, parent, -1, title)
        self.currentdir = os.path.abspath(os.path.expanduser(os.path.expandvars(str(initialdir))))
        self.typeinfo = typeinfo
        if len(typeinfo) > 1:
            self.typeinfo = [("By Extension", None)] + self.typeinfo
        self.str2ext = dict(typeinfo)

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

        # Other Event Listeneres
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def CreateControls(self):
        locdefault = self.currentdir
        if locdefault != "" and locdefault[-1] != os.sep:
            locdefault += os.sep

        self.locLabel = wx.StaticText(self, -1, "&Location:", size=wx.DLG_UNIT(self, -1, -1), style=wx.ALIGN_RIGHT)

        self.locField = wx.TextCtrl(self, -1, size=wx.DLG_UNIT(self, 150, -1), style=wx.TE_PROCESS_ENTER)
        self.locField.SetValue(locdefault)
        self.locField.SetInsertionPointEnd()
        self.locField.SetToolTip(wx.ToolTip("The filename to save to."))
        self.locField.Bind(wx.EVT_TEXT_ENTER, self.OnLocFieldEnter)
        self.locField.Bind(wx.EVT_TEXT, self.OnLocFieldChar)

        self.browseButton = wx.Button(self, -1, "Browse...")
        self.browseButton.SetToolTip(wx.ToolTip("Open a file selector dialog box."))
        self.browseButton.Bind(wx.EVT_BUTTON, self.OnBrowse)

        self.typeLabel = wx.StaticText(self, -1, "Determine File Type:", size=wx.DLG_UNIT(self, -1, -1),
                                       style=wx.ALIGN_RIGHT)

        self.typeChoice = wx.Choice(self, -1, choices=[desc for (desc, ext) in self.typeinfo])
        self.typeChoice.Enable(len(self.typeinfo) > 1)
        self.typeChoice.SetSelection(0)
        self.typeChoice.SetToolTip(wx.ToolTip("Available formats (this will auto-update filename if appropriate)."))
        self.typeChoice.Bind(wx.EVT_CHOICE, self.OnTypeChoice)

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)

        self.saveButton = wx.Button(self, wx.ID_OK, "Save")
        self.saveButton.Enable(False)
        self.saveButton.Bind(wx.EVT_BUTTON, self.OnSave)

        self.SetDefaultItem(self.locField)

        self.locField.SetFocus()

    def CreateLayout(self):
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(self.locField, 1, wx.EXPAND | wx.RIGHT, border=10)
        hsizer1.Add(self.browseButton, 0, wx.EXPAND)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(self.typeLabel, 0, wx.ALIGN_CENTER | wx.RIGHT, border=10)
        hsizer2.Add(self.typeChoice, 0, wx.ALIGN_CENTER)

        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer3.Add((0, 0), 1, wx.EXPAND)
        hsizer3.Add(self.cancelButton, 0, wx.EXPAND | wx.RIGHT, border=10)
        hsizer3.Add(self.saveButton, 0, wx.EXPAND)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.locLabel, 0, wx.LEFT | wx.TOP | wx.RIGHT, border=10)
        vsizer.Add(hsizer1, 0, wx.EXPAND | wx.ALL, border=10)
        vsizer.Add(hsizer2, 0, wx.EXPAND | wx.ALL, border=10)
        vsizer.Add(hsizer3, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
        vsizer.Fit(self)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(vsizer)
        self.CentreOnParent()

    def OnTypeChoice(self, event):
        typestring = str(self.typeChoice.GetStringSelection())
        if typestring == "By Extension":
            return

        filename = str(self.locField.GetValue())
        if not filename:
            return

        base, ext = os.path.splitext(filename)
        if not base.endswith(os.sep):
            newfilename = base + "." + self.str2ext[typestring]
            self.locField.SetValue(newfilename)
        self.locField.SetInsertionPointEnd()

    def OnClose(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnSave(self, event):
        self.filename = str(self.locField.GetValue())
        self.filetype = str(self.typeChoice.GetStringSelection())

        self.filename = os.path.abspath(os.path.expanduser(os.path.expandvars(self.filename)))

        if self.filetype != "By Extension":
            self.ext = self.str2ext[self.filetype]
        else:
            base, self.ext = os.path.splitext(self.filename)
            if not self.ext or self.ext == '.':
                wx.MessageBox(parent=self, message="Filename error: '%s' has no extension" % self.filename,
                              caption="Save Error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                return
            self.ext = self.ext[1:]
            if self.ext not in self.str2ext.values():
                wx.MessageBox(parent=self, message="Filename error: Unknown extension '%s'" % self.ext,
                              caption="Save Error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                return

        if os.path.exists(self.filename):
            overwrite = wx.MessageBox(parent=self,
                                      message="File '%s' already exists. Do you want to overwrite it?" % self.filename,
                                      caption="Confirm Overwrite",
                                      style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)

            if overwrite != wx.OK:
                return

        self.EndModal(wx.ID_OK)

    def OnLocFieldChar(self, event):
        self.saveButton.Enable(str(self.locField.GetValue()) != "")

    def OnLocFieldEnter(self, event):
        self.OnSave(None)

    def OnBrowse(self, event):
        directory = os.path.dirname(str(self.locField.GetValue()))
        if not directory:
            directory = self.currentdir
        directory = os.path.abspath(os.path.expanduser(os.path.expandvars(directory)))
        filename = wx.FileSelector("Save As...", default_path=directory, flags=wx.FD_SAVE, parent=self)
        if filename:
            self.locField.SetValue(filename)
            self.locField.SetInsertionPointEnd()
            self.saveButton.SetFocus()
            self.currentdir = os.path.dirname(filename)

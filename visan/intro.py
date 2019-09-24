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


class IntroFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Getting Started with VISAN")

        self.SetIcon(wx.Icon(os.path.join(wx.GetApp().datadir, "visan.ico"), wx.BITMAP_TYPE_ICO))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        intropanel = IntroPanel(self)
        self.sizer.Add(intropanel, 1, wx.EXPAND)

        self.SetSizerAndFit(self.sizer)
        self.CentreOnParent()


class IntroPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.CreateControls()
        self.CreateLayout()
        self.InstallToolTips()
        self.InstallEventListeners()

    def CreateControls(self):
        intro = ("Welcome to VISAN!\n\nIf you are new to VISAN you can do any of the following to get you started "
                 "using this application:\n\n"
                 "(a) Have a look at the VISAN documentation. You can open the documentation in your webbrowser by "
                 "chosing 'VISAN Documentation' from the 'Help' menu. The VISAN documentation contains a small "
                 "Tutorial to get you on your way quickly;\n\n"
                 "(b) To learn more about the language (Python) that you use to enter commands in VISAN, have a "
                 "look at the Python documentation which is also accessible from the 'Help' menu. This documentation "
                 "comes with a very extensive Tutorial explaining the basics of the Python language;\n\n"
                 "(c) In the examples directory of your VISAN installation ('" + wx.GetApp().exampledir + "') you "
                 "can find several example scripts. You can examine the contents of a script by opening it in a text "
                 "editor and/or you can run the script in VISAN using the 'Load and Execute Script...' option from "
                 "the 'File' menu.")
        if wx.Platform == '__WXMAC__':
            pointSize = 12
            width = 400
            height = 370
        else:
            pointSize = 10
            width = 470
            height = 430
        self.introText = wx.TextCtrl(self, -1, size=(width, height),
                                     style=wx.TE_RICH | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)

        font = wx.Font(pointSize=pointSize, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL,
                       weight=wx.FONTWEIGHT_BOLD)
        style = wx.TextAttr(colText=wx.Colour(153, 51, 51), font=font)
        self.introText.SetDefaultStyle(style)
        self.introText.SetEditable(False)
        self.introText.AppendText(intro)
        self.introText.Layout()
        self.againCheckBox = wx.CheckBox(self, -1, "Show this window at next startup")
        self.againCheckBox.SetValue(wx.Config.Get().ReadBool("ShowIntroFrame", True))
        self.againCheckBox.SetFocus()

    def CreateLayout(self):
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.vsizer.Add(self.introText, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.BOTTOM, border=10)
        self.vsizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
        self.vsizer.Add(self.againCheckBox, 0, wx.TOP, border=10)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.vsizer, 1, wx.ADJUST_MINSIZE | wx.EXPAND | wx.ALL, border=10)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.sizer)

        self.introText.ShowPosition(1)

    def InstallToolTips(self):
        self.againCheckBox.SetToolTip(wx.ToolTip("Even if you turn this option off, this window can always be "
                                                 "explicitly displayed via the 'Help' menu"))

    def InstallEventListeners(self):
        self.againCheckBox.Bind(wx.EVT_CHECKBOX, self.OnAgain)

    def OnAgain(self, event):
        wx.Config.Get().WriteBool("ShowIntroFrame", self.againCheckBox.IsChecked())

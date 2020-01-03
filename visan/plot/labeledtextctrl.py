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

import wx
import wx.lib.newevent

ValueChangedEvent, EVT_VALUE_CHANGED = wx.lib.newevent.NewCommandEvent()


class LabeledTextCtrl(wx.Panel):

    def __init__(self, parent=None, id=-1, label=None, value=None, formatstring=None, **keywd):
        wx.Panel.__init__(self, parent, id)

        self.formatstring = formatstring

        if label:
            self.label = wx.StaticText(self, -1, label, size=(-1, -1))

        if value is None:
            value = ""
        self.text = wx.TextCtrl(self, -1, value=str(value), **keywd)
        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)
        self.text.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.text.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

        self.hasfocus = False

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        if label:
            self.sizer.Add(self.label, 0, wx.ALIGN_CENTER | wx.RIGHT, border=3)
        self.sizer.Add(self.text, 1, wx.ALIGN_CENTER | wx.RIGHT)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.sizer)

    def GetValue(self):
        return self.text.GetValue()

    def SetValue(self, value):
        if value is None:
            value = ""
        if self.formatstring:
            try:
                return self.text.SetValue(self.formatstring % value)
            except TypeError:
                raise RuntimeError("Type of '%s' does not match format string '%s'" % (value, self.formatstring))
        else:
            return self.text.SetValue(str(value))

    def SetFormat(self, formatstring):
        self.formatstring = formatstring

    def OnTextEnter(self, event):
        self.text.SetSelection(-1, -1)
        wx.PostEvent(self, ValueChangedEvent(self.GetId(), value=event.GetString()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def OnSetFocus(self, event):
        self.hasfocus = True
        self.text.SetSelection(-1, -1)
        event.Skip()

    def OnKillFocus(self, event):
        event.Skip()
        self.text.SetSelection(0, 0)
        if self.text.IsModified() and self.hasfocus:
            wx.PostEvent(self, ValueChangedEvent(self.GetId(), value=self.text.GetValue()))
            if wx.Platform == '__WXMAC__':
                wx.Yield()
        self.hasfocus = False

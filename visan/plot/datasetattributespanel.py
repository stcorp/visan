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


def _isList(obj):
    try:
        iter(obj)
    except Exception:
        return False
    else:
        try:
            import numpy
            if isinstance(obj, numpy.ndarray):
                return True
        except Exception:
            pass
        try:
            obj + ''
        except Exception:
            return True
        else:
            return False


class DataSetAttributesPanel(wx.Panel):

    def __init__(self, parent):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        # Create the two column list for showing attributes
        self.attributeList = wx.ListCtrl(self, -1, style=(wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_VRULES),
                                         size=(100, -1))
        self.attributeList.InsertColumn(0, "attribute")
        self.attributeList.InsertColumn(1, "value")

    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.attributeList, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def UpdateAttributes(self, attributes, keyframe):
        self.attributeList.DeleteAllItems()
        keys = sorted(attributes.keys())
        for key in keys:
            value = attributes[key]
            if _isList(value):
                # try to see if we can use a keyframe index for the value
                try:
                    value = value[keyframe]
                except IndexError:
                    # if the keyframe is out of range, just use the final value
                    value = value[-1]
                except Exception:
                    pass
            self.attributeList.Append([key, value])
        self.attributeList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        if wx.Platform == '__WXMSW__':
            self.attributeList.SetColumnWidth(0, self.attributeList.GetColumnWidth(0) + 5)
        self.attributeList.SetColumnWidth(1, wx.LIST_AUTOSIZE)

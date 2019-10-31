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

import sys
from code import InteractiveInterpreter

import wx
import wx.py


class VisanShell(wx.py.shell.Shell):

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 introText='', locals={}, *args, **kwargs):
        self.runStartupCommands(locals)
        super(VisanShell, self).__init__(parent, id, pos, size, style, introText, locals, *args, **kwargs)
        self.setDisplayLineNumbers(True)
        if wx.Platform == '__WXMAC__':
            self.zoom(-1)

    def runStartupCommands(self, locals):
        interp = InteractiveInterpreter(locals)
        """Execute the startup commands that import default modules"""
        interp.runsource("import os")
        interp.runsource("import sys")
        interp.runsource("import wx")
        interp.runsource("import vtk")
        interp.runsource("import numpy")
        interp.runsource("np = numpy")
        interp.runsource("import coda")
        interp.runsource("import harp")
        interp.runsource("import visan")
        interp.runsource("import visan.math")
        interp.runsource("from visan.commands import *")
        self.version = interp.locals['visan'].VERSION
        self.component_versions = [
            "Python %d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]),
            "wxPython %s" % interp.locals['wx'].VERSION_STRING,
            "VTK %s" % interp.locals['vtk'].VTK_VERSION,
            "NumPy %s" % interp.locals['numpy'].__version__,
            "CODA %s" % interp.locals['coda'].version(),
            "HARP %s" % interp.locals['harp'].version(),
        ]

    def showIntro(self, text=''):
        if text:
            if not text.endswith(os.linesep):
                text += os.linesep
            self.write(text)
        else:
            self.write("Copyright (C) 2002-2019 S[&]T, The Netherlands.\n\n")
            self.write("Welcome to the VISAN/Python Control Shell.\n\n")
            self.write("VISAN %s (%s)\n" % (self.version, ", ".join(self.component_versions)))

    def autoCallTipShow(self, command, insertcalltip=True, forceCallTip=False):
        """Display argument spec and docstring in a popup window."""
        if self.CallTipActive():
            self.CallTipCancel()
        (name, argspec, tip) = self.interp.getCallTip(command)
        if not self.autoCallTip and not forceCallTip:
            return
        if argspec and insertcalltip:
            startpos = self.GetCurrentPos()
            self.write(argspec + ')')
            endpos = self.GetCurrentPos()
            self.SetSelection(startpos, endpos)

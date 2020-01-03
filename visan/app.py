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
import sys
import traceback
import webbrowser

import wx
import wx.adv
import wx.py
from wx.lib.mixins.inspection import InspectionMixin

import harp
import coda

from .frame import VisanFrame
from .intro import IntroFrame
from .harpimport import HarpImportDialog
from .productbrowser import ProductBrowser
from . import windowhandler as WindowHandler

from . import VERSION


class VisanApp(wx.App, InspectionMixin):

    def __init__(self):
        visanhomedir = os.path.dirname(__file__)
        # setup directory locations
        self.homedir = visanhomedir
        self.datadir = os.path.join(visanhomedir, 'data')
        self.exampledir = os.path.join(visanhomedir, 'examples')
        if wx.Platform == '__WXMSW__':
            self.docdir = os.path.join(visanhomedir, 'Doc')
        else:
            self.docdir = os.path.join(visanhomedir, 'doc')
        self.htmldir = os.path.join(self.docdir, 'html')

        wx.App.__init__(self, redirect=(sys.platform == 'win32'))

        wx.SystemOptions.SetOption("mac.listctrl.always_use_generic", "1")

        # add current working directory to sys.path (if applicable)
        if wx.Platform == '__WXGTK__':
            sys.path.insert(0, os.getcwd())
        elif wx.Platform == '__WXMSW__':
            if os.getcwd() != sys.prefix + '\\bin':
                sys.path.insert(0, os.getcwd())

    def OnInit(self):

        # Make sure the file location for our preferences exists
        userDataDir = wx.StandardPaths.Get().GetUserDataDir()
        if not os.path.exists(userDataDir):
            os.mkdir(userDataDir)

        self.productdir = wx.StandardPaths.Get().GetDocumentsDir()

        # Initialize preferences
        configStyle = wx.CONFIG_USE_LOCAL_FILE
        if wx.Platform == '__WXGTK__':
            configStyle |= wx.CONFIG_USE_SUBDIR
        config = wx.Config(appName='visan', style=configStyle)
        config.SetRecordDefaults()
        wx.Config.Set(config)

        # Set some global defaults
        config.Read('UserMode', 'EndUser')
        config.Read('DirectoryLocation/Export', wx.StandardPaths.Get().GetDocumentsDir())
        config.Read('DirectoryLocation/Products', self.productdir)
        config.Read('DirectoryLocation/Scripts', self.exampledir)
        # datadir is not something that the user should change, but it is usefull to be able to get
        # to this parameter using the Config system, so that is why we set it here explicitly
        config.Write('DirectoryLocation/ApplicationData', self.datadir)
        # since icons are platform specific we store the appropriate icon to use in the config
        if wx.Platform == '__WXGTK__':
            config.Write('IconFile', os.path.join(self.datadir, "visan32.ico"))
        else:
            config.Write('IconFile', os.path.join(self.datadir, "visan.ico"))

        if config.Read('UserMode') == 'Developer':
            # allows you to pop up a window with an overview of all the widgets in VISAN
            # the shortcut for this is Ctrl-Alt-I (or Cmd-Alt-I on Mac)
            InspectionMixin.Init(self)

        self.filehistory = wx.FileHistory()
        self.recentfiles = False

        coda.set_option_perform_conversions(config.ReadBool('CODA/PerformConversions', True))
        coda.set_option_filter_record_fields(config.ReadBool('CODA/FilterRecordFields', True))

        self.frame = VisanFrame(self, "VISAN " + VERSION, WindowHandler.GetNextPosition((800, 640)), (800, 640))
        self.SetTopWindow(self.frame)
        self.shell = self.frame.shell

        self._PrefsToFileHistory()

        self._SetupLogging()

        wx.py.dispatcher.connect(receiver=self.CheckForExit, signal='Interpreter.push')

        self.frame.Show(True)

        if wx.Config.Get().ReadBool('ShowIntroFrame', True):
            self.ShowIntro()

        self._CreateSplashScreen()

        if len(sys.argv) > 1:
            # don't treat macos -psn arguments as a startup script
            if not (wx.Platform == '__WXMAC__' and sys.argv[1].startswith('-psn_')):
                self._ExecuteScript(sys.argv[1])

        return True

    def _FileHistoryToPrefs(self):
        if self.recentfiles:
            config = wx.Config.Get()
            if config.HasGroup('RecentScripts'):
                config.DeleteGroup('RecentScripts')
            # we write the files in reverse order in order to balance to reversal caused by _AddFileToHistory
            for i in range(self.filehistory.GetCount()):
                filename = self.filehistory.GetHistoryFile(self.filehistory.GetCount() - i - 1)
                config.Write('RecentScripts/file%d' % i, filename)

    def _PrefsToFileHistory(self):
        config = wx.Config.Get()
        i = 0
        while config.Exists('RecentScripts/file%d' % i):
            self._AddFileToHistory(config.Read('RecentScripts/file%d' % i))
            i += 1

    def _SetupLogging(self):
        self.loggingMode = True
        self.sessionlogFrame = LogWindow(self.frame, -1, "VISAN Session Log", size=(450, 200))
        self.sessionlisting = SessionListing(self.sessionlogFrame)
        self.sessionlisting.Start()

    def CloseLogWindow(self):
        self.sessionlogFrame.Show(False)

    def ShowLog(self):
        self.sessionlogFrame.Raise()
        self.sessionlogFrame.Show(True)

    def ClearLog(self):
        self.sessionlisting.Clear()

    def SaveLog(self):
        filename = wx.FileSelector("Save VISAN/Python Script", default_extension="py",
                                   default_path=wx.Config.Get().Read('DirectoryLocation/Scripts'),
                                   wildcard="VISAN/Python Script|*.py", flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                                   parent=self.frame)
        if filename:
            if not filename.endswith(".py"):
                filename = filename + ".py"
            saved = self.sessionlisting.SaveFile(filename)
            if saved:
                self._AddFileToHistory(filename)
                wx.Config.Get().Write('DirectoryLocation/Scripts', os.path.dirname(filename))

    def ExecuteScript(self):
        filename = wx.FileSelector("Open VISAN/Python Script", default_extension="py",
                                   default_path=wx.Config.Get().Read('DirectoryLocation/Scripts'),
                                   wildcard="VISAN/Python Scripts|*.py|All Files|*",
                                   flags=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, parent=self.frame)
        if filename:
            self._ExecuteScript(filename)
            self._AddFileToHistory(filename)
            wx.Config.Get().Write('DirectoryLocation/Scripts', os.path.dirname(filename))

    def _ExecuteScript(self, filename):
        self.shell.clearCommand()
        self.shell.interp.more = False
        self.shell.DocumentEnd()
        self.shell.write("execute script: " + filename)
        self.shell.push('executescript(%r, globals())\n' % filename)
        self.shell.DocumentEnd()

    def BrowseProduct(self, filename=None):
        if filename is None:
            filename = wx.FileSelector("Browse Product File",
                                       default_path=wx.Config.Get().Read('DirectoryLocation/Products'),
                                       wildcard="All Files|*", flags=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                                       parent=self.frame)
        if filename:
            try:
                browser = ProductBrowser(self.frame, filename)
            except coda.CodacError as ex:
                message = wx.MessageDialog(self.frame,
                                           "Could not open product.\n\nCODA error message: \"%s\"" % str(ex),
                                           "CODA error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                message.ShowModal()
                return
            browser.SetPosition(WindowHandler.GetNextPosition(browser.GetSize()))
            if wx.Config.Get().Read("IconFile"):
                browser.SetIcon(wx.Icon(wx.Config.Get().Read("IconFile")))
            browser.Show()
            wx.Config.Get().Write('DirectoryLocation/Products', os.path.dirname(filename))

    def HarpImport(self, filename=None, operations=None, ingestionOptions=None, variableName=None):
        if filename is None:
            importDialog = HarpImportDialog(self.frame)
            if importDialog.ShowModal() == wx.ID_OK:
                filename = importDialog.GetFilename()
                operations = importDialog.GetOperations()
                ingestionOptions = importDialog.GetIngestionOptions()
                variableName = importDialog.GetVariableName()
            importDialog.Destroy()
        if not filename:
            return
        if variableName:
            self.shell.clearCommand()
            self.shell.interp.more = False
            self.shell.DocumentEnd()
            command = "%s = harp.import_product(r\"%s\"" % (variableName, filename)
            if operations:
                command += ", operations='%s'" % (operations,)
            if ingestionOptions:
                command += ", options='%s'" % (ingestionOptions,)
            command += ")\n"
            self.shell.write(command)
            self.shell.push(command)
            self.shell.DocumentEnd()
        else:
            try:
                data = harp.import_product(filename, operations, ingestionOptions)
            except harp.Error as ex:
                message = wx.MessageDialog(self.frame,
                                           "Could not import product(s).\n\nHARP error message: \"%s\"" % str(ex),
                                           "HARP error", style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP)
                message.ShowModal()
                return

    def _AddFileToHistory(self, filename):
        if not self.recentfiles:
            self.recentfiles = True
            self.frame.recentMenuItem.Enable(True)

        self.filehistory.AddFileToHistory(filename)

    def FileHistory(self, filenum):
        path = self.filehistory.GetHistoryFile(filenum)
        self._ExecuteScript(path)

    def CheckForExit(self, command, more):
        if command in ["exit", "quit", "close"]:
            wx.CallAfter(self.frame.Close)

    def OpenShell(self):
        shellframe = wx.py.shell.ShellFrame(parent=self.frame, title="VISAN shell", locals=self.shell.interp.locals)
        shellframe.SetSize((700, 500))
        shellframe.Show()
        return True

    def OpenCrust(self):
        shellframe = wx.py.crust.CrustFrame(parent=self.frame, title="VISAN Crust", locals=self.shell.interp.locals)
        shellframe.SetSize((700, 500))
        shellframe.Show()
        return True

    def _CreateSplashScreen(self, timeout=True):
        self.aboutIsShown = True
        mode = wx.adv.SPLASH_CENTRE_ON_PARENT
        if timeout:
            mode |= wx.adv.SPLASH_TIMEOUT
        else:
            mode |= wx.adv.SPLASH_NO_TIMEOUT
        splashscreen = wx.adv.SplashScreen(wx.Bitmap(os.path.join(self.datadir, 'visan-logo.png'), wx.BITMAP_TYPE_PNG),
                                           mode, 750, self.frame, -1)
        splashscreen.Bind(wx.EVT_CLOSE, self.CloseAbout)
        wx.Yield()

    def ShowAbout(self):
        if self.aboutIsShown:
            return
        self._CreateSplashScreen(False)

    def CloseAbout(self, event):
        self.aboutIsShown = False
        event.Skip()

    def Exit(self):
        self._FileHistoryToPrefs()
        config = wx.Config.Get()
        config.WriteBool('CODA/PerformConversions', coda.get_option_perform_conversions())
        config.WriteBool('CODA/FilterRecordFields', coda.get_option_filter_record_fields())
        config.DeleteEntry('DirectoryLocation/ApplicationData')
        config.DeleteEntry('IconFile')
        config.Flush()
        sys.exit(0)

    def ShowIntro(self):
        try:
            if self.introframe.IsIconized():
                self.introframe.Iconize(False)
            if not self.introframe.IsShown():
                self.introframe.Show(True)
            self.introframe.Raise()
        except (AttributeError, RuntimeError):
            self.introframe = IntroFrame(self.frame)
            self.introframe.Show(True)

    def ShowHelp(self, mode):
        if mode == "coda":
            helpurl = "http://stcorp.github.io/coda/doc/html/index.html"
        elif mode == "harp":
            helpurl = "http://stcorp.github.io/harp/doc/html/index.html"
        elif mode == "codadef":
            helpurl = "http://stcorp.nl/coda/codadef/"
        elif mode == "python":
            helpurl = "http://docs.python.org/%d.%d/" % (sys.version_info.major, sys.version_info.minor)
        elif mode == "numpy":
            helpurl = "http://docs.scipy.org/doc/numpy/reference/"
        else:
            helpurl = "http://stcorp.github.io/visan/"

        try:
            webbrowser.open_new(helpurl)
        except Error as ex:
            wx.MessageBox("Error launching external browser:\n%s" % str(ex),
                          "VISAN Error", wx.OK | wx.ICON_INFORMATION)


class LogWindow(wx.Frame):

    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=(650, 400)):
        wx.Frame.__init__(self, parent, id, title, pos, size)
        if wx.Config.Get().Read("IconFile"):
            self.SetIcon(wx.Icon(wx.Config.Get().Read("IconFile")))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        if event.CanVeto():
            self.Show(False)
            event.Veto()
        else:
            self.Destroy()


class SessionListing(wx.TextCtrl):
    """Text control containing all commands for session."""

    def __init__(self, parent=None, id=-1):
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_DONTWRAP
        wx.TextCtrl.__init__(self, parent=parent, id=id, style=style)

    def Start(self):
        wx.py.dispatcher.connect(receiver=self.Push, signal='Interpreter.push')

    def Stop(self):
        wx.py.dispatcher.disconnect(receiver=self.Push, signal='Interpreter.push')

    def Push(self, command, more):
        """Receiver for Interpreter.push signal."""
        if command and not more:
            self.SetInsertionPointEnd()
            (start, end) = self.GetSelection()
            if start != end:
                self.SetSelection(0, 0)
            self.AppendText(command + '\n')

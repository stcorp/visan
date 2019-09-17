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
import wx
import wx.lib.newevent

from .util import DetermineCharSize

KeyframeEvent, EVT_KEYFRAME_CHANGED = wx.lib.newevent.NewEvent()


class AnimationToolbar(wx.Panel):

    """ This class can be used to create animation. It fires an
    EVT_KEYFRAME_CHANGED if the slider has moved either by hand
    or by the integrated Timer control"""

    def __init__(self, parent, plotWindow):
        panelStyle = wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER
        if sys.platform == 'win32':
            # We need to add the full repaint on resize property on Windows to force proper drawing of the controls
            panelStyle = panelStyle | wx.FULL_REPAINT_ON_RESIZE

        wx.Panel.__init__(self, parent, -1, style=panelStyle)

        # Initialize state
        self.plotWindow = plotWindow
        self.currentKeyframe = 0
        self.numKeyframes = plotWindow.GetNumKeyframes()
        self.interval = 50
        self.running = False
        self.loop = False

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        self.playString = "Play"
        self.pauseString = "Pause"
        # NOTE: The following lines would cause a segmentation fault. I suspect
        # that internally, ToolTips (or their C proxies) are deleted
        # regardless of Python refcount, so you can't reuse them like
        # this (similar to what is documented for Icons).
        #
        # self.playtip  = wx.ToolTip("Display the frames in the plot in sequence")
        # self.pausetip = wx.ToolTip("Pause the plot frame animation")
        self.playtipstr = "Start running through the frames in the plot in sequence."
        self.pausetipstr = "Pause the plot frame animation."

        (charWidth, charHeight) = DetermineCharSize(self)

        maxRangeValue = self.numKeyframes - 1
        if self.numKeyframes <= 1:
            # GTK2 doesn't like it if 'min' equals 'max' for a range
            maxRangeValue = 1

        self.TIMER = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.PLAY = wx.Button(self, -1, self.playString)
        self.PLAY.SetToolTip(wx.ToolTip(self.playtipstr))
        self.PLAY.Bind(wx.EVT_BUTTON, self.OnAnimate)

        self.SLIDER = wx.Slider(self, -1, value=0, minValue=0, maxValue=maxRangeValue)
        self.SLIDER.SetToolTip(wx.ToolTip("Pause the plot frame animation."))
        self.SLIDER.Bind(wx.EVT_COMMAND_SCROLL, self.OnScroll)

        self.RESET = wx.Button(self, -1, "Reset")
        self.RESET.SetToolTip(wx.ToolTip("Drag this slider to manually animate the plot frames."))
        self.RESET.Bind(wx.EVT_BUTTON, self.OnReset)

        self.KEYFRAME = wx.SpinCtrl(self, -1, str(0), size=(5 * charWidth, -1),
                                    style=wx.SP_WRAP | wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER | wx.TE_RIGHT,
                                    min=0, max=maxRangeValue, initial=0)
        self.KEYFRAME.SetToolTip(wx.ToolTip("Enter the number of a plot frame to display. "
                                            "Use the arrows to increment/decrement by one."))
        self.KEYFRAME.Bind(wx.EVT_SPINCTRL, self.OnKeyframe)
        self.KEYFRAME.Bind(wx.EVT_TEXT_ENTER, self.OnKeyframe)

        self.LOOP = wx.CheckBox(self, -1, "Loop")
        self.LOOP.SetToolTip(wx.ToolTip("Automatically restart the animation at the first plot frame."))
        self.LOOP.SetValue(self.loop)
        self.LOOP.Bind(wx.EVT_CHECKBOX, self.OnLoop)

        self.SPEEDLABEL = wx.StaticText(self, -1, "Speed:")
        self.SPEEDLABEL.SetToolTip(wx.ToolTip("Enter the animation speed to use, in frames per second. "
                                              "Use the arrows to increment/decrement by one."))

        self.SPEEDFIELD = wx.SpinCtrl(self, -1, str(self.GetFPS()), size=(5 * charWidth, -1),
                                      style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER, min=1, max=60,
                                      initial=self.GetFPS())
        self.SPEEDFIELD.SetToolTip(wx.ToolTip("Enter the animation speed to use, in frames per second. "
                                              "Use the arrows to increment/decrement by one."))
        self.SPEEDFIELD.Bind(wx.EVT_SPINCTRL, self.OnSpeed)
        self.SPEEDFIELD.Bind(wx.EVT_TEXT_ENTER, self.OnSpeed)

    def CreateLayout(self):
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.PLAY, 0, wx.ALIGN_CENTER | wx.ALL, border=5)
        hsizer.Add(self.SLIDER, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.RIGHT, border=5)
        hsizer.Add(self.RESET, 0, wx.ALIGN_CENTER | wx.RIGHT, border=5)
        hsizer.Add(self.KEYFRAME, 0, wx.ALIGN_CENTER | wx.RIGHT, border=5)
        hsizer.Add(wx.StaticLine(self, -1, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.RIGHT, border=5)
        hsizer.Add(self.LOOP, 0, wx.ALIGN_CENTER | wx.RIGHT, border=5)
        hsizer.Add(wx.StaticLine(self, -1, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.RIGHT, border=5)
        hsizer.Add(self.SPEEDLABEL, 0, wx.ALIGN_CENTER | wx.RIGHT, border=5)

        # On MacOS, the right lower corner of a frame is taken up by the resize window widget, so we must keep our
        # animation toolbar controls away from it. Since gratuituous spacing is butt-ugly on other platforms, I
        # am solving this by special-casing for the Mac.
        if '__WXMAC__' in wx.PlatformInfo:
            endspace = 15
        else:
            endspace = 5

        hsizer.Add(self.SPEEDFIELD, 0, wx.ALIGN_CENTER | wx.RIGHT, border=endspace)

        self.SetSizerAndFit(hsizer)

        self.PLAY.SetFocus()

    def UpdateNumKeyframes(self):
        self.numKeyframes = self.plotWindow.GetNumKeyframes()

        hascurrentfocus = wx.Window.FindFocus()
        maxRangeValue = self.numKeyframes - 1
        if self.numKeyframes <= 1:
            # GTK2 doesn't like it if 'min' equals 'max' for a range
            maxRangeValue = 1
        self.SLIDER.SetRange(0, maxRangeValue)
        self.KEYFRAME.SetRange(0, maxRangeValue)
        if hascurrentfocus:
            hascurrentfocus.SetFocus()

    def SetFPS(self, fps):
        """ Set Timer interval in FPS. Restarts timer if it is currently running """
        self.interval = int((1.0 / float(fps)) * 1000.0)
        self.SPEEDFIELD.SetValue(fps)
        if (self.running):
            self.TIMER.Start(self.interval)

    def GetFPS(self):
        """ Return Timer interval in FPS """
        return int((1.0 / self.interval) * 1000.0)

    def SetIntervalMSec(self, ms):
        """ Set interval to ms (msec) """
        self.interval = ms
        if (self.running):
            self.TIMER.Start(self.interval)

    def SetLoop(self, loop):
        """ Set whether the slider should loop on end """
        self.LOOP.SetValue(loop)
        self.loop = loop

    def GetLoop(self):
        """ Get the loop state """
        return self.loop

    def SetKeyframe(self, keyframe):
        """ Set the current keyframe """
        keyframe = min(keyframe, self.numKeyframes - 1)
        if keyframe != self.currentKeyframe:
            self.currentKeyframe = keyframe
            self.SLIDER.SetValue(keyframe)
            self.KEYFRAME.SetValue(keyframe)
            self.Update()
            wx.PostEvent(self, KeyframeEvent(keyframe=keyframe))

    def GetKeyframe(self):
        """ Get the current keyframe """
        return self.currentKeyframe

    def Play(self):
        """ Start animation """
        if self.currentKeyframe == self.numKeyframes - 1:
            self.Reset()

        self.running = True
        self.TIMER.Start(self.interval)
        self.PLAY.SetLabel(self.pauseString)
        self.PLAY.SetToolTip(wx.ToolTip(self.pausetipstr))
        self.KEYFRAME.Enable(False)

    def Pause(self):
        """ Pause animation """
        self.running = False
        self.TIMER.Stop()
        self.PLAY.SetLabel(self.playString)
        self.PLAY.SetToolTip(wx.ToolTip(self.playtipstr))
        self.KEYFRAME.Enable(True)

    def Reset(self):
        """ Reset animation """
        self.SetKeyframe(0)

    def TogglePlayPause(self):
        """ Toggle animation Play / Pause """
        if self.running:
            self.Pause()
        else:
            self.Play()

    def Destroy(self):
        self.Pause()
        wx.Panel.Destroy(self)

    def OnLoop(self, event):
        self.SetLoop(event.IsChecked())

    def OnSpeed(self, event):
        self.SetFPS(event.GetString())

    def OnScroll(self, event):
        """ Event Handler for Slider-Scroll """
        self.SetKeyframe(self.SLIDER.GetValue())

    def OnAnimate(self, event):
        self.TogglePlayPause()

    def OnStart(self, event):
        self.Play()

    def OnPause(self, event):
        self.Pause()

    def OnReset(self, event):
        """ Event Handler Reset Button """
        self.Reset()

    def OnTimer(self, event):
        """ Event Handler for Timer Event """
        # Discard timer events still arriving after animation has been stopped.
        if not self.running:
            return

        if self.currentKeyframe < self.numKeyframes - 1:
            # Advance 1
            self.SetKeyframe(self.currentKeyframe + 1)
        else:
            # Auto stop
            if self.loop:
                self.Reset()
            else:
                self.Pause()

    def OnKeyframe(self, event):
        """ Event Handler for TextCtrl->Press_Enter """
        self.SetKeyframe(event.GetString())

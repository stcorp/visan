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

import math
import numpy


class Pong:
    """ This is what happens if you get over-enthousiastic... [eddy]"""

    def __init__(self):
        self.nr_frames = 100

        self.bat1_x = [.005, .050, .050, .005, .005, .050, .005, .050, .005, .050]
        self.bat2_x = [.950, .995, .995, .950, .950, .995, .950, .995, .950, .995]

        self.bat_base_y = [0, 0, .5, .5, 0, .1, .2, .3, .4, .5]

        self.ball_base_x = .06
        self.ball_base_y = .5

        self.ball_state_x = 0
        self.ball_state_y = 0

        self.table_x = [0, 1, 1, 0, 0]
        self.table_y = [1, 1, 0, 0, 1]

        self.CalculateData()

    def bat1_func_y(self, y, x):
        return numpy.array(self.bat_base_y) + (numpy.sin((y + 1) * 2 * math.pi / self.nr_frames) / 2 + .5) / 2

    def bat2_func_y(self, y, x):
        return numpy.array(self.bat_base_y) + (numpy.cos((y + 10) * 4 * math.pi / self.nr_frames) / 2 + .5) / 2

    def ball_func_x(self, y, x):
        return 1 - (numpy.fabs((y - 50) / 56.8) + .06)

    def ball_func_y(self, y, x):
        return numpy.where(y < 25, ((y / 50.5) + .505) % 1, numpy.fabs(.995 - (y - 25) / 50.5))

    def CalculateData(self):
        import wx
        from visan.plot import PlotFrame

        plot = PlotFrame(wx.GetApp().GetTopWindow(), -1)
        dataSetId = plot.AddDataSet(self.table_x, self.table_y)
        plot.SetPlotColor(dataSetId, (0, 0, 0))
        plot.SetDataSetLabel(dataSetId, "Ping Pong Table")

        dataSetId = plot.AddDataSet(numpy.array(self.bat1_x),
                                    numpy.fromfunction(self.bat1_func_y, (self.nr_frames, len(self.bat_base_y))))
        plot.SetPlotColor(dataSetId, (0, 1.0, 0))
        plot.SetDataSetLabel(dataSetId, "Player 1")

        dataSetId = plot.AddDataSet(numpy.array(self.bat2_x),
                                    numpy.fromfunction(self.bat2_func_y, (self.nr_frames, len(self.bat_base_y))))
        plot.SetPlotColor(dataSetId, (0, 0, 1.0))
        plot.SetDataSetLabel(dataSetId, "Player 2")

        dataSetId = plot.AddDataSet(numpy.fromfunction(self.ball_func_x, (self.nr_frames, 1)),
                                    numpy.fromfunction(self.ball_func_y, (self.nr_frames, 1)))
        plot.SetPlotPoints(dataSetId, True)
        plot.SetPlotColor(dataSetId, (1.0, 0, 0))
        plot.SetPointSize(dataSetId, 3)
        plot.SetDataSetLabel(dataSetId, "The Ball")

        plot.SetPlotTitle("Pong")
        plot.SetXAxisRange((-0.1, 1.1))
        plot.SetYAxisRange((-0.1, 1.1))
        plot.ShowAnimationToolbar(False)

        plot.animationToolbar.SetLoop(True)
        plot.animationToolbar.SetFPS(40)
        plot.animationToolbar.Play()


def pong():
    Pong()

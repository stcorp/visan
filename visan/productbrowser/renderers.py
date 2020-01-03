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
import wx.grid
import coda
import numpy

import sys
import math

from . import frame
from . import model

usePlotRenderer = 1
try:
    from visan.plot.plotwindow import PlotWindow
except ImportError:
    usePlotRenderer = 0


# EXCEPTION HIERARCHY
class RenderError(Exception):
    """Generalization of all rendering errors"""
    pass


# CUSTOM EVENTS
wxEVT_SLICE_CHANGED = wx.NewEventType()
EVT_SLICE_CHANGED = wx.PyEventBinder(wxEVT_SLICE_CHANGED)


class SliceChangedEvent(wx.PyCommandEvent):

    def __init__(self, id):
        wx.PyCommandEvent.__init__(self, wxEVT_SLICE_CHANGED, id)


# UTILITY FUNCTIONS
def GetDecimalWidth(dc, number, template="%s"):
    assert number >= 0, "No negative numbers allowed."

    if number == 0:
        digitCount = 1
    else:
        digitCount = int(math.log10(number)) + 1

    tmp = template % ("9" * digitCount,)
    return dc.GetTextExtent(tmp)[0]


class NumpySlicer1D(wx.Panel):

    def __init__(self, parent, id, array, axisLabel):
        wx.Panel.__init__(self, parent, id)

        assert array.ndim >= 2, "Expected numpy array of at least rank 2."

        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey). taken
        # from: PlotFrame.py
        self.SetBackgroundColour(self.GetBackgroundColour())

        self.array = array
        self.spinMap = {}
        self.spinners = []
        self.index = [0] * self.array.ndim

        # create UI
        self.axisGroup = frame.ButtonGroup()

        # compute button dimensions
        buttonWidth, buttonHeight = self.GetTextExtent(axisLabel)

        # compute spinner width
        spinnerWidth = 0
        for i in range(0, self.array.ndim):
            spinnerWidth = max(spinnerWidth, GetDecimalWidth(self, self.array.shape[i] - 1))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((0, 0), 1)
        for i in range(0, self.array.ndim):
            spinControl = wx.SpinCtrl(self, -1, style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER)
            spinControl.SetRange(0, self.array.shape[i] - 1)
            spinControl.SetValue(0)
            spinControl.SetSizeHints(spinnerWidth + 30, -1)
            self.spinMap[spinControl.GetId()] = i
            self.spinners.append(spinControl)

            button = wx.ToggleButton(self, -1, axisLabel)
            button.SetSizeHints(buttonWidth + 10, -1)
            self.axisGroup.AppendButton(button)

            axisSizer = wx.BoxSizer(wx.VERTICAL)
            axisSizer.Add(spinControl, 0, wx.EXPAND, 0)
            axisSizer.Add((3, 3), 0, 0, 0)
            axisSizer.Add(button, 0, wx.EXPAND, 0)
            sizer.Add(axisSizer, 0, wx.ALIGN_CENTER | wx.ALL, 3)
        sizer.Add((0, 0), 1)
        self.SetSizer(sizer)

        self.spinners[-1].Disable()
        self.axisGroup.SetSelected(self.array.ndim - 1)
        self.sliceAxis = self.array.ndim - 1
        self.activeAxes = [x for x in range(0, self.array.ndim) if x != self.sliceAxis]

        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleButton)
        self.Bind(wx.EVT_SPINCTRL, self.OnSpinCtrl)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSpinCtrl)

    def _GetIndexRange(self, dim):
        if dim in self.activeAxes:
            return self.index[dim]
        else:
            return slice(None)

    def GetSlice(self):
        return self.array[tuple([self._GetIndexRange(x) for x in range(self.array.ndim)])]

    def _SetSliceAxis(self, axis):
        self.sliceAxis = axis
        self.activeAxes = [x for x in range(self.array.ndim) if x != self.sliceAxis]

        wx.PostEvent(self, SliceChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def OnToggleButton(self, event):
        prevAxis = self.axisGroup.GetSelected()
        if self.axisGroup.ProcessToggleEvent(event.GetEventObject()):
            currentAxis = self.axisGroup.GetSelected()
            self.spinners[prevAxis].Enable()
            self.spinners[currentAxis].Disable()
            self._SetSliceAxis(currentAxis)

    def OnSpinCtrl(self, event):
        spinner = event.GetEventObject()

        try:
            axis = self.spinMap[event.GetId()]
        except KeyError:
            raise frame.ProductBrowserError("Event received from unknown SpinCtrl (%i,%i)" %
                                            (self.GetId(), event.GetId()))

        spinner.SetValue(event.GetString())
        self.index[axis] = spinner.GetValue()

        wx.PostEvent(self, SliceChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()


class NumpySlicer2D(wx.Panel):

    def __init__(self, parent, id, array, axisLabels):
        wx.Panel.__init__(self, parent, id)

        assert array.ndim >= 3, "Expected numpy array of at least rank 3."

        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey). taken
        # from: PlotFrame.py
        self.SetBackgroundColour(self.GetBackgroundColour())

        self.array = array
        self.spinMap = {}
        self.spinners = []
        self.axisGroups = []
        self.index = [0] * self.array.ndim

        # create UI
        self.axisGroups.append(frame.ButtonGroup())
        self.axisGroups.append(frame.ButtonGroup())

        # compute button dimensions
        buttonWidth = 0
        for i in range(0, 2):
            buttonWidth = max(buttonWidth, self.GetTextExtent(axisLabels[i])[0])

        # compute spinner width
        spinnerWidth = 0
        for i in range(0, self.array.ndim):
            spinnerWidth = max(spinnerWidth, GetDecimalWidth(self, self.array.shape[i] - 1))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((0, 0), 1)
        for i in range(0, self.array.ndim):
            spinControl = wx.SpinCtrl(self, -1, style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER)
            spinControl.SetRange(0, self.array.shape[i] - 1)
            spinControl.SetValue(0)
            spinControl.SetSizeHints(spinnerWidth + 30, -1)
            self.spinMap[spinControl.GetId()] = i
            self.spinners.append(spinControl)

            buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

            # slow dimension (0)
            button = wx.ToggleButton(self, -1, axisLabels[0])
            button.SetSizeHints(buttonWidth + 10, -1)
            self.axisGroups[0].AppendButton(button)
            buttonSizer.Add(button, 1, 0, 0)

            buttonSizer.Add((3, 3), 0, 0, 0)

            # fast dimension (1)
            button = wx.ToggleButton(self, -1, axisLabels[1])
            button.SetSizeHints(buttonWidth + 10, -1)
            self.axisGroups[1].AppendButton(button)
            buttonSizer.Add(button, 1, 0, 0)

            axisSizer = wx.BoxSizer(wx.VERTICAL)
            axisSizer.Add(spinControl, 0, wx.EXPAND, 0)
            axisSizer.Add((3, 3), 0, 0, 0)
            axisSizer.Add(buttonSizer, 0, wx.EXPAND, 0)
            sizer.Add(axisSizer, 0, wx.ALIGN_CENTER | wx.ALL, 3)

        sizer.Add((0, 0), 1)
        self.SetSizer(sizer)

        # one dimension before the fastest dimension
        self.spinners[-2].Disable()
        self.axisGroups[0].SetSelected(self.array.ndim - 2)
        # fastest dimension
        self.spinners[-1].Disable()
        self.axisGroups[1].SetSelected(self.array.ndim - 1)

        self.sliceAxes = [self.array.ndim - 2, self.array.ndim - 1]
        self.activeAxes = [x for x in range(0, self.array.ndim) if x not in self.sliceAxes]

        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleButton)
        self.Bind(wx.EVT_SPINCTRL, self.OnSpinCtrl)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSpinCtrl)

    def _GetIndexRange(self, dim):
        if dim in self.activeAxes:
            return self.index[dim]
        else:
            return slice(None)

    def GetSlice(self):
        return self.array[tuple(self._GetIndexRange(x) for x in range(self.array.ndim))]

    def _SetSliceAxes(self, sliceAxis, axis):
        self.sliceAxes[sliceAxis] = axis
        self.activeAxes = [x for x in range(0, self.array.ndim) if x not in self.sliceAxes]

        wx.PostEvent(self, SliceChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def _TransposeSliceAxes(self):
        self.sliceAxes.reverse()

        wx.PostEvent(self, SliceChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def OnToggleButton(self, event):
        currentSlow = self.axisGroups[0].GetSelected()
        currentFast = self.axisGroups[1].GetSelected()

        if self.axisGroups[0].ProcessToggleEvent(event.GetEventObject()):
            newSlow = self.axisGroups[0].GetSelected()

            if newSlow == currentFast:
                self.axisGroups[0].SetSelected(newSlow)
                self.axisGroups[1].SetSelected(currentSlow)
                self._TransposeSliceAxes()
            else:
                self.spinners[currentSlow].Enable()
                self.spinners[newSlow].Disable()
                self._SetSliceAxes(0, newSlow)

        elif self.axisGroups[1].ProcessToggleEvent(event.GetEventObject()):
            newFast = self.axisGroups[1].GetSelected()

            if newFast == currentSlow:
                self.axisGroups[0].SetSelected(currentFast)
                self.axisGroups[1].SetSelected(newFast)
                self._TransposeSliceAxes()
            else:
                self.spinners[currentFast].Enable()
                self.spinners[newFast].Disable()
                self._SetSliceAxes(1, newFast)

    def OnSpinCtrl(self, event):
        spinner = event.GetEventObject()

        try:
            axis = self.spinMap[event.GetId()]
        except KeyError:
            raise frame.ProductBrowserError("Event received from unknown SpinCtrl (%i,%i)" %
                                            (self.GetId(), event.GetId()))

        spinner.SetValue(event.GetString())
        self.index[axis] = spinner.GetValue()

        wx.PostEvent(self, SliceChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()


class NumpyWrapper(wx.grid.GridTableBase):

    def __init__(self, base, array):
        wx.grid.GridTableBase.__init__(self)

        self.base = base
        self.array = array

    def GetAttr(self, row, col, kind):
        tmp = wx.grid.GridCellAttr()
        tmp.SetReadOnly(True)
        return tmp

    def GetNumberRows(self):
        return self.array.shape[0]

    def GetNumberCols(self):
        return self.array.shape[1]

    def GetColLabelValue(self, col):
        return str(col)

    def GetRowLabelValue(self, row):
        return str(row)

    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):
        return model.GetDataAsString(self.base, self.array[row, col])

    def SetValue(self, row, col, value):
        pass


class HexNumpyWrapper(wx.grid.GridTableBase):

    def __init__(self, array):
        assert (array.ndim == 1), "only arrays of rank one are supported"
        assert array.size > 0, "array should not be empty"

        wx.grid.GridTableBase.__init__(self)
        self.array = array

        self.rowCount = int(math.ceil(float(array.size) / 16.0))
        self.rowLabelSize = int(math.ceil(math.log10(array.size) / math.log10(16)))

    def GetAttr(self, row, col, kind):
        tmp = wx.grid.GridCellAttr()
        tmp.SetReadOnly(True)
        return tmp

    def GetNumberRows(self):
        return self.rowCount

    def GetNumberCols(self):
        return 16

    def GetColLabelValue(self, col):
        return "%.1X" % (col,)

    def GetRowLabelValue(self, row):
        value = "%X" % (row * 16,)
        padding = "0" * (self.rowLabelSize - len(value))
        return padding + value

    def IsEmptyCell(self, row, col):
        return ((row * 16 + col) >= self.array.size)

    def GetValue(self, row, col):
        # why do we have to check for empty cells here?
        # on would expect the wx.Grid class to first check if a
        # cell is empty, and only call GetValue() if it is not.
        if self.IsEmptyCell(row, col):
            return ""
        else:
            return "%.2X" % (self.array[row * 16 + col],)

    def SetValue(self, row, col, value):
        pass


class ArrayRenderer(wx.Panel):

    # class method that can examine a node to make sure
    # it can be rendered by this renderer.
    def CanRender(cls, node):
        return (not isinstance(node, model.ObjectArrayNode)) and (len(node) > 0)
    CanRender = classmethod(CanRender)

    name = "2D Grid"

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey). taken
        # from: PlotFrame.py
        self.SetBackgroundColour(self.GetBackgroundColour())

    def Initialize(self, node):
        assert node.type == model.TYPE_ARRAY, "ArrayRenderer can only render node of type TYPE_ARRAY"
        assert not isinstance(node, model.ObjectArrayNode), "ArrayRenderer cannot render arrays of compound types"

        # coda.fetch() will promote a rank-0 array to a 1x1 array,
        # so a rank of 1 is the smallest possible rank.
        try:
            self.array = coda.fetch(node.cursor)
        except (coda.CodaError, coda.CodacError) as ex:
            raise RenderError("[CODA] %s" % (str(ex),))

        # array sanity check
        ok = True
        if node.isRankZero():
            ok = (self.array.ndim == 1) and (self.array.shape[0] == 1)
        else:
            ok = (self.array.ndim == len(node.dimensions)) and (self.array.size == len(node))
            i = 0
            while ok and i < len(node.dimensions):
                ok = ok and (self.array.shape[i] == node.dimensions[i])
                i += 1

        if not ok:
            raise RenderError("[ArrayRenderer] Array read from product does not match description.")

        self.base = node.base
        self.slice = None

        # coda.fetch() will promote a rank-0 array to a 1x1 array,
        # so a rank of 1 is the smallest possible rank.
        if self.array.ndim == 1:
            self.array = self.array[:, numpy.newaxis]

        self.valueText = wx.TextCtrl(self, -1, "")
        valueSizer = wx.BoxSizer(wx.HORIZONTAL)
        valueSizer.Add(wx.StaticText(self, -1, "Value:"), 0, wx.ALIGN_CENTER, 0)
        valueSizer.Add((5, 5), 0, wx.EXPAND)
        valueSizer.Add(self.valueText, 1, 0, 0)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.grid.Grid(self, -1, style=wx.BORDER_SUNKEN)

        # TODO: use wxGrid::SetDefaultColSize() and row equiv. as an approx.
        # of AutoSize().
        if self.array.ndim > 2:
            self.slicer = NumpySlicer2D(self, -1, self.array, ("row", "col"))
            self.Bind(EVT_SLICE_CHANGED, self.OnSliceChanged)

        self.UpdateGridData()
        # _really_ slow, so only used for string data (which can require a large cell width).
        if self.base == model.TYPE_STRING:
            self.grid.AutoSize()

        self.sizer.Add(valueSizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        self.sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        if self.array.ndim > 2:
            self.sizer.Add(self.slicer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        self.SetSizer(self.sizer)

        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)

    def UpdateGridData(self):
        if self.array.ndim <= 2:
            self.slice = self.array
        else:
            self.slice = self.slicer.GetSlice()

        self.grid.SetTable(NumpyWrapper(self.base, self.slice), True)
        self.valueText.SetValue(model.GetDataAsString(self.base, self.slice.flat[0], 256))

    def OnSliceChanged(self, event):
        self.sizer.Detach(self.grid)
        self.grid.Destroy()

        self.grid = wx.grid.Grid(self, -1)
        self.UpdateGridData()
        # _really_ slow...
        if self.base == model.TYPE_STRING:
            self.grid.AutoSize()

        self.sizer.Insert(2, self.grid, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Layout()

    def OnSelectCell(self, event):
        if event.Selecting():
            self.valueText.SetValue(model.GetDataAsString(self.base, self.slice[event.GetRow(), event.GetCol()], 256))
        else:
            self.valueText.SetValue("")
        event.Skip()


class PlotRenderer(wx.Panel):

    # class method that can examine a node to make sure
    # it can be rendered by this renderer.
    plotableTypes = (model.TYPE_INT8, model.TYPE_UINT8, model.TYPE_INT16, model.TYPE_UINT16, model.TYPE_INT32,
                     model.TYPE_UINT32, model.TYPE_INT64, model.TYPE_UINT64, model.TYPE_VSF_INTEGER,
                     model.TYPE_FLOAT32, model.TYPE_FLOAT64)

    def CanRender(cls, node):
        return (usePlotRenderer and (not isinstance(node, model.ObjectArrayNode)) and
                (node.base in PlotRenderer.plotableTypes) and (len(node) > 0))
    CanRender = classmethod(CanRender)

    name = "2D Plot"

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundColour(self.GetBackgroundColour())  # Set the background 'explicitly' to have it stick

    def Initialize(self, node):
        assert node.type == model.TYPE_ARRAY, "PlotRenderer can only render node of type TYPE_ARRAY"
        assert not isinstance(node, model.ObjectArrayNode), "PlotRenderer cannot render arrays of compound types"

        # coda.fetch() will promote a rank-0 array to a 1x1 array,
        # so a rank of 1 is the smallest possible rank.
        try:
            self.array = coda.fetch(node.cursor)
        except (coda.CodaError, coda.CodacError) as ex:
            raise RenderError("[CODA] %s" % (str(ex),))

        # array sanity check
        ok = True
        if node.isRankZero():
            ok = (self.array.ndim == 1) and (self.array.shape[0] == 1)
        else:
            ok = (self.array.ndim == len(node.dimensions)) and (self.array.size == len(node))
            i = 0
            while ok and i < len(node.dimensions):
                ok = ok and (self.array.shape[i] == node.dimensions[i])
                i += 1

        if not ok:
            raise RenderError("[PlotRenderer] Array read from product does not match description.")

        self.plot = PlotWindow(self, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plot, 1, wx.EXPAND | wx.ALL, 5)
        if self.array.ndim > 1:
            self.slicer = NumpySlicer1D(self, -1, self.array, "select")
            sizer.Add(self.slicer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
            self.Bind(EVT_SLICE_CHANGED, self.OnSliceChanged)

        self.SetSizer(sizer)

        if self.array.ndim == 1:
            self.plot.AddDataSet(numpy.arange(self.array.shape[0]), self.array)
        else:
            slice = self.slicer.GetSlice()
            self.plot.AddDataSet(numpy.arange(slice.shape[0]), slice)

    def UpdatePlotData(self):
        if self.array.ndim > 1:
            slice = self.slicer.GetSlice()
            self.plot.UpdateDataSet(0, numpy.arange(slice.shape[0]), slice)
            # update x-axis and y-axis ranges
            self.plot.SetAxisRange(0, 0, slice.shape[0] - 1)
            self.plot.SetAxisRange(1, numpy.nanmin(slice), numpy.nanmax(slice))

    def OnSliceChanged(self, event):
        self.UpdatePlotData()


class RecordRenderer(wx.ListCtrl):

    # class method that can examine a node to make sure
    # it can be rendered by this renderer.
    def CanRender(cls, node):
        return not node.dirty() and len(node) > 0
    CanRender = classmethod(CanRender)

    name = "List"

    def __init__(self, parent):
        style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_VRULES | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, -1, style=style)

        self.SetImageList(model.iconImageList, wx.IMAGE_LIST_SMALL)
        self.InsertColumn(0, "ID", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "Name")
        self.InsertColumn(2, "Value")

    def Initialize(self, node):
        for i in range(0, len(node)):
            field = node[i]

            if not (coda.get_option_filter_record_fields() and (field.hidden or not field.available)):
                idx = self.InsertItem(i, str(i))
                self.SetItem(idx, 1, field.real_name, model.GetNodeIcon(field, model.iconDictionary))

                if field.available:
                    if field.type == model.TYPE_RECORD:
                        self.SetItem(idx, 2, "<record of %u field(s)>" % (len(field),))

                    elif field.type == model.TYPE_ARRAY:
                        if field.isRankZero():
                            self.SetItem(idx, 2, "<rank-0 array of %s>" % (model.GetTypeAsString(field.base),))

                        else:
                            dimensionString = ""
                            for dim in field.dimensions[:-1]:
                                dimensionString += "%u x " % (dim,)
                            dimensionString += "%u" % (field.dimensions[-1],)

                            self.SetItem(idx, 2, "[%s %s]" % (dimensionString, model.GetTypeAsString(field.base)))

                    else:
                        # a maximum size of _maxLineLength characters is specified, because
                        # GDK may crash if the length of a string item gets too long.
                        # also, if the line is really long the user will probably not want
                        # to view as a single line in a ListCtrl anyway.
                        try:
                            data = coda.fetch(field.cursor)
                        except (coda.CodaError, coda.CodacError) as ex:
                            raise RenderError("[CODA] %s" % (str(ex),))

                        self.SetItem(idx, 2, model.GetDataAsString(field.type, data, frame._maxLineLength))
                else:
                    self.SetItem(idx, 2, "<unavailable>")

        # _AutoSize() sets the width of a column to the maximum of the
        # width of the longest item in the column and the width of the column
        # header.
        # I would like to _AutoSize() only column 0 and 1, and have column 2
        # take up the rest of the available space (maybe constrained to a
        # minimum width, i.e. the width of the smallest item in the column).
        # This would be desirable, because sometimes there can be very long
        # items, which result in very small scrollbars. However, there does not
        # seem to be an easy way to achieve this. (Note that if an item is
        # longer than the column width, it is automatically clipped and
        # padded with '...' by the ListCtrl.)
        #
        # UPDATE: A specified maximum length (productbrowser.frame._maxLength) is
        # now used to avoid very long items. Therefore, we can now _AutoSize()
        # column 2 as well. However, _AutoSize()-ing only column 0 and 1, and
        # having column 2 take up the rest of the available space would still
        # be a better solution.
        self._AutoSize((0, 1, 2))

    def _AutoSize(self, columns):
        for col in columns:
            header = self.GetColumn(col)
            if header is not None:
                self.SetColumnWidth(col, wx.LIST_AUTOSIZE)
                columnWidth = self.GetColumnWidth(col)
                headerWidth, headerHeight = self.GetTextExtent(header.GetText())
                self.SetColumnWidth(col, max(columnWidth, headerWidth + 15))
                if wx.Platform == '__WXMSW__' and col == 0:
                    self.SetColumnWidth(0, self.GetColumnWidth(0) + 15)


class BytesRenderer(wx.grid.Grid):

    # class method that can examine a node to make sure
    # it can be rendered by this renderer.
    def CanRender(cls, node):
        return True
    CanRender = classmethod(CanRender)

    name = "Hex"

    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent, -1, style=wx.BORDER_SUNKEN)

    def Initialize(self, node):
        try:
            array = coda.fetch(node.cursor)
        except (coda.CodaError, coda.CodacError) as ex:
            raise RenderError("[CODA] %s" % (str(ex),))

        # array sanity check
        if not array.ndim == 1:
            raise RenderError("[BytesRenderer] Array read from product does not match description.")

        if array.size == 0:
            raise RenderError("[BytesRenderer] Array read from product is empty.")

        width, height = self.GetTextExtent("FF")
        self.SetDefaultColSize(width + 10)
        self.SetDefaultRowSize(height + 10)
        self.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.SetTable(HexNumpyWrapper(array), True)


class ScalarRenderer(wx.TextCtrl):

    # class method that can examine a node to make sure
    # it can be rendered by this renderer.
    def CanRender(cls, node):
        return True
    CanRender = classmethod(CanRender)

    name = "String"

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1, "", style=wx.TE_READONLY | wx.TE_MULTILINE)

    def Initialize(self, node):
        try:
            valueString = model.GetDataAsString(node.type, coda.fetch(node.cursor))
        except (coda.CodaError, coda.CodacError) as ex:
            raise RenderError("[CODA] %s" % (str(ex),))

        self.SetValue(valueString)


class UnavailableRenderer(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        # this corrects the colour of the panel in win32 (without this
        # line it defaults to dark grey, instead of light grey). taken
        # from: PlotFrame.py
        self.SetBackgroundColour(self.GetBackgroundColour())

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0, 0), 1)
        sizer.Add(wx.StaticText(self, -1, "Data unavailable or no renderer associated with this type."), 0,
                  wx.ALIGN_CENTER, 0)
        sizer.Add((0, 0), 1)
        self.SetSizer(sizer)

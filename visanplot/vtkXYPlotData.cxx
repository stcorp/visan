//
// Copyright (C) 2002-2021 S[&]T, The Netherlands.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
//
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from
//    this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//

#include "vtkXYPlotData.h"

#include "vtkCollection.h"
#include "vtkDoubleArray.h"

vtkStandardNewMacro(vtkXYPlotData);

vtkXYPlotData::vtkXYPlotData()
{
    this->xrange[0] = 1;
    this->xrange[1] = 0;
    this->yrange[0] = 1;
    this->yrange[1] = 0;
    this->xrangeAbove0[0] = 1;
    this->xrangeAbove0[1] = 0;
    this->yrangeAbove0[0] = 1;
    this->yrangeAbove0[1] = 0;
    this->pointSet = vtkSmartPointer<vtkCollection>::New();
    this->currentPoints = nullptr;
}

void vtkXYPlotData::AddData(vtkDoubleArray *xdata, vtkDoubleArray *ydata)
{
    auto points = vtkSmartPointer<vtkPoints>::New();
    int numPoints;
    int i;

    if (xdata == nullptr && ydata == nullptr)
    {
        vtkErrorMacro("x and y data cannot be both null");
        return;
    }
    numPoints = xdata != nullptr ? xdata->GetNumberOfTuples() : ydata->GetNumberOfTuples();

    if (this->pointSet->GetNumberOfItems() == 0)
    {
        this->xrange[0] = VTK_DOUBLE_MAX;
        this->xrange[1] = VTK_DOUBLE_MIN;
        this->yrange[0] = VTK_DOUBLE_MAX;
        this->yrange[1] = VTK_DOUBLE_MIN;
        this->xrangeAbove0[0] = VTK_DOUBLE_MAX;
        this->xrangeAbove0[1] = 0;
        this->yrangeAbove0[0] = VTK_DOUBLE_MAX;
        this->yrangeAbove0[1] = 0;
    }

    points->SetNumberOfPoints(numPoints);
    for (i = 0; i < numPoints; i++)
    {
        double x = xdata == nullptr ? i : xdata->GetValue(i);
        double y = ydata == nullptr ? i : ydata->GetValue(i);

        points->SetPoint(i, x, y, 0);

        if (vtkMath::IsFinite(x))
        {
            if (x < this->xrange[0])
            {
                this->xrange[0] = x;
            }
            if (x > this->xrange[1])
            {
                this->xrange[1] = x;
            }
            if (x > 0)
            {
                if (x < this->xrangeAbove0[0])
                {
                    this->xrangeAbove0[0] = x;
                }
                if (x > this->xrangeAbove0[1])
                {
                    this->xrangeAbove0[1] = x;
                }
            }
        }
        if (vtkMath::IsFinite(y))
        {
            if (y < this->yrange[0])
            {
                this->yrange[0] = y;
            }
            if (y > this->yrange[1])
            {
                this->yrange[1] = y;
            }
            if (y > 0)
            {
                if (y < this->yrangeAbove0[0])
                {
                    this->yrangeAbove0[0] = y;
                }
                if (y > this->yrangeAbove0[1])
                {
                    this->yrangeAbove0[1] = y;
                }
            }
        }
    }

    this->pointSet->AddItem(points.GetPointer());

    if (this->pointSet->GetNumberOfItems() == 1)
    {
        this->SetKeyframe(0);
    }

    this->Modified();
}

void vtkXYPlotData::SetData(vtkDoubleArray *xdata, vtkDoubleArray *ydata)
{
    this->pointSet = vtkSmartPointer<vtkCollection>::New();
    this->AddData(xdata, ydata);
}

void vtkXYPlotData::SetKeyframe(int keyframe)
{
    if (this->pointSet->GetNumberOfItems() == 0)
    {
        return;
    }

    if (keyframe >= this->pointSet->GetNumberOfItems())
    {
        keyframe = this->pointSet->GetNumberOfItems() - 1;
    }
    if (keyframe < 0)
    {
        keyframe = 0;
    }

    this->currentPoints = vtkPoints::SafeDownCast(this->pointSet->GetItemAsObject(keyframe));
    this->Modified();
}

int vtkXYPlotData::GetNumberOfKeyframes()
{
    return this->pointSet->GetNumberOfItems();
}

void vtkXYPlotData::GetDataRange(double range[2], int dim)
{
    switch (dim)
    {
        case 0:
            range[0] = this->xrange[0];
            range[1] = this->xrange[1];
            break;
        case 1:
            range[0] = this->yrange[0];
            range[1] = this->yrange[1];
            break;
        default:
            range[0] = 0.0;
            range[1] = 0.0;
            break;
    }
    vtkDebugMacro(<< "GetDataRange (dim=" << dim << "): range = (" << range[0] << "," << range[1] << ")");
}

void vtkXYPlotData::GetDataRangeAbove0(double range[2], int dim)
{
    switch (dim)
    {
        case 0:
            range[0] = this->xrangeAbove0[0];
            range[1] = this->xrangeAbove0[1];
            break;
        case 1:
            range[0] = this->yrangeAbove0[0];
            range[1] = this->yrangeAbove0[1];
            break;
        default:
            range[0] = 0.0;
            range[1] = 0.0;
            break;
    }
}

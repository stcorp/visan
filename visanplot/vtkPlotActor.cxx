//
// Copyright (C) 2002-2022 S[&]T, The Netherlands.
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

#include "vtkPlotActor.h"

#include "vtkActor2DCollection.h"
#include "vtkAppendPolyData.h"
#include "vtkNewAxisActor2D.h"
#include "vtkDataObjectCollection.h"
#include "vtkGlyph2D.h"
#include "vtkGlyphSource2D.h"
#include "vtkIntArray.h"
#include "vtkLegendBoxActor.h"
#include "vtkMath.h"
#include "vtkObjectFactory.h"
#include "vtkPlane.h"
#include "vtkPlanes.h"
#include "vtkPlotData.h"
#include "vtkPlotDataCollection.h"
#include "vtkPolyData.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkProperty2D.h"
#include "vtkTextMapper.h"
#include "vtkTextProperty.h"
#include "vtkViewport.h"

vtkStandardNewMacro(vtkPlotActor);

vtkCxxSetObjectMacro(vtkPlotActor,TitleTextProperty,vtkTextProperty);
vtkCxxSetObjectMacro(vtkPlotActor,AxisLabelTextProperty,vtkTextProperty);
vtkCxxSetObjectMacro(vtkPlotActor,AxisTitleTextProperty,vtkTextProperty);

vtkPlotActor::vtkPlotActor()
{
    this->PositionCoordinate->SetCoordinateSystemToNormalizedViewport();
    this->PositionCoordinate->SetValue(0.015, 0.025);
    this->Position2Coordinate->SetCoordinateSystemToNormalizedViewport();
    this->Position2Coordinate->SetReferenceCoordinate(this->PositionCoordinate);
    this->Position2Coordinate->SetValue(0.97, 0.95);

    this->Title = nullptr;
    this->XTitle = nullptr;
    this->YTitle = nullptr;

    this->NumberOfXLabels = 6;
    this->NumberOfYLabels = 6;

    this->ComputedNumberOfXLabels = -1;
    this->ComputedNumberOfYLabels = -1;

    this->TitleTextProperty = vtkSmartPointer<vtkTextProperty>::New();
    this->TitleTextProperty->SetBold(1);
    this->TitleTextProperty->SetItalic(1);
    this->TitleTextProperty->SetShadow(0);
    this->TitleTextProperty->SetFontFamilyToArial();
    this->TitleTextProperty->SetColor(0, 0, 0);

    this->AxisLabelTextProperty = vtkSmartPointer<vtkTextProperty>::New();
    this->AxisLabelTextProperty->ShallowCopy(this->TitleTextProperty);

    this->AxisTitleTextProperty = vtkSmartPointer<vtkTextProperty>::New();
    this->AxisTitleTextProperty->ShallowCopy(this->AxisLabelTextProperty);

    this->LabelXFormat = new char[10];
    snprintf(this->LabelXFormat, 10, "%s", "%-#.4g");
    this->LabelYFormat = new char[10];
    snprintf(this->LabelYFormat, 10, "%s", "%-#.4g");

    this->LogX = 0;
    this->LogY = 0;
    this->BaseX = 10;
    this->BaseY = 10;
    this->MinLogValue = 1 / VTK_DOUBLE_MAX;

    // The Plot ranges are initialy invalid and will be set to valid values at the first Render
    this->XRange[0] = 1.0;
    this->XRange[1] = 0.0;
    this->YRange[0] = 1.0;
    this->YRange[1] = 0.0;

    this->DataXRange[0] = 0.0;
    this->DataXRange[1] = 0.0;
    this->DataYRange[0] = 0.0;
    this->DataYRange[1] = 0.0;

    this->DataXRangeAbove0[0] = 1.0;
    this->DataXRangeAbove0[1] = 0.0;
    this->DataYRangeAbove0[0] = 1.0;
    this->DataYRangeAbove0[1] = 0.0;

    this->TitleMapper = vtkSmartPointer<vtkTextMapper>::New();
    this->TitleMapper->GetTextProperty()->ShallowCopy(this->TitleTextProperty);
    this->TitleActor = vtkSmartPointer<vtkActor2D>::New();
    this->TitleActor->SetMapper(this->TitleMapper);
    this->TitleActor->GetPositionCoordinate()->SetCoordinateSystemToViewport();

    this->XAxis = vtkSmartPointer<vtkNewAxisActor2D>::New();
    this->XAxis->GetLabelTextProperty()->ShallowCopy(this->AxisLabelTextProperty);
    this->XAxis->GetTitleTextProperty()->ShallowCopy(this->AxisTitleTextProperty);
    this->XAxis->GetPositionCoordinate()->SetCoordinateSystemToViewport();
    this->XAxis->GetPosition2Coordinate()->SetCoordinateSystemToViewport();
    this->XAxis->SetProperty(this->GetProperty());
    this->XAxis->AdjustRangeOff();
    this->XAxis->AdjustTicksOn();

    this->YAxis = vtkSmartPointer<vtkNewAxisActor2D>::New();
    this->YAxis->GetLabelTextProperty()->ShallowCopy(this->AxisLabelTextProperty);
    this->YAxis->GetTitleTextProperty()->ShallowCopy(this->AxisTitleTextProperty);
    this->YAxis->GetPositionCoordinate()->SetCoordinateSystemToViewport();
    this->YAxis->GetPosition2Coordinate()->SetCoordinateSystemToViewport();
    this->YAxis->SetProperty(this->GetProperty());
    this->YAxis->AdjustRangeOff();
    this->YAxis->AdjustTicksOn();

    this->PlotData = vtkSmartPointer<vtkPlotDataCollection>::New();
    this->PlotActors = vtkSmartPointer<vtkActor2DCollection>::New();

    this->Legend = 0;
    this->LegendActor = vtkSmartPointer<vtkLegendBoxActor>::New();
    this->LegendActor->GetPositionCoordinate()->SetCoordinateSystemToNormalizedViewport();
    this->LegendActor->GetPositionCoordinate()->SetReferenceCoordinate(this->PositionCoordinate);
    this->LegendActor->GetPositionCoordinate()->SetValue(0.75, 0.65);
    this->LegendActor->GetPosition2Coordinate()->SetCoordinateSystemToNormalizedViewport();
    this->LegendActor->GetPosition2Coordinate()->SetReferenceCoordinate(this->LegendActor->GetPositionCoordinate());
    this->LegendActor->GetPosition2Coordinate()->SetValue(0.15, 0.20);
    this->LegendActor->BorderOff();

    // TODO: Allocate number of entries for Legend Actor

    auto glyphSource = vtkSmartPointer<vtkGlyphSource2D>::New();
    glyphSource->SetGlyphTypeToNone();
    this->DefaultLegendSymbol = glyphSource->GetOutput();

    // The Inner PlotBounds are initialy invalid and will be set to valid values at the first Render
    this->InnerPlotBounds[0] = 1.0;
    this->InnerPlotBounds[1] = 0.0;
    this->InnerPlotBounds[2] = 1.0;
    this->InnerPlotBounds[3] = 0.0;

    this->OuterPlotBounds[0] = 1.0;
    this->OuterPlotBounds[1] = 0.0;
    this->OuterPlotBounds[2] = 1.0;
    this->OuterPlotBounds[3] = 0.0;

    this->CachedViewportSize[0] = 0;
    this->CachedViewportSize[1] = 0;
}

vtkPlotActor::~vtkPlotActor()
{
    if (this->Title)
    {
        delete [] this->Title;
    }

    if (this->XTitle)
    {
        delete [] this->XTitle;
    }

    if (this->YTitle)
    {
        delete [] this->YTitle;
    }

    if (this->LabelXFormat)
    {
        delete [] this->LabelXFormat;
    }

    if (this->LabelYFormat)
    {
        delete [] this->LabelYFormat;
    }
}

void vtkPlotActor::AddData(vtkPlotData *plotData, vtkProperty2D *property)
{
    if (plotData == nullptr)
    {
        vtkErrorMacro(<< "Trying to add an empty object");
        return;
    }

    // Check if plotdata is not already in the list
    if (this->PlotData->IsItemPresent(plotData) == 0)
    {
        this->PlotData->AddItem(plotData);
        auto plotMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
        plotMapper->SetInputConnection(plotData->GetOutputPort());
        auto plotActor = vtkSmartPointer<vtkActor2D>::New();
        plotActor->SetMapper(plotMapper);
        plotActor->PickableOn();
        if (property)
        {
            plotActor->SetProperty(property);
        }
        this->PlotActors->AddItem(plotActor.GetPointer());
        plotData->SetLogX(this->LogX);
        plotData->SetLogY(this->LogY);
        this->CalculateDataRanges();
        this->SetXRange(this->DataXRange);
        this->SetYRange(this->DataYRange);
    }
}

void vtkPlotActor::RemoveData(vtkPlotData *plotData)
{
    int location = this->PlotData->IsItemPresent(plotData);
    if (location != 0)
    {
        this->PlotData->RemoveItem(location);
        this->PlotActors->RemoveItem(location);
        this->Modified();
    }
}

vtkPlotData *vtkPlotActor::GetPlotDataFromActor(vtkActor2D *plotActor)
{
    vtkPlotData *plotData = nullptr;
    int location = this->PlotActors->IsItemPresent(plotActor);
    if (location != 0)
    {
        plotData = this->PlotData->GetItem(location);
    }
    return plotData;
}

void vtkPlotActor::SetXRange(double xmin, double xmax)
{
    vtkDebugMacro(<< "Setting XRange to (" << xmin << ", " << xmax << ")");
    this->XRange[0] = xmin;
    this->XRange[1] = xmax;
    this->Modified();
    this->InvokeEvent("XRangeChanged");
}

void vtkPlotActor::SetYRange(double ymin, double ymax)
{
    vtkDebugMacro(<< "Setting YRange to (" << ymin << ", " << ymax << ")");
    this->YRange[0] = ymin;
    this->YRange[1] = ymax;
    this->Modified();
    this->InvokeEvent("YRangeChanged");
}

void vtkPlotActor::SetLogX(int logX)
{
    vtkDebugMacro(<< this->GetClassName() << " (" << this << "): " << "setting LogX to " << logX);
    if (this->LogX != logX)
    {
        vtkPlotData *plotData;
        this->LogX = logX;
        // Update logarithmic axes setting in plot data
        this->PlotData->InitTraversal();
        while ((plotData = this->PlotData->GetNextItem()) != nullptr)
        {
            plotData->SetLogX(this->LogX);
        }
        // reset number of computed labels
        this->ComputedNumberOfXLabels = -1;

        this->Modified();
    }
}

void vtkPlotActor::SetLogY(int logY)
{
    vtkDebugMacro(<< this->GetClassName() << " (" << this << "): " << "setting LogY to " << logY);
    if (this->LogY != logY)
    {
        vtkPlotData *plotData;
        this->LogY = logY;
        // Update logarithmic axes setting in plot data
        this->PlotData->InitTraversal();
        while ((plotData = this->PlotData->GetNextItem()) != nullptr)
        {
            plotData->SetLogY(this->LogY);
        }
        // reset number of computed labels
        this->ComputedNumberOfXLabels = -1;

        this->Modified();
    }
}

void vtkPlotActor::SetMinLogValue(double value)
{
    if (value > 0 && value < VTK_DOUBLE_MAX)
    {
        this->MinLogValue = value;
    }
}

int vtkPlotActor::RenderOverlay(vtkViewport *viewport)
{
    int renderedSomething = 0;

    vtkActor2D *plotActor;
    this->PlotActors->InitTraversal();
    while ((plotActor = this->PlotActors->GetNextItem()) != nullptr)
    {
        renderedSomething += plotActor->RenderOverlay(viewport);
    }

    renderedSomething += this->XAxis->RenderOverlay(viewport);
    renderedSomething += this->YAxis->RenderOverlay(viewport);

    if ( this->Title )
    {
        renderedSomething += this->TitleActor->RenderOverlay(viewport);
    }

    if ( this->Legend )
    {
        renderedSomething += this->LegendActor->RenderOverlay(viewport);
    }

    return renderedSomething;
}


int vtkPlotActor::RenderOpaqueGeometry(vtkViewport *viewport)
{
    unsigned long plotDataMTime = 0;
    vtkPlotData *plotData;
    vtkActor2D *plotActor;
    int renderedSomething = 0;

    if (this->PlotData->GetNumberOfItems() > 0)
    {
        vtkDebugMacro(<< "Plotting input data");
    }

    // Update plotdata and calculate modification time
    this->PlotData->InitTraversal();
    while ((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->Update();
        unsigned long mTime = plotData->GetMTime();
        if (mTime > plotDataMTime)
        {
            plotDataMTime = mTime;
        }
    }

    if (this->Title && !this->TitleTextProperty)
    {
        vtkErrorMacro(<< "Need a title text property to render plot title");
        return 0;
    }

    // Check modification time to see whether we have to rebuild.
    // Pay attention that GetMTime() has been redefined (see below)
    int *viewportSize = viewport->GetSize();
    if (plotDataMTime > this->BuildTime || this->GetMTime() > this->BuildTime ||
        viewportSize[0] != this->CachedViewportSize[0] || viewportSize[1] != this->CachedViewportSize[1] ||
        (this->TitleTextProperty->GetMTime() > this->BuildTime) ||
        (this->AxisLabelTextProperty->GetMTime() > this->BuildTime) ||
        (this->AxisTitleTextProperty->GetMTime() > this->BuildTime))
    {
        double range[2];
        int stringSize[2];

        vtkDebugMacro(<< "Rebuilding plot");
        this->CachedViewportSize[0] = viewportSize[0];
        this->CachedViewportSize[1] = viewportSize[1];

        // manage legend
        vtkDebugMacro(<< "Rebuilding legend");
        if (this->Legend)
        {
            this->LegendActor->SetNumberOfEntries(this->PlotData->GetNumberOfItems());
            this->PlotData->InitTraversal();
            this->PlotActors->InitTraversal();
            for (int i = 0; i < this->PlotData->GetNumberOfItems(); i++)
            {
                plotData = this->PlotData->GetNextItem();
                plotActor = this->PlotActors->GetNextItem();
                if (plotData->GetPlotPoints())
                {
                    this->LegendActor->SetEntrySymbol(i, plotData->GetPlotSymbol());
                }
                else
                {
                    this->LegendActor->SetEntrySymbol(i, DefaultLegendSymbol);
                }
                this->LegendActor->SetEntryString(i, plotData->GetPlotLabel());
                this->LegendActor->SetEntryColor(i, plotActor->GetProperty()->GetColor());
            }
            this->LegendActor->SetPadding(2);
            this->LegendActor->GetProperty()->DeepCopy(this->GetProperty());
            this->LegendActor->ScalarVisibilityOff();
        }

        // Rebuid text props
        // Perform shallow copy here since each individual axis can be
        // accessed through the class API (i.e. each individual axis text prop
        // can be changed). Therefore, we can not just assign pointers otherwise
        // each individual axis text prop would point to the same text prop.

        if (this->AxisLabelTextProperty->GetMTime() > this->BuildTime)
        {
            if (this->XAxis->GetLabelTextProperty())
            {
                this->XAxis->GetLabelTextProperty()->ShallowCopy(this->AxisLabelTextProperty);
            }
            if (this->YAxis->GetLabelTextProperty())
            {
                this->YAxis->GetLabelTextProperty()->ShallowCopy(this->AxisLabelTextProperty);
            }
        }

        if ( this->AxisTitleTextProperty->GetMTime() > this->BuildTime)
        {
            if (this->XAxis->GetTitleTextProperty())
            {
                this->XAxis->GetTitleTextProperty()->ShallowCopy(this->AxisTitleTextProperty);
            }
            if (this->YAxis->GetTitleTextProperty())
            {
                this->YAxis->GetTitleTextProperty()->ShallowCopy(this->AxisTitleTextProperty);
            }
        }

        // Recalculate ranges
        this->CalculateDataRanges();

        // setup x-axis
        vtkDebugMacro(<< "Rebuilding x-axis");

        this->XAxis->SetTitle(this->XTitle);
        this->XAxis->SetLabelFormat(this->LabelXFormat);
        this->XAxis->SetBase(this->BaseX);
        this->XAxis->AdjustRangeOff();
        this->XAxis->SetProperty(this->GetProperty());

        range[0] = this->XRange[0];
        range[1] = this->XRange[1];
        if (range[0] > range[1])
        {
            // Use data range of data sets
            range[0] = this->DataXRange[0];
            range[1] = this->DataXRange[1];
        }

        if (this->LogX && range[0] <= 0)
        {
            // Use the data range above 0 if available
            if (this->DataXRangeAbove0[0] > this->DataXRangeAbove0[1])
            {
                range[0] = 1;
                range[1] = 1;
            }
            else
            {
                range[0] = this->DataXRangeAbove0[0];
                if (range[1] < range[0])
                {
                    range[1] = this->DataXRangeAbove0[1];
                }
            }
        }
        if (range[0] != this->XRange[0] || range[1] != this->XRange[1])
        {
            this->SetXRange(range);
        }

        if (this->ComputedNumberOfXLabels == -1)
        {
            this->XAxis->SetNumberOfLabels(this->NumberOfXLabels);
        }
        else
        {
            this->XAxis->SetNumberOfLabels(this->ComputedNumberOfXLabels);
        }
        this->XAxis->SetRange(this->XRange[0], this->XRange[1]);
        this->XAxis->SetLog(this->LogX);

        // setup y-axis
        vtkDebugMacro(<< "Rebuilding y-axis");

        this->YAxis->SetTitle(this->YTitle);
        this->YAxis->SetLabelFormat(this->LabelYFormat);
        this->YAxis->SetBase(this->BaseY);
        this->YAxis->SetProperty(this->GetProperty());

        range[0] = this->YRange[0];
        range[1] = this->YRange[1];
        if (range[0] > range[1])
        {
            // Use data range of data sets
            range[0] = this->DataYRange[0];
            range[1] = this->DataYRange[1];
        }

        if (this->LogY && range[0] <= 0)
        {
            // Use the data range above 0 if available
            if (this->DataYRangeAbove0[0] > this->DataYRangeAbove0[1])
            {
                range[0] = 1;
                range[1] = 1;
            }
            else
            {
                range[0] = this->DataYRangeAbove0[0];
                if (range[1] < range[0])
                {
                    range[1] = this->DataYRangeAbove0[1];
                }
            }
        }
        if (range[0] != this->YRange[0] || range[1] != this->YRange[1])
        {
            this->SetYRange(range);
        }

        if (this->ComputedNumberOfYLabels == -1)
        {
            this->YAxis->SetNumberOfLabels(this->NumberOfYLabels);
        }
        else
        {
            this->YAxis->SetNumberOfLabels(this->ComputedNumberOfYLabels);
        }
        this->YAxis->SetRange(this->YRange[1], this->YRange[0]);
        this->YAxis->SetLog(this->LogY);

        // Also sets the inner plot bounds
        this->PlaceAxes(viewport);

        // Manage title
        if (this->TitleTextProperty->GetMTime() > this->BuildTime)
        {
            this->TitleMapper->GetTextProperty()->ShallowCopy(this->TitleTextProperty);
        }
        if (this->Title)
        {
            this->TitleMapper->SetInput(this->Title);
            vtkNewAxisActor2D::SetFontSize(viewport, this->TitleMapper, viewportSize, 1, stringSize);
            this->TitleActor->GetPositionCoordinate()->SetValue(this->InnerPlotBounds[0] + 0.5 *
                                                                (this->InnerPlotBounds[1] - this->InnerPlotBounds[0]) -
                                                                0.5 * stringSize[0],
                                                                this->InnerPlotBounds[3] + 0.5 * stringSize[1]);
            this->TitleActor->SetProperty(this->GetProperty());
        }

        // Update bounds in plot data
        this->PlotData->InitTraversal();
        while ((plotData = this->PlotData->GetNextItem()) != nullptr)
        {
            plotData->SetViewportBounds(this->InnerPlotBounds[0], this->InnerPlotBounds[1], this->InnerPlotBounds[2],
                                        this->InnerPlotBounds[3], 0, 0);
            plotData->SetClipXRange(this->XRange);
            plotData->SetClipYRange(this->YRange);
        }

        this->BuildTime.Modified();
    }

    vtkDebugMacro(<< "Rendering Plot Actors");
    this->PlotActors->InitTraversal();
    while ((plotActor = this->PlotActors->GetNextItem()) != nullptr)
    {
        renderedSomething += plotActor->RenderOpaqueGeometry(viewport);
    }

    vtkDebugMacro(<< "Rendering Axes");
    renderedSomething += this->XAxis->RenderOpaqueGeometry(viewport);
    renderedSomething += this->YAxis->RenderOpaqueGeometry(viewport);

    if (this->Title)
    {
        vtkDebugMacro(<< "Rendering Title Actor");
        renderedSomething += this->TitleActor->RenderOpaqueGeometry(viewport);
    }

    if (this->Legend)
    {
        vtkDebugMacro(<< "Rendering Legend Actor");
        renderedSomething += this->LegendActor->RenderOpaqueGeometry(viewport);
    }

    return renderedSomething;
}

int vtkPlotActor::HasTranslucentPolygonalGeometry()
{
    return 0;
}

void vtkPlotActor::ReleaseGraphicsResources(vtkWindow *win)
{
    vtkActor2D *plotActor;
    this->PlotActors->InitTraversal();
    while ((plotActor = this->PlotActors->GetNextItem()) != nullptr)
    {
        plotActor->ReleaseGraphicsResources(win);
    }
    this->XAxis->ReleaseGraphicsResources(win);
    this->YAxis->ReleaseGraphicsResources(win);
    this->TitleActor->ReleaseGraphicsResources(win);
    this->LegendActor->ReleaseGraphicsResources(win);
}

vtkMTimeType vtkPlotActor::GetMTime()
{
    unsigned long mtime, mtime2;
    mtime = this->vtkActor2D::GetMTime();

    if (this->Legend)
    {
        mtime2 = this->LegendActor->GetMTime();
        if (mtime2 > mtime)
        {
            mtime = mtime2;
        }
    }

    return mtime;
}

void vtkPlotActor::PrintSelf(ostream& os, vtkIndent indent)
{
    vtkActor2D::PrintSelf(os, indent);

    os << indent << "Input PlotData Objects:" << endl;
    this->PlotData->PrintSelf(os, indent.GetNextIndent());

    if (this->TitleTextProperty)
    {
        os << indent << "Title Text Property:\n";
        this->TitleTextProperty->PrintSelf(os,indent.GetNextIndent());
    }
    else
    {
        os << indent << "Title Text Property: (none)\n";
    }

    if (this->AxisTitleTextProperty)
    {
        os << indent << "Axis Title Text Property:\n";
        this->AxisTitleTextProperty->PrintSelf(os,indent.GetNextIndent());
    }
    else
    {
        os << indent << "Axis Title Text Property: (none)\n";
    }

    if (this->AxisLabelTextProperty)
    {
        os << indent << "Axis Label Text Property:\n";
        this->AxisLabelTextProperty->PrintSelf(os,indent.GetNextIndent());
    }
    else
    {
        os << indent << "Axis Label Text Property: (none)\n";
    }

    os << indent << "InnerPlotBounds: (" << this->InnerPlotBounds[0] << ", " << this->InnerPlotBounds[1] << ", "
        << this->InnerPlotBounds[2] << ", " << this->InnerPlotBounds[3] << ")" << endl;

    os << indent << "Title: " << (this->Title ? this->Title : "(none)") << endl;

    os << indent << "X Title: " << (this->XTitle ? this->XTitle : "(none)") << endl;
    os << indent << "Y Title: " << (this->YTitle ? this->YTitle : "(none)") << endl;

    os << indent << "X Range: (" << this->XRange[0] << ", " << this->XRange[1] << ")" << endl;
    os << indent << "Y Range: (" << this->YRange[0] << ", " << this->YRange[1] << ")" << endl;

    os << indent << "Data X Range: (" << this->DataXRange[0] << ", " << this->DataXRange[1] << ")" << endl;
    os << indent << "Data Y Range: (" << this->DataYRange[0] << ", " << this->DataYRange[1] << ")" << endl;

    os << indent << "Data X Range Above 0: (" << this->DataXRangeAbove0[0]
        << ", " << this->DataXRangeAbove0[1] << ")" << endl;
    os << indent << "Data Y Range Above 0: (" << this->DataYRangeAbove0[0]
        << ", " << this->DataYRangeAbove0[1] << ")" << endl;

    os << indent << "Logarithmic X Axis: " << (this->LogX ? "On" : "Off") << endl;
    os << indent << "Logarithmic Y Axis: " << (this->LogY ? "On" : "Off") << endl;

    os << indent << "Base for X Axis: " << this->BaseX << endl;
    os << indent << "Base for Y Axis: " << this->BaseY << endl;

    os << indent << "Minimum Logarithmic Value: " << this->MinLogValue << endl;

    os << indent << "Number Of X Labels: " << this->NumberOfXLabels << endl;
    os << indent << "Number Of Y Labels: " << this->NumberOfYLabels << endl;

    os << indent << "Label X Format: " << this->LabelXFormat << endl;
    os << indent << "Label Y Format: " << this->LabelYFormat << endl;

    os << indent << "Legend: " << (this->Legend ? "On" : "Off") << endl;
    LegendActor->Print(os);
}

// Position the axes taking into account the expected padding due to labels
// and titles. We want the result to fit in the box specified. This method
// knows something about how the vtkAxisActor2D functions, so it may have
// to change if that class changes.
void vtkPlotActor::PlaceAxes(vtkViewport *viewport)
{
    int titleSize[2], titleSizeX[2], titleSizeY[2], labelSizeX[2], labelSizeY[2];
    double labelFactorX, labelFactorY;
    double fontFactorX, fontFactorY;
    double tickOffsetX, tickOffsetY;
    double tickLengthX, tickLengthY;
    int *absolutePositionCoordinate;
    int *absolutePosition2Coordinate;
    char str1[512], str2[512];

    fontFactorY = this->YAxis->GetFontFactor();
    fontFactorX = this->XAxis->GetFontFactor();

    labelFactorY = this->YAxis->GetLabelFactor();
    labelFactorX = this->XAxis->GetLabelFactor();

    // Create a dummy text mapper for getting font sizes

    auto textMapper = vtkSmartPointer<vtkTextMapper>::New();
    vtkTextProperty *tprop = textMapper->GetTextProperty();

    // Estimate the padding around the X and Y axes

    if (this->Title != nullptr)
    {
        if (this->TitleTextProperty)
        {
            tprop->ShallowCopy(this->TitleTextProperty);
        }
        textMapper->SetInput(this->Title);
        vtkNewAxisActor2D::SetFontSize(viewport, textMapper, this->CachedViewportSize, 1, titleSize);
    }
    else
    {
        titleSize[0] = 0;
        titleSize[1] = 0;
    }

    tprop->ShallowCopy(this->XAxis->GetTitleTextProperty());
    textMapper->SetInput(this->XAxis->GetTitle());
    vtkNewAxisActor2D::SetFontSize(viewport, textMapper, this->CachedViewportSize, fontFactorX, titleSizeX);

    tprop->ShallowCopy(this->YAxis->GetTitleTextProperty());
    textMapper->SetInput(this->YAxis->GetTitle());
    vtkNewAxisActor2D::SetFontSize(viewport, textMapper, this->CachedViewportSize, fontFactorY, titleSizeY);

    // At this point the thing to do would be to actually ask the Y axis
    // actor to return the largest label.
    // In the meantime, let's try with the min and max

    snprintf(str1, 512, this->YAxis->GetLabelFormat(), this->YAxis->GetTickRange()[0]);
    snprintf(str2, 512, this->YAxis->GetLabelFormat(), this->YAxis->GetTickRange()[1]);
    tprop->ShallowCopy(this->YAxis->GetLabelTextProperty());
    textMapper->SetInput(strlen(str1) > strlen(str2) ? str1 : str2);
    vtkNewAxisActor2D::SetFontSize(viewport, textMapper, this->CachedViewportSize, labelFactorY * fontFactorY,
                                   labelSizeY);

    snprintf(str1, 512, this->XAxis->GetLabelFormat(), this->XAxis->GetTickRange()[0]);
    snprintf(str2, 512, this->XAxis->GetLabelFormat(), this->XAxis->GetTickRange()[1]);
    tprop->ShallowCopy(this->XAxis->GetLabelTextProperty());
    textMapper->SetInput(strlen(str1) > strlen(str2) ? str1 : str2);
    vtkNewAxisActor2D::SetFontSize(viewport, textMapper, this->CachedViewportSize, labelFactorX * fontFactorX,
                                   labelSizeX);

    // Get tick sizes

    tickOffsetX = this->XAxis->GetTickOffset();
    tickOffsetY = this->YAxis->GetTickOffset();
    tickLengthX = this->XAxis->GetTickLength();
    tickLengthY = this->YAxis->GetTickLength();

    // Estimate the size of the axes
    // These calculations are based on the exact same calculations that
    // are used in vtkAxisActor2D. So if vtkAxisActor2D changes its
    // behavior the calculations below may need to be refined.

    absolutePositionCoordinate = this->PositionCoordinate->GetComputedViewportValue(viewport);
    absolutePosition2Coordinate = this->Position2Coordinate->GetComputedViewportValue(viewport);
    // left X value
    this->InnerPlotBounds[0] = absolutePositionCoordinate[0] +  titleSizeY[0] + tickOffsetY +
        tickLengthY + 1.2 * labelSizeY[0];
    // right X value
    this->InnerPlotBounds[1] = absolutePosition2Coordinate[0] - labelSizeX[0] / 2;
    // lower Y value
    this->InnerPlotBounds[2] = absolutePositionCoordinate[1] + titleSizeX[1] + tickOffsetX +
        tickLengthX + 1.2 * labelSizeX[1];
    // upper Y value
    this->InnerPlotBounds[3] = absolutePosition2Coordinate[1] - 1.5 * titleSize[1];

    // Save the boundaries of the plot in viewport coordinates

    this->OuterPlotBounds[0] = absolutePositionCoordinate[0];
    this->OuterPlotBounds[1] = absolutePosition2Coordinate[0];
    this->OuterPlotBounds[2] = absolutePositionCoordinate[1];
    this->OuterPlotBounds[3] = absolutePosition2Coordinate[1];

    // Now specify the location of the axes

    this->XAxis->GetPositionCoordinate()->SetValue(this->InnerPlotBounds[0], this->InnerPlotBounds[2]);
    this->XAxis->GetPosition2Coordinate()->SetValue(this->InnerPlotBounds[1], this->InnerPlotBounds[2]);
    this->YAxis->GetPositionCoordinate()->SetValue(this->InnerPlotBounds[0], this->InnerPlotBounds[3]);
    this->YAxis->GetPosition2Coordinate()->SetValue(this->InnerPlotBounds[0], this->InnerPlotBounds[2]);
}

void vtkPlotActor::CalculateDataRanges()
{
    vtkPlotData *plotData;
    double plotDataRange[2];
    double range[2];

    // Calculate Data X Range
    range[0] = VTK_DOUBLE_MAX;
    range[1] = VTK_DOUBLE_MIN;
    this->PlotData->InitTraversal();
    while ((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->GetDataXRange(plotDataRange);
        if (plotDataRange[0] <= plotDataRange[1])
        {
            if (plotDataRange[0] < range[0])
            {
                range[0] = plotDataRange[0];
            }
            if (plotDataRange[1] > range[1])
            {
                range[1] = plotDataRange[1];
            }
        }
    }
    if (range[0] <= range[1])
    {
        this->DataXRange[0] = range[0];
        this->DataXRange[1] = range[1];
    }
    else
    {
        this->DataXRange[0] = 0;
        this->DataXRange[1] = 0;
    }

    // Calculate Data Y Range
    range[0] = VTK_DOUBLE_MAX;
    range[1] = VTK_DOUBLE_MIN;
    this->PlotData->InitTraversal();
    while ((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->GetDataYRange(plotDataRange);
        if (plotDataRange[0] <= plotDataRange[1])
        {
            if (plotDataRange[0] < range[0])
            {
                range[0] = plotDataRange[0];
            }
            if (plotDataRange[1] > range[1])
            {
                range[1] = plotDataRange[1];
            }
        }
    }
    if (range[0] <= range[1])
    {
        this->DataYRange[0] = range[0];
        this->DataYRange[1] = range[1];
    }
    else
    {
        this->DataYRange[0] = 0;
        this->DataYRange[1] = 0;
    }

    // Calculate Data X Range Above 0
    range[0] = VTK_DOUBLE_MAX;
    range[1] = VTK_DOUBLE_MIN;
    this->PlotData->InitTraversal();
    while ((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->GetDataXRangeAbove0(plotDataRange);
        if (plotDataRange[0] <= plotDataRange[1])
        {
            if (plotDataRange[0] < range[0])
            {
                range[0] = plotDataRange[0];
            }
            if (plotDataRange[1] > range[1])
            {
                range[1] = plotDataRange[1];
            }
        }
    }
    if (range[0] <= range[1])
    {
        this->DataXRangeAbove0[0] = range[0];
        this->DataXRangeAbove0[1] = range[1];
    }
    else
    {
        this->DataXRangeAbove0[0] = 1;
        this->DataXRangeAbove0[1] = 1;
    }

    // Calculate Data Y Range Above 0
    range[0] = VTK_DOUBLE_MAX;
    range[1] = VTK_DOUBLE_MIN;
    this->PlotData->InitTraversal();
    while ((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->GetDataYRangeAbove0(plotDataRange);
        if (plotDataRange[0] <= plotDataRange[1])
        {
            if (plotDataRange[0] < range[0])
            {
                range[0] = plotDataRange[0];
            }
            if (plotDataRange[1] > range[1])
            {
                range[1] = plotDataRange[1];
            }
        }
    }
    if (range[0] <= range[1])
    {
        this->DataYRangeAbove0[0] = range[0];
        this->DataYRangeAbove0[1] = range[1];
    }
    else
    {
        this->DataYRangeAbove0[0] = 0;
        this->DataYRangeAbove0[1] = 0;
    }
}

void vtkPlotActor::ZoomToOuterXRange()
{
    double range[2];
    double interval;
    vtkNewAxisActor2D::ComputeRange(this->XRange, range, this->NumberOfXLabels, this->BaseX,
                                    this->LogX, this->ComputedNumberOfXLabels, interval);
    this->SetXRange(range);
}

void vtkPlotActor::ZoomToOuterYRange()
{
    double range[2];
    double interval;
    vtkNewAxisActor2D::ComputeRange(this->YRange, range, this->NumberOfYLabels, this->BaseY,
                                    this->LogY, this->ComputedNumberOfYLabels, interval);
    this->SetYRange(range);
}

void vtkPlotActor::ZoomToInnerXRange()
{
    double range[2];
    double interval;
    vtkNewAxisActor2D::ComputeInnerRange(this->XRange, range, this->NumberOfXLabels, this->BaseX,
                                         this->LogX, this->ComputedNumberOfXLabels, interval);
    this->SetXRange(range);
}

void vtkPlotActor::ZoomToInnerYRange()
{
    double range[2];
    double interval;
    vtkNewAxisActor2D::ComputeInnerRange(this->YRange, range, this->NumberOfYLabels, this->BaseY,
                                         this->LogY, this->ComputedNumberOfYLabels, interval);
    this->SetYRange(range);
}

void vtkPlotActor::ZoomInAtXValue(double x, double zoomFactor)
{
    double range[2];
    if (this->LogX && x > 0 && this->XRange[0] > 0)
    {
        range[0] = exp(log(x) - (log(x) - log(this->XRange[0])) / zoomFactor);
        range[1] = exp(log(x) + (log(this->XRange[1]) - log(x)) / zoomFactor);
        this->SetXRange(range);
    }
    else
    {
        range[0] = this->XRange[0] + (x - this->XRange[0]) * (zoomFactor - 1) / zoomFactor;
        range[1] = range[0] + (this->XRange[1] - this->XRange[0]) / zoomFactor;
        this->SetXRange(range);
    }
}

void vtkPlotActor::ZoomInAtYValue(double y, double zoomFactor)
{
    double range[2];
    if (this->LogY && y > 0 && this->YRange[0] > 0)
    {
        range[0] = exp(log(y) - (log(y) - log(this->YRange[0])) / zoomFactor);
        range[1] = exp(log(y) + (log(this->YRange[1]) - log(y)) / zoomFactor);
        this->SetYRange(range);
    }
    else
    {
        range[0] = this->YRange[0] + (y - this->YRange[0]) * (zoomFactor - 1) / zoomFactor;
        range[1] = range[0] + (this->YRange[1] - this->YRange[0]) / zoomFactor;
        this->SetYRange(range);
    }
}

void vtkPlotActor::PanXRange(double panFactor)
{
    double range[2];
    if (this->LogX && this->XRange[0] > 0)
    {
        range[0] = exp(log(this->XRange[0]) - panFactor * (log(this->XRange[1]) - log(this->XRange[0])));
        range[1] = exp(log(this->XRange[1]) - panFactor * (log(this->XRange[1]) - log(this->XRange[0])));
        this->SetXRange(range);
    }
    else
    {
        range[0] = this->XRange[0] - panFactor * (this->XRange[1] - this->XRange[0]);
        range[1] = this->XRange[1] - panFactor * (this->XRange[1] - this->XRange[0]);
        this->SetXRange(range);
    }
}

void vtkPlotActor::PanYRange(double panFactor)
{
    double range[2];
    if (this->LogY && this->YRange[0] > 0)
    {
        range[0] = exp(log(this->YRange[0]) - panFactor * (log(this->YRange[1]) - log(this->YRange[0])));
        range[1] = exp(log(this->YRange[1]) - panFactor * (log(this->YRange[1]) - log(this->YRange[0])));
        this->SetYRange(range);
    }
    else
    {
        range[0] = this->YRange[0] - panFactor * (this->YRange[1] - this->YRange[0]);
        range[1] = this->YRange[1] - panFactor * (this->YRange[1] - this->YRange[0]);
        this->SetYRange(range);
    }
}

int vtkPlotActor::IsInPlot(double x, double y)
{
    return (x >= this->InnerPlotBounds[0] && x <= this->InnerPlotBounds[1] &&
            y >= this->InnerPlotBounds[2] && y <= this->InnerPlotBounds[3]);
}

int vtkPlotActor::IsXAxis(double x, double y)
{
    vtkDebugMacro(<< "XAxis check " << this->InnerPlotBounds[0] << ", " << this->InnerPlotBounds[1] << ", "
                  << this->OuterPlotBounds[2] << ", " << this->InnerPlotBounds[2]);
    return (x>=this->InnerPlotBounds[0] && x<=this->InnerPlotBounds[1] &&
            y>=this->OuterPlotBounds[2] && y<=this->InnerPlotBounds[2]);
}

int vtkPlotActor::IsYAxis(double x, double y)
{
    vtkDebugMacro(<< "YAxis check " << this->OuterPlotBounds[1] << ", " << this->InnerPlotBounds[0] << ", "
                  << this->InnerPlotBounds[2] << ", " << this->InnerPlotBounds[3]);
    return (x>=this->OuterPlotBounds[0] && x<=this->InnerPlotBounds[0] &&
            y>=this->InnerPlotBounds[2] && y<=this->InnerPlotBounds[3]);
}

vtkPlotData *vtkPlotActor::FindPlotData(double x, double y)
{
    double minDistance = VTK_DOUBLE_MAX;
    vtkPlotData *nearestPlotData = 0;
    vtkPlotData *plotData;

    this->PlotData->InitTraversal();
    while((plotData = this->PlotData->GetNextItem()) != nullptr)
    {
        plotData->Update();
        vtkIdType point = plotData->GetOutput()->FindPoint(x, y, 0);
        if (point >= 0)
        {
            double *xyz = plotData->GetOutput()->GetPoint(point);
            double distance = (x - xyz[0]) * (x - xyz[0]) + (y - xyz[1]) * (y - xyz[1]);
            if (distance < minDistance)
            {
                minDistance = distance;
                nearestPlotData = plotData;
            }
        }
    }
    return nearestPlotData;
}

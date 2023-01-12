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

#include "vtkNewAxisActor2D.h"

#include "vtkActor2DCollection.h"
#include "vtkCellArray.h"
#include "vtkCoordinate.h"
#include "vtkObjectFactory.h"
#include "vtkPolyData.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkTextMapper.h"
#include "vtkTextProperty.h"
#include "vtkTimeStamp.h"
#include "vtkViewport.h"
#include "vtkWindow.h"

#define VTK_EPS 0.00001

// returns a * x^y, with a and b of type double and y of type int
static double a_pow_xy(double a, double x, int y)
{
    int i = abs(y);
    double val = 1.0;

    while (--i >= 0)
    {
        val *= x;
    }

    if (y < 0)
    {
        return a / val;
    }
    return a * val;
}

static int GetNumberOfLines(const char *str)
{
    if (str == nullptr || *str == '\0')
    {
        return 0;
    }

    int result = 1;
    while (str != nullptr)
    {
        if ((str = strstr(str, "\n")) != nullptr)
        {
            result++;
            str++; // Skip '\n'
        }
    }
    return result;
}

vtkStandardNewMacro(vtkNewAxisActor2D);

vtkCxxSetObjectMacro(vtkNewAxisActor2D, LabelTextProperty, vtkTextProperty);
vtkCxxSetObjectMacro(vtkNewAxisActor2D, TitleTextProperty, vtkTextProperty);

vtkNewAxisActor2D::vtkNewAxisActor2D()
{
    this->PositionCoordinate->SetCoordinateSystemToNormalizedViewport();
    this->PositionCoordinate->SetValue(0.0, 0.0);

    this->Position2Coordinate->SetCoordinateSystemToNormalizedViewport();
    this->Position2Coordinate->SetValue(0.75, 0.0);
    this->Position2Coordinate->SetReferenceCoordinate(nullptr);

    this->NumberOfLabels = 5;

    this->Title = nullptr;

    this->AdjustRange = 1;
    this->AdjustTicks = 0;

    this->TickLength = 5;
    this->TickOffset = 2;

    this->Range[0] = 0.0;
    this->Range[1] = 1.0;

    this->FontFactor = 0.85;
    this->LabelFactor = 0.85;

    this->Log = 0;
    this->Base = 10;

    this->LabelTextProperty = vtkSmartPointer<vtkTextProperty>::New();
    this->LabelTextProperty->SetBold(1);
    this->LabelTextProperty->SetItalic(1);
    this->LabelTextProperty->SetShadow(1);
    this->LabelTextProperty->SetFontFamilyToArial();

    this->TitleTextProperty = vtkSmartPointer<vtkTextProperty>::New();
    this->TitleTextProperty->ShallowCopy(this->LabelTextProperty);

    this->LabelFormat = new char[8];
    snprintf(this->LabelFormat, 8, "%s", "%-#.4g");

    auto TitleMapper = vtkSmartPointer<vtkTextMapper>::New();
    TitleMapper->GetTextProperty()->ShallowCopy(this->TitleTextProperty);
    this->TitleActor = vtkSmartPointer<vtkActor2D>::New();
    this->TitleActor->SetMapper(TitleMapper);

    // To avoid deleting/rebuilding create once up front

    this->AdjustedNumberOfLabels = 0;
    this->LabelActors = vtkSmartPointer<vtkActor2DCollection>::New();
    for (int i = 0; i < VTK_MAX_LABELS; i++)
    {
        auto LabelMapper = vtkSmartPointer<vtkTextMapper>::New();
        auto LabelActor = vtkSmartPointer<vtkActor2D>::New();
        LabelActor->SetMapper(LabelMapper);
        this->LabelActors->AddItem(LabelActor.GetPointer());
    }

    this->Axis = vtkSmartPointer<vtkPolyData>::New();
    this->AxisMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    this->AxisMapper->SetInputData(this->Axis);
    this->AxisActor = vtkSmartPointer<vtkActor2D>::New();
    this->AxisActor->SetMapper(this->AxisMapper);

    this->AxisVisibility = 1;
    this->TickVisibility = 1;
    this->LabelVisibility = 1;
    this->TitleVisibility = 1;

    this->LastPosition[0] = this->LastPosition[1] = 0;
    this->LastPosition2[0] = this->LastPosition2[1] = 0;

    this->LastSize[0] = this->LastSize[1] = 0;
    this->LastMaxLabelSize[0] = this->LastMaxLabelSize[1] = 0;
}

vtkNewAxisActor2D::~vtkNewAxisActor2D()
{
    if (this->LabelFormat)
    {
        delete [] this->LabelFormat;
        this->LabelFormat = nullptr;
    }

    if (this->Title)
    {
        delete [] this->Title;
        this->Title = nullptr;
    }
}

// Build the axis, ticks, title, and labels and render.
int vtkNewAxisActor2D::RenderOpaqueGeometry(vtkViewport *viewport)
{
    int i, renderedSomething = 0;

    this->BuildAxis(viewport);

    // Everything is built, just have to render
    if (this->Title != nullptr && this->TitleVisibility)
    {
        renderedSomething += this->TitleActor->RenderOpaqueGeometry(viewport);
    }

    if (this->AxisVisibility || this->TickVisibility)
    {
        renderedSomething += this->AxisActor->RenderOpaqueGeometry(viewport);
    }

    if (this->LabelVisibility)
    {
        this->LabelActors->InitTraversal();
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            renderedSomething += this->LabelActors->GetNextItem()->RenderOpaqueGeometry(viewport);
        }
    }

    return renderedSomething;
}

// Render the axis, ticks, title, and labels.
int vtkNewAxisActor2D::RenderOverlay(vtkViewport *viewport)
{
    int i, renderedSomething = 0;

    // Everything is built, just have to render
    if (this->Title != nullptr && this->TitleVisibility)
    {
        renderedSomething += this->TitleActor->RenderOverlay(viewport);
    }

    if (this->AxisVisibility || this->TickVisibility)
    {
        renderedSomething += this->AxisActor->RenderOverlay(viewport);
    }

    if (this->LabelVisibility)
    {
        this->LabelActors->InitTraversal();
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            renderedSomething += this->LabelActors->GetNextItem()->RenderOverlay(viewport);
        }
    }

    return renderedSomething;
}

// Release any graphics resources that are being consumed by this actor.
// The parameter window could be used to determine which graphic
// resources to release.
void vtkNewAxisActor2D::ReleaseGraphicsResources(vtkWindow *win)
{
    this->TitleActor->ReleaseGraphicsResources(win);
    this->LabelActors->InitTraversal();
    for (int i = 0; i < VTK_MAX_LABELS; i++)
    {
        this->LabelActors->GetNextItem()->ReleaseGraphicsResources(win);
    }
    this->AxisActor->ReleaseGraphicsResources(win);
}


void vtkNewAxisActor2D::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os,indent);

    if (this->TitleTextProperty)
    {
        os << indent << "Title Text Property:" << endl;
        this->TitleTextProperty->PrintSelf(os,indent.GetNextIndent());
    }
    else
    {
        os << indent << "Title Text Property: (none)" << endl;
    }

    if (this->LabelTextProperty)
    {
        os << indent << "Label Text Property:" << endl;
        this->LabelTextProperty->PrintSelf(os,indent.GetNextIndent());
    }
    else
    {
        os << indent << "Label Text Property: (none)" << endl;
    }

    os << indent << "Title: " << (this->Title ? this->Title : "(none)") << endl;
    os << indent << "Number Of Labels: " << this->NumberOfLabels << endl;
    os << indent << "Range: (" << this->Range[0] << ", " << this->Range[1] << ")" << endl;

    os << indent << "Adjusted Number Of Labels: " << this->AdjustedNumberOfLabels << endl;
    os << indent << "Adjusted Range: (" << this->AdjustedRange[0] << ", " << this->AdjustedRange[1] << ")" << endl;
    os << indent << "Tick Range: (" << this->TickRange[0] << ", " << this->TickRange[1] << ")" << endl;
    os << indent << "Interval: " << this->Interval << endl;

    os << indent << "Label Format: " << this->LabelFormat << endl;
    os << indent << "Font Factor: " << this->FontFactor << endl;
    os << indent << "Label Factor: " << this->LabelFactor << endl;
    os << indent << "Tick Length: " << this->TickLength << endl;
    os << indent << "Tick Offset: " << this->TickOffset << endl;

    os << indent << "Adjust Range: " << (this->AdjustRange ? "On" : "Off") << endl;
    os << indent << "Adjust Ticks: " << (this->AdjustTicks ? "On" : "Off") << endl;
    os << indent << "Axis Visibility: " << (this->AxisVisibility ? "On" : "Off") << endl;
    os << indent << "Tick Visibility: " << (this->TickVisibility ? "On" : "Off") << endl;
    os << indent << "Label Visibility: " << (this->LabelVisibility ? "On" : "Off") << endl;
    os << indent << "Title Visibility: " << (this->TitleVisibility ? "On" : "Off") << endl;
}


void vtkNewAxisActor2D::BuildAxis(vtkViewport *viewport)
{
    int i, *x, viewportSizeHasChanged, positionsHaveChanged;
    vtkIdType ptIds[2];
    double pRange1[3], pRange2[3];
    double pTicks1[3], pTicks2[3];
    double stringOffset;
    double deltaX, deltaY;
    double xTick[3];
    double theta;
    double val;
    int *size, stringSize[2];
    char string[512];

    if (this->TitleVisibility && !this->TitleTextProperty)
    {
        vtkErrorMacro(<< "Need title text property to render axis actor");
        return;
    }

    if (this->LabelVisibility && !this->LabelTextProperty)
    {
        vtkErrorMacro(<< "Need label text property to render axis actor");
        return;
    }

    positionsHaveChanged = 0;
    if (viewport->GetMTime() > this->BuildTime || (viewport->GetVTKWindow() &&
                                                   viewport->GetVTKWindow()->GetMTime() > this->BuildTime))
    {
        // Check to see whether we have to rebuild everything
        // Viewport change may not require rebuild
        int *lastPosition = this->PositionCoordinate->GetComputedViewportValue(viewport);
        int *lastPosition2 = this->Position2Coordinate->GetComputedViewportValue(viewport);
        if (lastPosition[0] != this->LastPosition[0] || lastPosition[1] != this->LastPosition[1] ||
            lastPosition2[0] != this->LastPosition2[0] || lastPosition2[1] != this->LastPosition2[1] )
        {
            positionsHaveChanged = 1;
        }
    }

    if (!positionsHaveChanged && this->GetMTime() < this->BuildTime &&
        (this->LabelTextProperty->GetMTime() < this->BuildTime) &&
        (this->TitleTextProperty->GetMTime() < this->BuildTime))
    {
        return;
    }

    vtkDebugMacro(<< "Rebuilding axis");

    // Initialize and get important info

    this->Axis->Initialize();
    this->AxisActor->SetProperty(this->GetProperty());
    this->TitleActor->SetProperty(this->GetProperty());

    // Compute the location of tick marks and labels

    this->UpdateAdjustedRange();

    // Generate the axis and tick marks.
    // We'll do our computation in viewport coordinates. First determine the
    // location of the range and ticks endpoints.

    x = this->PositionCoordinate->GetComputedViewportValue(viewport);
    pRange1[0] = (double)x[0];
    pRange1[1] = (double)x[1];
    pRange1[2] = 0.0;
    this->LastPosition[0] = x[0];
    this->LastPosition[1] = x[1];
    x = this->Position2Coordinate->GetComputedViewportValue(viewport);
    pRange2[0] = (double)x[0];
    pRange2[1] = (double)x[1];
    pRange2[2] = 0.0;
    this->LastPosition2[0] = x[0];
    this->LastPosition2[1] = x[1];

    size = viewport->GetSize();

    auto pts = vtkSmartPointer<vtkPoints>::New();
    pts->SetDataTypeToDouble();
    auto lines = vtkSmartPointer<vtkCellArray>::New();
    this->Axis->SetPoints(pts);
    this->Axis->SetLines(lines);

    // Calculate tick starting and end points
    if (this->AdjustedRange[0] == this->AdjustedRange[1])
    {
        // we only have one point -> create one tick in the center
        pTicks1[0] = (pRange1[0] + pRange2[0]) / 2;
        pTicks1[1] = (pRange1[1] + pRange2[1]) / 2;
        pTicks2[0] = pTicks1[0];
        pTicks2[1] = pTicks1[1];
    }
    else if (this->TickRange[0] != this->AdjustedRange[0] ||
             this->TickRange[1] != this->AdjustedRange[1])
    {
        // first and last tick may start somewhere else
        if (this->Log)
        {
            pTicks1[0] = pRange1[0] + (pRange2[0] - pRange1[0]) * (log(this->TickRange[0]) - log(this->AdjustedRange[0])) /
                (log(this->AdjustedRange[1]) - log(this->AdjustedRange[0]));
            pTicks1[1] = pRange1[1] + (pRange2[1] - pRange1[1]) * (log(this->TickRange[0]) - log(this->AdjustedRange[0])) /
                (log(this->AdjustedRange[1]) - log(this->AdjustedRange[0]));
            pTicks2[0] = pRange1[0] + (pRange2[0] - pRange1[0]) * (log(this->TickRange[1]) - log(this->AdjustedRange[0])) /
                (log(this->AdjustedRange[1]) - log(this->AdjustedRange[0]));
            pTicks2[1] = pRange1[1] + (pRange2[1] - pRange1[1]) * (log(this->TickRange[1]) - log(this->AdjustedRange[0])) /
                (log(this->AdjustedRange[1]) - log(this->AdjustedRange[0]));
        }
        else
        {
            pTicks1[0] = pRange1[0] + (pRange2[0] - pRange1[0]) * (this->TickRange[0] - this->AdjustedRange[0]) /
                (this->AdjustedRange[1] - this->AdjustedRange[0]);
            pTicks1[1] = pRange1[1] + (pRange2[1] - pRange1[1]) * (this->TickRange[0] - this->AdjustedRange[0]) /
                (this->AdjustedRange[1] - this->AdjustedRange[0]);
            pTicks2[0] = pRange1[0] + (pRange2[0] - pRange1[0]) * (this->TickRange[1] - this->AdjustedRange[0]) /
                (this->AdjustedRange[1] - this->AdjustedRange[0]);
            pTicks2[1] = pRange1[1] + (pRange2[1] - pRange1[1]) * (this->TickRange[1] - this->AdjustedRange[0]) /
                (this->AdjustedRange[1] - this->AdjustedRange[0]);
        }
    }
    else
    {
        pTicks1[0] = pRange1[0];
        pTicks1[1] = pRange1[1];
        pTicks2[0] = pRange2[0];
        pTicks2[1] = pRange2[1];
    }
    pTicks1[2] = 0;
    pTicks2[2] = 0;

    // Generate point along axis (as well as tick points)

    deltaX = pRange2[0] - pRange1[0];
    deltaY = pRange2[1] - pRange1[1];

    if (deltaX == 0. && deltaY == 0.)
    {
        theta = 0.;
    }
    else
    {
        theta = atan2(deltaY, deltaX);
    }

    xTick[2] = 0;
    for (i = 0; i < (this->AdjustedNumberOfLabels - 1); i++)
    {
        xTick[0] = pTicks1[0] + (pTicks2[0] - pTicks1[0]) * ((double)i / (this->AdjustedNumberOfLabels - 1));
        xTick[1] = pTicks1[1] + (pTicks2[1] - pTicks1[1]) * ((double)i / (this->AdjustedNumberOfLabels - 1));
        pts->InsertNextPoint(xTick);
        xTick[0] = xTick[0] + this->TickLength * sin(theta);
        xTick[1] = xTick[1] - this->TickLength * cos(theta);
        pts->InsertNextPoint(xTick);
    }

    // Make sure we don't make any rounding errors for the last tick
    pts->InsertNextPoint(pTicks2);                //last axis point
    xTick[0] = pTicks2[0] + this->TickLength * sin(theta);
    xTick[1] = pTicks2[1] - this->TickLength * cos(theta);
    pts->InsertNextPoint(xTick);

    // Create Axis

    if (this->AxisVisibility)
    {
        ptIds[0] = pts->InsertNextPoint(pRange1); //first axis point
        ptIds[1] = pts->InsertNextPoint(pRange2); //last axis point
        lines->InsertNextCell(2, ptIds);
    }

    // Create points and lines

    if (this->TickVisibility)
    {
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            ptIds[0] = 2 * i;
            ptIds[1] = 2 * i + 1;
            lines->InsertNextCell(2, ptIds);
        }
    }

    // See whether fonts have to be rebuilt (font size depends on viewport size)

    if (this->LastSize[0] != size[0] || this->LastSize[1] != size[1])
    {
        viewportSizeHasChanged = 1;
        this->LastSize[0] = size[0];
        this->LastSize[1] = size[1];
    }
    else
    {
        viewportSizeHasChanged = 0;
    }

    // Build the labels

    if (this->LabelVisibility)
    {
        // Update the labels text. Do it only if the range has been adjusted,
        // i.e. if we think that new labels must be created.
        // WARNING: if LabelFormat has changed, they should be recreated too
        // but at this point the check on LabelFormat is "included" in
        // UpdateAdjustedRange(), which is the function that updates
        // AdjustedRangeBuildTime.
        vtkTextMapper *LabelMappers[VTK_MAX_LABELS];
        this->LabelActors->InitTraversal();
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            LabelMappers[i] = vtkTextMapper::SafeDownCast(this->LabelActors->GetNextItem()->GetMapper());
        }

        unsigned long labeltime = this->AdjustedRangeBuildTime;
        if (this->AdjustedRangeBuildTime > this->BuildTime)
        {
            for (i = 0; i < this->AdjustedNumberOfLabels; i++)
            {
                if (this->Log)
                {
                    val = a_pow_xy(this->TickRange[0], this->Interval, i);
                }
                else
                {
                    val = this->TickRange[0] + i * this->Interval;
                    // Correct rounding error for 0.0 value
                    if (fabs(val / this->Interval) < 1e-6)
                    {
                        val = 0.0;
                    }
                }
                snprintf(string, 8, this->LabelFormat, val);
                LabelMappers[i]->SetInput(string);

                // Check if the label text has changed

                if (LabelMappers[i]->GetMTime() > labeltime)
                {
                    labeltime = LabelMappers[i]->GetMTime();
                }
            }
        }

        // Copy prop and text prop eventually

        this->LabelActors->InitTraversal();
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            vtkActor2D *LabelActor = this->LabelActors->GetNextItem();
            LabelActor->SetProperty(this->GetProperty());
            if (this->LabelTextProperty->GetMTime() > this->BuildTime || labeltime > this->BuildTime)
            {
                // Shallow copy here so that the size of the label prop is not
                // affected by the automatic adjustment of its text mapper's
                // size (i.e. its mapper's text property is identical except
                // for the font size which will be modified later). This
                // allows text actors to share the same text property, and in
                // that case specifically allows the title and label text prop
                // to be the same.
                LabelMappers[i]->GetTextProperty()->ShallowCopy(this->LabelTextProperty);
            }
        }

        // Resize the mappers if needed (i.e. viewport has changed, than
        // font size should be changed, or label text property has changed,
        // or some of the labels have changed (got bigger for example)

        if (viewportSizeHasChanged || this->LabelTextProperty->GetMTime() > this->BuildTime ||
            labeltime > this->BuildTime)
        {
            this->SetMultipleFontSize(viewport, LabelMappers, this->AdjustedNumberOfLabels, size,
                                      this->FontFactor * this->LabelFactor, this->LastMaxLabelSize);
        }

        // Position the mappers

        this->LabelActors->InitTraversal();
        for (i = 0; i < this->AdjustedNumberOfLabels; i++)
        {
            pts->GetPoint(2 * i + 1, xTick);
            LabelMappers[i]->GetSize(viewport, stringSize);
            this->SetOffsetPosition(xTick, theta, this->LastMaxLabelSize[0], this->LastMaxLabelSize[1],
                                    this->TickOffset, this->LabelActors->GetNextItem());
        }
    }

    // Now build the title

    vtkTextMapper *TitleMapper = vtkTextMapper::SafeDownCast(this->TitleActor->GetMapper());
    if (this->Title)
    {
        TitleMapper->SetInput(this->Title);
    }
    if (this->TitleTextProperty->GetMTime() > this->BuildTime)
    {
        // Shallow copy here so that the size of the title prop is not
        // affected by the automatic adjustment of its text mapper's
        // size (i.e. its mapper's text property is identical except for
        // the font size which will be modified later). This allows text
        // actors to share the same text property, and in that case
        // specifically allows the title and label text prop to be the same.
         TitleMapper->GetTextProperty()->ShallowCopy(this->TitleTextProperty);
    }
    this->SetFontSize(viewport, TitleMapper, size, this->FontFactor, stringSize);
    xTick[0] = pRange1[0] + (pRange2[0] - pRange1[0]) / 2.0;
    xTick[1] = pRange1[1] + (pRange2[1] - pRange1[1]) / 2.0;
    xTick[0] = xTick[0] + (this->TickLength + this->TickOffset) * sin(theta);
    xTick[1] = xTick[1] - (this->TickLength + this->TickOffset) * cos(theta);

    stringOffset = 0.0;
    if (this->LabelVisibility)
    {
        stringOffset = this->ComputeStringOffset(this->LastMaxLabelSize[0], this->LastMaxLabelSize[1], theta);
    }

    this->SetOffsetPosition(xTick, theta, stringSize[0], stringSize[1], static_cast<int>(stringOffset),
                            this->TitleActor);

    this->BuildTime.Modified();
}

#define VTK_AA2D_FACTOR 0.015

int vtkNewAxisActor2D::SetFontSize(vtkViewport *viewport, vtkTextMapper *textMapper, int *targetSize, double factor,
                                   int *stringSize)
{
    int fontSize, targetWidth, targetHeight;

    // Find the best size for the font
    targetWidth = targetSize [0] > targetSize[1] ? targetSize[0] : targetSize[1];
    factor *= GetNumberOfLines(textMapper->GetInput());
    targetHeight = (int)(VTK_AA2D_FACTOR * factor * targetSize[0] + VTK_AA2D_FACTOR * factor * targetSize[1]);
    fontSize = textMapper->SetConstrainedFontSize(viewport, targetWidth, targetHeight);
    textMapper->GetSize(viewport, stringSize);

    return fontSize;
}


int vtkNewAxisActor2D::SetMultipleFontSize(vtkViewport *viewport, vtkTextMapper **textMappers, int nbOfMappers,
                                           int *targetSize, double factor, int *stringSize)
{
    int fontSize, targetWidth, targetHeight;

    // Find the best size for the font
    // WARNING: check that the below values are in sync with the above similar function.
    targetWidth = targetSize[0] > targetSize[1] ? targetSize[0] : targetSize[1];
    targetHeight = (int)(VTK_AA2D_FACTOR * factor * targetSize[0] + VTK_AA2D_FACTOR * factor * targetSize[1]);
    fontSize = vtkTextMapper::SetMultipleConstrainedFontSize(viewport, targetWidth, targetHeight, textMappers,
                                                             nbOfMappers, stringSize);
    return fontSize;
}

void vtkNewAxisActor2D::UpdateAdjustedRange()
{
    // Try not to update/adjust the range too often, do not update it if the object has not been modified.
    // Nevertheless, try the following optimization: there is no need to update the range if the position
    // coordinate of this actor has changed. But since vtkActor2D::GetMTime() includes the check for
    // both Position and Position2 coordinates, we will have to bypass it.

    if (this->vtkActor2D::Superclass::GetMTime() <= this->AdjustedRangeBuildTime)
    {
        return;
    }

    if (this->AdjustRange)
    {
        this->ComputeRange(this->Range, this->AdjustedRange, this->NumberOfLabels, this->Base, this->Log,
                           this->AdjustedNumberOfLabels, this->Interval);
        vtkDebugMacro("Compute Range : range = (" << this->AdjustedRange[0] << ", " << this->AdjustedRange[1]
            << "), interval = " << this->Interval);
        this->TickRange[0] = this->AdjustedRange[0];
        this->TickRange[1] = this->AdjustedRange[1];
    }
    else
    {
        this->AdjustedRange[0] = this->Range[0];
        this->AdjustedRange[1] = this->Range[1];
        if (this->AdjustTicks)
        {
            this->ComputeInnerRange(this->Range, this->TickRange, this->NumberOfLabels, this->Base, this->Log,
                                    this->AdjustedNumberOfLabels, this->Interval);
            vtkDebugMacro("Compute Tick Range : range = (" << this->TickRange[0] << ", " << this->TickRange[1]
                << "), interval = " << this->Interval);
        }
        else
        {
            // compute spacing based on values for Range and NumberOfLabels
            this->TickRange[0] = this->Range[0];
            this->TickRange[1] = this->Range[1];
            this->AdjustedNumberOfLabels = this->NumberOfLabels;
            if (this->AdjustedNumberOfLabels > 1)
            {
                if (this->Log)
                {
                    this->Interval = exp((log(this->Range[1]) - log(this->Range[0])) /
                                         (this->AdjustedNumberOfLabels - 1));
                }
                else
                {
                    this->Interval = (this->Range[1] - this->Range[0]) / (this->AdjustedNumberOfLabels - 1);
                }
            }
            else
            {
                this->Interval = 0;
            }
        }
    }
    this->AdjustedRangeBuildTime.Modified();
}


void vtkNewAxisActor2D::ComputeRange(double inRange[2], double outRange[2], int inNumTicks, double base, int logAxis,
                                     int &numTicks, double &interval)
{
    double range;
    double lbase;
    double sRange[2];
    int flbase;
    int norminterval;

    // Handle the range
    if (inRange[0] < inRange[1])
    {
        sRange[0] = inRange[0];
        sRange[1] = inRange[1];
    }
    else if (inRange[0] > inRange[1])
    {
        sRange[1] = inRange[0];
        sRange[0] = inRange[1];
    }
    else
    {
        // they're equal, so just use 1 tick
        outRange[0] = inRange[0];
        outRange[1] = inRange[1];
        numTicks = 1;
        interval = 0;
        return;
    }

    if (inNumTicks <= 1)
    {
        inNumTicks = 2;
    }

    if (base <= 1.0)
    {
        // invalid base -> create ugly ticks
        numTicks = inNumTicks;
        interval = (sRange[1] - sRange[0]) / (numTicks - 1);
        return;
    }

    if (logAxis && sRange[0] > 0)
    {
        range = (log(sRange[1]) - log(sRange[0])) / log(base);
        interval = ceil(range / (inNumTicks - 1));

        // Calculate the logarithms of the outRange values and store them
        // temporarily in outRange
        outRange[0] = interval * floor(log(sRange[0]) / (log(base) * interval) + VTK_EPS);
        outRange[1] = interval * ceil(log(sRange[1]) / (log(base) * interval) - VTK_EPS);

        numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;

        // We want at least 2 ticks. If we have less, we calculate 2 ticks via
        // the linear method (logAxis = 0, inNumTicks = 2)
        if (numTicks <= 1)
        {
            // The amount of powers of 2 in the range is less then 2
            range = sRange[1] - sRange[0];
            lbase = log(range / (inNumTicks - 1)) / log(base);
            flbase = (int)floor(lbase);
            norminterval = (int)ceil(-0.5 + pow(base, lbase - flbase));

            interval = a_pow_xy(norminterval, base, flbase);

            outRange[0] = interval * floor(sRange[0] / interval - VTK_EPS);
            outRange[1] = interval * ceil(sRange[1] / interval + VTK_EPS);

            numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;
            if (numTicks > 2)
            {
                numTicks = 2;
            }
            // set interval to the multiplicational interval
            interval = outRange[1] / outRange[0];
        }
        else
        {
            // The interval we return is the multiplicationfactor between ticks
            interval = pow(base, interval);

            outRange[0] = pow(base, outRange[0]);
            outRange[1] = pow(base, outRange[1]);
        }
    }
    else
    {
        range = sRange[1] - sRange[0];
        lbase = log(range / (inNumTicks - 1)) / log(base);
        flbase = (int)floor(lbase);
        norminterval = (int)ceil(-0.5 + pow(base, lbase - flbase));

        // Calculate the distance between ticks
        interval = a_pow_xy(norminterval, base, flbase);

        outRange[0] = interval * floor(sRange[0] / interval + VTK_EPS);
        outRange[1] = interval * ceil(sRange[1] / interval - VTK_EPS);

        numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;
    }

#if 0
    cout << "-O- " << (logAxis ? 'l' : 'n') << " " << base << " ("
        << sRange[0] << "," << sRange[1] << ") " << range << " / "
        << inNumTicks - 1 << " (" << lbase << " "
        << (logAxis ? 0 : pow(base, lbase - flbase)) << " "
        << (logAxis ? 0 : norminterval) << ") -> (" << outRange[0]
        << "," << outRange[1] << ") " << outRange[1] - outRange[0]
        << " / " << numTicks - 1 << " " << interval << endl;
#endif

    if (inRange[0] > inRange[1])
    {                                             // Swap ranges back again
        if (logAxis)
        {
            interval = 1.0 / interval;
        }
        else
        {
            interval = -interval;
        }
        double temp = outRange[0];
        outRange[0] = outRange[1];
        outRange[1] = temp;
    }
}

void vtkNewAxisActor2D::ComputeInnerRange(double inRange[2], double outRange[2], int inNumTicks, double base,
                                          int logAxis, int &numTicks, double &interval)
{
    double range;
    double lbase;
    double sRange[2];
    int flbase;
    int norminterval;

    // Handle the range
    if (inRange[0] < inRange[1])
    {
        sRange[0] = inRange[0];
        sRange[1] = inRange[1];
    }
    else if (inRange[0] > inRange[1])
    {
        sRange[1] = inRange[0];
        sRange[0] = inRange[1];
    }
    else                                          // they're equal, so just use 1 tick
    {
        outRange[0] = inRange[0];
        outRange[1] = inRange[1];
        numTicks = 1;
        interval = 0;
        return;
    }

    if (inNumTicks <= 1)
    {
        inNumTicks = 2;
    }

    if (base <= 1.0)
    {
        // invalid base -> create ugly ticks
        numTicks = inNumTicks;
        interval = (sRange[1] - sRange[0]) / (numTicks - 1);
        return;
    }

    if (logAxis && sRange[0] > 0)
    {
        range = (log(sRange[1]) - log(sRange[0])) / log(base);
        interval = ceil(range / (inNumTicks - 1));

        // Calculate the logarithms of the outRange values and store them
        // temporarily in outRange
        outRange[0] = interval * ceil(log(sRange[0]) / (log(base) * interval) - VTK_EPS);
        outRange[1] = interval * floor(log(sRange[1]) / (log(base) * interval) + VTK_EPS);

        numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;

        // We want at least 2 ticks. If we have less, we calculate 2 ticks via
        // the linear method (logAxis = 0, inNumTicks = 2)
        if (numTicks <= 1)
        {
            // The amount of powers of 2 in the range is less then 2
            range = sRange[1] - sRange[0];
            lbase = log(range / (inNumTicks - 1)) / log(base);
            flbase = (int)floor(lbase);
            norminterval = (int)floor(0.5 + pow(base, lbase - flbase));

            interval = a_pow_xy(norminterval, base, flbase);

            outRange[0] = interval * ceil(sRange[0] / interval - VTK_EPS);
            outRange[1] = interval * floor(sRange[1] / interval + VTK_EPS);

            numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;
            if (numTicks > 2)
            {
                numTicks = 2;
            }
            // set interval to the multiplicational interval
            interval = outRange[1] / outRange[0];
        }
        else
        {
            // The interval we return is the multiplicationfactor between ticks
            interval = pow(base, interval);

            outRange[0] = pow(base, outRange[0]);
            outRange[1] = pow(base, outRange[1]);
        }
    }
    else
    {
        range = sRange[1] - sRange[0];
        lbase = log(range / (inNumTicks - 1)) / log(base);
        flbase = (int)floor(lbase);
        norminterval = (int)floor(0.5 + pow(base, lbase - flbase));

        interval = a_pow_xy(norminterval, base, flbase);

        outRange[0] = interval * ceil(sRange[0] / interval - VTK_EPS);
        outRange[1] = interval * floor(sRange[1] / interval + VTK_EPS);

        numTicks = (int)floor(0.5 + (outRange[1] - outRange[0]) / interval) + 1;
    }

#if 0
    cout << "-I- " << (logAxis ? 'l' : 'n') << " " << base << " ("
        << sRange[0] << "," << sRange[1] << ") " << range << " / "
        << inNumTicks - 1 << " (" << lbase << " "
        << (logAxis ? 0 : pow(base, lbase - flbase)) << " "
        << (logAxis ? 0 : norminterval) << ") -> (" << outRange[0]
        << "," << outRange[1] << ") " << outRange[1] - outRange[0]
        << " / " << numTicks - 1 << " " << interval << endl;
#endif

    if (inRange[0] > inRange[1])
    {
        // Swap ranges back again
        if (logAxis)
        {
            interval = 1.0 / interval;
        }
        else
        {
            interval = -interval;
        }
        double temp = outRange[0];
        outRange[0] = outRange[1];
        outRange[1] = temp;
    }
}

// Position text with respect to a point (xTick) where the angle of the line
// from the point to the center of the text is given by theta. The offset
// is the spacing between ticks and labels.
void vtkNewAxisActor2D::SetOffsetPosition(double xTick[3], double theta, int stringWidth, int stringHeight, int offset,
                                          vtkActor2D *actor)
{
    double x, y, center[2];
    int pos[2];

    x = stringWidth/2.0 + offset;
    y = stringHeight/2.0 + offset;

    center[0] = xTick[0] + x*sin(theta);
    center[1] = xTick[1] - y*cos(theta);

    pos[0] = (int)(center[0] - stringWidth/2.0);
    pos[1] = (int)(center[1] - stringHeight/2.0);

    actor->SetPosition(pos[0], pos[1]);
}

double vtkNewAxisActor2D::ComputeStringOffset(double width, double height, double theta)
{
    double f1 = height * cos(theta);
    double f2 = width * sin(theta);
    return (1.2 * sqrt(f1*f1 + f2*f2));
}

void vtkNewAxisActor2D::ShallowCopy(vtkProp *prop)
{
    vtkNewAxisActor2D *a = vtkNewAxisActor2D::SafeDownCast(prop);
    if (a != 0)
    {
        this->SetRange(a->GetRange());
        this->SetNumberOfLabels(a->GetNumberOfLabels());
        this->SetLabelFormat(a->GetLabelFormat());
        this->SetAdjustRange(a->GetAdjustRange());
        this->SetAdjustTicks(a->GetAdjustTicks());
        this->SetLog(a->GetLog());
        this->SetBase(a->GetBase());
        this->SetTitle(a->GetTitle());
        this->SetTickLength(a->GetTickLength());
        this->SetTickOffset(a->GetTickOffset());
        this->SetAxisVisibility(a->GetAxisVisibility());
        this->SetTickVisibility(a->GetTickVisibility());
        this->SetLabelVisibility(a->GetLabelVisibility());
        this->SetTitleVisibility(a->GetTitleVisibility());
        this->SetFontFactor(a->GetFontFactor());
        this->SetLabelFactor(a->GetLabelFactor());
        this->SetLabelTextProperty(a->GetLabelTextProperty());
        this->SetTitleTextProperty(a->GetTitleTextProperty());
    }

    // Now do superclass
    this->vtkActor2D::ShallowCopy(prop);
}

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

#include "vtkInteractorStylePlot.h"

#include "vtkActor2D.h"
#include "vtkCommand.h"
#include "vtkIndent.h"
#include "vtkMath.h"
#include "vtkObjectFactory.h"
#include "vtkOutlineSource.h"
#include "vtkPlotData.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkPropCollection.h"
#include "vtkProperty2D.h"
#include "vtkRenderer.h"
#include "vtkRenderWindowInteractor.h"
#include "vtkPlotActor.h"

vtkStandardNewMacro(vtkInteractorStylePlot);


vtkInteractorStylePlot::vtkInteractorStylePlot()
{
    this->OutlineActor = vtkSmartPointer<vtkActor2D>::New();
    this->OutlineSource = vtkSmartPointer<vtkOutlineSource>::New();
    auto outlineMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    outlineMapper->SetInputConnection(this->OutlineSource->GetOutputPort());
    this->OutlineActor->SetMapper(outlineMapper);
    this->UseTimers = 1;
}


void vtkInteractorStylePlot::FindPokedPlotActor(int x, int y)
{
    vtkDebugMacro(<< "Poking vtkPlotActor at (" << x << ", " << y << ")");

    this->FindPokedRenderer(x, y);

    this->CurrentPlotActor = nullptr;
    this->CurrentPlotElement = -1;
    if (this->CurrentRenderer)
    {
        vtkPropCollection *props;
        vtkProp *prop;
        props = this->CurrentRenderer->GetViewProps();
        props->InitTraversal();
        while ((prop = props->GetNextProp()) != nullptr && !this->CurrentPlotActor)
        {
            vtkPlotActor *plotActor = vtkPlotActor::SafeDownCast(prop);
            if (plotActor != 0)
            {
                // Check if current mouse position is within plotactor bounds
                int *p = plotActor->GetPositionCoordinate()->GetComputedViewportValue(CurrentRenderer);
                if (x >= p[0] && y >= p[1])
                {
                    p = plotActor->GetPosition2Coordinate()->GetComputedViewportValue(CurrentRenderer);
                    if (x <= p[0] && y <= p[1])
                    {
                        this->CurrentPlotActor = plotActor;
                    }
                }
            }
        }
        if (this->CurrentPlotActor)
        {
            vtkDebugMacro(<< "Picked plotactor " << this->CurrentPlotActor.GetPointer());
            if (this->CurrentPlotActor->IsInPlot(x, y))
            {
                vtkDebugMacro(<< "We are in the plot area");
                this->CurrentPlotElement = VTKIS_Plot_PLOT_AREA;
            }
            else if (this->CurrentPlotActor->IsXAxis(x, y))
            {
                vtkDebugMacro(<< "We are at the X Axis");
                this->CurrentPlotElement = VTKIS_Plot_X_AXIS;
            }
            else if (this->CurrentPlotActor->IsYAxis(x, y))
            {
                vtkDebugMacro(<< "We are at the Y Axis");
                this->CurrentPlotElement = VTKIS_Plot_Y_AXIS;
            }
        }
    }
}


void vtkInteractorStylePlot::Pan()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
            if (x != this->PrevPos[0])
            {
                this->CurrentPlotActor->PanXRange((x - this->PrevPos[0]) /
                                                  (this->ViewportBounds[1] - this->ViewportBounds[0]));
            }
            if (y != this->PrevPos[1])
            {
                this->CurrentPlotActor->PanYRange((y - this->PrevPos[1]) /
                                                  (this->ViewportBounds[3] - this->ViewportBounds[2]));
            }
            if (x != this->PrevPos[0] || y != this->PrevPos[1])
            {
                this->Interactor->Render();
            }
            break;
        case VTKIS_Plot_X_AXIS:
            if (x != this->PrevPos[0])
            {
                this->CurrentPlotActor->PanXRange((x - this->PrevPos[0]) /
                                                  (this->ViewportBounds[1] - this->ViewportBounds[0]));
                this->Interactor->Render();
            }
            break;
        case VTKIS_Plot_Y_AXIS:
            if (y != this->PrevPos[1])
            {
                this->CurrentPlotActor->PanYRange((y - this->PrevPos[1]) /
                                                  (this->ViewportBounds[3] - this->ViewportBounds[2]));
                this->Interactor->Render();
            }
        default:
            break;
    }
    this->PrevPos[0] = x;
    this->PrevPos[1] = y;
}


void vtkInteractorStylePlot::OutlineZoom()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
            if (x != this->PrevPos[0] || y != this->PrevPos[1])
            {
                double bounds[6];
                this->OutlineSource->GetBounds(bounds);
                bounds[1] = x;
                bounds[3] = y;
                this->OutlineSource->SetBounds(bounds);
                this->OutlineSource->Update();
                this->Interactor->Render();
            }
            break;
        default:
            break;
    }
    this->PrevPos[0] = x;
    this->PrevPos[1] = y;
}


void vtkInteractorStylePlot::Zoom()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
            if (x != this->PrevPos[0])
            {
                this->CurrentPlotActor->ZoomInAtXValue(this->ZoomStartPos[0], exp(0.01 * (x - this->PrevPos[0])));
            }
            if (y != this->PrevPos[1])
            {
                this->CurrentPlotActor->ZoomInAtYValue(this->ZoomStartPos[1], exp(0.01 * (y - this->PrevPos[1])));
            }
            if (x != this->PrevPos[0] || y != this->PrevPos[1])
            {
                this->Interactor->Render();
            }
            break;
        case VTKIS_Plot_X_AXIS:
            if (x != this->PrevPos[0])
            {
                this->CurrentPlotActor->ZoomInAtXValue(this->ZoomStartPos[0], exp(0.01 * (x - this->PrevPos[0])));
                this->Interactor->Render();
            }
            break;
        case VTKIS_Plot_Y_AXIS:
            if (y != this->PrevPos[1])
            {
                this->CurrentPlotActor->ZoomInAtYValue(this->ZoomStartPos[1], exp(0.01 * (y - this->PrevPos[1])));
                this->Interactor->Render();
            }
            break;
        default:
            break;
    }
    this->PrevPos[0] = x;
    this->PrevPos[1] = y;
}


void vtkInteractorStylePlot::StartPan()
{
    int pos[2];

    this->Interactor->GetEventPosition(pos);

    vtkDebugMacro(<< "Starting Pan");

    if (this->State != VTKIS_START)
    {
        return;
    }

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
        case VTKIS_Plot_X_AXIS:
        case VTKIS_Plot_Y_AXIS:
            this->CurrentPlotActor->GetInnerPlotBounds(this->ViewportBounds);
            this->PrevPos[0] = pos[0];
            this->PrevPos[1] = pos[1];
            this->StartState(VTKIS_PAN);
            break;
        default:
            break;
    }
}


void vtkInteractorStylePlot::StartOutlineZoom()
{
    double color[3];
    int pos[2];

    this->Interactor->GetEventPosition(pos);

    vtkDebugMacro(<< "Starting Zoom (using an outline)");

    if (this->State != VTKIS_START)
    {
        return;
    }

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
            this->CurrentPlotActor->GetInnerPlotBounds(this->ViewportBounds);
            this->OutlineSource->SetBounds(pos[0], pos[0], pos[1], pos[1], 0, 0);
            this->CurrentRenderer->GetBackground(color);
            color[0] = 1.0 - color[0];
            color[1] = 1.0 - color[1];
            color[2] = 1.0 - color[2];
            this->OutlineActor->GetProperty()->SetColor(color);
            this->OutlineActor->GetProperty()->SetLineStipplePattern(0xCCCC);
            this->CurrentRenderer->AddActor2D(this->OutlineActor);
            this->PrevPos[0] = pos[0];
            this->PrevPos[1] = pos[1];
            this->StartState(VTKIS_OUTLINEZOOM);
            break;
        default:
            break;
    }
}


void vtkInteractorStylePlot::StartZoom()
{
    double *range;
    int pos[2];

    this->Interactor->GetEventPosition(pos);

    vtkDebugMacro(<< "Starting Zoom");

    if (this->State != VTKIS_START)
    {
        return;
    }

    switch (this->CurrentPlotElement)
    {
        case VTKIS_Plot_PLOT_AREA:
        case VTKIS_Plot_X_AXIS:
        case VTKIS_Plot_Y_AXIS:
            this->CurrentPlotActor->GetInnerPlotBounds(this->ViewportBounds);
            this->ZoomStartPos[0] = pos[0];
            this->ZoomStartPos[1] = pos[1];
            range = this->CurrentPlotActor->GetXRange();
            vtkPlotData::ViewportToData(this->ZoomStartPos[0], this->ViewportBounds,
                                        range, this->CurrentPlotActor->GetLogX());
            range = this->CurrentPlotActor->GetYRange();
            vtkPlotData::ViewportToData(this->ZoomStartPos[1], &(this->ViewportBounds[2]),
                                        range, this->CurrentPlotActor->GetLogY());
            this->PrevPos[0] = pos[0];
            this->PrevPos[1] = pos[1];
            this->StartState(VTKIS_ZOOM);
            break;
        default:
            break;
    }
}


void vtkInteractorStylePlot::EndOutlineZoom()
{
    if (this->State != VTKIS_OUTLINEZOOM)
    {
        return;
    }

    if (CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
    {
        double zoomBounds[6];
        this->OutlineSource->GetBounds(zoomBounds);
        // Only zoom if the axis of the zoombox are not zero
        if (zoomBounds[0] != zoomBounds[1] && zoomBounds[2] != zoomBounds[3])
        {
            double newRange[2];
            double *range;
            if (zoomBounds[0] > zoomBounds[1])
            {
                double temp = zoomBounds[0];
                zoomBounds[0] = zoomBounds[1];
                zoomBounds[1] = temp;
            }
            if (zoomBounds[2] > zoomBounds[3])
            {
                double temp = zoomBounds[2];
                zoomBounds[2] = zoomBounds[3];
                zoomBounds[3] = temp;
            }
            range = this->CurrentPlotActor->GetXRange();
            newRange[0] = zoomBounds[0];
            vtkPlotData::ViewportToData(newRange[0], this->ViewportBounds,
                                        range, this->CurrentPlotActor->GetLogX());
            newRange[1] = zoomBounds[1];
            vtkPlotData::ViewportToData(newRange[1], this->ViewportBounds,
                                        range, this->CurrentPlotActor->GetLogX());
            this->CurrentPlotActor->SetXRange(newRange);
            range = this->CurrentPlotActor->GetYRange();
            newRange[0] = zoomBounds[2];
            vtkPlotData::ViewportToData(newRange[0], &(this->ViewportBounds[2]),
                                        range, this->CurrentPlotActor->GetLogY());
            newRange[1] = zoomBounds[3];
            vtkPlotData::ViewportToData(newRange[1], &(this->ViewportBounds[2]),
                                        range, this->CurrentPlotActor->GetLogY());
            this->CurrentPlotActor->SetYRange(newRange);
        }
        this->CurrentRenderer->RemoveActor2D(this->OutlineActor);
        this->Interactor->Render();
    }
    this->StopState();
}


void vtkInteractorStylePlot::OnChar()
{
    // Completely overrule the default key behaviour of vtkInteractorStyle
    char keycode = this->Interactor->GetKeyCode();

    switch (keycode)
    {
        case 'Q':
        case 'q':
        case 'E':
        case 'e':
            this->Interactor->ExitCallback();
            break;
        case 'R':
        case 'r':                                 // Reset the pan and zoom values
            this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
                this->Interactor->GetEventPosition()[1]);
            // Only allow resetting if we are not panning/zooming.
            if (this->CurrentPlotActor && this->State == VTKIS_START)
            {
                double range[2];
                this->CurrentPlotActor->GetDataXRange(range);
                this->CurrentPlotActor->SetXRange(range);
                this->CurrentPlotActor->GetDataYRange(range);
                this->CurrentPlotActor->SetYRange(range);
                this->Interactor->Render();
            }
            break;
        case 'U':
        case 'u':
            this->Interactor->UserCallback();
            break;
        case 'A':
        case 'a':                                 // Adjust labels on axes to 'nice' range
            this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
                this->Interactor->GetEventPosition()[1]);
            if (this->CurrentPlotActor && this->State == VTKIS_START)
            {
                switch (this->CurrentPlotElement)
                {
                    case VTKIS_Plot_X_AXIS:
                        if (keycode == 'A')
                        {
                            this->CurrentPlotActor->ZoomToInnerXRange();
                        }
                        else
                        {
                            this->CurrentPlotActor->ZoomToOuterXRange();
                        }
                        this->Interactor->Render();
                        break;
                    case VTKIS_Plot_Y_AXIS:
                        if (keycode == 'A')
                        {
                            this->CurrentPlotActor->ZoomToInnerYRange();
                        }
                        else
                        {
                            this->CurrentPlotActor->ZoomToOuterYRange();
                        }
                        this->Interactor->Render();
                        break;
                    case VTKIS_Plot_PLOT_AREA:
                        if (keycode == 'A')
                        {
                            this->CurrentPlotActor->ZoomToInnerXRange();
                            this->CurrentPlotActor->ZoomToInnerYRange();
                        }
                        else
                        {
                            this->CurrentPlotActor->ZoomToOuterXRange();
                            this->CurrentPlotActor->ZoomToOuterYRange();
                        }
                        this->Interactor->Render();
                        break;
                    default:
                        break;
                }
            }
            break;
        case 'L':
        case 'l':                                 // Switch on/off logarithmic axes
            this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
                this->Interactor->GetEventPosition()[1]);
            if (this->CurrentPlotActor && this->State == VTKIS_START)
            {
                switch (this->CurrentPlotElement)
                {
                    case VTKIS_Plot_X_AXIS:
                        this->CurrentPlotActor->SetLogX(!this->CurrentPlotActor->GetLogX());
                        this->Interactor->Render();
                        break;
                    case VTKIS_Plot_Y_AXIS:
                        this->CurrentPlotActor->SetLogY(!this->CurrentPlotActor->GetLogY());
                        this->Interactor->Render();
                        break;
                    default:
                        break;
                }
            }
            break;
        default:
            break;
    }
}


void vtkInteractorStylePlot::OnTimer()
{
    switch (this->State)
    {
        case VTKIS_PAN:
            this->Pan();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
        case VTKIS_OUTLINEZOOM:
            this->OutlineZoom();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
        case VTKIS_ZOOM:
            this->Zoom();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
        case VTKIS_TIMER:
            this->Interactor->Render();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
    }
}


void vtkInteractorStylePlot::OnLeftButtonDown()
{
    this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
        this->Interactor->GetEventPosition()[1]);

    if (this->CurrentPlotActor)
    {
        if (this->Interactor->GetControlKey())
        {
            if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
            {
                this->StartZoom();
            }
        }
        else
        {
            if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
            {
                this->StartPan();
            }
        }
    }
}


void vtkInteractorStylePlot::OnLeftButtonUp()
{
    if (this->CurrentPlotActor)
    {
        if (this->Interactor->GetControlKey())
        {
            if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
            {
                this->EndZoom();
            }
        }
        else
        {
            if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
                this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
            {
                this->EndPan();
            }
        }
    }
}


void vtkInteractorStylePlot::OnMiddleButtonDown()
{
    this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
        this->Interactor->GetEventPosition()[1]);

    if (this->CurrentPlotActor)
    {
        if (this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
        {
            this->StartOutlineZoom();
        }
    }
}


void vtkInteractorStylePlot::OnMiddleButtonUp()
{
    if (this->CurrentPlotActor)
    {
        if (this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
        {
            this->EndOutlineZoom();
        }
    }
}


void vtkInteractorStylePlot::OnRightButtonDown()
{
    this->FindPokedPlotActor(this->Interactor->GetEventPosition()[0],
        this->Interactor->GetEventPosition()[1]);

    if (this->CurrentPlotActor)
    {
        if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
            this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
            this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
        {
            this->StartZoom();
        }
    }
}


void vtkInteractorStylePlot::OnRightButtonUp()
{
    if (this->CurrentPlotActor)
    {
        if (this->CurrentPlotElement == VTKIS_Plot_X_AXIS ||
            this->CurrentPlotElement == VTKIS_Plot_Y_AXIS ||
            this->CurrentPlotElement == VTKIS_Plot_PLOT_AREA)
        {
            this->EndZoom();
        }
    }
}


void vtkInteractorStylePlot::PrintSelf(ostream& os, vtkIndent indent)
{
    vtkInteractorStyle::PrintSelf(os,indent);

    os << indent << "CurrentPlotActor: " << this->CurrentPlotActor << endl;
    os << indent << "CurrentPlotElement: " << this->CurrentPlotElement << endl;
    os << indent << "ZoomStartPos: (" << this->ZoomStartPos[0] << ", " << this->ZoomStartPos[1] << ")" << endl;
    os << indent << "PrevPos: (" << this->PrevPos[0] << ", " << this->PrevPos[1] << ")" << endl;
    os << indent << "ViewportBounds: (" << this->ViewportBounds[0] << ", " << this->ViewportBounds[1] << ", " <<
        this->ViewportBounds[2] << ", " << this->ViewportBounds[3] << ")" << endl;
}

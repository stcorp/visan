//
// Copyright (C) 2002-2020 S[&]T, The Netherlands.
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

#include "vtkInteractorStyleWorldPlot2D.h"

#include "vtkActor2D.h"
#include "vtkCommand.h"
#include "vtkCoordinate.h"
#include "vtkIndent.h"
#include "vtkMath.h"
#include "vtkObjectFactory.h"
#include "vtkOutlineSource.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkProperty2D.h"
#include "vtkRenderer.h"
#include "vtkRenderWindowInteractor.h"
#include "vtkTransformCollection.h"

vtkStandardNewMacro(vtkInteractorStyleWorldPlot2D);

vtkInteractorStyleWorldPlot2D::vtkInteractorStyleWorldPlot2D()
{
    this->UseTimers = 1;

    this->Size[0] = 1.0;
    this->Size[1] = 1.0;
    this->MidPoint[0] = 0.5;
    this->MidPoint[1] = 0.5;

    this->RatioVector[0] = 1.0;
    this->RatioVector[1] = 1.0;

    this->OutlineActor = nullptr;
    this->OutlineSource = vtkSmartPointer<vtkOutlineSource>::New();

    this->ViewportSize[0] = 1;
    this->ViewportSize[1] = 1;

    this->dataRatio = 1.0;
    this->zoomScale = 1.0;

    this->DefaultZoom = 1.0;

    this->TransformCollection = vtkSmartPointer<vtkTransformCollection>::New();

    this->AutoAdjustCameraClippingRangeOn();
}

void vtkInteractorStyleWorldPlot2D::SetTransformCollection(vtkTransformCollection *collection)
{
    if (collection != nullptr)
    {
        collection->Register(this);
        if (this->TransformCollection != nullptr)
        {
            TransformCollection->UnRegister(this);
        }
        this->TransformCollection = collection;
    }
}

vtkTransformCollection *vtkInteractorStyleWorldPlot2D::GetTransformCollection()
{
    return this->TransformCollection;
}

void vtkInteractorStyleWorldPlot2D::SetViewParameters(int width, int height, double xyRatio, double zoomScale,
                                                      double viewMidPointX, double viewMidPointY)
{
    this->ViewportSize[0] = width;
    this->ViewportSize[1] = height;
    this->dataRatio = xyRatio;                    // x/y

    // The Size is ALWAYS a zoomScale multiple of the RatioVector.

    this->RatioVector[0] = ((double)ViewportSize[1]) / ViewportSize[0];
    this->RatioVector[1] = this->dataRatio;

    // set the zoom scale
    if (zoomScale < 1.0)
    {
        this->zoomScale = 1.0;
    }
    else
    {
        this->zoomScale = zoomScale;
    }

    this->Size[0] = this->zoomScale * this->RatioVector[0] * this->dataRatio;
    this->Size[1] = this->zoomScale * this->RatioVector[1] * this->dataRatio;;

    this->SetViewMidPoint(viewMidPointX,viewMidPointY);
}

void vtkInteractorStyleWorldPlot2D::SetViewMidPoint(double x, double y)
{
    this->MidPoint[0] = 0.5 - this->Size[0] * (x - 0.5);
    this->MidPoint[1] = 0.5 - this->Size[1] * (y - 0.5);

    // clamp the view
    if (this->minX() > 0.5)
    {
        this->MidPoint[0] -= this->minX() - 0.5;
    }
    if (this->maxX() < 0.5)
    {
        this->MidPoint[0] += 0.5 - this->maxX();
    }
    if (this->minY() > 0.5)
    {
        this->MidPoint[1] -= this->minY() - 0.5;
    }
    if (this->maxY() < 0.5)
    {
        this->MidPoint[1] += 0.5 - this->maxY();
    }

    this->SetTransformation();
}

void vtkInteractorStyleWorldPlot2D::GetViewMidPoint(double &x, double &y)
{
    x = this->GetViewMidPointX();
    y = this->GetViewMidPointY();
}

double vtkInteractorStyleWorldPlot2D::GetViewMidPointX()
{
    return 0.5 - (this->MidPoint[0] - 0.5) / this->Size[0];
}

double vtkInteractorStyleWorldPlot2D::GetViewMidPointY()
{
    return 0.5 - (this->MidPoint[1] - 0.5) / this->Size[1];
}

void vtkInteractorStyleWorldPlot2D::SetViewZoom(double zoomScale)
{
    if (zoomScale != this->zoomScale)
    {
        double tmpX, tmpY;

        if (zoomScale < 1.0)
        {
            this->zoomScale = 1.0;
        }
        else
        {
            this->zoomScale = zoomScale;
        }

        // try and preserve the current window center
        tmpX = 0.5 + (0.5 - this->MidPoint[0]) / this->Size[0];
        tmpY = 0.5 + (0.5 - this->MidPoint[1]) / this->Size[1];

        this->Size[0] = this->zoomScale * this->RatioVector[0];
        this->Size[1] = this->zoomScale * this->RatioVector[1];

        SetViewMidPoint(tmpX, tmpY);
    }
}

double vtkInteractorStyleWorldPlot2D::GetViewZoom()
{
    return this->zoomScale;
}

void vtkInteractorStyleWorldPlot2D::SetViewportSizeAndDataXYRatio(int width, int height, double xyRatio)
{
    vtkDebugMacro(<< "Setting Viewport Size  to:" << width << "," << height);

    this->ViewportSize[0] = width;
    this->ViewportSize[1] = height;

    this->dataRatio = xyRatio;

    // Set the RatioVector. This represents the size of the
    // full projection in "normalized projection" units, and one of
    // the elements of this vector is 1.0 (the limiting dimension)
    // The other will be smaller than (or equal to) 1.0.
    // The Size is ALWAYS a zoomScale multiple of the RatioVector.

    this->RatioVector[0] = ((double)ViewportSize[1]) / ViewportSize[0];
    this->RatioVector[1] = this->dataRatio;

    SetViewZoom(this->zoomScale);
}

void vtkInteractorStyleWorldPlot2D::SetTransformation()
{
    vtkTransform *transform;

    this->TransformCollection->InitTraversal();
    while ((transform = this->TransformCollection->GetNextItem()))
    {
        transform->Identity();
        transform->Translate(this->minX(), this->minY(), 0);
        transform->Scale(this->Size[0], this->Size[1], 0);
    }
    this->InvokeEvent("WorldViewChanged");
}

double vtkInteractorStyleWorldPlot2D::maxX()
{
    return this->MidPoint[0] + this->Size[0] / 2;
}

double vtkInteractorStyleWorldPlot2D::minX()
{
    return this->MidPoint[0] - this->Size[0] / 2;
}

double vtkInteractorStyleWorldPlot2D::maxY()
{
    return this->MidPoint[1] + this->Size[1] / 2;
}

double vtkInteractorStyleWorldPlot2D::minY()
{
    return this->MidPoint[1] - this->Size[1] / 2;
}

void vtkInteractorStyleWorldPlot2D::StartOutlineZoom()
{
    double color[3];
    vtkPolyDataMapper2D *outlineMapper;
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);
    this->FindPokedRenderer(x, y);

    vtkDebugMacro(<< "Starting Outline Zoom");

    if (this->State != VTKIS_START)
    {
        return;
    }

    this->OutlineSource = vtkSmartPointer<vtkOutlineSource>::New();
    this->OutlineSource->SetBounds(x, x, y, y, 0, 0);

    outlineMapper = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    outlineMapper->SetInputConnection(this->OutlineSource->GetOutputPort());

    this->OutlineActor = vtkSmartPointer<vtkActor2D>::New();
    this->OutlineActor->SetMapper(outlineMapper);

    this->CurrentRenderer->GetBackground(color);
    color[0] = 1.0 - color[0];
    color[1] = 1.0 - color[1];
    color[2] = 1.0 - color[2];

    this->OutlineActor->GetProperty()->SetColor(color);
    this->OutlineActor->GetProperty()->SetLineStipplePattern(0xCCCC);

    this->CurrentRenderer->AddActor2D(this->OutlineActor);

    this->StartPos[0] = x;
    this->StartPos[1] = y;

    this->PrevPos[0] = x;
    this->PrevPos[1] = y;

    this->StartState(VTKIS_OUTLINEZOOM);
}

void vtkInteractorStyleWorldPlot2D::EndOutlineZoom()
{
    double bounds[6];

    if (this->State != VTKIS_OUTLINEZOOM)
    {
        return;
    }

    this->OutlineSource->GetBounds(bounds);

    if (bounds[0] != bounds[1] && bounds[2] != bounds[3])
    {
        double factor;
        double mPoint[2];
        double viewCenter[2];

        this->CurrentRenderer->RemoveActor2D(this->OutlineActor);
        this->OutlineActor = nullptr;

        // scale to fractions of the viewport
        bounds[0] /= this->ViewportSize[0];
        bounds[1] /= this->ViewportSize[0];
        bounds[2] /= this->ViewportSize[1];
        bounds[3] /= this->ViewportSize[1];

        // multiplicative scale length - both scales were constrained to be the same
        factor = 1.0 / fabs(bounds[1] - bounds[0]);

        // center of the zoom box in window fraction
        mPoint[0] = (bounds[0] + bounds[1]) / 2.0;
        mPoint[1] = (bounds[2] + bounds[3]) / 2.0;

        // compute the view center point (in normalized projection units)
        viewCenter[0] = 0.5 - (this->MidPoint[0] - mPoint[0]) / this->Size[0];
        viewCenter[1] = 0.5 - (this->MidPoint[1] - mPoint[1]) / this->Size[1];

        // resize (and adjust the Zoom)
        this->Size[0] *= factor;
        this->Size[1] *= factor;
        this->zoomScale *= factor;

        this->SetViewMidPoint(viewCenter[0], viewCenter[1]);
    }
    this->StopState();
    this->Interactor->Render();
}

void vtkInteractorStyleWorldPlot2D::Pan()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    if (x != this->PrevPos[0] || y != this->PrevPos[1])
    {
        double deltaX = x - this->PrevPos[0];     // +ve left
        double deltaY = y - this->PrevPos[1];     // +ve up
        double tmpMidpoint;
        bool updated = false;

        // change in terms of fractions of the visible range - this is the
        // intended increase in the mipoint.
        deltaX /= this->ViewportSize[0];
        deltaY /= this->ViewportSize[1];

        // only pan x when a point in the extent stays in the center of the window.
        tmpMidpoint = this->MidPoint[0];
        this->MidPoint[0] += deltaX;
        if (this->minX() > 0.5)
            this->MidPoint[0] -= this->minX() - 0.5;
        if (this->maxX() < 0.5)
            this->MidPoint[0] += 0.5 - this->maxX();
        updated = (tmpMidpoint != this->MidPoint[0]);

        // only pan y when y-border stays within window
        tmpMidpoint = this->MidPoint[1];
        this->MidPoint[1] += deltaY;
        if (this->minY() > 0.5)
            this->MidPoint[1] -= this->minY() - 0.5;
        if (this->maxY() < 0.5)
            this->MidPoint[1] += 0.5 - this->maxY();
        updated = (tmpMidpoint != this->MidPoint[1]);

        if (updated)
        {
            this->SetTransformation();
            this->Interactor->Render();
        }
        this->PrevPos[0] = x;
        this->PrevPos[1] = y;
    }
}

void vtkInteractorStyleWorldPlot2D::OutlineZoom()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    if (x != this->PrevPos[0] || y != this->PrevPos[1])
    {
        double fY = ((double)this->ViewportSize[0]) / this->ViewportSize[1];
        double dX = x - this->StartPos[0];
        double dY = y - this->StartPos[1];
        double bounds[6];

        this->OutlineSource->GetBounds(bounds);

        if (fabs(dX / dY) > fY)
        {
            // the box should be larger in HEIGHT, so take x as base and calc y
            if (dY * dX < 0)
            {
                // dy is negative or dx is negative and dy is not (so: dx*fy is negative and shouldn't be
                dY = dX / fY;
                dY *= -1;
            }
            else
            {
                dY = dX / fY;
            }
        }
        else
        {
            // the box should be larger in WIDTH, so take y as base and calc x
            if (dY * dX < 0)
            {
                // dy is negative and dx is not (so: dy*fy is negative and shouldn't be
                dX = dY * fY;
                dX *= -1;
            }
            else
            {
                dX = dY * fY;
            }
        }

        bounds[1] = bounds[0] + dX;
        bounds[3] = bounds[2] + dY;
        this->OutlineSource->SetBounds(bounds);
        this->OutlineSource->Update();

        this->Interactor->Render();

        this->PrevPos[0] = x;
        this->PrevPos[1] = y;
    }
}

void vtkInteractorStyleWorldPlot2D::Zoom()
{
    int x;
    int y;

    this->Interactor->GetEventPosition(x, y);

    if (y != this->StartPos[1])
    {
        double factor;

        factor = 1.0 + ((double)(y - this->StartPos[1])) / this->ViewportSize[1];
        // clamp it
        if (factor > 1.25)
        {
            factor = 1.25;
        }
        else if (factor < 1.0/1.25)
        {
            factor = 1.0/1.25;
        }

        factor *= this->zoomScale;                // increase or decrease the zoom factor

        // make an attempt to preserve the view center point

        SetViewZoom(factor);
        this->Interactor->Render();
    }
}

void vtkInteractorStyleWorldPlot2D::StartPan()
{
    int x;
    int y;

    if (this->State != VTKIS_START)
    {
        return;
    }

    vtkDebugMacro(<< "Starting Pan");

    this->Interactor->GetEventPosition(x, y);

    this->PrevPos[0] = x;
    this->PrevPos[1] = y;

    this->StartState(VTKIS_PAN);
}

void vtkInteractorStyleWorldPlot2D::StartZoom()
{
    int x;
    int y;

    if (this->State != VTKIS_START)
    {
        return;
    }

    vtkDebugMacro(<< "Starting Zoom");

    this->Interactor->GetEventPosition(x, y);

    this->StartPos[0] = x;
    this->StartPos[1] = y;

    this->StartState(VTKIS_ZOOM);
}

void vtkInteractorStyleWorldPlot2D::OnChar()
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
        case 'r':
            // Reset the pan and zoom values
            // Only allow resetting if we are not panning/zooming.
            if (this->State == VTKIS_START)
            {
                this->MidPoint[0] = 0.5;
                this->MidPoint[1] = 0.5;
                SetViewZoom(this->DefaultZoom);
                this->Interactor->Render();
            }
            break;
        case 'U':
        case 'u':
            this->Interactor->UserCallback();
            break;
        default:
            break;
    }
}

void vtkInteractorStyleWorldPlot2D::OnTimer()
{
    switch (this->State)
    {
        case VTKIS_PAN:
            this->Pan();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
        case VTKIS_ZOOM:
            this->Zoom();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
        case VTKIS_OUTLINEZOOM:
            this->OutlineZoom();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
        case VTKIS_TIMER:
            this->Interactor->Render();
            this->Interactor->CreateTimer(VTKI_TIMER_UPDATE);
            break;
    }
}

void vtkInteractorStyleWorldPlot2D::OnLeftButtonDown()
{
    if (this->Interactor->GetControlKey())
    {
        this->StartZoom();
    }
    else
    {
        this->StartPan();
    }
}

void vtkInteractorStyleWorldPlot2D::OnLeftButtonUp()
{
    switch (this->State)
    {
        case VTKIS_ZOOM:
            this->EndZoom();
            break;
        case VTKIS_PAN:
            this->EndPan();
            break;
    }
}

void vtkInteractorStyleWorldPlot2D::OnRightButtonDown()
{
    this->StartZoom();
}

void vtkInteractorStyleWorldPlot2D::OnRightButtonUp()
{
    this->EndZoom();
}

void vtkInteractorStyleWorldPlot2D::OnMiddleButtonDown()
{
    this->StartOutlineZoom();
}

void vtkInteractorStyleWorldPlot2D::OnMiddleButtonUp()
{
    this->EndOutlineZoom();
}

void vtkInteractorStyleWorldPlot2D::PrintSelf(ostream& os, vtkIndent indent)
{
    vtkInteractorStyle::PrintSelf(os,indent);

    os << indent << "MidPoint: (" << this->MidPoint[0] << ", " << this->MidPoint[1] << ")" << endl;
    os << indent << "PrevPos: (" << this->PrevPos[0] << ", " << this->PrevPos[1] << ")" << endl;
    os << indent << "RatioVector: (" << this->RatioVector[0] << ", " << this->RatioVector[1] << ")" << endl;
    os << indent << "Size: (" << this->Size[0] << ", " << this->Size[1] << ")" << endl;
    os << indent << "StartPos: (" << this->StartPos[0] << ", " << this->StartPos[1] << ")" << endl;
    os << indent << "ViewportSize: (" << this->ViewportSize[0] << ", " << this->ViewportSize[1] << ")" << endl;
}

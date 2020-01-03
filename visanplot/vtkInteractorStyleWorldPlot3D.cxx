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

#include "vtkInteractorStyleWorldPlot3D.h"

#include "vtkCamera.h"
#include "vtkCommand.h"
#include "vtkMath.h"
#include "vtkObjectFactory.h"
#include "vtkRenderer.h"
#include "vtkRenderWindow.h"
#include "vtkRenderWindowInteractor.h"

vtkStandardNewMacro(vtkInteractorStyleWorldPlot3D);

static inline void clipMin(double &x, double min)
{
    if (x < min)
    {
        x = min;
    }
}

static inline void clipMax(double &x, double max)
{
    if (x > max)
    {
        x = max;
    }
}

static inline void clipWrap(double &x, double min, double max)
{
    x = fmod(x - min, max - min);

    if (x < 0)
    {
        x += max;
    }
    else
    {
        x += min;
    }
}

static void latlon2position(double latitude, double longitude, double position[3])
{
    // convert degrees to radians
    double theta = latitude * 0.017453292519943295;
    double phi = longitude * 0.017453292519943295;

    // Convert spherical coordinates to cartesian coordinates
    position[0] = cos(phi) * cos(theta);
    position[1] = sin(phi) * cos(theta);
    position[2] = sin(theta);
}

vtkInteractorStyleWorldPlot3D::vtkInteractorStyleWorldPlot3D()
{
    // Start in trackball mode
    this->UseTimers = 0;

    this->MotionSpeed = 1.5;

    this->FactorRoll =  50.0;

    this->SetDefaultViewParameters(0.0, 0.0, 0.0, 1.0);
    this->SetDefaultView();
}

void vtkInteractorStyleWorldPlot3D::OnChar()
{
    // Overrule the default key behavior of vtkInteractorStyle
    char keycode = this->Interactor->GetKeyCode();

    switch (keycode)
    {
        case 'T':
        case 't':
            // Switch to trackball mode
            this->UseTimers = 0;
            break;

        case 'J':
        case 'j':
            // switch to joystick mode
            this->UseTimers = 1;
            break;

        case 'R':
        case 'r':
            // Only allow resetting when we are not interacting
            if (this->State == VTKIS_START)
            {
                this->SetDefaultView();
                this->Interactor->Render();
            }
            break;

        case 'Q':
        case 'q':
        case 'U':
        case 'u':
        case 'W':
        case 'w':
        case 'S':
        case 's':
            // Use default behavior defined in parent class
            vtkInteractorStyle::OnChar();
            break;

        default:
            break;
    }
}

void vtkInteractorStyleWorldPlot3D::OnMouseMove()
{
    int x = this->Interactor->GetEventPosition()[0];
    int y = this->Interactor->GetEventPosition()[1];

    switch (this->State)
    {
        case VTKIS_PAN:
            this->FindPokedRenderer(x, y);
            this->Pan();
            this->InvokeEvent(vtkCommand::InteractionEvent, nullptr);
            break;

        case VTKIS_DOLLY:
            this->FindPokedRenderer(x, y);
            this->Dolly();
            this->InvokeEvent(vtkCommand::InteractionEvent, nullptr);
            break;

        case VTKIS_ROTATE:
            this->FindPokedRenderer(x, y);
            this->Rotate();
            this->InvokeEvent(vtkCommand::InteractionEvent, nullptr);
            break;
    }
}

void vtkInteractorStyleWorldPlot3D::OnLeftButtonDown()
{
    this->FindPokedRenderer(this->Interactor->GetEventPosition()[0], this->Interactor->GetEventPosition()[1]);
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    if (this->Interactor->GetShiftKey())
    {
        if (this->Interactor->GetControlKey())
        {
            this->StartRotate();
        }
        else
        {
            this->StartDolly();
        }
    }
    else
    {
        this->StartPan();
    }
}

void vtkInteractorStyleWorldPlot3D::OnLeftButtonUp()
{
    switch (this->State)
    {
        case VTKIS_DOLLY:
            this->EndDolly();
            break;
        case VTKIS_PAN:
            this->EndPan();
            break;
        case VTKIS_ROTATE:
            this->EndRotate();
            break;
    }
}

void vtkInteractorStyleWorldPlot3D::OnMiddleButtonDown()
{
    this->FindPokedRenderer(this->Interactor->GetEventPosition()[0], this->Interactor->GetEventPosition()[1]);
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    this->StartRotate();
}

void vtkInteractorStyleWorldPlot3D::OnMiddleButtonUp()
{
    switch (this->State)
    {
        case VTKIS_ROTATE:
            this->EndRotate();
            break;
    }
}

void vtkInteractorStyleWorldPlot3D::OnRightButtonDown()
{
    this->FindPokedRenderer(this->Interactor->GetEventPosition()[0], this->Interactor->GetEventPosition()[1]);
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    this->StartDolly();
}

void vtkInteractorStyleWorldPlot3D::OnRightButtonUp()
{
    switch (this->State)
    {
        case VTKIS_DOLLY:
            this->EndDolly();
            break;
    }
}

void vtkInteractorStyleWorldPlot3D::getMouseMotion(double &dx, double &dy)
{
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    if (this->GetUseTimers() == 1)
    {
        // When in joystick mode, use motion relative to window center
        double *center = this->CurrentRenderer->GetCenter();

        dx = (double)(this->Interactor->GetEventPosition()[0] - center[0]) / 10.0;
        dy = (double)(this->Interactor->GetEventPosition()[1] - center[1]) / 10.0;
    }
    else
    {
        // When in trackball mode, use motion relative to last position
        dx = (double)(this->Interactor->GetEventPosition()[0] - this->Interactor->GetLastEventPosition()[0]);
        dy = (double)(this->Interactor->GetEventPosition()[1] - this->Interactor->GetLastEventPosition()[1]);
    }
}

void vtkInteractorStyleWorldPlot3D::Pan()
{
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    // Retrieve mouse motion
    double dx, dy = 0.0;
    getMouseMotion(dx, dy);

    // Determine pan speed
    int *size = this->CurrentRenderer->GetRenderWindow()->GetSize();

    // Panning acts as though the cursor is moving the earth as if it was a trackball (ie.
    // based on the tangent at the surface). The scale is defined by the window height and the
    // camera projection scheme. This is because the FoV is defiend in the vertical plane.

    // map a pixel to a tangent scale on the earth in earth-radius units.
    double speed = 2.0 * 3.0 / (this->Zoom * (double)size[1]);

    // Set the camera view
    if (this->GetUseTimers() == 1)
    {
        // Use reversed panning in joystick mode!
        // This behavior may seem counterintuitive when zoomed out, but it is very intuitive when zoomed in.
        this->Latitude  += 57.29577951 * dy * speed;
        this->Longitude += 57.29577951 * dx * speed;
    }
    else
    {
        // this SHOULD be 180/pi atan(dy*speed), but consider atan(x) ~= x
        this->Latitude  -= 57.29577951 * dy * speed;
        this->Longitude -= 57.29577951 * dx * speed;
    }
    this->SetView();
    this->Interactor->Render();
}

void vtkInteractorStyleWorldPlot3D::Rotate()
{
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    // Retrieve mouse motion
    double dx, dy = 0.0;
    getMouseMotion(dx, dy);

    // Determine roll speed
    double *center = this->CurrentRenderer->GetCenter();
    double rollSpeed = this->FactorRoll * this->MotionSpeed / (double)center[1];

    // Set the camera view
    this->Roll -= (dy * rollSpeed);
    this->SetView();
    this->Interactor->Render();
}

void vtkInteractorStyleWorldPlot3D::Dolly()
{
    if (this->CurrentRenderer == nullptr)
    {
        return;
    }

    // Retrieve mouse motion
    double dx, dy = 0.0;
    getMouseMotion(dx, dy);

    // Determine zoom speed
    double *center = this->CurrentRenderer->GetCenter();
    double zoomSpeed = this->MotionSpeed * this->Zoom / (double)center[1];

    // Set the camera view - this is not actually a Dolly, but this hijacks the
    // Dolly interation scheme. This is done to prevent the camera from being
    // moved inside the earth.
    this->Zoom += (dy * zoomSpeed);
    this->SetView();
    this->Interactor->Render();
}

void vtkInteractorStyleWorldPlot3D::Modified()
{
    vtkInteractorStyle::Modified();

    this->SetView();
}

void vtkInteractorStyleWorldPlot3D::SetDefaultViewParameters(double latitude, double longitude, double roll, double zoom)
{
    this->DefaultLatitude = latitude;
    this->DefaultLongitude = longitude;
    this->DefaultRoll = roll;
    this->DefaultZoom = zoom;
}

void vtkInteractorStyleWorldPlot3D::GetDefaultViewParameters(double &latitude, double &longitude, double &roll, double &zoom)
{
    latitude = this->DefaultLatitude;
    longitude = this->DefaultLongitude;
    roll = this->DefaultRoll;
    zoom = this->DefaultZoom;
}

void vtkInteractorStyleWorldPlot3D::SetDefaultView()
{
    this->Latitude = this->DefaultLatitude;
    this->Longitude = this->DefaultLongitude;
    this->Roll = this->DefaultRoll;
    this->Zoom = this->DefaultZoom;

    this->SetView();
}

void vtkInteractorStyleWorldPlot3D::SetViewParameters(double latitude, double longitude, double roll, double zoom)
{
    this->Latitude = latitude;
    this->Longitude = longitude;
    this->Roll = roll;
    this->Zoom = zoom;

    this->SetView();
}

void vtkInteractorStyleWorldPlot3D::GetViewParameters(double &latitude, double &longitude, double &roll, double &zoom)
{
    latitude = this->Latitude;
    longitude = this->Longitude;
    roll = this->Roll;
    zoom = this->Zoom;
}

double vtkInteractorStyleWorldPlot3D::GetViewCenterLatitude()
{
    return this->Latitude;
}

double vtkInteractorStyleWorldPlot3D::GetViewCenterLongitude()
{
    return this->Longitude;
}

double vtkInteractorStyleWorldPlot3D::GetViewZoom()
{
    return this->Zoom;
}

void vtkInteractorStyleWorldPlot3D::SetView()
{
    vtkRenderer *renderer = this->CurrentRenderer;
    if (renderer == nullptr)
    {
        return;
    }

    // Restrict input values to proper range
    // longitude in [-180.0, +180.0)
    clipWrap(this->Longitude, -180.0, +180.0);
    // latitude in (-90.0, +90.0)
    clipMin(this->Latitude, -89.999);
    clipMax(this->Latitude, +89.999);
    // roll in [-180.0, +180.0)
    clipMin(this->Roll, -180.0);
    clipMax(this->Roll, +180.0);
    // zoom in [+1.0, -->)
    clipMin(this->Zoom, 1.0);

    // Set default camera viewUp
    const double viewUp[3] = {0.0, 0.0, 1.0};

    // Determine the (x, y, z) position on the surface from (latitude, longitude)
    double positionSurface[3];
    latlon2position(0.0, this->Longitude, positionSurface);

    // Position the camera so that it hovers above the unit sphere
    // The distance chosen makes the entire sphere visible
    double positionCamera[3];
    for (int i = 0; i < 3; i++)
    {
        positionCamera[i] = positionSurface[i] * 4.0;
    }

    // Reposition the camera so it hovers above the unit sphere and looks at the origin
    vtkCamera *camera = renderer->GetActiveCamera();
    camera->SetViewUp(viewUp);
    camera->SetPosition(positionCamera);
    camera->Roll(this->Roll);
    camera->Elevation(this->Latitude);

    // approx 73 degrees at Zoom = 1.0
    double angle = 57.29577951 * 2.0 * atan(0.75 / this->Zoom);

    camera->SetViewAngle(angle);

    // Adjust camera parameters
    if (this->AutoAdjustCameraClippingRange)
    {
        renderer->ResetCameraClippingRange();
    }

    if (this->Interactor == nullptr)
    {
        return;
    }

    if (this->Interactor->GetLightFollowCamera())
    {
        renderer->UpdateLightsGeometryToFollowCamera();
    }

    // Post and event to the renderWindowInteractor
    this->InvokeEvent("WorldViewChanged");
};

void vtkInteractorStyleWorldPlot3D::PrintSelf(ostream& os, vtkIndent indent)
{
    vtkInteractorStyle::PrintSelf(os,indent);

    os << indent << "Latitude: " << this->Latitude << endl;
    os << indent << "Longitude: " << this->Longitude << endl;
    os << indent << "Roll: " << this->Roll << endl;
    os << indent << "Zoom: " << this->Zoom << endl;

    os << indent << "DefaultLatitude: " << this->DefaultLatitude << endl;
    os << indent << "DefaultLongitude: " << this->DefaultLongitude << endl;
    os << indent << "DefaultRoll: " << this->DefaultRoll << endl;
    os << indent << "DefaultZoom: " << this->DefaultZoom << endl;

    os << indent << "MotionSpeed: " << this->MotionSpeed << endl;
    os << indent << "FactorRoll: " << this->FactorRoll << endl;
}

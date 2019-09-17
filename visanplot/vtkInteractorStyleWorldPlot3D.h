//
// Copyright (C) 2002-2019 S[&]T, The Netherlands.
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

#ifndef __vtkInteractorStyleWorldPlot3D_h
#define __vtkInteractorStyleWorldPlot3D_h

#include "vtkInteractorStyle.h"

class vtkInteractorStyleWorldPlot3D : public vtkInteractorStyle
{
    public:
        vtkTypeMacro(vtkInteractorStyleWorldPlot3D, vtkInteractorStyle);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkInteractorStyleWorldPlot3D *New();

        // Set and get the default view
        void SetDefaultViewParameters(double  latitude, double  longitude, double  roll, double  zoom);
        void GetDefaultViewParameters(double &latitude, double &longitude, double &roll, double &zoom);

        // Set the current view to the default view
        void SetDefaultView();

        // Set and get the current view
        void SetViewParameters(double  latitude, double  longitude, double  roll, double  zoom);
        void GetViewParameters(double &latitude, double &longitude, double &roll, double &zoom);
        double GetViewCenterLatitude();
        double GetViewCenterLongitude();
        double GetViewZoom();

        // Set and get for individual Default view parameters
        vtkSetMacro(DefaultLatitude, double);
        vtkGetMacro(DefaultLatitude, double);

        vtkSetMacro(DefaultLongitude, double);
        vtkGetMacro(DefaultLongitude, double);

        vtkSetMacro(DefaultRoll, double);
        vtkGetMacro(DefaultRoll, double);

        vtkSetMacro(DefaultZoom, double);
        vtkGetMacro(DefaultZoom, double);

        // Set and get for individual current view parameters
        vtkSetMacro(Latitude, double);
        vtkGetMacro(Latitude, double);

        vtkSetMacro(Longitude, double);
        vtkGetMacro(Longitude, double);

        vtkSetMacro(Roll, double);
        vtkGetMacro(Roll, double);

        vtkSetMacro(Zoom, double);
        vtkGetMacro(Zoom, double);

        // The relative speed of all interactor motions
        vtkSetClampMacro(MotionSpeed, double, 0.1, 10.0);
        vtkGetMacro(MotionSpeed, double);

        // Description:
        // Event bindings controlling the effects of pressing mouse buttons
        // or moving the mouse.
        virtual void OnChar() override;
        virtual void OnMouseMove() override;
        virtual void OnRightButtonDown() override;
        virtual void OnRightButtonUp() override;
        virtual void OnMiddleButtonDown() override;
        virtual void OnMiddleButtonUp() override;
        virtual void OnLeftButtonDown() override;
        virtual void OnLeftButtonUp() override;

        // These methods for the different interactions in different modes
        // are overridden in subclasses to perform the correct motion. Since
        // they are called by OnTimer, they do not have mouse coord parameters
        // (use interactor's GetEventPosition and GetLastEventPosition)
        virtual void Pan() override;
        virtual void Dolly() override;
        virtual void Rotate() override;

    protected:
        vtkInteractorStyleWorldPlot3D();

        // Current view parameters
        double Latitude;
        double Longitude;
        double Roll;
        double Zoom;

        // Default view parameters
        double DefaultLatitude;
        double DefaultLongitude;
        double DefaultRoll;
        double DefaultZoom;

        // Speed of all motions
        double MotionSpeed;

        // Speed factor of individual motions
        double FactorRoll;

        // Retrieve mouse motion, both for trackball mode and joystick mode
        void getMouseMotion(double &dx, double &dy);

        // Called by macro setters to set current view
        virtual void Modified() override;

        // Set the current view
        void SetView();

    private:
        vtkInteractorStyleWorldPlot3D(const vtkInteractorStyleWorldPlot3D&) = delete;
        void operator=(const vtkInteractorStyleWorldPlot3D&) = delete;
};
#endif

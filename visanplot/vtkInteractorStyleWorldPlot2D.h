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

#ifndef __vtkInteractorStyleWorldPlot2D_h
#define __vtkInteractorStyleWorldPlot2D_h

#include "vtkInteractorStyle.h"

#include "vtkSmartPointer.h"

class vtkIndent;
class vtkOutlineSource;
class vtkRenderer;
class vtkTransform;
class vtkTransformCollection;
class vtkActor2D;

// This interactorstyle only uses VTKIS_NONE, VTKIS_ZOOM, VTKIS_PAN

// Define our own VTKIS types
#define VTKIS_OUTLINEZOOM 100

class VTK_EXPORT vtkInteractorStyleWorldPlot2D : public vtkInteractorStyle
{
    public:
        vtkTypeMacro(vtkInteractorStyleWorldPlot2D, vtkInteractorStyle);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkInteractorStyleWorldPlot2D *New();

        // Description:
        // Event bindings controlling the effects of pressing mouse buttons
        // or moving the mouse.
        virtual void OnRightButtonDown() override;
        virtual void OnRightButtonUp() override;
        virtual void OnMiddleButtonDown() override;
        virtual void OnMiddleButtonUp() override;
        virtual void OnLeftButtonDown() override;
        virtual void OnLeftButtonUp() override;
        virtual void OnChar() override;
        virtual void OnTimer() override;

        void SetTransformCollection(vtkTransformCollection *collection);
        vtkTransformCollection *GetTransformCollection();

        void SetViewportSizeAndDataXYRatio(int width, int height, double xyRatio);
        void SetViewParameters(int width, int height, double xyRatio, double zoomScale,
                               double viewMidPointX, double viewMidPointY);
        void SetViewMidPoint(double x, double y);
        void SetViewZoom(double zoomScale);

        void GetViewMidPoint(double &x, double &y);
        double GetViewMidPointX(void);
        double GetViewMidPointY(void);
        double GetViewZoom();

        vtkSetMacro(DefaultZoom, double);
        vtkGetMacro(DefaultZoom, double);

    protected:
        vtkInteractorStyleWorldPlot2D();

        void Pan() override;
        void OutlineZoom();
        void Zoom() override;

        void StartPan() override;
        void StartZoom() override;
        void StartOutlineZoom();
        void EndOutlineZoom();

        void SetTransformation();

        double minX();
        double maxX();
        double minY();
        double maxY();

    protected:

        vtkSmartPointer<vtkTransformCollection> TransformCollection;
        int StartPos[2];
        int PrevPos[2];
        double MidPoint[2];
        double Size[2];
        double ZoomTranslateX;
        double ZoomTranslateY;
        int ViewportSize[2];
        double RatioVector[2];
        double dataRatio, zoomScale;
        double DefaultZoom;

        vtkSmartPointer<vtkOutlineSource> OutlineSource;
        vtkSmartPointer<vtkActor2D> OutlineActor;

    private:
        vtkInteractorStyleWorldPlot2D(const vtkInteractorStyleWorldPlot2D&) = delete;
        void operator=(const vtkInteractorStyleWorldPlot2D&) = delete;
};
#endif

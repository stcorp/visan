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

#ifndef __vtkWorldPlotData_h
#define __vtkWorldPlotData_h

#include "vtkObject.h"
#include "vtkSmartPointer.h"
#include "visanplotModule.h"

class vtkActor;
class vtkActor2D;
class vtkAlgorithmOutput;
class vtkCollection;
class vtkColorTable;
class vtkPolyData;
class vtkProjFilter;
class vtkTransform;

class VISANPLOT_EXPORT vtkWorldPlotData : public vtkObject
{
    public:
        vtkTypeMacro(vtkWorldPlotData,vtkObject);

        static vtkWorldPlotData *New();

        void SetKeyframe(int keyframe);
        int GetNumberOfKeyframes();

        void SetProjection(int projection);
        int GetProjection();

        void SetProjectionCenterLatitude(double latitude);
        void SetProjectionCenterLongitude(double longitude);

        void SetOpacity(double opacity);
        double GetOpacity();

        void SetPointSize(double size);
        double GetPointSize();

        void SetLineWidth(double width);
        double GetLineWidth();

        void SetPlotLabel(const char *label);
        const char *GetPlotLabel();

        void SetColorBarTitle(const char *label);
        const char *GetColorBarTitle();

        void SetNumColorBarLabels(int numLabels);
        int GetNumColorBarLabels();

        // Get/Set the relative height of the data with respect to the earth sphere for 3D plots
        virtual void SetReferenceHeight(double referenceHeight);
        virtual double GetReferenceHeight();

        // Get/Set the scale factor for height plots
        // If the value is 0 (the default) no height information is used
        virtual void SetHeightFactor(double heightFactor)
        {
        }
        virtual double GetHeightFactor()
        {
            return 0.0;
        }

        // Get/Set the height range to use for height plots
        virtual void SetMinHeightValue(double minValue)
        {
        }
        virtual double GetMinHeightValue()
        {
            return 0.0;
        }
        virtual void SetMaxHeightValue(double maxValue)
        {
        }
        virtual double GetMaxHeightValue()
        {
            return 0.0;
        }

        vtkActor2D *GetActor2D();
        vtkActor *GetActor3D();
        vtkTransform *GetTransform();

        double GetXYRatio();

        vtkColorTable *GetColorTable();

    protected:
        vtkWorldPlotData();
        ~vtkWorldPlotData() override;
        void AddInputData(vtkPolyData *input);
        void AddInputConnection(vtkAlgorithmOutput *input);


        char *plotLabel;
        char *colorBarTitle;
        int numColorBarLabels;
        vtkSmartPointer<vtkColorTable> colorTable;
        vtkSmartPointer<vtkTransform> transform;
        vtkSmartPointer<vtkProjFilter> filter;
        vtkSmartPointer<vtkActor2D> actor2D;
        vtkSmartPointer<vtkActor> actor3D;
        vtkSmartPointer<vtkCollection> algorithms;

    private:
        vtkWorldPlotData(const vtkWorldPlotData&) = delete;
        void operator=(const vtkWorldPlotData&) = delete;
};
#endif

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

#ifndef __vtkColorTable_h
#define __vtkColorTable_h

#include "vtkObject.h"
#include "vtkLookupTable.h"
#include "vtkSmartPointer.h"
#include "vtkStdString.h"

#define GRADIENT_INTERPOLATION_MODE_LINEAR 0
#define GRADIENT_INTERPOLATION_MODE_SQRT 1
#define GRADIENT_INTERPOLATION_MODE_SCURVE 2

// TODO: Change the commented-out wx Event to a VTK Command/Observer pattern

// wxWidget includes (for notifications)
//#include "wx/wxprec.h"      // For compilers that support precompilation.
//#include "wx/wx.h"

// Custom events
// DECLARE_LOCAL_EVENT_TYPE(wxEVT_COLORTABLE_CHANGED, -1)

// A color table is defined by a series of gradient edge values and a table size
// The table size is defined using the numTableColors value.
// The gradient edges are defined by a series of colors (RGBA) and positions (0.0 <= x <= 1.0)
// The entries in the color table are then constructed by interpolating between the available gradient edge values
// Interpolation is done such that position 0.0 will correspond with the first color table value and
// position 1.0 with the last color table value. A color table can thus also never have less than 2 elements.

class VTK_EXPORT vtkColorTable : public vtkObject
{
    public:
        vtkTypeMacro(vtkColorTable,vtkObject);

        static vtkColorTable *New();

        vtkLookupTable *GetVTKLookupTable()
        {
            return lut.GetPointer();
        }

        // Defines the range to use to map values to colors
        void SetColorRange(double range[2])
        {
            this->SetColorRange(range[0], range[1]);
        }
        void SetColorRange(double minValue, double maxValue);
        double *GetColorRange() VTK_SIZEHINT(2);
        void GetColorRange(double range[2])
        {
            this->GetColorRange(&range[0], &range[1]);
        }
        void GetColorRange(double *minValue, double *maxValue);

        // The number of entries in the color table
        int GetNumTableColors();
        void SetNumTableColors(int num_colors);

        double *GetTableColor(int index) VTK_SIZEHINT(4);
        void GetTableColor(int index, double *r, double *g, double *b, double *a);

        // A color table is constructed by interpolating between color values at specified relative positions
        // The relative position (x) is a value in the range [0,1].

        // The number of gradient edges
        int GetNumGradientEdges()
        {
            return this->numberOfGradientEdges;
        }

        double *GetGradientEdgeValue(int index) VTK_SIZEHINT(5);
        void GetGradientEdgeValue(int index, double *x, double *r, double *g, double *b, double *a);

        int InsertGradientEdgeValue(double x, double r, double g, double b, double a);
        void SetGradientEdgeValue(int index, double x, double r, double g, double b, double a);
        void RemoveGradientEdgeValue(int index);

        // Possible values are:
        // - Default
        // - BlackToWhite
        // - WhiteToBlack
        // - GreenToRed
        // - RedToGreen
        // - Cloud
        // - Rainbow
        // - Ozone
        // - Blackbody
        // - Aerosol
        void SetColorTableByName(const vtkStdString &name);
        void SetColorTableByName(const char *name);
        // Will return nullptr for custom color tables
        const vtkStdString &GetColorTableName()
        {
            return this->colorTableName;
        }

        // The interpolation mode that is used to interpolate between gradient values
        void SetGradientInterpolationMode(int interpolationMode);
        int GetGradientInterpolationMode()
        {
            return this->interpolationMode;
        }

        void Import(const vtkStdString &filename);
        void Export(const vtkStdString &filename);

    protected:
        vtkColorTable();
        ~vtkColorTable() override;

        void UpdateColorTable();

    private:
        vtkColorTable(const vtkColorTable&) = delete;
        void operator=(const vtkColorTable&) = delete;

        typedef struct
        {
            double x;
            double r;
            double g;
            double b;
            double a;
        } GradientEdge;

        vtkStdString colorTableName;
        int interpolationMode;
        int numberOfGradientEdges;
        GradientEdge *gradientEdge;

        vtkSmartPointer<vtkLookupTable> lut;
};
#endif

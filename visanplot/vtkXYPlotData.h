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

#ifndef __vtkXYPlotData_h
#define __vtkXYPlotData_h

#include "vtkPlotData.h"

class VTK_EXPORT vtkXYPlotData : public vtkPlotData
{
    public:
        vtkTypeMacro(vtkXYPlotData, vtkPlotData);

        static vtkXYPlotData *New();

        void SetKeyframe(int keyframe);
        int GetNumberOfKeyframes();

        void AddData(vtkDoubleArray *xdata, vtkDoubleArray *ydata);

        void GetDataRange(double range[2], int dim) override;
        void GetDataRangeAbove0(double range[2], int dim) override;

        double GetXValue(int i) override
        {
            return this->currentPoints->GetPoint(i)[0];
        }
        double GetYValue(int i) override
        {
            return this->currentPoints->GetPoint(i)[1];
        }
        double GetZValue(int) override
        {
            return 0;
        }
        int GetNumberOfItems() override
        {
            return this->currentPoints->GetNumberOfPoints();
        }

    protected:
        vtkXYPlotData();

    protected:
        double xrange[2];
        double yrange[2];
        double xrangeAbove0[2];
        double yrangeAbove0[2];

        vtkSmartPointer<vtkCollection> pointSet;
        vtkPoints *currentPoints;

    private:
        vtkXYPlotData(const vtkXYPlotData&) = delete;
        void operator=(const vtkXYPlotData&) = delete;
};
#endif

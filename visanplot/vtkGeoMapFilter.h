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

#ifndef __vtkGeoMapFilter_h
#define __vtkGeoMapFilter_h

#include "vtkPolyDataAlgorithm.h"
#include "vtkSmartPointer.h"
#include "visanplotModule.h"

class vtkCellArray;
class vtkDoubleArray;
class vtkPoints;
class vtkPolyData;
class vtkUnsignedCharArray;

class VISANPLOT_EXPORT vtkGeoMapFilter : public vtkPolyDataAlgorithm
{
    public:
        vtkTypeMacro(vtkGeoMapFilter,vtkPolyDataAlgorithm);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkGeoMapFilter *New();

        void SetValues(vtkDoubleArray*);
        vtkDoubleArray *GetValues();

        void SetHeights(vtkDoubleArray*);
        vtkDoubleArray *GetHeights();

        void SetLongitudes(vtkDoubleArray*);
        vtkDoubleArray *GetLongitudes();

        void SetLatitudes(vtkDoubleArray*);
        vtkDoubleArray *GetLatitudes();

        vtkSetMacro(MinMappedValue,double);
        vtkGetMacro(MinMappedValue,double);

        vtkSetMacro(MaxMappedValue,double);
        vtkGetMacro(MaxMappedValue,double);

        vtkSetMacro(Factor,double);
        vtkGetMacro(Factor,double);

        vtkSetMacro(Radius,double);
        vtkGetMacro(Radius,double);

        vtkSetMacro(MapWidth,int);
        vtkGetMacro(MapWidth,int);

        vtkSetMacro(MapHeight,int);
        vtkGetMacro(MapHeight,int);

    protected:
        vtkGeoMapFilter();

        int RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                        vtkInformationVector *outputVector) override;

        vtkSmartPointer<vtkDoubleArray> Values;
        vtkSmartPointer<vtkDoubleArray> Heights;
        vtkSmartPointer<vtkDoubleArray> Longitudes;
        vtkSmartPointer<vtkDoubleArray> Latitudes;
        vtkSmartPointer<vtkUnsignedCharArray> Valid;

        double MinMappedValue;
        double MaxMappedValue;

        double Factor;
        double Radius;

        int MapWidth;
        int MapHeight;

    private:
        vtkGeoMapFilter(const vtkGeoMapFilter&) = delete;
        void operator=(const vtkGeoMapFilter&) = delete;
};
#endif

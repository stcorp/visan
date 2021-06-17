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

#ifndef __vtkGeoGridSource_h
#define __vtkGeoGridSource_h

#include "vtkPolyDataAlgorithm.h"
#include "visanplotModule.h"

class VISANPLOT_EXPORT vtkGeoGridSource : public vtkPolyDataAlgorithm
{
    public:
        vtkTypeMacro(vtkGeoGridSource, vtkPolyDataAlgorithm);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkGeoGridSource *New();

        // Description:
        // Sets the distance (in degrees) between gridlines. The same distance
        // (graticule) is used for meridians and parallels. The default is 30
        // degrees between gridlines.
        // The graticule should be a divisor of 180 or you may get unexpected
        // results.
        vtkSetClampMacro(Graticule, double, 0.001, 90.0);
        vtkGetMacro(Graticule, double);

        // Description:
        // Sets the distance (in degrees) between the points making up a gridline.
        // The default is 1 degree between points.
        // The point distance should be a divisor of 180 or you may get unexpected
        // results.
        vtkSetClampMacro(PointDistance, double, 0.001, 90);
        vtkGetMacro(PointDistance, double);

        // Description:
        // This option determines whether the poles (+90 latitude and -90 latitude)
        // should have parallels.
        // If the graticule is not a divisor of 90 this options will be ignored
        // (since in that case a pole wouldn't have a parallel anyway).
        // By default parallels for poles are created.
        vtkSetMacro(CreateParallelsForPoles, int);
        vtkGetMacro(CreateParallelsForPoles, int);
        vtkBooleanMacro(CreateParallelsForPoles, int);

    protected:
        vtkGeoGridSource();
        int RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                        vtkInformationVector *outputVector) override;

        double Graticule;
        double PointDistance;
        int CreateParallelsForPoles;

    private:
        vtkGeoGridSource(const vtkGeoGridSource&) = delete;
        void operator=(const vtkGeoGridSource&) = delete;
};
#endif

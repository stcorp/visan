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

#include "vtkGeoGridSource.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkFloatArray.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"

vtkStandardNewMacro(vtkGeoGridSource);

vtkGeoGridSource::vtkGeoGridSource()
{
    this->Graticule = 30;
    this->PointDistance = 1;
    this->CreateParallelsForPoles = 1;
    this->SetNumberOfInputPorts(0);
}


int vtkGeoGridSource::RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                                  vtkInformationVector *outputVector)
{
    int numMeridians;                             // Line with constant longitude value
    int numParallels;                             // Line with constant latitude value
    int numPointsPerMeridian;
    int numPointsPerParallel;
    int numLines;
    int numPoints;
    int i, j;

    vtkPolyData *output = this->GetOutput();
    auto points = vtkSmartPointer<vtkPoints>::New();
    points->SetDataTypeToDouble();
    auto cells = vtkSmartPointer<vtkCellArray>::New();
    auto color = vtkSmartPointer<vtkFloatArray>::New();
    output->SetPoints(points);
    output->SetLines(cells);
    output->GetCellData()->SetScalars(color);

    numMeridians = (int)(360.0 / this->Graticule);
    numParallels = (int)(180.0 / this->Graticule);
    if (!this->CreateParallelsForPoles && numParallels * this->Graticule == 180.0)
    {
        --numParallels;
    }
    else
    {
        ++numParallels;
    }

    numPointsPerMeridian = (int)(180.0 / this->PointDistance) + 1;
    numPointsPerParallel = (int)(360.0 / this->PointDistance) + 1;

    numLines = numMeridians + numParallels;
    numPoints = numMeridians * numPointsPerMeridian + numParallels * numPointsPerParallel;

    cells->Allocate(numLines);
    points->Allocate(numPoints);

    // Meridians (constant longitude)
    for (i = 0; i < numMeridians; i++)
    {
        double longitude = i * this->Graticule - 180.0;
        vtkIdType cell = cells->InsertNextCell(numPointsPerMeridian);
        color->InsertTuple1(cell, 0.0);

        for (j = 0; j < numPointsPerMeridian; j++)
        {
            double latitude = j * this->PointDistance - 90.0;
            vtkIdType point = points->InsertNextPoint(longitude, latitude, 0.0);
            cells->InsertCellPoint(point);
        }
    }

    // Parallels (constant latitude)
    for (j = 0; j < numParallels; j++)
    {
        double latitude = j * this->Graticule - 90.0;
        vtkIdType cell = cells->InsertNextCell(numPointsPerParallel);
        color->InsertTuple1(cell, 0.0);

        for (i = 0; i < numPointsPerParallel; i++)
        {
            double longitude = i * this->PointDistance - 180.0;
            vtkIdType point = points->InsertNextPoint(longitude, latitude, 0.0);
            cells->InsertCellPoint(point);
        }
    }

    return 1;
}


void vtkGeoGridSource::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os, indent);

    os << indent << "Graticule: " << this->Graticule << endl;
    os << indent << "Point distance: " << this->PointDistance << endl;
    os << indent << "Create parallels for poles: " << this->CreateParallelsForPoles << endl;
}

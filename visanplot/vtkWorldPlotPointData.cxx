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

#include <assert.h>
#include <stdlib.h>

#include "vtkWorldPlotPointData.h"

#include "vtkActor.h"
#include "vtkActor2D.h"
#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkCollection.h"
#include "vtkColorTable.h"
#include "vtkDoubleArray.h"
#include "vtkMath.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"
#include "vtkProperty.h"
#include "vtkProperty2D.h"

vtkStandardNewMacro(vtkWorldPlotPointData);

vtkWorldPlotPointData::vtkWorldPlotPointData()
{
    this->actor2D->GetProperty()->SetPointSize(2);
    this->actor3D->GetProperty()->SetPointSize(2);
    this->colorTable->SetColorTableByName("Aerosol");
}


void vtkWorldPlotPointData::AddData(vtkDoubleArray *latitude, vtkDoubleArray *longitude, vtkDoubleArray *data)
{
    auto path = vtkSmartPointer<vtkPolyData>::New();
    auto verts = vtkSmartPointer<vtkCellArray>::New();
    auto points = vtkSmartPointer<vtkPoints>::New();
    double *latitudes = nullptr;
    double *longitudes = nullptr;
    double *values = nullptr;
    int numPoints;
    int numValues;
    int i;

    numPoints = latitude->GetNumberOfTuples();
    if (numPoints <= 0)
    {
        vtkErrorMacro("Invalid value for number of points");
        return;
    }
    if (longitude->GetNumberOfTuples() != numPoints)
    {
        vtkErrorMacro("Number of latitude and longitude points is not the same");
        return;
    }
    numValues = data == nullptr ? 0 : data->GetNumberOfTuples();
    if (numValues != 0 && numValues != numPoints)
    {
        vtkErrorMacro("Number of values and number of latitude/longitude points is not the same");
        return;
    }

    points->SetNumberOfPoints(numPoints);
    latitudes = latitude->GetPointer(0);
    longitudes = longitude->GetPointer(0);
    for (i = 0; i < numPoints; i++)
    {
        points->SetPoint(i, longitudes[i], latitudes[i], 0);
    }
    path->SetPoints(points);

    for (i = 0; i < numPoints; i++)
    {
        verts->InsertNextCell(1);
        verts->InsertCellPoint(i);
    }
    path->SetVerts(verts);

    if (numValues > 0)
    {
        auto value = vtkSmartPointer<vtkDoubleArray>::New();
        value->DeepCopy(data);
        path->GetCellData()->SetScalars(value);
    }

    this->AddInputData(path);

    if (numValues > 0 && this->algorithms->GetNumberOfItems() == 1)
    {
        this->colorTable->SetColorRange(data->GetFiniteRange());
    }
}

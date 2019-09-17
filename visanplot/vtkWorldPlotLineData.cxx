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

#include <assert.h>
#include <stdlib.h>

#include "vtkWorldPlotLineData.h"

#include "vtkActor.h"
#include "vtkActor2D.h"
#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkColorTable.h"
#include "vtkDoubleArray.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"
#include "vtkProperty.h"
#include "vtkProperty2D.h"

vtkStandardNewMacro(vtkWorldPlotLineData);

vtkWorldPlotLineData::vtkWorldPlotLineData()
{
    this->actor2D->GetProperty()->SetPointSize(2);
    this->actor3D->GetProperty()->SetPointSize(2);
}

void vtkWorldPlotLineData::AddData(vtkDoubleArray *latitude, vtkDoubleArray *longitude)
{
    auto path = vtkSmartPointer<vtkPolyData>::New();
    auto lines = vtkSmartPointer<vtkCellArray>::New();
    auto points = vtkSmartPointer<vtkPoints>::New();
    double *latitudes = nullptr;
    double *longitudes = nullptr;
    int numPoints;
    int i;

    numPoints = latitude->GetNumberOfTuples();
    if (numPoints <= 0)
    {
        vtkErrorMacro("Invalid number of points");
        return;
    }
    if (longitude->GetNumberOfTuples() != numPoints)
    {
        vtkErrorMacro("Number of latitude and longitude points is not the same");
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
    for (i = 0; i < numPoints - 1; i++)
    {
        lines->InsertNextCell(2);
        lines->InsertCellPoint(i);
        lines->InsertCellPoint(i + 1);
    }
    path->SetLines(lines);

    this->AddInputData(path);
}

//
// Copyright (C) 2002-2020 S[&]T, The Netherlands.
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

#include "vtkWorldPlotGridData.h"

#include "vtkColorTable.h"
#include "vtkCollection.h"
#include "vtkDoubleArray.h"
#include "vtkGeoMapFilter.h"
#include "vtkMath.h"
#include "vtkShortArray.h"

vtkStandardNewMacro(vtkWorldPlotGridData);

vtkWorldPlotGridData::vtkWorldPlotGridData()
{
    this->colorTable->SetColorTableByName("Aerosol");
    this->heightFactor = 0.0;
    this->minHeightValue = 0.0;
    this->maxHeightValue = 0.0;
}


void vtkWorldPlotGridData::AddData(vtkDoubleArray *latitude, vtkDoubleArray *longitude, vtkDoubleArray *data)
{
    auto value = vtkSmartPointer<vtkDoubleArray>::New();
    auto bitarray = vtkSmartPointer<vtkShortArray>::New();
    auto geoMapFilter = vtkSmartPointer<vtkGeoMapFilter>::New();

    int width = longitude->GetNumberOfTuples();
    int height = latitude->GetNumberOfTuples();
    if (width <= 1)
    {
        vtkErrorMacro("Grid width should be > 1");
        return;
    }
    if (height <= 1)
    {
        vtkErrorMacro("Grid height should be > 1");
        return;
    }
    if (data->GetNumberOfTuples() != width * height)
    {
        vtkErrorMacro("Number of items in grid data does not match dimensions");
        return;
    }

    geoMapFilter->SetValues(data);
    geoMapFilter->SetHeights(data);
    geoMapFilter->SetLongitudes(longitude);
    geoMapFilter->SetLatitudes(latitude);
    geoMapFilter->SetFactor(0);
    geoMapFilter->SetRadius(this->GetReferenceHeight());
    geoMapFilter->SetMapWidth(width);
    geoMapFilter->SetMapHeight(height);

    this->AddInputConnection(geoMapFilter->GetOutputPort());

    double *finiteRange = data->GetFiniteRange();
    if (this->algorithms->GetNumberOfItems() == 1)
    {
        this->SetMinHeightValue(finiteRange[0]);
        this->SetMaxHeightValue(finiteRange[1]);
        this->colorTable->SetColorRange(this->minHeightValue, this->maxHeightValue);
    }
    else
    {
        if (finiteRange[0] < this->minHeightValue)
        {
            this->SetMinHeightValue(finiteRange[0]);
        }
        if (finiteRange[1] > this->maxHeightValue)
        {
            this->SetMaxHeightValue(finiteRange[1]);
        }
    }
}

void vtkWorldPlotGridData::SetReferenceHeight(double referenceHeight)
{
    vtkGeoMapFilter *algorithm;

    vtkWorldPlotData::SetReferenceHeight(referenceHeight);
    this->algorithms->InitTraversal();
    while ((algorithm = vtkGeoMapFilter::SafeDownCast(this->algorithms->GetNextItemAsObject())) != 0)
    {
        algorithm->SetRadius(referenceHeight);
    }
}

void vtkWorldPlotGridData::SetHeightFactor(double heightFactor)
{
    vtkGeoMapFilter *algorithm;

    this->heightFactor = heightFactor;
    this->algorithms->InitTraversal();
    while ((algorithm = vtkGeoMapFilter::SafeDownCast(this->algorithms->GetNextItemAsObject())) != 0)
    {
        algorithm->SetFactor(heightFactor);
    }
}

double vtkWorldPlotGridData::GetHeightFactor()
{
    return this->heightFactor;
}

void vtkWorldPlotGridData::SetMinHeightValue(double minValue)
{
    vtkGeoMapFilter *algorithm;

    this->minHeightValue = minValue;
    this->algorithms->InitTraversal();
    while ((algorithm = vtkGeoMapFilter::SafeDownCast(this->algorithms->GetNextItemAsObject())) != 0)
    {
        algorithm->SetMinMappedValue(minValue);
    }
}

double vtkWorldPlotGridData::GetMinHeightValue()
{
    return this->minHeightValue;
}

void vtkWorldPlotGridData::SetMaxHeightValue(double maxValue)
{
    vtkGeoMapFilter *algorithm;

    this->maxHeightValue = maxValue;
    this->algorithms->InitTraversal();
    while ((algorithm = vtkGeoMapFilter::SafeDownCast(this->algorithms->GetNextItemAsObject())) != 0)
    {
        algorithm->SetMaxMappedValue(maxValue);
    }
}

double vtkWorldPlotGridData::GetMaxHeightValue()
{
    return this->maxHeightValue;
}

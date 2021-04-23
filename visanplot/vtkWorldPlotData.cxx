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

#include <assert.h>

#include "vtkActor.h"
#include "vtkActor2D.h"
#include "vtkAlgorithmOutput.h"
#include "vtkCoordinate.h"
#include "vtkCollection.h"
#include "vtkLookupTable.h"
#include "vtkPolyDataMapper.h"
#include "vtkPolyDataMapper2D.h"
#include "vtkProperty.h"
#include "vtkProperty2D.h"
#include "vtkSmartPointer.h"
#include "vtkTransform.h"
#include "vtkTransformPolyDataFilter.h"
#include "vtkTrivialProducer.h"

#include "vtkProjFilter.h"

#include "vtkColorTable.h"
#include "vtkWorldPlotData.h"

vtkStandardNewMacro(vtkWorldPlotData);

vtkWorldPlotData::vtkWorldPlotData()
{
    auto coord = vtkSmartPointer<vtkCoordinate>::New();
    auto transformFilter = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
    auto mapper2D = vtkSmartPointer<vtkPolyDataMapper2D>::New();
    auto mapper3D = vtkSmartPointer<vtkPolyDataMapper>::New();

    this->plotLabel = nullptr;
    this->colorBarTitle = nullptr;
    this->numColorBarLabels = 2;
    this->colorTable = vtkSmartPointer<vtkColorTable>::New();
    this->transform = vtkSmartPointer<vtkTransform>::New();
    this->filter = vtkSmartPointer<vtkProjFilter>::New();
    this->actor2D = vtkSmartPointer<vtkActor2D>::New();
    this->actor3D = vtkSmartPointer<vtkActor>::New();
    this->algorithms = vtkSmartPointer<vtkCollection>::New();

#ifdef __WIN32__
    this->filter->SetInterpolationDistance(0.02);
#endif
    this->filter->SetProjection(VTK_PROJ_3D);
    // Make sure we always have an input set (to not break the pipeline)
    auto producer = vtkSmartPointer<vtkTrivialProducer>::New();
    producer->SetOutput(vtkSmartPointer<vtkPolyData>::New());
    this->filter->SetInputConnection(producer->GetOutputPort());

    coord->SetCoordinateSystemToNormalizedViewport();
    transform->Identity();
    transformFilter->SetInputConnection(this->filter->GetOutputPort());
    transformFilter->SetTransform(transform);
    mapper2D->SetInputConnection(transformFilter->GetOutputPort());
    mapper2D->SetTransformCoordinate(coord);
    mapper2D->SetScalarModeToUseCellData();
    mapper2D->SetLookupTable(colorTable->GetVTKLookupTable());
    mapper2D->UseLookupTableScalarRangeOn();
    this->actor2D->SetMapper(mapper2D);
    this->actor2D->GetProperty()->SetColor(0, 0, 0);

    mapper3D->SetInputConnection(this->filter->GetOutputPort());
    mapper3D->SetScalarModeToUseCellData();
    mapper3D->SetLookupTable(colorTable->GetVTKLookupTable());
    mapper3D->UseLookupTableScalarRangeOn();
    this->actor3D->SetMapper(mapper3D);
    this->actor3D->GetProperty()->SetColor(0, 0, 0);
    this->actor3D->GetProperty()->SetInterpolationToPhong();
    this->actor3D->GetProperty()->BackfaceCullingOn();

    this->SetOpacity(0.7);
    this->SetLineWidth(1.0);
}

vtkWorldPlotData::~vtkWorldPlotData()
{
    if (this->plotLabel != nullptr)
    {
        delete [] this->plotLabel;
    }
    if (this->colorBarTitle != nullptr)
    {
        delete [] this->colorBarTitle;
    }
}

void vtkWorldPlotData::SetKeyframe(int keyframe)
{
    if (keyframe >= this->algorithms->GetNumberOfItems())
    {
        keyframe = this->algorithms->GetNumberOfItems() - 1;
    }
    if (keyframe < 0)
    {
        keyframe = 0;
    }
    vtkAlgorithm *algorithm = vtkAlgorithm::SafeDownCast(this->algorithms->GetItemAsObject(keyframe));
    this->filter->SetInputConnection(algorithm->GetOutputPort());
}

int vtkWorldPlotData::GetNumberOfKeyframes()
{
    return this->algorithms->GetNumberOfItems();
}

void vtkWorldPlotData::AddInputData(vtkPolyData *input)
{
    auto producer = vtkSmartPointer<vtkTrivialProducer>::New();
    producer->SetOutput(input);
    this->AddInputConnection(producer->GetOutputPort());
}

void vtkWorldPlotData::AddInputConnection(vtkAlgorithmOutput *input)
{
    this->algorithms->AddItem(input->GetProducer());
    if (this->algorithms->GetNumberOfItems() == 1)
    {
        this->SetKeyframe(0);
    }
}

void vtkWorldPlotData::SetProjection(int projection)
{
    this->filter->SetProjection(projection);
}

int vtkWorldPlotData::GetProjection()
{
    return this->filter->GetProjection();
}

void vtkWorldPlotData::SetProjectionCenterLatitude(double latitude)
{
    this->filter->SetCenterLatitude(latitude);
}

void vtkWorldPlotData::SetProjectionCenterLongitude(double longitude)
{
    this->filter->SetCenterLongitude(longitude);
}

void vtkWorldPlotData::SetOpacity(double opacity)
{
    this->actor2D->GetProperty()->SetOpacity(opacity);
    this->actor3D->GetProperty()->SetOpacity(opacity);
}

double vtkWorldPlotData::GetOpacity()
{
    return this->actor2D->GetProperty()->GetOpacity();
}

void vtkWorldPlotData::SetLineWidth(double width)
{
    this->actor2D->GetProperty()->SetLineWidth(width);
    this->actor3D->GetProperty()->SetLineWidth(width);
}

double vtkWorldPlotData::GetLineWidth()
{
    return this->actor2D->GetProperty()->GetLineWidth();
}

void vtkWorldPlotData::SetPointSize(double size)
{
    this->actor2D->GetProperty()->SetPointSize(size);
    this->actor3D->GetProperty()->SetPointSize(size);
}

void vtkWorldPlotData::SetPlotLabel(const char *label)
{
    if (this->plotLabel == nullptr)
    {
        delete [] this->plotLabel;
    }
    this->plotLabel = new char[strlen(label) + 1];
    assert(this->plotLabel != nullptr);
    strcpy(this->plotLabel, label);
}

const char *vtkWorldPlotData::GetPlotLabel()
{
    return this->plotLabel;
}

void vtkWorldPlotData::SetColorBarTitle(const char *title)
{
    if (this->colorBarTitle == nullptr)
    {
        delete [] this->colorBarTitle;
    }
    this->colorBarTitle = new char[strlen(title) + 1];
    assert(this->colorBarTitle != nullptr);
    strcpy(this->colorBarTitle, title);
}

const char *vtkWorldPlotData::GetColorBarTitle()
{
    return this->colorBarTitle;
}

void vtkWorldPlotData::SetNumColorBarLabels(int numLabels)
{
    this->numColorBarLabels = numLabels;
}

int vtkWorldPlotData::GetNumColorBarLabels()
{
    return this->numColorBarLabels;
}

void vtkWorldPlotData::SetReferenceHeight(double referenceHeight)
{
    this->filter->SetReferenceHeight(referenceHeight);
}

double vtkWorldPlotData::GetReferenceHeight()
{
    return this->filter->GetReferenceHeight();
}

double vtkWorldPlotData::GetPointSize()
{
    return this->actor2D->GetProperty()->GetPointSize();
}

vtkActor2D *vtkWorldPlotData::GetActor2D()
{
    return this->actor2D.GetPointer();
}

vtkActor *vtkWorldPlotData::GetActor3D()
{
    return this->actor3D.GetPointer();
}

vtkTransform *vtkWorldPlotData::GetTransform()
{
    return this->transform.GetPointer();
}

double vtkWorldPlotData::GetXYRatio()
{
    return this->filter->GetXYRatio();
}

vtkColorTable *vtkWorldPlotData::GetColorTable()
{
    return this->colorTable.GetPointer();
}

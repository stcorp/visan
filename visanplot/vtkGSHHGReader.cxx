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

#include "vtkGSHHGReader.h"

#include "vtkByteSwap.h"
#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkFloatArray.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"
#include "vtkSmartPointer.h"

vtkStandardNewMacro(vtkGSHHGReader);

int vtkGSHHGReader::readint(FILE *f, int *value)
{
    size_t numItems;

    numItems = fread(value, 4, 1, f);
    if (numItems != 1)
    {
        if (feof(f))
        {
            fclose(f);
            return 1;
        }
        vtkErrorMacro(<< "Could not read from GSHHG file");
        fclose(f);
        return -1;
    }
    vtkByteSwap::Swap4BE(value);

    return 0;
}

int vtkGSHHGReader::readshort(FILE *f, short *value)
{
    unsigned char buffer[2];
    size_t numItems;

    numItems = fread(buffer, 2, 1, f);
    if (numItems != 1)
    {
        if (feof(f))
        {
            fclose(f);
            return 1;
        }
        vtkErrorMacro(<< "Could not read from GSHHG file");
        fclose(f);
        return -1;
    }

    *value = buffer[0] * 256 + buffer[1];

    return 0;
}

vtkGSHHGReader::vtkGSHHGReader()
{
    this->FileName = nullptr;
    this->MaxLevel = VTK_INT_MAX;
    this->SetNumberOfInputPorts(0);
}

vtkGSHHGReader::~vtkGSHHGReader()
{
    if (this->FileName != nullptr)
    {
        delete [] this->FileName;
    }
}

int vtkGSHHGReader::RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                                vtkInformationVector *outputVector)

{
    vtkPolyData *output = this->GetOutput();
    auto points = vtkSmartPointer<vtkPoints>::New();
    auto lines = vtkSmartPointer<vtkCellArray>::New();
    auto color = vtkSmartPointer<vtkFloatArray>::New();

    points->SetDataTypeToDouble();
    output->SetPoints(points);
    output->SetLines(lines);
    output->GetCellData()->SetScalars(color);

    if (this->FileName == nullptr)
    {
        // if no filename was specified we return empty polydata
        return 1;
    }

    FILE *f = fopen(this->FileName, "rb");
    if (f == nullptr)
    {
        vtkErrorMacro(<< "Could not open GSHHG file");
        return 0;
    }

    // read id of first polygon
    int id;
    if (readint(f, &id) != 0)
    {
        return 0;
    }

    // read until we encounter end-of-file or until we encounter an error
    for (;;)
    {
        int numPoints;
        int flag;
        int level;
        int extent[4];
        int unused;

        // read number of points
        if (readint(f, &numPoints) != 0)
        {
            return 0;
        }
        // read flag
        if (readint(f, &flag) != 0)
        {
            return 0;
        }
        level = flag & 255;
        // read extent (west, east, south, north)
        if (readint(f, &(extent[0])) != 0)
        {
            return 0;
        }
        if (readint(f, &(extent[1])) != 0)
        {
            return 0;
        }
        if (readint(f, &(extent[2])) != 0)
        {
            return 0;
        }
        if (readint(f, &(extent[3])) != 0)
        {
            return 0;
        }
        // read area
        if (readint(f, &unused) != 0)
        {
            return 0;
        }
        // read area_full
        if (readint(f, &unused) != 0)
        {
            return 0;
        }
        // read container
        if (readint(f, &unused) != 0)
        {
            return 0;
        }
        // read ancestor
        if (readint(f, &unused) != 0)
        {
            return 0;
        }

        if (level <= this->MaxLevel)
        {
            vtkIdType cell = lines->InsertNextCell(numPoints);
            color->InsertTuple1(cell, 0.0);
        }

        // read points
        for (int i = 0; i < numPoints; ++i)
        {
            int pt[2];

            // read point (x, y)
            if (readint(f, &(pt[0])) != 0)
            {
                return 0;
            }
            if (readint(f, &(pt[1])) != 0)
            {
                return 0;
            }

            if (level <= this->MaxLevel)
            {
                double longitude = pt[0] / 1000000.0;
                if (longitude > 180)
                {
                    longitude -= 360;
                }
                double latitude = pt[1] / 1000000.0;

                vtkIdType point = points->InsertNextPoint(longitude, latitude, 0.0);
                lines->InsertCellPoint(point);
            }
        }

        if (level <= this->MaxLevel)
        {
            vtkDebugMacro(<< numPoints << " points read");
        }
        else
        {
            vtkDebugMacro(<< "polygon skipped");
        }

        // read id of next polygon
        if (readint(f, &id) != 0)
        {
            return 1;
        }
    }
}

void vtkGSHHGReader::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os, indent);

    os << indent << "File Name: " << (this->FileName ? this->FileName : "(none)") << endl;
    os << indent << "Maximum Level: " << this->MaxLevel << endl;
}

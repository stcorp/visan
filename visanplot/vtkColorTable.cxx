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

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "vtkColorTable.h"

#include "vtkLookupTable.h"

vtkStandardNewMacro(vtkColorTable);

vtkColorTable::vtkColorTable()
{
    this->gradientEdge = nullptr;
    this->numberOfGradientEdges = 0;
    this->colorTableName = vtkStdString("");
    this->interpolationMode = GRADIENT_INTERPOLATION_MODE_LINEAR;

    this->lut = vtkSmartPointer<vtkLookupTable>::New();
    this->lut->SetNumberOfTableValues(256);
    this->lut->SetTableRange(0, 1);

    this->SetColorTableByName(vtkStdString("Default"));
}

vtkColorTable::~vtkColorTable()
{
    if (gradientEdge != nullptr)
    {
        free(gradientEdge);
        gradientEdge = nullptr;
    }
}

void vtkColorTable::SetColorRange(double minValue, double maxValue)
{
    this->lut->SetTableRange(minValue, maxValue);
    this->InvokeEvent("ColorTableChanged");
}

double *vtkColorTable::GetColorRange()
{
    return this->lut->GetTableRange();
}

void vtkColorTable::GetColorRange(double *minValue, double *maxValue)
{
    double range[2];

    this->lut->GetTableRange(range);
    *minValue = range[0];
    *maxValue = range[1];
}

int vtkColorTable::GetNumTableColors()
{
    return this->lut->GetNumberOfTableValues();
}

void vtkColorTable::SetNumTableColors(int num_colors)
{
    this->lut->SetNumberOfTableValues(num_colors);
    this->UpdateColorTable();
}

double *vtkColorTable::GetTableColor(int index)
{
    return this->lut->GetTableValue(index);
}

void vtkColorTable::GetTableColor(int index, double *r, double *g, double *b, double *a)
{
    double *rgba;

    rgba = this->lut->GetTableValue(index);
    *r = rgba[0];
    *g = rgba[1];
    *b = rgba[2];
    *a = rgba[3];
}


double *vtkColorTable::GetGradientEdgeValue(int index)
{
    if (index < 0 || index >= this->numberOfGradientEdges)
    {
        vtkErrorMacro("Invalid gradient edge index for color table");
        return nullptr;
    }
    static_assert(sizeof(GradientEdge)==sizeof(double[5]),
                  "GradientEdge layout must be compatible with double[5]");
    return &gradientEdge[index].x;
}

void vtkColorTable::GetGradientEdgeValue(int index, double *x, double *r, double *g, double *b, double *a)
{
    if (index < 0 || index >= this->numberOfGradientEdges)
    {
        vtkErrorMacro("Invalid gradient edge index for color table");
        return;
    }

    *x = gradientEdge[index].x;
    *r = gradientEdge[index].r;
    *g = gradientEdge[index].g;
    *b = gradientEdge[index].b;
    *a = gradientEdge[index].a;
}

int vtkColorTable::InsertGradientEdgeValue(double x, double r, double g, double b, double a)
{
    GradientEdge *newGradientEdge;
    int index;
    int i;

    if (x < 0 || x > 1 || r < 0 || r > 1 || g < 0 || g > 1 || b < 0 || b > 1 || a < 0 || a > 1)
    {
        vtkErrorMacro("Gradient edge values are out of range (should be between 0 and 1)");
        return -1;
    }

    newGradientEdge = (GradientEdge *)realloc(gradientEdge, (numberOfGradientEdges + 1) * sizeof(GradientEdge));
    assert(newGradientEdge);
    gradientEdge = newGradientEdge;
    index = 1;
    while (index < numberOfGradientEdges && x > gradientEdge[index].x)
    {
        index++;
    }
    for (i = this->numberOfGradientEdges; i > index; i--)
    {
        gradientEdge[i] = gradientEdge[i - 1];
    }
    gradientEdge[index].x = x;
    gradientEdge[index].r = r;
    gradientEdge[index].g = g;
    gradientEdge[index].b = b;
    gradientEdge[index].a = a;
    numberOfGradientEdges++;

    // We now have a custom color table, so clear the color table name
    this->colorTableName = vtkStdString("");

    this->UpdateColorTable();

    return index;
}

void vtkColorTable::SetGradientEdgeValue(int index, double x, double r, double g, double b, double a)
{
    if (index < 0 || index >= this->numberOfGradientEdges)
    {
        vtkErrorMacro("Invalid gradient edge index for color table");
        return;
    }
    if (r < 0 || r > 1 || g < 0 || g > 1 || b < 0 || b > 1 || a < 0 || a > 1)
    {
        vtkErrorMacro("Gradient edge color values are out of range (should be between 0 and 1)");
        return;
    }
    if ((index == 0 && x != 0.0) || (index > 0 && x < gradientEdge[index - 1].x) ||
        (index == numberOfGradientEdges - 1 && x != 1.0) ||
        (index < numberOfGradientEdges - 1 && x > gradientEdge[index + 1].x))
    {
        vtkErrorMacro("Gradient edge position is not valid");
        return;
    }

    gradientEdge[index].x = x;
    gradientEdge[index].r = r;
    gradientEdge[index].g = g;
    gradientEdge[index].b = b;
    gradientEdge[index].a = a;

    // We now have a custom color table, so clear the color table name
    this->colorTableName = vtkStdString("");

    this->UpdateColorTable();
}

void vtkColorTable::RemoveGradientEdgeValue(int index)
{
    int i;

    if (index < 0 || index >= this->numberOfGradientEdges)
    {
        vtkErrorMacro("Invalid gradient edge index for color table");
        return;
    }

    for (i = index; i < this->numberOfGradientEdges - 1; i++)
    {
        gradientEdge[i] = gradientEdge[i + 1];
    }

    this->numberOfGradientEdges--;

    // We now have a custom color table, so clear the color table name
    this->colorTableName = vtkStdString("");

    this->UpdateColorTable();
}

void vtkColorTable::SetColorTableByName(const char *name)
{
    SetColorTableByName(vtkStdString(name));
}

void vtkColorTable::SetColorTableByName(const vtkStdString &name)
{
    if (name == "Default")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 0.0;
        this->gradientEdge[1].g = 0.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;
    }
    else if (name == "BlackToWhite")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 1.0;
        this->gradientEdge[1].g = 1.0;
        this->gradientEdge[1].b = 1.0;
        this->gradientEdge[1].a = 1.0;
    }
    else if (name == "WhiteToBlack")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 1.0;
        this->gradientEdge[0].g = 1.0;
        this->gradientEdge[0].b = 1.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 0.0;
        this->gradientEdge[1].g = 0.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;
    }
    else if (name == "GreenToRed")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 1.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 1.0;
        this->gradientEdge[1].g = 0.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;
    }
    else if (name == "RedToGreen")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 1.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 0.0;
        this->gradientEdge[1].g = 1.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;
    }
    else if (name == "Cloud")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 2;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);
        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 1.0;
        this->gradientEdge[0].g = 1.0;
        this->gradientEdge[0].b = 1.0;
        this->gradientEdge[0].a = 0.0;

        this->gradientEdge[1].x = 1.0;
        this->gradientEdge[1].r = 0.5;
        this->gradientEdge[1].g = 0.5;
        this->gradientEdge[1].b = 0.5;
        this->gradientEdge[1].a = 0.5;
    }
    else if (name == "Rainbow")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 5;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 1.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0/3;
        this->gradientEdge[1].r = 1.0;
        this->gradientEdge[1].g = 1.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;

        this->gradientEdge[2].x = 0.5;
        this->gradientEdge[2].r = 0.0;
        this->gradientEdge[2].g = 1.0;
        this->gradientEdge[2].b = 0.0;
        this->gradientEdge[2].a = 1.0;

        this->gradientEdge[3].x = 2.0/3;
        this->gradientEdge[3].r = 0.0;
        this->gradientEdge[3].g = 0.0;
        this->gradientEdge[3].b = 1.0;
        this->gradientEdge[3].a = 1.0;

        this->gradientEdge[4].x = 1.0;
        this->gradientEdge[4].r = 1.0;
        this->gradientEdge[4].g = 0.0;
        this->gradientEdge[4].b = 1.0;
        this->gradientEdge[4].a = 1.0;
    }
    else if (name == "Ozone")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 8;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0/7;
        this->gradientEdge[1].r = 0.0;
        this->gradientEdge[1].g = 0.0;
        this->gradientEdge[1].b = 1.0;
        this->gradientEdge[1].a = 1.0;

        this->gradientEdge[2].x = 2.0/7;
        this->gradientEdge[2].r = 0.0;
        this->gradientEdge[2].g = 1.0;
        this->gradientEdge[2].b = 1.0;
        this->gradientEdge[2].a = 1.0;

        this->gradientEdge[3].x = 3.0/7;
        this->gradientEdge[3].r = 0.0;
        this->gradientEdge[3].g = 1.0;
        this->gradientEdge[3].b = 0.0;
        this->gradientEdge[3].a = 1.0;

        this->gradientEdge[4].x = 4.0/7;
        this->gradientEdge[4].r = 1.0;
        this->gradientEdge[4].g = 1.0;
        this->gradientEdge[4].b = 0.0;
        this->gradientEdge[4].a = 1.0;

        this->gradientEdge[5].x = 5.0/7;
        this->gradientEdge[5].r = 1.0;
        this->gradientEdge[5].g = 0.0;
        this->gradientEdge[5].b = 0.0;
        this->gradientEdge[5].a = 1.0;

        this->gradientEdge[6].x = 6.0/7;
        this->gradientEdge[6].r = 1.0;
        this->gradientEdge[6].g = 0.0;
        this->gradientEdge[6].b = 1.0;
        this->gradientEdge[6].a = 1.0;

        this->gradientEdge[7].x = 1.0;
        this->gradientEdge[7].r = 1.0;
        this->gradientEdge[7].g = 1.0;
        this->gradientEdge[7].b = 1.0;
        this->gradientEdge[7].a = 1.0;
    }
    else if (name == "Blackbody")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 4;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 1.0/3;
        this->gradientEdge[1].r = 1.0;
        this->gradientEdge[1].g = 0.0;
        this->gradientEdge[1].b = 0.0;
        this->gradientEdge[1].a = 1.0;

        this->gradientEdge[2].x = 2.0/3;
        this->gradientEdge[2].r = 1.0;
        this->gradientEdge[2].g = 1.0;
        this->gradientEdge[2].b = 0.0;
        this->gradientEdge[2].a = 1.0;

        this->gradientEdge[3].x = 1.0;
        this->gradientEdge[3].r = 1.0;
        this->gradientEdge[3].g = 1.0;
        this->gradientEdge[3].b = 1.0;
        this->gradientEdge[3].a = 1.0;
    }
    else if (name == "Aerosol")
    {
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = 5;
        this->gradientEdge = (GradientEdge *)malloc(this->numberOfGradientEdges * sizeof(GradientEdge));
        assert(this->gradientEdge);

        this->gradientEdge[0].x = 0.0;
        this->gradientEdge[0].r = 0.0;
        this->gradientEdge[0].g = 0.0;
        this->gradientEdge[0].b = 0.0;
        this->gradientEdge[0].a = 1.0;

        this->gradientEdge[1].x = 0.25;
        this->gradientEdge[1].r = 0.0;
        this->gradientEdge[1].g = 0.5;
        this->gradientEdge[1].b = 1.0;
        this->gradientEdge[1].a = 1.0;

        this->gradientEdge[2].x = 0.5;
        this->gradientEdge[2].r = 0.0;
        this->gradientEdge[2].g = 1.0;
        this->gradientEdge[2].b = 1.0;
        this->gradientEdge[2].a = 1.0;

        this->gradientEdge[3].x = 0.75;
        this->gradientEdge[3].r = 1.0;
        this->gradientEdge[3].g = 1.0;
        this->gradientEdge[3].b = 0.0;
        this->gradientEdge[3].a = 1.0;

        this->gradientEdge[4].x = 1.0;
        this->gradientEdge[4].r = 1.0;
        this->gradientEdge[4].g = 0.0;
        this->gradientEdge[4].b = 0.0;
        this->gradientEdge[4].a = 1.0;
    }
    else
    {
        vtkErrorMacro("Unknown color table name");
        return;
    }
    this->colorTableName = name;
    this->UpdateColorTable();
}

void vtkColorTable::SetGradientInterpolationMode(int interpolationMode)
{
    if (interpolationMode < 0 || interpolationMode > 2)
    {
        vtkErrorMacro("Invalid color table interpolation mode");
        return;
    }
    this->interpolationMode = interpolationMode;
    this->UpdateColorTable();
}

void vtkColorTable::Import(const vtkStdString &filename)
{
    FILE *f;
    char name[51];
    int numValues;
    int n;
    int i;

    f = fopen(filename.c_str(), "r");
    if (f == nullptr)
    {
        vtkErrorMacro("could not open ColorTable file for import");
        return;
    }

    n = 0;
    fscanf(f, "ColorTable 1.0\n%n", &n);
    if (n != 15)
    {
        fclose(f);
        vtkErrorMacro("could not import ColorTable file: invalid header");
        return;
    }
    n = fscanf(f, "TableSize=%d\n", &numValues);
    if (n != 1)
    {
        fclose(f);
        vtkErrorMacro("could not import ColorTable file: invalid format (TableSize)");
        return;
    }
    this->lut->SetNumberOfTableValues(numValues);
    n = 0;
    fscanf(f, "Name=%50[^\n]\n%n", name, &n);
    if (n == 0)
    {
        fclose(f);
        vtkErrorMacro("could not import ColorTable file: invalid format (Name)");
        return;
    }
    name[n - 6] = '\0';
    if (strcmp(name, "Custom") == 0)
    {
        int mode;
        this->colorTableName = vtkStdString("");
        n = fscanf(f, "NumberOfGradientEdges=%d\n", &numValues);
        if (n != 1)
        {
            fclose(f);
            vtkErrorMacro("could not import ColorTable file: invalid format (NumberOfGradientEdges)");
            return;
        }
        if (this->gradientEdge)
        {
            free(this->gradientEdge);
        }
        this->numberOfGradientEdges = numValues;
        this->gradientEdge = (GradientEdge *)malloc(numValues * sizeof(GradientEdge));
        assert(this->gradientEdge);
        n = fscanf(f, "InterPolationMode=%d\n", &mode);
        if (n != 1 || mode < 0 || mode > 2)
        {
            fclose(f);
            vtkErrorMacro("could not import ColorTable file: invalid format (InterPolationMode)");
            return;
        }
        this->interpolationMode = mode;
        for (i = 0; i < numValues; i++)
        {
            double x;
            double rgba[4];

            n = fscanf(f, "%lf %lf %lf %lf %lf\n", &x, &rgba[0], &rgba[1], &rgba[2], &rgba[3]);
            if (n != 5)
            {
                fclose(f);
                vtkErrorMacro("could not import ColorTable file: invalid format (xrgba value)");
                return;
            }
            this->gradientEdge[i].x = x;
            this->gradientEdge[i].r = rgba[0];
            this->gradientEdge[i].g = rgba[1];
            this->gradientEdge[i].b = rgba[2];
            this->gradientEdge[i].a = rgba[3];
        }
    }
    else
    {
        this->SetColorTableByName(name);
    }
    this->UpdateColorTable();

    fclose(f);
}


void vtkColorTable::Export(const vtkStdString &filename)
{
    FILE *f;
    int numValues;

    f = fopen(filename.c_str(), "w");
    if (f == nullptr)
    {
        vtkErrorMacro("could not open ColorTable file for export");
        return;
    }

    numValues = this->lut->GetNumberOfTableValues();
    fprintf(f, "ColorTable 1.0\n");
    fprintf(f, "TableSize=%d\n", numValues);
    if (this->colorTableName != "")
    {
        const char *str = this->colorTableName;
        fprintf(f, "Name=%s\n", str);
    }
    else
    {
        int i;

        fprintf(f, "Name=Custom\n");
        fprintf(f, "NumberOfGradientEdges=%d\n", this->numberOfGradientEdges);
        fprintf(f, "InterPolationMode=%d\n", this->interpolationMode);
        for (i = 0; i < this->numberOfGradientEdges; i++)
        {
            fprintf(f, "%lf %lf %lf %lf %lf\n", this->gradientEdge[i].x, this->gradientEdge[i].r,
                    this->gradientEdge[i].g, this->gradientEdge[i].b, this->gradientEdge[i].a);
        }
    }

    fclose(f);
}

void vtkColorTable::UpdateColorTable()
{
    int numValues;
    int index;
    int i;

    numValues = this->lut->GetNumberOfTableValues();

    index = 0;
    for (i = 0; i < numValues; i++)
    {
        const double pi = 3.141592653589793;
        double x, r, g, b, a;
        double d;                                 // interpolation distance between x and lower gradient edge

        x = (numValues > 1) ? ((double)i) / (numValues - 1) : 0;
        while (x > gradientEdge[index + 1].x)
        {
            index++;
        }
        d = (x - gradientEdge[index].x) / (gradientEdge[index + 1].x - gradientEdge[index].x);
        switch (this->interpolationMode)
        {
            case GRADIENT_INTERPOLATION_MODE_LINEAR:
                // use d as-is
                break;
            case GRADIENT_INTERPOLATION_MODE_SQRT:
                d = sqrt(d);
                break;
            case GRADIENT_INTERPOLATION_MODE_SCURVE:
                d = (1 + cos(1 - d * pi)) / 2;
                break;
        }
        r = gradientEdge[index].r * (1 - d) + gradientEdge[index + 1].r * d;
        g = gradientEdge[index].g * (1 - d) + gradientEdge[index + 1].g * d;
        b = gradientEdge[index].b * (1 - d) + gradientEdge[index + 1].b * d;
        a = gradientEdge[index].a * (1 - d) + gradientEdge[index + 1].a * d;
        this->lut->SetTableValue(i, r, g, b, a);
    }

    this->InvokeEvent("ColorTableChanged");
}

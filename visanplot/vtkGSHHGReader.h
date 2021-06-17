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

#ifndef __vtkGSHHGReader_h
#define __vtkGSHHGReader_h

#include <stdio.h>

#include "vtkPolyDataAlgorithm.h"
#include "visanplotModule.h"

class VISANPLOT_EXPORT vtkGSHHGReader : public vtkPolyDataAlgorithm
{
    public:
        vtkTypeMacro(vtkGSHHGReader, vtkPolyDataAlgorithm);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkGSHHGReader *New();

        // Description:
        // Specify file name of GSHHG file.
        vtkSetStringMacro(FileName);
        vtkGetStringMacro(FileName);

        // Description:
        // Specify the maximum level of data to be read.
        // For coastline data, level 1 data comprises the mayor coastlines
        // and higher level data are rivers and lakes.
        vtkSetMacro(MaxLevel, int);
        vtkGetMacro(MaxLevel, int);

    protected:
        vtkGSHHGReader();
        ~vtkGSHHGReader() override;

        int RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                        vtkInformationVector *outputVector) override;

        char *FileName;
        int MaxLevel;

    private:
        vtkGSHHGReader(const vtkGSHHGReader&) = delete;
        void operator=(const vtkGSHHGReader&) = delete;

        int readint(FILE *f, int *value);
        int readshort(FILE *f, short *value);
};
#endif

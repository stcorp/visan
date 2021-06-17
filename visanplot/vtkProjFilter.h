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

#ifndef __vtkProjFilter_h
#define __vtkProjFilter_h

#include "vtkPolyDataAlgorithm.h"
#include "visanplotModule.h"

#include <vector>

// (Pseudo) Cylindrical projections:
// - Lambert Cylindrical Equal Area
#define VTK_PROJ_LAMBERT_CYLINDRICAL        1
// - Plate Caree
#define VTK_PROJ_PLATE_CAREE                2
// - Mollweide
#define VTK_PROJ_MOLLWEIDE                  3
// - Robinson
#define VTK_PROJ_ROBINSON                   4

// Azimuthal projections:
// - Lambert Azimuthal
#define VTK_PROJ_LAMBERT_AZIMUTHAL          5
// - Azimuthal Equidistant
#define VTK_PROJ_AZIMUTHAL_EQUIDISTANT      6

// 3D projections
#define VTK_PROJ_3D                         7

class VISANPLOT_EXPORT vtkProjFilter : public vtkPolyDataAlgorithm
{
    public:
        vtkTypeMacro(vtkProjFilter, vtkPolyDataAlgorithm);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkProjFilter *New();

        // Description:
        // The type of projections that needs to be performed
        // Valid projections are:
        // - Lambert Cylindrical Equal Area
        // - Plate Caree
        // - Mollweide
        // - Robinson
        // - Lambert Azimuthal
        // - Azimuthal Equidistant
        // - 3D
        // The default projection is the Plate Caree projection
        vtkSetClampMacro(Projection, int, 1, 7);
        vtkGetMacro(Projection, int);

        // Description:
        // The default height to use in case the heights of the input are 0
        // The default is 1.0.
        // This property is only used for 3D projections.
        vtkSetMacro(ReferenceHeight, double);
        vtkGetMacro(ReferenceHeight, double);

        // Description:
        // The latitude value in degrees of the center position of the map.
        // The default is 0 degrees.
        // This property is not used for some projections.
        vtkSetClampMacro(CenterLatitude, double, -90, 90);
        vtkGetMacro(CenterLatitude, double);

        // Description:
        // The longitude value in degrees of the center position of the map.
        // The default is 0 degrees.
        // This property is not used for some projections.
        vtkSetClampMacro(CenterLongitude, double, -180, 180);
        vtkGetMacro(CenterLongitude, double);

        // Description:
        // Geographical positions that can not be properly mapped by a certain
        // projection will be moved a tiny amount to bring it back on the map.
        // The amount such points are shifted is determined by the value of Eps.
        // The default value of Eps is 0.00001.
        // The unit of Eps is 'degrees'.
        vtkSetMacro(Eps, double);
        vtkGetMacro(Eps, double);

        // Description:
        // When the distance between two points for a line or poly in the projected
        // space is larger than this value then one or more intermediate points will
        // be inserted in order to reduce the distance between consecutive points.
        // The default value of InterpolationDistance is 0.005.
        // For cylindrical and azimuthal projections the distance is the carthesian
        // distance within the projected space, which has an extent of [0, 1]x[0, 1].
        // For 3D projections the distance is the arcdistance between two points (in
        // degrees) divided by 360 (so the default InterpolationDistance is 0.005 x
        // 360 = 1.8 degrees). The radius of 3D projected points is ignored when
        // calculating the distance (i.e. distances are taken along a unit sphere).
        vtkSetMacro(InterpolationDistance, double);
        vtkGetMacro(InterpolationDistance, double);

        // Description:
        // When using an Azimuthal projection some polygons that lie near the
        // cutting point may be triangulated incorrectly by VTK. To remove such
        // polygons for every polygon all points are measured against the cutting
        // point. If the arc distance (in degrees) between the farthest point in the
        // polygon and the cutting point is below the AzimuthalIgnorePolyDistance then
        // the polygon is not included in the output.
        // The default value of AzimuthalIgnorePolyDistance is 7 (degrees).
        vtkSetMacro(AzimuthalIgnorePolyDistance, double);
        vtkGetMacro(AzimuthalIgnorePolyDistance, double);

        // Description:
        // Get X/Y ratio of the current projection.
        double GetXYRatio();

        static void GetExtent(int projection, double extent[6]);
        static void NormalizedProjection2D(int projection, double centerLat, double centerLon,
                                           double lat, double lon, double &x, double &y);
        static std::vector<double> NormalizedProjection2D(int projection, double centerLat, double centerLon,
                                                          double lat, double lon);
        static void NormalizedDeprojection2D(int projection, double centerLat, double centerLon,
                                             double x, double y, double &lat, double &lon);
        static std::vector<double> NormalizedDeprojection2D(int projection, double centerLat, double centerLon,
                                                            double x, double y);

    protected:
        vtkProjFilter();

        int RequestData(vtkInformation* request, vtkInformationVector** inputVector,
                        vtkInformationVector* outputVector) override;

        void GetExtent(double extent[6]);
        void Perform3DProjection(vtkPolyData *input);
        void PerformAzimuthalProjection(vtkPolyData *input);
        void PerformCylindricalProjection(vtkPolyData *input);

        double Eps;
        int Projection;
        double ReferenceHeight;
        double CenterLatitude;
        double CenterLongitude;
        double InterpolationDistance;
        double AzimuthalIgnorePolyDistance;

    private:
        vtkProjFilter(const vtkProjFilter&) = delete;
        void operator=(const vtkProjFilter&) = delete;
};
#endif

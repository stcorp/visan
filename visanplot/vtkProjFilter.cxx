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

#include "vtkProjFilter.h"

#include <math.h>
#include <string.h>

#include "vtkCell.h"
#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkIdList.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkPolyData.h"
#include "vtkSmartPointer.h"
#include "vtkUnstructuredGrid.h"

#include "proj.h"

#ifndef RAD_TO_DEG
#define RAD_TO_DEG    57.295779513082321
#endif
#ifndef DEG_TO_RAD
#define DEG_TO_RAD   .017453292519943296
#endif

vtkStandardNewMacro(vtkProjFilter);

// Find the arc distance in degrees between two points p and q, where p and q
// are given in (x,y,z) coordinates
static double arcdistancexyz(double px, double py, double pz, double qx, double qy, double qz)
{
    double R = sqrt((px * px + py * py + pz * pz) * (qx * qx + qy * qy + qz * qz));
    if (R == 0)
    {
        // If either or both p and q are (0,0,0) then return 0
        return 0;
    }

    // the arc-distance is the arccos of the normalized inproduct of p and q
    return RAD_TO_DEG * acos((px * qx + py * qy + pz * qz) / R);
}

// Find the arc distance in degrees between two points p and q, where p and q
// are given in (longitude,latitude) angles (phi,tau)
static double arcdistance(double phi_p, double tau_p, double phi_q, double tau_q)
{
    // pp = phi_p (longitude)
    // tp = tau_p (latitude)
    // pq = phi_q (longitude)
    // tq = tau_q (latitude)

    double pp = phi_p * DEG_TO_RAD;
    double tp = tau_p * DEG_TO_RAD;
    double pq = phi_q * DEG_TO_RAD;
    double tq = tau_q * DEG_TO_RAD;

    double cpp = cos(pp);
    double spp = sin(pp);
    double ctp = cos(tp);
    double stp = sin(tp);
    double cpq = cos(pq);
    double spq = sin(pq);
    double ctq = cos(tq);
    double stq = sin(tq);

    double px = cpp * ctp;
    double py = spp * ctp;
    double pz = stp;

    double qx = cpq * ctq;
    double qy = spq * ctq;
    double qz = stq;

    // the arc-distance is the arccos of the inproduct of p and q
    return RAD_TO_DEG * acos(px * qx + py * qy + pz * qz);
}

// Calculate the latitude (tau_u) of the point u that lies on the greatcircle
// through p and q where the longitude of point u is given (phi_u)
static double cuttingpoint(double phi_p, double tau_p, double phi_q,
double tau_q, double phi_u)
{
    // pp = phi_p (longitude)
    // tp = tau_p (latitude)
    // pq = phi_q (longitude)
    // tq = tau_q (latitude)

    double pp = phi_p * DEG_TO_RAD;
    double tp = tau_p * DEG_TO_RAD;
    double pq = phi_q * DEG_TO_RAD;
    double tq = tau_q * DEG_TO_RAD;
    double pu = phi_u * DEG_TO_RAD;

    double cpp = cos(pp);
    double spp = sin(pp);
    double ctp = cos(tp);
    double stp = sin(tp);
    double cpq = cos(pq);
    double spq = sin(pq);
    double ctq = cos(tq);
    double stq = sin(tq);
    double cpu = cos(pu);
    double spu = sin(pu);

    double px = cpp * ctp;
    double py = spp * ctp;
    double pz = stp;

    double qx = cpq * ctq;
    double qy = spq * ctq;
    double qz = stq;

    // n = p x q (cross product)
    double nx =   py * qz - pz * qy;
    double ny = -(px * qz - pz * qx);
    double nz =   px * qy - py * qx;

    // calculate ||n||
    double norm_n = sqrt(nx*nx+ny*ny+nz*nz);

    // if ||n|| == 0 then p and q are opposite or identical points and
    // we can't interpolate -> just return latitude of p (tau_p)
    if (norm_n == 0)
    {
        return tau_p;
    }

    // normalize n
    nx = nx / norm_n;
    ny = ny / norm_n;
    nz = nz / norm_n;

    // calculate cos(phi_n), sin(phi_n), cos(tau_n), sin(tau_n)
    double stn = nz;
    double ctn = sqrt(1 - stn * stn);             // because stn^2 + ctn^2 = 1 and ctn >= 0
    double cpn, spn;
    if (ctn == 0)
    {
        // we are at one of the poles -> chose phi_n = 0
        cpn = 1;
        spn = 0;
    }
    else
    {
        cpn = nx / ctn;
        spn = ny / ctn;
    }

    // find tau_u for the point u that has the required longitude (phi_u)
    // we transform the creatcircle through p and q to the creatcircle
    // that runs through the poles and (-90, 0) and (0, 90) (i.e. the y-z plane)
    // The transformation using rotation matrixes Ry and Rz should thus follow:
    // (nx, ny, nz) = Rz * Ry * (1, 0, 0) (this is the transformation of the
    // normals)
    // This results in
    //
    // / cpn -spn 0 \
    // Rz = | spn  cpn 0 |
    //      \  0    0  1 /
    //
    //      / ctn 0 -stn \
    // Ry = |  0  1   0  |
    //      \ stn 0  ctn /
    //
    // and
    //
    //           / ctn*cpn -spn -stn*cpn \
    // Rz * Ry = | ctn*spn  cpn -stn*spn |
    //           \   stn     0     ctn   /
    //
    // The inverse transformation will then be
    //
    //                /  ctn*cpn  ctn*spn stn \
    // (Rz * Ry)^-1 = |   -spn      cpn    0  |
    //                \ -stn*cpn -stn*spn ctn /
    //
    // (0, cos(alpha_u), sin(alpha_u)) = (Rz * Ry)^-1 * u can be reduced to
    // tan(alpha_u) = (cpu*cpn+spu*spn)/(stn*(cpu*spn-spu*cpn)) =>
    //
    double alpha_u = atan2(cpu * cpn + spu * spn, stn * (cpu * spn - spu * cpn));
    // since y = -(cpu*spn+spu*spn)/stn and x = -cpu*spn+spu*cpn, we need to
    // compensate for the sign of -stn when we move it from the y to x in the atan
    // so if -stn < 0 then alpha_u = -alpha_u
    if (-stn < 0)
    {
        alpha_u = -alpha_u;
    }

    // calculate tau_u
    double sau = sin(alpha_u);
    double uz = sau * ctn;
    double tu = asin(uz);

    return tu * RAD_TO_DEG;
}

// Calculate N intermediate points that lie on the greatcircle through p and q
// (given in carthesian coordinates) the resulting points are stored in the
// arrays ux, uz and uz (wich need to be allocated by the caller of this
// function).
// The function returns the amount of intermediate points that were created
// (this is zero if a failure occured).
// The returned points will not include p and/or q
static int intermediatepointsxyz(double px, double py, double pz, double qx, double qy, double qz, int numPoints,
                                 double *ux, double *uy, double *uz)
{
    const double pi = 3.14159265358979;
    int i;

    // determine radius of p and q
    double pr = sqrt(px * px + py * py + pz * pz);
    double qr = sqrt(qx * qx + qy * qy + qz * qz);
    if (pr == 0 || qr == 0)
    {
        return 0;
    }
    // normalize p and q
    px /= pr;
    py /= pr;
    pz /= pr;
    qx /= qr;
    qy /= qr;
    qz /= qr;

    // n = p x q (cross product)
    double nx =   py * qz - pz * qy;
    double ny = -(px * qz - pz * qx);
    double nz =   px * qy - py * qx;

    // calculate ||n||
    double norm_n = sqrt(nx*nx+ny*ny+nz*nz);

    // if ||n|| == 0 then p and q are opposite or identical points and
    // we can't interpolate -> return 0 (no intermediate points created)
    if (norm_n == 0)
    {
        return 0;
    }

    // normalize n
    nx = nx / norm_n;
    ny = ny / norm_n;
    nz = nz / norm_n;

    // calculate cos(phi_n), sin(phi_n), cos(tau_n), sin(tau_n)
    double stn = nz;
    double ctn = sqrt(1 - stn * stn); // because stn^2 + ctn^2 = 1 and ctn >= 0
    double cpn, spn;
    if (ctn == 0)
    {
        // we are at one of the poles -> chose phi_n = 0
        cpn = 1;
        spn = 0;
    }
    else
    {
        cpn = nx / ctn;
        spn = ny / ctn;
    }

    // find alpha_p and alpha_q
    // we transform the creatcircle through p and q to the creatcircle
    // that runs through the poles and (-90, 0) and (0, 90) (i.e. the y-z plane)
    // The transformation using rotation matrixes Ry and Rz should thus follow:
    // (nx, ny, nz) = Rz * Ry * (1, 0, 0) (this is the transformation of the
    // normals)
    // This results in
    //
    //      / cpn -spn 0 \
    // Rz = | spn  cpn 0 |
    //      \  0    0  1 /
    //
    //      / ctn 0 -stn \
    // Ry = |  0  1   0  |
    //      \ stn 0  ctn /
    //
    // and
    //
    //           / ctn*cpn -spn -stn*cpn \
    // Rz * Ry = | ctn*spn  cpn -stn*spn |
    //           \   stn     0     ctn   /
    //
    // The inverse transformation will then be
    //
    //                /  ctn*cpn  ctn*spn stn \
    // (Rz * Ry)^-1 = |   -spn      cpn    0  |
    //                \ -stn*cpn -stn*spn ctn /
    //
    // (0, cos(alpha_p), sin(alpha_p)) = (Rz * Ry)^-1 * p =>
    //
    double alpha_p = atan2(-px * stn * cpn - py * stn * spn + pz * ctn, -px * spn + py * cpn);

    // do the same for q
    double alpha_q = atan2(-qx * stn * cpn - qy * stn * spn + qz * ctn, -qx * spn + qy * cpn);

    // adapt alpha_q such that we take the shortest route from p to q
    // (alpha has a range of [-pi, pi])
    if (alpha_q - alpha_p < pi)
    {
        alpha_q = alpha_q + 2 * pi;
    }
    if (alpha_q - alpha_p > pi)
    {
        alpha_q = alpha_q - 2 * pi;
    }

    // now vary alpha from alpha_p to alpha_q (not including p and q)
    for (i = 0; i < numPoints; i++)
    {
        // calculate intermediate point u
        double alpha_u = alpha_p + (i + 1) * (alpha_q - alpha_p) / (numPoints + 1);

        // u = (Rz * Ry) * (0, cos(alpha_u), sin(alpha_u))
        double cau = cos(alpha_u);
        double sau = sin(alpha_u);

        // radius is linear interpolation between pr and qr
        double ur = pr + (i + 1) * (qr - pr) / (numPoints + 1);

        ux[i] = ur * (-cau * spn - sau * stn * cpn);
        uy[i] = ur * ( cau * cpn - sau * stn * spn);
        uz[i] = ur * ( sau * ctn);
    }

    return numPoints;
}

// Calculate N intermediate points that lie on the greatcircle through p and q
// (given in longitude/latitude coordinates) the resulting points are stored in the arrays phi_u and tau_u
// (wich need to be allocated by the caller of this function).
// The function returns the amount of intermediate points that were created (this is zero if a failure occured).
// The returned points will not include p and/or q
static int intermediatepoints(double phi_p, double tau_p, double phi_q, double tau_q, int numPoints, double *phi_u,
                              double *tau_u)
{
    const double pi = 3.14159265358979;
    int i;

    // pp = phi_p (longitude)
    // tp = tau_p (latitude)
    // pq = phi_q (longitude)
    // tq = tau_q (latitude)

    double pp = phi_p * DEG_TO_RAD;
    double tp = tau_p * DEG_TO_RAD;
    double pq = phi_q * DEG_TO_RAD;
    double tq = tau_q * DEG_TO_RAD;

    double cpp = cos(pp);
    double spp = sin(pp);
    double ctp = cos(tp);
    double stp = sin(tp);
    double cpq = cos(pq);
    double spq = sin(pq);
    double ctq = cos(tq);
    double stq = sin(tq);

    double px = cpp * ctp;
    double py = spp * ctp;
    double pz = stp;

    double qx = cpq * ctq;
    double qy = spq * ctq;
    double qz = stq;

    // n = p x q (cross product)
    double nx =   py * qz - pz * qy;
    double ny = -(px * qz - pz * qx);
    double nz =   px * qy - py * qx;

    // calculate ||n||
    double norm_n = sqrt(nx*nx+ny*ny+nz*nz);

    // if ||n|| == 0 then p and q are opposite or identical points and
    // we can't interpolate -> return 0 (no intermediate points created)
    if (norm_n == 0)
    {
        return 0;
    }

    // normalize n
    nx = nx / norm_n;
    ny = ny / norm_n;
    nz = nz / norm_n;

    // calculate cos(phi_n), sin(phi_n), cos(tau_n), sin(tau_n)
    double stn = nz;
    double ctn = sqrt(1 - stn * stn); // because stn^2 + ctn^2 = 1 and ctn >= 0
    double cpn, spn;
    if (ctn == 0)
    {
        // we are at one of the poles -> chose phi_n = 0
        cpn = 1;
        spn = 0;
    }
    else
    {
        cpn = nx / ctn;
        spn = ny / ctn;
    }

    // find alpha_p and alpha_q
    // we transform the creatcircle through p and q to the creatcircle
    // that runs through the poles and (-90, 0) and (0, 90) (i.e. the y-z plane)
    // The transformation using rotation matrixes Ry and Rz should thus follow:
    // (nx, ny, nz) = Rz * Ry * (1, 0, 0) (this is the transformation of the
    // normals)
    // This results in
    //
    //      / cpn -spn 0 \
    // Rz = | spn  cpn 0 |
    //      \  0    0  1 /
    //
    //      / ctn 0 -stn \
    // Ry = |  0  1   0  |
    //      \ stn 0  ctn /
    //
    // and
    //
    //           / ctn*cpn -spn -stn*cpn \
    // Rz * Ry = | ctn*spn  cpn -stn*spn |
    //           \   stn     0     ctn   /
    //
    // The inverse transformation will then be
    //
    //                /  ctn*cpn  ctn*spn stn \
    // (Rz * Ry)^-1 = |   -spn      cpn    0  |
    //                \ -stn*cpn -stn*spn ctn /
    //
    // (0, cos(alpha_p), sin(alpha_p)) = (Rz * Ry)^-1 * p =>
    //
    double alpha_p = atan2(-px * stn * cpn - py * stn * spn + pz * ctn, -px * spn + py * cpn);

    // do the same for q
    double alpha_q = atan2(-qx * stn * cpn - qy * stn * spn + qz * ctn, -qx * spn + qy * cpn);

    // adapt alpha_q such that we take the shortest route from p to q
    // (alpha has a range of [-pi, pi])
    if (alpha_q - alpha_p < pi)
    {
        alpha_q = alpha_q + 2 * pi;
    }
    if (alpha_q - alpha_p > pi)
    {
        alpha_q = alpha_q - 2 * pi;
    }

    // now vary alpha from alpha_p to alpha_q (not including p and q)
    for (i = 0; i < numPoints; i++)
    {
        // calculate intermediate point u
        double alpha_u = alpha_p + (i + 1) * (alpha_q - alpha_p) / (numPoints + 1);

        // u = (Rz * Ry) * (0, cos(alpha_u), sin(alpha_u))
        double cau = cos(alpha_u);
        double sau = sin(alpha_u);

        double ux = -cau * spn - sau * stn * cpn;
        double uy =  cau * cpn - sau * stn * spn;
        double uz =  sau * ctn;

        // calculate phi_u and tau_u
        double tu = asin(uz);
        // atan2 automatically 'does the right thing' ((ux,uy)=(0,0) -> pu=0)
        double pu = atan2(uy, ux);

        tau_u[i] = tu * RAD_TO_DEG;
        phi_u[i] = pu * RAD_TO_DEG;
    }

    return numPoints;
}

static void CreateInterPoints(double *p1, double *projP1, double *p2, double *projP2, double *extent,
                              vtkPoints *newPoints, vtkPointData *pointData, vtkPointData *newPointData,
                              vtkIdType firstPt, vtkIdList *idList, PJ *projRef, double interpolationDistance,
                              int cylindricalProjection)
{
    static int depth = 0;
    double distance;

    if (interpolationDistance <= 0)
    {
        return;
    }

    if (depth > 3)
    {
        // prevent endless recursion;
        return;
    }

    distance = sqrt((projP1[0] - projP2[0]) * (projP1[0] - projP2[0]) +
                    (projP1[1] - projP2[1]) * (projP1[1] - projP2[1]));
    if (distance > interpolationDistance)
    {
        double *phi_u;
        double *tau_u;
        int numPoints;
        int result;

        numPoints = (int)(distance / interpolationDistance) + 1;

        if ( (phi_u = new double[numPoints]) == nullptr)
        {
            return;
        }
        if ( (tau_u = new double[numPoints]) == nullptr)
        {
            delete [] phi_u;
            return;
        }

        result = intermediatepoints(p1[0], p1[1], p2[0], p2[1], numPoints, phi_u, tau_u);
        if (result == numPoints)
        {
            double prevP[3];
            double projPrevP[3];
            int k;

            prevP[0] = p1[0];
            prevP[1] = p1[1];
            prevP[2] = p1[2];
            projPrevP[0] = projP1[0];
            projPrevP[1] = projP1[1];
            projPrevP[2] = projP1[2];

            for (k = 0; k < numPoints; k++)
            {
                double interP[3];
                PJ_COORD projLPData;
                PJ_COORD projXYData;

                interP[0] = phi_u[k];
                interP[1] = tau_u[k];
                interP[2] = projP1[2] + (k + 1) * (projP2[2] - projP1[2]) / (numPoints + 1);
                projLPData.lp.lam = phi_u[k] * DEG_TO_RAD;
                projLPData.lp.phi = tau_u[k] * DEG_TO_RAD;
                projXYData = proj_trans(projRef, PJ_FWD, projLPData);
                if (projXYData.xy.x != HUGE_VAL && projXYData.xy.y != HUGE_VAL)
                {
                    double projInterP[3];
                    vtkIdType projPt;

                    projInterP[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
                    projInterP[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
                    projInterP[2] = interP[2];
                    if (cylindricalProjection)
                    {
                        if ((projP1[0] < 0.5 && projP2[0] < 0.5 && projInterP[0] > 0.5) ||
                            (projP1[0] > 0.5 && projP2[0] > 0.5 && projInterP[0] < 0.5))
                        {
                            // Map projected point to correct edge
                            projInterP[0] = 1.0 - projInterP[0];
                        }
                    }
                    // recursively call this function to check whether our interpolated
                    // points are now within the required margins
                    depth++;
                    CreateInterPoints(prevP, projPrevP, interP, projInterP, extent, newPoints, pointData, newPointData,
                                      firstPt, idList, projRef, interpolationDistance, cylindricalProjection);
                    depth--;
                    projPt = newPoints->InsertNextPoint(projInterP);
                    newPointData->CopyData(pointData, firstPt, projPt);
                    idList->InsertNextId(projPt);
                    prevP[0] = interP[0];
                    prevP[1] = interP[1];
                    prevP[2] = interP[2];
                    projPrevP[0] = projInterP[0];
                    projPrevP[1] = projInterP[1];
                    projPrevP[2] = projInterP[2];
                }
            }
            if (!(prevP[0] == p1[0] && prevP[1] == p1[1]))
            {
                // recursively call this function to check whether our interpolated
                // points are now within the required margins
                depth++;
                CreateInterPoints(prevP, projPrevP, p2, projP2, extent, newPoints, pointData, newPointData, firstPt,
                                  idList, projRef, interpolationDistance, cylindricalProjection);
                depth--;
            }
        }

        delete [] tau_u;
        delete [] phi_u;
    }
}

//
// The Projections currently only support Verts, Lines, and Polys.
// Strips are thus currently not supported.
//

vtkProjFilter::vtkProjFilter()
{
    this->ReferenceHeight = 1.007;
    this->CenterLatitude = 0.0;
    this->CenterLongitude = 0.0;
    this->Eps = 0.00001;
    this->InterpolationDistance = 0.005;
    this->AzimuthalIgnorePolyDistance = 7;
    this->Projection = VTK_PROJ_PLATE_CAREE;
}

double vtkProjFilter::GetXYRatio()
{
    double extent[6];

    GetExtent(extent);
    return (extent[3] - extent[2]) / (extent[1] - extent[0]);
}

int vtkProjFilter::RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                               vtkInformationVector *outputVector)
{
    vtkDebugMacro(<< "Performing projection on polygonal data");

    // attributes Input, Output, and Points can be a nullptr
    // attributes Verts, Lines, Polys, Strips, PointData, and CellData are
    // never a nullptr (but can be empty)

    vtkPolyData *input = vtkPolyData::SafeDownCast(this->GetInput());
    if (input == nullptr || input->GetPoints() == nullptr)
    {
        return 1;
    }

    // Because vtkPolyData can't handle cellData properly when using a
    // combination of Verts, Lines, Polys, and/or Strips we restrict this
    // filter to vtkPolyData with only one type of cells
    if ((input->GetVerts()->GetNumberOfCells() > 0) + (input->GetLines()->GetNumberOfCells() > 0) +
        (input->GetPolys()->GetNumberOfCells() > 0) + (input->GetStrips()->GetNumberOfCells() > 0) > 1)
    {
        vtkErrorMacro(<< "this filter does not work on polydata with different types of cells");
        return 0;
    }

    switch (this->Projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
        case VTK_PROJ_PLATE_CAREE:
        case VTK_PROJ_MOLLWEIDE:
        case VTK_PROJ_ROBINSON:
            this->PerformCylindricalProjection(input);
            break;
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            this->PerformAzimuthalProjection(input);
            break;
        case VTK_PROJ_3D:
            this->Perform3DProjection(input);
            break;
        default:
            vtkErrorMacro(<< "unknown projection");
            return 0;
    }

    return 1;
}

void vtkProjFilter::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os,indent);

    os << indent << "Projection: ";
    switch (this->Projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
            os << "Lambert Cylindrical Equal Area" << endl;
            break;
        case VTK_PROJ_PLATE_CAREE:
            os << "Plate Caree" << endl;
            break;
        case VTK_PROJ_MOLLWEIDE:
            os << "Mollweide" << endl;
            break;
        case VTK_PROJ_ROBINSON:
            os << "Robinson" << endl;
            break;
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
            os << "Lambert Azimuthal Equal Area" << endl;
            break;
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            os << "Azimuthal Equidistant" << endl;
            break;
        case VTK_PROJ_3D:
            os << "3D" << endl;
            break;
        default:
            os << "unknown (" << this->Projection << ")" << endl;
            break;
    }
    os << indent << "Center Latitude: " << this->CenterLatitude << endl;
    os << indent << "Center Longitude: " << this->CenterLongitude << endl;
}

// extent = (min_x, max_x, min_y, max_y, min_z, max_z)
void vtkProjFilter::GetExtent(int projection, double extent[6])
{
    switch (projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
            extent[0] = -3.1416;
            extent[1] =  3.1416;
            extent[2] = -1.0;
            extent[3] =  1.0;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_PLATE_CAREE:
            extent[0] = -3.1416;
            extent[1] =  3.1416;
            extent[2] = -1.5710;
            extent[3] =  1.5710;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_MOLLWEIDE:
            extent[0] = -2.83;
            extent[1] =  2.83;
            extent[2] = -1.415;
            extent[3] =  1.415;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_ROBINSON:
            extent[0] = -2.6667;
            extent[1] =  2.6667;
            extent[2] = -1.3525;
            extent[3] =  1.3525;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
            extent[0] = -2.0;
            extent[1] =  2.0;
            extent[2] = -2.0;
            extent[3] =  2.0;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            extent[0] = -3.1416;
            extent[1] =  3.1416;
            extent[2] = -3.1416;
            extent[3] =  3.1416;
            extent[4] =  0.0;
            extent[5] =  0.0;
            break;
        case VTK_PROJ_3D:
        default:
            extent[0] = -1.0;
            extent[1] =  1.0;
            extent[2] = -1.0;
            extent[3] =  1.0;
            extent[4] = -1.0;
            extent[5] =  1.0;
            break;
    }
}

void vtkProjFilter::NormalizedProjection2D(int projection, double centerLat, double centerLon,
                                           double lat, double lon, double &x, double &y)
{
    double extent[6];
    PJ *projRef;
    PJ_COORD projLPData;
    PJ_COORD projXYData;
    char centerLatitudeParam[100];
    char centerLongitudeParam[100];

    static char *parameters[] =
    {
        (char *)"",
        (char *)"",
        (char *)"",
        (char *)"R=1.0",
        (char *)"ellps=WGS84",
        (char *)"no_defs"
    };

    switch (projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
            parameters[0] = (char *)"proj=cea";
            break;
        case VTK_PROJ_PLATE_CAREE:
            parameters[0] = (char *)"proj=eqc";
            break;
        case VTK_PROJ_MOLLWEIDE:
            parameters[0] = (char *)"proj=moll";
            break;
        case VTK_PROJ_ROBINSON:
            parameters[0] = (char *)"proj=robin";
            break;
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
            parameters[0] = (char *)"proj=laea";
            break;
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            parameters[0] = (char *)"proj=aeqd";
            break;
        case VTK_PROJ_3D:
        default:
            // this is meaningles ...
            x = y = 0.0;
            return;
            break;
    }

    sprintf(centerLatitudeParam, "lat_0=%7.3f", centerLat);
    sprintf(centerLongitudeParam, "lon_0=%7.3f", centerLon);
    parameters[1] = centerLatitudeParam;
    parameters[2] = centerLongitudeParam;

    // initialize the projection library
    projRef = proj_create_argv(0, sizeof(parameters)/sizeof(char *), parameters);
    if (projRef == 0)
    {
        return;
    }

    vtkProjFilter::GetExtent(projection, extent);

    // map the point lat,lon to projection coordinates
    projLPData.lp.lam = lon * DEG_TO_RAD;
    projLPData.lp.phi = lat * DEG_TO_RAD;
    projXYData = proj_trans(projRef, PJ_FWD, projLPData);

    // normalize the projection
    x = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
    y = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);

    proj_destroy(projRef);
}

std::vector<double> vtkProjFilter::NormalizedProjection2D(int projection, double centerLat, double centerLon,
                                                          double lat, double lon)
{
    std::vector<double> coord(2);
    vtkProjFilter::NormalizedProjection2D(projection, centerLat, centerLon, lat, lon, coord[0], coord[1]);
    return coord;
}

void vtkProjFilter::NormalizedDeprojection2D(int projection, double centerLat, double centerLon,
                                             double x, double y, double &lat, double &lon)
{
    double extent[6];
    PJ *projRef;
    PJ_COORD projLPData;
    PJ_COORD projXYData;
    char centerLatitudeParam[100];
    char centerLongitudeParam[100];

    static char *parameters[] =
    {
        (char *)"",
        (char *)"",
        (char *)"",
        (char *)"R=1.0",
        (char *)"ellps=WGS84",
        (char *)"no_defs"
    };

    switch (projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
            parameters[0] = (char *)"proj=cea";
            break;
        case VTK_PROJ_PLATE_CAREE:
            parameters[0] = (char *)"proj=eqc";
            break;
        case VTK_PROJ_MOLLWEIDE:
            parameters[0] = (char *)"proj=moll";
            break;
        case VTK_PROJ_ROBINSON:
            parameters[0] = (char *)"proj=robin";
            break;
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
            parameters[0] = (char *)"proj=laea";
            break;
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            parameters[0] = (char *)"proj=aeqd";
            break;
        case VTK_PROJ_3D:
        default:
            // this is meaningles ...
            lat = lon = 0.0;
            return;
    }

    sprintf(centerLatitudeParam, "lat_0=%7.3f", centerLat);
    sprintf(centerLongitudeParam, "lon_0=%7.3f", centerLon);
    parameters[1] = centerLatitudeParam;
    parameters[2] = centerLongitudeParam;

    // initialize the projection library
    projRef = proj_create_argv(0, sizeof(parameters)/sizeof(char *), parameters);
    if (projRef == 0)
    {
        return;
    }

    vtkProjFilter::GetExtent(projection, extent);

    // denormalize the projection point
    projXYData.xy.x = x * (extent[1] - extent[0]) + extent[0];
    projXYData.xy.y = y * (extent[3] - extent[2]) + extent[2];

    // map the projected point to lat,lon
    projLPData = proj_trans(projRef, PJ_INV, projXYData);

    // convert to degrees and consider the range.
    lon = projLPData.lp.lam * RAD_TO_DEG;
    lat = projLPData.lp.phi * RAD_TO_DEG;
    if (lon < -180.0)
    {
        lon = -180.0;
    }
    else if (lon > 180.0)
    {
        lon = 180.0;
    }
    if (lat < -90.0)
    {
        lat = -90.0;
    }
    else if (lat > 90.0)
    {
        lon = 90.0;
    }

    proj_destroy(projRef);
}

std::vector<double> vtkProjFilter::NormalizedDeprojection2D(int projection, double centerLat, double centerLon,
                                                            double x, double y)
{
    std::vector<double> coord(2);
    vtkProjFilter::NormalizedDeprojection2D(projection, centerLat, centerLon, x, y, coord[0], coord[1]);
    return coord;
}

void vtkProjFilter::GetExtent(double extent[6])
{
    vtkProjFilter::GetExtent(this->Projection, extent);
}

void vtkProjFilter::Perform3DProjection(vtkPolyData *input)
{
    vtkPoints *points;
    vtkCellArray *verts;
    vtkCellArray *lines;
    vtkCellArray *polys;
    vtkPointData *pointData;
    vtkPointData *newPointData;
    vtkCellData *cellData;
    vtkCellData *newCellData;
    vtkIdType id;
    vtkIdType numPoints;

    vtkDebugMacro(<< "Performing 3D projection on polygonal data");

    points = input->GetPoints();
    verts = input->GetVerts();
    lines = input->GetLines();
    polys = input->GetPolys();
    pointData = input->GetPointData();
    cellData = input->GetCellData();

    // create the vtkCellArray in output
    vtkPolyData *output = this->GetOutput();
    output->Allocate(input);
    newPointData = output->GetPointData();
    newCellData = output->GetCellData();

    // points need to be transfered and projected
    numPoints = points->GetNumberOfPoints();
    auto newPoints = vtkSmartPointer<vtkPoints>::New();
    newPoints->SetDataTypeToFloat();
    newPoints->SetNumberOfPoints(numPoints);

    for (id = 0; id < numPoints; ++id)
    {
        double sinLatitude, cosLatitude, sinLongitude, cosLongitude;
        double pt[3];
        double R;

        points->GetPoint(id, pt);
        R = this->ReferenceHeight;
        if (pt[2] > 0)
        {
            // use z value as radius
            R = pt[2];
        }
        sinLongitude = sin(pt[0] * DEG_TO_RAD);
        cosLongitude = cos(pt[0] * DEG_TO_RAD);
        sinLatitude = sin(pt[1] * DEG_TO_RAD);
        cosLatitude = cos(pt[1] * DEG_TO_RAD);
        pt[0] = R * cosLongitude * cosLatitude;
        pt[1] = R * sinLongitude * cosLatitude;
        pt[2] = R * sinLatitude;
        newPoints->SetPoint(id, pt);
    }

    output->SetPoints(newPoints);

    // pointData is first copied and later extended as needed
    newPointData->DeepCopy(pointData);

    // Vertices are copied
    if (verts->GetNumberOfCells() > 0)
    {
        auto newVerts = vtkSmartPointer<vtkCellArray>::New();
        output->SetVerts(newVerts);
        newVerts->DeepCopy(verts);
        newCellData->DeepCopy(cellData);
    }

    // Lines are interpolated if necessary
    if (lines->GetNumberOfCells() > 0)
    {
        auto newLines = vtkSmartPointer<vtkCellArray>::New();
        output->SetLines(newLines);
        if (this->InterpolationDistance <= 0)
        {
            newLines->DeepCopy(lines);
            newCellData->DeepCopy(cellData);
        }
        else
        {
            vtkIdType numLines;
            vtkIdType cellId;

            newCellData->CopyAllocate(cellData);

            numLines = lines->GetNumberOfCells();

            auto idList = vtkSmartPointer<vtkIdList>::New();
            idList->Allocate(1000);

            lines->InitTraversal();
            for (cellId = 0; cellId < numLines; cellId++)
            {
                vtkIdType npts;
                vtkIdType const *pts;

                lines->GetNextCell(npts, pts);

                if (npts > 0)
                {
                    double p1[3];
                    int j;

                    newPoints->GetPoint(pts[0], p1);
                    idList->Reset();
                    idList->InsertNextId(pts[0]);

                    for (j = 1; j < npts; j++)
                    {
                        double p2[3];
                        double distance;

                        newPoints->GetPoint(pts[j], p2);
                        distance = arcdistancexyz(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);
                        if (distance > 360 * this->InterpolationDistance)
                        {
                            int numIntermediatePoints;
                            int result;
                            double *ux;
                            double *uy;
                            double *uz;

                            numIntermediatePoints = (int)(distance / (360 * this->InterpolationDistance)) ;
                            if ((ux = new double[numIntermediatePoints]) == nullptr)
                            {
                                return;
                            }
                            if ((uy = new double[numIntermediatePoints]) == nullptr)
                            {
                                delete [] ux;
                                return;
                            }
                            if ((uz = new double[numIntermediatePoints]) == nullptr)
                            {
                                delete [] ux;
                                delete [] uy;
                                return;
                            }
                            result = intermediatepointsxyz(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2],
                                                           numIntermediatePoints, ux, uy, uz);
                            if (result == numIntermediatePoints)
                            {
                                int k;

                                for (k = 0; k < numIntermediatePoints; k++)
                                {
                                    vtkIdType newPt;

                                    newPt = newPoints->InsertNextPoint(ux[k], uy[k], uz[k]);
                                    newPointData->CopyData(pointData, pts[j - 1], newPt);
                                    idList->InsertNextId(newPt);
                                }
                            }

                            delete [] ux;
                            delete [] uy;
                            delete [] uz;
                        }
                        idList->InsertNextId(pts[j]);
                        p1[0] = p2[0];
                        p1[1] = p2[1];
                        p1[2] = p2[2];
                    }

                    if (idList->GetNumberOfIds() > 1)
                    {
                        vtkIdType newCellId;

                        newCellId = output->InsertNextCell(VTK_LINE, idList);
                        newCellData->CopyData(cellData, cellId, newCellId);
                    }
                }
            }
        }
    }

    // Polys are interpolated if necessary
    if (polys->GetNumberOfCells() > 0)
    {
        auto newPolys = vtkSmartPointer<vtkCellArray>::New();
        output->SetPolys(newPolys);
        if (this->InterpolationDistance <= 0)
        {
            newPolys->DeepCopy(polys);
            newCellData->DeepCopy(cellData);
        }
        else
        {
            vtkIdType numPolys;
            vtkIdType cellId;

            newCellData->CopyAllocate(cellData);

            numPolys = polys->GetNumberOfCells();

            auto idList = vtkSmartPointer<vtkIdList>::New();
            idList->Allocate(1000);

            polys->InitTraversal();
            for (cellId = 0; cellId < numPolys; cellId++)
            {
                vtkIdType npts;
                vtkIdType const *pts;

                polys->GetNextCell(npts, pts);

                if (npts > 0)
                {
                    double p1[3];
                    int j;

                    newPoints->GetPoint(pts[0], p1);
                    idList->Reset();
                    idList->InsertNextId(pts[0]);

                    for (j = 1; j < npts; j++)
                    {
                        double p2[3];
                        double distance;

                        newPoints->GetPoint(pts[j], p2);
                        distance = arcdistancexyz(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);
                        if (distance > 360 * this->InterpolationDistance)
                        {
                            int numIntermediatePoints;
                            int result;
                            double *ux;
                            double *uy;
                            double *uz;

                            numIntermediatePoints = (int)(distance / (360 * this->InterpolationDistance)) ;
                            if ( (ux = new double[numIntermediatePoints]) == nullptr)
                            {
                                return;
                            }
                            if ( (uy = new double[numIntermediatePoints]) == nullptr)
                            {
                                delete [] ux;
                                return;
                            }
                            if ( (uz = new double[numIntermediatePoints]) == nullptr)
                            {
                                delete [] ux;
                                delete [] uy;
                                return;
                            }
                            result = intermediatepointsxyz(p1[0], p1[1], p1[2], p2[0], p2[1],
                                p2[2], numIntermediatePoints, ux,
                                uy, uz);
                            if (result == numIntermediatePoints)
                            {
                                int k;

                                for (k = 0; k < numIntermediatePoints; k++)
                                {
                                    vtkIdType newPt;

                                    newPt = newPoints->InsertNextPoint(ux[k], uy[k], uz[k]);
                                    newPointData->CopyData(pointData, pts[j - 1], newPt);
                                    idList->InsertNextId(newPt);
                                }
                            }

                            delete [] ux;
                            delete [] uy;
                            delete [] uz;
                        }
                        idList->InsertNextId(pts[j]);
                        p1[0] = p2[0];
                        p1[1] = p2[1];
                        p1[2] = p2[2];
                    }

                    if (idList->GetNumberOfIds() > 1)
                    {
                        vtkIdType newCellId;

                        newCellId = output->InsertNextCell(VTK_POLYGON, idList);
                        newCellData->CopyData(cellData, cellId, newCellId);
                    }
                }
            }
        }
    }
}

void vtkProjFilter::PerformAzimuthalProjection(vtkPolyData *input)
{
    vtkPoints *points;
    vtkCellArray *verts;
    vtkCellArray *lines;
    vtkCellArray *polys;
    vtkPointData *pointData;
    vtkPointData *newPointData;
    vtkCellData *cellData;
    vtkCellData *newCellData;
    vtkIdType id;
    vtkIdType numPoints;
    PJ *projRef;
    PJ_COORD projLPData;
    PJ_COORD projXYData;
    char centerLatitudeParam[100];
    char centerLongitudeParam[100];
    double extent[6];
    double cuttingLatitude;
    double cuttingLongitude;

    vtkDebugMacro(<< "Performing Azimuthal projection on polygonal data");

    points = input->GetPoints();
    verts = input->GetVerts();
    lines = input->GetLines();
    polys = input->GetPolys();
    pointData = input->GetPointData();
    cellData = input->GetCellData();

    // create the vtkCellArray in output
    vtkPolyData *output = this->GetOutput();
    output->Allocate(input);
    newPointData = output->GetPointData();
    newCellData = output->GetCellData();

    // points need to be transfered and projected
    numPoints = points->GetNumberOfPoints();
    auto newPoints = vtkSmartPointer<vtkPoints>::New();
    newPoints->SetDataTypeToFloat();
    newPoints->SetNumberOfPoints(numPoints);

    if (this->CenterLatitude == 0.0)
    {
        cuttingLatitude = this->CenterLatitude;
    }
    else
    {
        cuttingLatitude = -this->CenterLatitude;
    }
    cuttingLongitude = this->CenterLongitude + 180.0;
    if (cuttingLongitude >= 180.0)
    {
        cuttingLongitude -= 360.0;
    }

    static char *parameters[] =
    {
        (char *)"",
        (char *)"",
        (char *)"",
        (char *)"R=1.0",
        (char *)"ellps=WGS84",
        (char *)"no_defs"
    };

    switch (this->Projection)
    {
        case VTK_PROJ_LAMBERT_AZIMUTHAL:
            parameters[0] = (char *)"proj=laea";
            break;
        case VTK_PROJ_AZIMUTHAL_EQUIDISTANT:
            parameters[0] = (char *)"proj=aeqd";
            break;
        default:
            vtkErrorMacro("Unknown cylindrical projection");
            return;
    }
    sprintf(centerLatitudeParam, "lat_0=%7.3f", this->CenterLatitude);
    sprintf(centerLongitudeParam, "lon_0=%7.3f", this->CenterLongitude);
    parameters[1] = centerLatitudeParam;
    parameters[2] = centerLongitudeParam;

    projRef = proj_create_argv(0, sizeof(parameters)/sizeof(char *), parameters);
    if (projRef == 0)
    {
        vtkErrorMacro(<< "Could not initialize PROJ library (" << proj_errno_string(proj_errno(0)) << ")");
        return;
    }

    GetExtent(extent);

    for (id = 0; id < numPoints; ++id)
    {
        double pt[3];

        points->GetPoint(id, pt);
        while (pt[0] >= 180)
        {
            pt[0] -= 360;
        }
        while (pt[0] < -180)
        {
            pt[0] += 360;
        }
        projLPData.lp.lam = pt[0] * DEG_TO_RAD;
        projLPData.lp.phi = pt[1] * DEG_TO_RAD;
        projXYData = proj_trans(projRef, PJ_FWD, projLPData);
        pt[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
        pt[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
        newPoints->SetPoint(id, pt);
    }

    output->SetPoints(newPoints);

    // pointData is first copied and later extended as needed
    newPointData->DeepCopy(pointData);

    // Vertices are filtered for Verts that correspond with the cutting point
    if (verts->GetNumberOfCells() > 0)
    {
        auto newVerts = vtkSmartPointer<vtkCellArray>::New();
        vtkIdType numVerts;
        vtkIdType cellId;

        // initialize newCellData for CopyData invocations
        newCellData->CopyAllocate(cellData);

        output->SetVerts(newVerts);
        numVerts = verts->GetNumberOfCells();

        verts->InitTraversal();
        for (cellId = 0; cellId < numVerts; cellId++)
        {
            vtkIdType npts;
            vtkIdType const *pts;

            verts->GetNextCell(npts, pts);

            // we ignore cells that do not contain vertices (i.e. only one point)
            if (npts == 1)
            {
                double pt[3];

                newPoints->GetPoint(pts[0], pt);
                if (pt[0] != HUGE_VAL && pt[1] != HUGE_VAL)
                {
                    vtkIdType newCellId;
                    newCellId = output->InsertNextCell(VTK_VERTEX, 1, pts);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
            }
        }
    }

    // Lines need to be filtered for points that correspond with the cutting point
    if (lines->GetNumberOfCells() > 0)
    {
        auto newLines = vtkSmartPointer<vtkCellArray>::New();
        vtkIdType numLines;
        vtkIdType cellId;

        // initialize newCellData for CopyData invocations
        newCellData->CopyAllocate(cellData);

        output->SetLines(newLines);
        numLines = lines->GetNumberOfCells();

        auto idList = vtkSmartPointer<vtkIdList>::New();
        idList->Allocate(1000);

        lines->InitTraversal();
        for(cellId = 0; cellId < numLines; cellId++)
        {
            vtkIdType npts;
            vtkIdType const *pts;

            lines->GetNextCell(npts, pts);

            if (npts > 0)
            {
                double p1[3];
                double projP1[3];
                vtkIdType newCellId;
                int j;

                points->GetPoint(pts[0], p1);
                newPoints->GetPoint(pts[0], projP1);
                while (p1[0] >= 180)
                {
                    p1[0] -= 360;
                }
                while (p1[0] < -180)
                {
                    p1[0] += 360;
                }
                idList->Reset();
                if (projP1[0] != HUGE_VAL && projP1[1] != HUGE_VAL)
                {
                    idList->InsertNextId(pts[0]);
                }

                for (j = 1; j < npts; j++)
                {
                    double p2[3];
                    double projP2[3];

                    points->GetPoint(pts[j], p2);
                    newPoints->GetPoint(pts[j], projP2);
                    while (p2[0] >= 180)
                    {
                        p2[0] -= 360;
                    }
                    while (p2[0] < -180)
                    {
                        p2[0] += 360;
                    }
                    if (projP2[0] == HUGE_VAL || projP2[1] == HUGE_VAL)
                    {
                        // Skip this point and start a new line
                        if (idList->GetNumberOfIds() > 1)
                        {
                            newCellId = output->InsertNextCell(VTK_LINE, idList);
                            newCellData->CopyData(cellData, cellId, newCellId);
                        }
                        idList->Reset();
                    }
                    else
                    {
                        // check for interpolation
                        if (projP1[0] != HUGE_VAL && projP1[1] != HUGE_VAL)
                        {
                            CreateInterPoints(p1, projP1, p2, projP2, extent, newPoints, pointData, newPointData,
                                              pts[j - 1], idList, projRef, this->InterpolationDistance, 0);
                        }
                        idList->InsertNextId(pts[j]);
                    }

                    p1[0] = p2[0];
                    p1[1] = p2[1];
                    p1[2] = p2[2];
                    projP1[0] = projP2[0];
                    projP1[1] = projP2[1];
                    projP1[2] = projP2[2];
                }

                if (idList->GetNumberOfIds() > 1)
                {
                    newCellId = output->InsertNextCell(VTK_LINE, idList);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
            }
        }
    }

    // Polys need to be filtered for points that correspond with the cutting point
    // and polys that lie within the AzimuthalIgnorePolyDistance distance of the
    // cutting point will be filtered out
    if (polys->GetNumberOfCells() > 0)
    {
        auto newPolys = vtkSmartPointer<vtkCellArray>::New();
        vtkIdType numPolys;
        vtkIdType cellId;

        // initialize newCellData for CopyData invocations
        newCellData->CopyAllocate(cellData);

        output->SetPolys(newPolys);
        numPolys = polys->GetNumberOfCells();

        auto idList = vtkSmartPointer<vtkIdList>::New();
        idList->Allocate(1000);

        polys->InitTraversal();
        for (cellId = 0; cellId < numPolys; cellId++)
        {
            double mindistance = this->AzimuthalIgnorePolyDistance;
            vtkIdType npts;
            vtkIdType const *pts;

            polys->GetNextCell(npts, pts);

            if (npts > 0)
            {
                vtkIdType newCellId;
                double p1[3];
                double projP1[3];
                double distance;
                int lastId = -1;
                int j;

                points->GetPoint(pts[0], p1);
                distance = arcdistance(p1[0], p1[1], cuttingLongitude, cuttingLatitude);
                if (distance < mindistance)
                {
                    mindistance = distance;
                }
                newPoints->GetPoint(pts[0], projP1);
                idList->Reset();
                if (projP1[0] != HUGE_VAL && projP1[1] != HUGE_VAL)
                {
                    idList->InsertNextId(pts[0]);
                    lastId = 0;
                }

                for (j = 1; j < npts; j++)
                {
                    double projP2[3];

                    newPoints->GetPoint(pts[j], projP2);
                    if (projP2[0] != HUGE_VAL && projP2[1] != HUGE_VAL)
                    {
                        double p2[3];

                        points->GetPoint(pts[j], p2);
                        distance = arcdistance(p2[0], p2[1], cuttingLongitude, cuttingLatitude);
                        if (distance < mindistance)
                        {
                            mindistance = distance;
                        }
                        if (lastId >= 0)
                        {
                            CreateInterPoints(p1, projP1, p2, projP2, extent, newPoints, pointData, newPointData,
                                              pts[lastId], idList, projRef, this->InterpolationDistance, 0);
                        }
                        idList->InsertNextId(pts[j]);

                        p1[0] = p2[0];
                        p1[1] = p2[1];
                        p1[2] = p2[2];
                        projP1[0] = projP2[0];
                        projP1[1] = projP2[1];
                        projP1[2] = projP2[2];
                        lastId = j;
                    }
                }

                if (idList->GetNumberOfIds() > 1 &&
                    mindistance >= this->AzimuthalIgnorePolyDistance)
                {
                    vtkIdType id1, id2;
                    id1 = idList->GetId(0);
                    id2 = idList->GetId(idList->GetNumberOfIds() - 1);
                    // if the first and last id are not the same interpolate between these points
                    if (id1 != id2)
                    {
                        double firstP[3];
                        double lastP[3];
                        double projFirstP[3];
                        double projLastP[3];
                        points->GetPoint(id1, firstP);
                        points->GetPoint(id2, lastP);
                        newPoints->GetPoint(id1, projFirstP);
                        newPoints->GetPoint(id2, projLastP);
                        if (firstP[0] != lastP[0] || firstP[1] != lastP[1])
                        {
                            CreateInterPoints(lastP, projLastP, firstP, projFirstP, extent, newPoints, pointData,
                                              newPointData, id2, idList, projRef, this->InterpolationDistance, 0);
                        }
                    }
                    newCellId = output->InsertNextCell(VTK_POLYGON, idList);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
            }
        }
    }

    proj_destroy(projRef);
}

void vtkProjFilter::PerformCylindricalProjection(vtkPolyData *input)
{
    vtkPoints *points;
    vtkCellArray *verts;
    vtkCellArray *lines;
    vtkCellArray *polys;
    vtkPointData *pointData;
    vtkPointData *newPointData;
    vtkCellData *cellData;
    vtkCellData *newCellData;
    vtkIdType id;
    vtkIdType numPoints;
    PJ *projRef;
    PJ_COORD projLPData;
    PJ_COORD projXYData;
    char centerLongitudeParam[100];
    double extent[6];
    double cuttingLongitude;

    vtkDebugMacro(<< "Performing Cylindrical projection on polygonal data");

    points = input->GetPoints();
    verts = input->GetVerts();
    lines = input->GetLines();
    polys = input->GetPolys();
    pointData = input->GetPointData();
    cellData = input->GetCellData();

    // create the vtkCellArray in output
    vtkPolyData *output = this->GetOutput();
    output->Allocate(input);
    newPointData = output->GetPointData();
    newCellData = output->GetCellData();

    // points need to be transfered and projected
    numPoints = points->GetNumberOfPoints();
    auto newPoints = vtkSmartPointer<vtkPoints>::New();
    newPoints->SetDataTypeToFloat();
    newPoints->SetNumberOfPoints(numPoints);

    cuttingLongitude = this->CenterLongitude + 180.0;
    if (cuttingLongitude >= 180.0)
    {
        cuttingLongitude -= 360.0;
    }

    static char *parameters[] =
    {
        (char *)"",
        (char *)"",
        (char *)"R=1.0",
        (char *)"ellps=WGS84",
        (char *)"no_defs"
    };

    switch (this->Projection)
    {
        case VTK_PROJ_LAMBERT_CYLINDRICAL:
            parameters[0] = (char *)"proj=cea";
            break;
        case VTK_PROJ_PLATE_CAREE:
            parameters[0] = (char *)"proj=eqc";
            break;
        case VTK_PROJ_MOLLWEIDE:
            parameters[0] = (char *)"proj=moll";
            break;
        case VTK_PROJ_ROBINSON:
            parameters[0] = (char *)"proj=robin";
            break;
        default:
            vtkErrorMacro("Unknown cylindrical projection");
            return;
    }
    sprintf(centerLongitudeParam, "lon_0=%7.3f", this->CenterLongitude);
    parameters[1] = centerLongitudeParam;

    projRef = proj_create_argv(0, sizeof(parameters)/sizeof(char *), parameters);
    if (projRef == 0)
    {
        vtkErrorMacro(<< "Could not initialize PROJ library (" << proj_errno_string(proj_errno(0)) << ")");
        return;
    }

    GetExtent(extent);

    for (id = 0; id < numPoints; id++)
    {
        double pt[3];
        int leftSide;

        points->GetPoint(id, pt);
        while (pt[0] >= 180)
        {
            pt[0] -= 360;
        }
        while (pt[0] < -180)
        {
            pt[0] += 360;
        }
        if (this->CenterLongitude > cuttingLongitude)
        {
            leftSide = (pt[0] >= cuttingLongitude && pt[0] < this->CenterLongitude);
        }
        else
        {
            leftSide = (pt[0] >= cuttingLongitude || pt[0] < this->CenterLongitude);
        }
        projLPData.lp.lam = pt[0] * DEG_TO_RAD;
        projLPData.lp.phi = pt[1] * DEG_TO_RAD;
        projXYData = proj_trans(projRef, PJ_FWD, projLPData);
        pt[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
        pt[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
        if ((leftSide && pt[0] > 0.5) || (!leftSide && pt[0] < 0.5))
        {
            // Fix rounding to the wrong side of the edge by PROJ
            pt[0] = 1.0 - pt[0];
        }
        newPoints->SetPoint(id, pt);
    }
    output->SetPoints(newPoints);

    // pointData is first copied and later extended as needed
    newPointData->DeepCopy(pointData);

    // Vertices are passed unmodified
    if (verts->GetNumberOfCells() > 0)
    {
        auto newVerts = vtkSmartPointer<vtkCellArray>::New();
        output->SetVerts(newVerts);
        newVerts->DeepCopy(verts);
        newCellData->DeepCopy(cellData);
    }

    // Lines need to be cut when passing a projection boundary
    if (lines->GetNumberOfCells() > 0)
    {
        auto newLines = vtkSmartPointer<vtkCellArray>::New();
        vtkIdType numLines;
        vtkIdType cellId;

        // initialize newCellData for CopyData invocations
        newCellData->CopyAllocate(cellData);

        output->SetLines(newLines);
        numLines = lines->GetNumberOfCells();

        auto idList = vtkSmartPointer<vtkIdList>::New();
        idList->Allocate(1000);

        lines->InitTraversal();
        for (cellId = 0; cellId < numLines; cellId++)
        {
            vtkIdType npts;
            vtkIdType const *pts;

            lines->GetNextCell(npts, pts);

            if (npts > 0)
            {
                vtkIdType newCellId;
                double p1[3];
                double projP1[3];
                int j;

                points->GetPoint(pts[0], p1);
                newPoints->GetPoint(pts[0], projP1);
                while (p1[0] >= 180)
                {
                    p1[0] -= 360;
                }
                while (p1[0] < -180)
                {
                    p1[0] += 360;
                }
                idList->Reset();
                idList->InsertNextId(pts[0]);

                for (j = 1; j < npts; j++)
                {
                    double p2[3];
                    double projP2[3];

                    points->GetPoint(pts[j], p2);
                    newPoints->GetPoint(pts[j], projP2);
                    while (p2[0] >= 180)
                    {
                        p2[0] -= 360;
                    }
                    while (p2[0] < -180)
                    {
                        p2[0] += 360;
                    }

                    // check if both points are on the cutting edge
                    if (p1[0] == cuttingLongitude && p2[0] == cuttingLongitude)
                    {
                        double projSecondP1[3];
                        double projSecondP2[3];
                        vtkIdType secondPt;

                        // the line segments coincides with the cutting meridian ->
                        // keep the line segment and add a second line at the other side
                        CreateInterPoints(p1, projP1, p2, projP2, extent, newPoints, pointData, newPointData,
                                          pts[j - 1], idList, projRef, this->InterpolationDistance, 1);
                        idList->InsertNextId(pts[j]);

                        auto idList2 = vtkSmartPointer<vtkIdList>::New();
                        idList2->Allocate(100);

                        projSecondP1[0] = 1.0 - projP1[0];
                        projSecondP1[1] = projP1[1];
                        projSecondP1[2] = projP1[2];
                        secondPt = newPoints->InsertNextPoint(projSecondP1);
                        newPointData->CopyData(pointData, pts[j - 1], secondPt);
                        idList2->InsertNextId(secondPt);

                        projSecondP2[0] = 1.0 - projP2[0];
                        projSecondP2[1] = projP2[1];
                        projSecondP2[2] = projP2[2];
                        secondPt = newPoints->InsertNextPoint(projSecondP2);
                        newPointData->CopyData(pointData, pts[j], secondPt);
                        CreateInterPoints(p1, projSecondP1, p2, projSecondP2, extent, newPoints, pointData,
                                          newPointData, pts[j - 1], idList2, projRef, this->InterpolationDistance, 1);
                        idList2->InsertNextId(secondPt);

                        newCellId = output->InsertNextCell(VTK_LINE, idList2);
                        newCellData->CopyData(cellData, cellId, newCellId);
                    }
                    else
                    {
                        int leftSide[2];
                        int splitLineSegment = 0;

                        // check whether both points lie in the range
                        // [cuttingLongitude, CenterLongitude] or
                        // [CenterLongitude, cuttingLongitude]
                        if (this->CenterLongitude > cuttingLongitude)
                        {
                            leftSide[0] = (p1[0] >= cuttingLongitude && p1[0] <= this->CenterLongitude);
                            leftSide[1] = (p2[0] >= cuttingLongitude && p2[0] <= this->CenterLongitude);
                        }
                        else
                        {
                            leftSide[0] = (p1[0] >= cuttingLongitude || p1[0] <= this->CenterLongitude);
                            leftSide[1] = (p2[0] >= cuttingLongitude || p2[0] <= this->CenterLongitude);
                        }
                        if (leftSide[0] != leftSide[1])
                        {
                            double d1, d2;
                            // check whether the shortest path between both points crosses
                            // the cuttingLongitude meridian (or the CenterLongitude meridian)
                            d1 = fabs(p1[0] - cuttingLongitude);
                            if (d1 >= 180)
                            {
                                d1 = 360 - d1;
                            }
                            d2 = fabs(p2[0] - cuttingLongitude);
                            if (d2 >= 180)
                            {
                                d2 = 360 - d2;
                            }
                            splitLineSegment = (d1 + d2 <= 180);
                        }
                        if (splitLineSegment)
                        {
                            // points are on different sides of the cutting edge ->
                            // introduce extra points at cutting edge (both sides);
                            // terminate this Line and start a new one
                            vtkIdType edgePt;
                            double edge[3];
                            double projEdgeP1[3];
                            double projEdgeP2[3];

                            edge[0] = cuttingLongitude;
                            edge[1] = cuttingpoint(p1[0], p1[1], p2[0], p2[1], cuttingLongitude);
                            // TODO: Use proper weighting
                            edge[2] = (p1[2] + p2[2]) / 2;
                            projLPData.lp.lam = edge[0] * DEG_TO_RAD;
                            projLPData.lp.phi = edge[1] * DEG_TO_RAD;
                            projXYData = proj_trans(projRef, PJ_FWD, projLPData);
                            projEdgeP1[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
                            projEdgeP1[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
                            projEdgeP1[2] = edge[2];
                            projEdgeP2[0] = projEdgeP1[0];
                            projEdgeP2[1] = projEdgeP1[1];
                            projEdgeP2[2] = projEdgeP1[2];
                            if ((leftSide[0] && projEdgeP1[0] > 0.5) || (!leftSide[0] && projEdgeP1[0] < 0.5))
                            {
                                projEdgeP1[0] = 1.0 - projEdgeP1[0];
                            }
                            if ((leftSide[1] && projEdgeP2[0] > 0.5) || (!leftSide[1] && projEdgeP2[0] < 0.5))
                            {
                                projEdgeP2[0] = 1.0 - projEdgeP2[0];
                            }
                            edgePt = newPoints->InsertNextPoint(projEdgeP1);
                            newPointData->CopyData(pointData, pts[j - 1], edgePt);
                            CreateInterPoints(p1, projP1, edge, projEdgeP1, extent, newPoints, pointData, newPointData,
                                              pts[j - 1], idList, projRef, this->InterpolationDistance, 1);
                            idList->InsertNextId(edgePt);

                            newCellId = output->InsertNextCell(VTK_LINE, idList);
                            newCellData->CopyData(cellData, cellId, newCellId);

                            idList->Reset();

                            edgePt = newPoints->InsertNextPoint(projEdgeP2);
                            newPointData->CopyData(pointData, pts[j], edgePt);
                            idList->InsertNextId(edgePt);
                            CreateInterPoints(edge, projEdgeP2, p2, projP2, extent, newPoints, pointData, newPointData,
                                              pts[j], idList, projRef, this->InterpolationDistance, 1);
                        }
                        else
                        {
                            CreateInterPoints(p1, projP1, p2, projP2, extent, newPoints, pointData, newPointData,
                                              pts[j - 1], idList, projRef, this->InterpolationDistance, 1);
                        }
                        idList->InsertNextId(pts[j]);
                    }

                    p1[0] = p2[0];
                    p1[1] = p2[1];
                    p1[2] = p2[2];
                    projP1[0] = projP2[0];
                    projP1[1] = projP2[1];
                    projP1[2] = projP2[2];
                }

                if (idList->GetNumberOfIds() > 1)
                {
                    newCellId = output->InsertNextCell(VTK_LINE, idList);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
            }
        }
    }

    // Polys need to be divided into sub-polys if they cross a projection boundary
    if (polys->GetNumberOfCells() > 0)
    {
        auto newPolys = vtkSmartPointer<vtkCellArray>::New();
        vtkIdList *idList[2];
        vtkIdType numPolys;
        vtkIdType cellId;

        // initialize newCellData for CopyData invocations
        newCellData->CopyAllocate(cellData);

        output->SetPolys(newPolys);
        numPolys = polys->GetNumberOfCells();

        // list 0 is for polys where the first point is in the range
        // [cuttingLongitude, CenterLongitude] or [CenterLongitude, cuttingLongitude]
        // (depending on which of the two longitudes is the smallest)
        // list 1 is for the other polys
        idList[0] = vtkIdList::New();
        idList[0]->Allocate(1000);
        idList[1] = vtkIdList::New();
        idList[1]->Allocate(1000);

        polys->InitTraversal();
        for (cellId = 0; cellId < numPolys; cellId++)
        {
            vtkIdType npts;
            vtkIdType const *pts;

            polys->GetNextCell(npts, pts);

            if (npts > 0)
            {
                vtkIdType newCellId;
                int currentList;
                int leftSide[2];
                // We need to keep track of the unprojected first and last point
                // of the idLists (in order to create a proper interpolation between
                // the last and first point if that is necessary)
                double listFirstP[2][3];
                double listLastP[2][3];
                double p1[3];
                double projP1[3];
                int j;

                points->GetPoint(pts[0], p1);
                newPoints->GetPoint(pts[0], projP1);
                while (p1[0] >= 180)
                {
                    p1[0] -= 360;
                }
                while (p1[0] < -180)
                {
                    p1[0] += 360;
                }
                idList[0]->Reset();
                idList[1]->Reset();

                if (this->CenterLongitude > cuttingLongitude)
                {
                    leftSide[0] = (p1[0] >= cuttingLongitude && p1[0] <= this->CenterLongitude);
                }
                else
                {
                    leftSide[0] = (p1[0] >= cuttingLongitude || p1[0] <= this->CenterLongitude);
                }
                currentList = leftSide[0] ? 0 : 1;

                idList[currentList]->InsertNextId(pts[0]);
                listFirstP[currentList][0] = p1[0];
                listFirstP[currentList][1] = p1[1];
                listFirstP[currentList][2] = p1[2];

                for (j = 1; j < npts + 1; j++)
                {
                    double p2[3];
                    double projP2[3];
                    int splitPolySegment = 0;

                    points->GetPoint(pts[j == npts ? 0 : j], p2);
                    newPoints->GetPoint(pts[j == npts ? 0 : j], projP2);
                    while (p2[0] >= 180)
                    {
                        p2[0] -= 360;
                    }
                    while (p2[0] < -180)
                    {
                        p2[0] += 360;
                    }

                    // check whether both points lie in the range
                    // [cuttingLongitude, CenterLongitude] or
                    // [CenterLongitude, cuttingLongitude]
                    if (this->CenterLongitude > cuttingLongitude)
                    {
                        leftSide[1] = (p2[0] >= cuttingLongitude && p2[0] <= this->CenterLongitude);
                    }
                    else
                    {
                        leftSide[1] = (p2[0] >= cuttingLongitude || p2[0] <= this->CenterLongitude);
                    }
                    if (leftSide[0] != leftSide[1])
                    {
                        double d1, d2;
                        // check whether the shortest path between both points crosses
                        // the cuttingLongitude meridian (or the CenterLongitude meridian)
                        d1 = fabs(p1[0] - cuttingLongitude);
                        if (d1 >= 180)
                        {
                            d1 = 360 - d1;
                        }
                        d2 = fabs(p2[0] - cuttingLongitude);
                        if (d2 >= 180)
                        {
                            d2 = 360 - d2;
                        }
                        splitPolySegment = (d1 + d2 <= 180);
                    }
                    if (splitPolySegment)
                    {
                        // points are on different sides of the cutting edge ->
                        // introduce extra points at both sides (in projected space) of cutting edge
                        double edge[3];
                        double projEdgeP1[3];
                        double projEdgeP2[3];
                        vtkIdType edgePt;

                        edge[0] = cuttingLongitude;
                        edge[1] = cuttingpoint(p1[0], p1[1], p2[0], p2[1], cuttingLongitude);
                                                  // TODO: Use proper weighting
                        edge[2] = (p1[2] + p2[2]) / 2;
                        projLPData.lp.lam = edge[0] * DEG_TO_RAD;
                        projLPData.lp.phi = edge[1] * DEG_TO_RAD;
                        projXYData = proj_trans(projRef, PJ_FWD, projLPData);
                        projEdgeP1[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
                        projEdgeP1[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
                        projEdgeP1[2] = edge[2];
                        projEdgeP2[0] = projEdgeP1[0];
                        projEdgeP2[1] = projEdgeP1[1];
                        projEdgeP2[2] = projEdgeP1[2];
                        if ((leftSide[0] && projEdgeP1[0] > 0.5) || (!leftSide[0] && projEdgeP1[0] < 0.5))
                        {
                            projEdgeP1[0] = 1.0 - projEdgeP1[0];
                        }
                        if ((leftSide[1] && projEdgeP2[0] > 0.5) || (!leftSide[1] && projEdgeP2[0] < 0.5))
                        {
                            projEdgeP2[0] = 1.0 - projEdgeP2[0];
                        }
                        edgePt = newPoints->InsertNextPoint(projEdgeP1);
                        newPointData->CopyData(pointData, pts[j - 1], edgePt);
                        CreateInterPoints(p1, projP1, edge, projEdgeP1, extent, newPoints, pointData, newPointData,
                                          pts[j - 1], idList[currentList], projRef, this->InterpolationDistance, 1);
                        idList[currentList]->InsertNextId(edgePt);

                        if ((currentList == 0 && leftSide[1]) || (currentList == 1 && !leftSide[1]))
                        {
                            // we've made a trip around the world, so we don't switch to
                            // the other list;
                            // we are going to connect both sides via one of the poles
                            double polar[3];
                            double projPolarP1[3];
                            double projPolarP2[3];
                            vtkIdType polarPt;

                            polar[0] = edge[0];
                            polar[1] = (edge[1] >= 0 ? 90 : -90);
                            polar[2] = edge[2];
                            projLPData.lp.lam = polar[0] * DEG_TO_RAD;
                            projLPData.lp.phi = polar[1] * DEG_TO_RAD;
                            projXYData = proj_trans(projRef, PJ_FWD, projLPData);
                            projPolarP1[0] = (projXYData.xy.x - extent[0]) / (extent[1] - extent[0]);
                            projPolarP1[1] = (projXYData.xy.y - extent[2]) / (extent[3] - extent[2]);
                            projPolarP1[2] = projEdgeP1[2];
                            projPolarP2[0] = projPolarP1[0];
                            projPolarP2[1] = projPolarP1[1];
                            projPolarP2[2] = projPolarP1[2];
                            if ((leftSide[0] && projPolarP1[0] > 0.5) || (!leftSide[0] && projPolarP1[0] < 0.5))
                            {
                                projPolarP1[0] = 1.0 - projPolarP1[0];
                            }
                            if ((leftSide[1] && projPolarP2[0] > 0.5) || (!leftSide[1] && projPolarP2[0] < 0.5))
                            {
                                projPolarP2[0] = 1.0 - projPolarP2[0];
                            }
                            polarPt = newPoints->InsertNextPoint(projPolarP1);
                            newPointData->CopyData(pointData, pts[j - 1], polarPt);
                            CreateInterPoints(edge, projEdgeP1, polar, projPolarP1, extent, newPoints, pointData,
                                              newPointData, pts[j - 1], idList[currentList], projRef,
                                              this->InterpolationDistance, 1);
                            idList[currentList]->InsertNextId(polarPt);
                            polarPt = newPoints->InsertNextPoint(projPolarP2);
                            newPointData->CopyData(pointData, pts[j == npts ? 0 : j], polarPt);
                            CreateInterPoints(polar, projPolarP2, edge, projEdgeP2, extent, newPoints, pointData,
                                              newPointData, pts[j == npts ? 0 : j], idList[currentList], projRef,
                                              this->InterpolationDistance, 1);
                            idList[currentList]->InsertNextId(polarPt);
                        }
                        else
                        {
                            // switch poly
                            listLastP[currentList][0] = edge[0];
                            listLastP[currentList][1] = edge[1];
                            listLastP[currentList][2] = edge[2];
                            currentList = 1 - currentList;
                            if (idList[currentList]->GetNumberOfIds() == 0)
                            {
                                listFirstP[currentList][0] = edge[0];
                                listFirstP[currentList][1] = edge[1];
                                listFirstP[currentList][2] = edge[2];
                            }
                            else
                            {
                                // interpolate between exit edge point and entry edge point
                                vtkIdType lastid;
                                double projLastP[3];
                                lastid = idList[currentList]->GetId(idList[currentList]->GetNumberOfIds() - 1);
                                newPoints->GetPoint(lastid, projLastP);
                                CreateInterPoints(listLastP[currentList], projLastP, edge, projEdgeP2, extent,
                                                  newPoints, pointData, newPointData, lastid, idList[currentList],
                                                  projRef, this->InterpolationDistance, 1);
                            }
                        }

                        edgePt = newPoints->InsertNextPoint(projEdgeP2);
                        newPointData->CopyData(pointData, pts[j == npts ? 0 : j], edgePt);
                        idList[currentList]->InsertNextId(edgePt);
                        CreateInterPoints(edge, projEdgeP2, p2, projP2, extent, newPoints, pointData, newPointData,
                                          pts[j == npts ? 0 : j], idList[currentList], projRef,
                                          this->InterpolationDistance, 1);
                    }
                    else
                    {
                        CreateInterPoints(p1, projP1, p2, projP2, extent, newPoints, pointData, newPointData,
                                          pts[j - 1], idList[currentList], projRef, this->InterpolationDistance, 1);
                    }

                    idList[currentList]->InsertNextId(pts[j == npts ? 0 : j]);

                    p1[0] = p2[0];
                    p1[1] = p2[1];
                    p1[2] = p2[2];
                    projP1[0] = projP2[0];
                    projP1[1] = projP2[1];
                    projP1[2] = projP2[2];
                    leftSide[0] = leftSide[1];
                }
                listLastP[currentList][0] = p1[0];
                listLastP[currentList][1] = p1[1];
                listLastP[currentList][2] = p1[2];

                if (idList[0]->GetNumberOfIds() > 1)
                {
                    vtkIdType id1, id2;
                    id1 = idList[0]->GetId(0);
                    id2 = idList[0]->GetId(idList[0]->GetNumberOfIds() - 1);
                    // if the first and last id are not the same interpolate between
                    // these points
                    if (id1 != id2)
                    {
                        double projFirstP[3];
                        double projLastP[3];
                        newPoints->GetPoint(id1, projFirstP);
                        newPoints->GetPoint(id2, projLastP);
                        if (listFirstP[0][0] != listLastP[0][0] || listFirstP[0][1] != listLastP[0][1])
                        {
                            CreateInterPoints(listLastP[0], projLastP, listFirstP[0], projFirstP, extent, newPoints,
                                              pointData, newPointData, id2, idList[0], projRef,
                                              this->InterpolationDistance, 1);
                        }
                    }
                    newCellId = output->InsertNextCell(VTK_POLYGON, idList[0]);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
                if (idList[1]->GetNumberOfIds() > 1)
                {
                    vtkIdType id1, id2;
                    id1 = idList[1]->GetId(0);
                    id2 = idList[1]->GetId(idList[1]->GetNumberOfIds() - 1);
                    // if the first and last id are not the same interpolate between
                    // these points
                    if (id1 != id2)
                    {
                        double projFirstP[3];
                        double projLastP[3];
                        newPoints->GetPoint(id1, projFirstP);
                        newPoints->GetPoint(id2, projLastP);
                        if (listFirstP[1][0] != listLastP[1][0] || listFirstP[1][1] != listLastP[1][1])
                        {
                            CreateInterPoints(listLastP[1], projLastP, listFirstP[1], projFirstP, extent, newPoints,
                                              pointData, newPointData, id2, idList[1], projRef,
                                              this->InterpolationDistance, 1);
                        }
                    }
                    newCellId = output->InsertNextCell(VTK_POLYGON, idList[1]);
                    newCellData->CopyData(cellData, cellId, newCellId);
                }
            }
        }
        idList[0]->Delete();
        idList[1]->Delete();
    }

    proj_destroy(projRef);
}

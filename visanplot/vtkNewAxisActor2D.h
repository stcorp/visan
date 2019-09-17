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

#ifndef __vtkNewAxisActor2D_h
#define __vtkNewAxisActor2D_h

#include "vtkActor2D.h"
#include "vtkTextProperty.h"

#include "vtkSmartPointer.h"

class vtkActor2DCollection;
class vtkCoordinate;
class vtkPolyData;
class vtkPolyDataMapper2D;
class vtkTextMapper;
class vtkTimeStamp;
class vtkViewport;

#define VTK_MAX_LABELS 100

class vtkNewAxisActor2D : public vtkActor2D
{
    public:
        vtkTypeMacro(vtkNewAxisActor2D,vtkActor2D);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkNewAxisActor2D *New();

        // Description:
        // Specify the (min,max) axis range. This will be used in the generation
        // of labels, if labels are visible.
        vtkSetVector2Macro(Range,double);
        vtkGetVectorMacro(Range,double,2);

        // Description:
        // Set/Get the number of annotation labels to show.
        vtkSetClampMacro(NumberOfLabels, int, 2, VTK_MAX_LABELS - 10);
        vtkGetMacro(NumberOfLabels, int);

        // Description:
        // Set/Get the format with which to print the labels on the scalar
        // bar.
        vtkSetStringMacro(LabelFormat);
        vtkGetStringMacro(LabelFormat);

        // Description:
        // Set/Get the flag that controls whether the range may be adjusted such
        // that the labels and ticks will have "nice" numerical values to make it
        // easier to read the labels. The adjusted range is based on the Range
        // instance variable.
        vtkSetMacro(AdjustRange, int);
        vtkGetMacro(AdjustRange, int);
        vtkBooleanMacro(AdjustRange, int);

        // Description:
        // Set/Get the flag that controls whether the labels and ticks do not
        // have to start/end at the range boundaries. If AdjustTicks is set then
        // the first tick will start at a "nice" numerical value to make it easier
        // to read the labels. The tick adjustment is based on the Range instance
        // variable.
        // If AdjustRange is also set then AdjustTicks will be ignored.
        vtkSetMacro(AdjustTicks, int);
        vtkGetMacro(AdjustTicks, int);
        vtkBooleanMacro(AdjustTicks, int);

        virtual double *GetAdjustedRange()
        {
            this->UpdateAdjustedRange();
            return this->AdjustedRange;
        }
        virtual void GetAdjustedRange(double &_arg1, double &_arg2)
        {
            this->UpdateAdjustedRange();
            _arg1 = this->AdjustedRange[0];
            _arg2 = this->AdjustedRange[1];
        };
        virtual void GetAdjustedRange(double _arg[2])
        {
            this->GetAdjustedRange(_arg[0], _arg[1]);
        }
        virtual double *GetTickRange()
        {
            this->UpdateAdjustedRange();
            return this->TickRange;
        }
        virtual void GetTickRange(double &_arg1, double &_arg2)
        {
            this->UpdateAdjustedRange();
            _arg1 = this->TickRange[0];
            _arg2 = this->TickRange[1];
        };
        virtual void GetTickRange(double _arg[2])
        {
            this->GetTickRange(_arg[0], _arg[1]);
        }
        virtual int GetAdjustedNumberOfLabels()
        {
            this->UpdateAdjustedRange();
            return this->AdjustedNumberOfLabels;
        }

        // Description:
        // Set logarithmic axis on/off.
        // The default is off.
        vtkSetMacro(Log, int)
        vtkGetMacro(Log, int);
        vtkBooleanMacro(Log, int);

        // Description:
        // Set the base for the linear and logarithmic tick calculcation.
        // Base should be > 1.0
        // The default is base 10.
        vtkSetMacro(Base, double);
        vtkGetMacro(Base, double);

        // Description:
        // Set/Get the title of the scalar bar actor,
        vtkSetStringMacro(Title);
        vtkGetStringMacro(Title);

        // Description:
        // Set/Get the title text property.
        virtual void SetTitleTextProperty(vtkTextProperty *p);
        vtkTextProperty *GetTitleTextProperty()
        {
            return TitleTextProperty.GetPointer();
        }

        // Description:
        // Set/Get the labels text property.
        virtual void SetLabelTextProperty(vtkTextProperty *p);
        vtkTextProperty *GetLabelTextProperty()
        {
            return LabelTextProperty.GetPointer();
        }

        // Description:
        // Set/Get the length of the tick marks (expressed in pixels or display
        // coordinates).
        vtkSetClampMacro(TickLength, int, 0, 100);
        vtkGetMacro(TickLength, int);

        // Description:
        // Set/Get the offset of the labels (expressed in pixels or display
        // coordinates). The offset is the distance of labels from tick marks
        // or other objects.
        vtkSetClampMacro(TickOffset, int, 0, 100);
        vtkGetMacro(TickOffset, int);

        // Description:
        // Set/Get visibility of the axis line.
        vtkSetMacro(AxisVisibility, int);
        vtkGetMacro(AxisVisibility, int);
        vtkBooleanMacro(AxisVisibility, int);

        // Description:
        // Set/Get visibility of the axis tick marks.
        vtkSetMacro(TickVisibility, int);
        vtkGetMacro(TickVisibility, int);
        vtkBooleanMacro(TickVisibility, int);

        // Description:
        // Set/Get visibility of the axis labels.
        vtkSetMacro(LabelVisibility, int);
        vtkGetMacro(LabelVisibility, int);
        vtkBooleanMacro(LabelVisibility, int);

        // Description:
        // Set/Get visibility of the axis title.
        vtkSetMacro(TitleVisibility, int);
        vtkGetMacro(TitleVisibility, int);
        vtkBooleanMacro(TitleVisibility, int);

        // Description:
        // Set/Get the factor that controls the overall size of the fonts used
        // to label and title the axes. This ivar used in conjunction with
        // the LabelFactor can be used to control font sizes.
        vtkSetClampMacro(FontFactor, double, 0.1, 2.0);
        vtkGetMacro(FontFactor, double);

        // Description:
        // Set/Get the factor that controls the relative size of the axis labels
        // to the axis title.
        vtkSetClampMacro(LabelFactor, double, 0.1, 2.0);
        vtkGetMacro(LabelFactor, double);

        // Description:
        // Draw the axis.
        int RenderOverlay(vtkViewport *viewport) override;
        int RenderOpaqueGeometry(vtkViewport *viewport) override;
        int RenderTranslucentGeometry(vtkViewport *) {return 0;}

        // Description:
        // Release any graphics resources that are being consumed by this actor.
        // The parameter window could be used to determine which graphic
        // resources to release.
        void ReleaseGraphicsResources(vtkWindow *) override;

        // Description:
        // This method computes the range of the axis given an input range.
        // It also computes the number of tick marks given a suggested number.
        // (The number of tick marks includes end ticks as well.)
        // The number of tick marks computed (in conjunction with the output
        // range) will yield "nice" tick values. For example, if the input range
        // is (0.25,96.7) and the number of ticks requested is 7 (with base=10),
        // the output range will be (0,100) with the number of computed ticks to 6
        // to yield tick values of (0,20,40,60,80,100).
        // If logAxis is false (linear axis) the distance between ticks will be
        // given by 'interval', otherwise (logarithmic axis) 'interval' equals the
        // multiplication factor between succesive ticks (t_(n+1) = interval * t_(n))
        static void ComputeRange(double inRange[2], double outRange[2], int inNumTicks, double base,
                                 int logAxis, int &outNumTicks, double &interval);

        // Description:
        // This method computes the ranges for the first and last tick of the axis
        // given an input range such that the new range is within the given range.
        // It also computes the number of tick marks given a suggested number.
        // (The number of tick marks includes end ticks as well.)
        // The number of tick marks computed will yield "nice" tick values.
        // For example, if the input range is (-0.25,11.38) and the number of ticks
        // requested is 5 (with base=10), the output range will be (0,9) with the
        // number of computed ticks to 4 to yield tick values of (0,3,6,9).
        // If logAxis is false (linear axis) the distance between ticks will be
        // given by 'interval', otherwise (logarithmic axis) 'interval' equals the
        // multiplication factor between succesive ticks (t_(n+1) = interval * t_(n))
        static void ComputeInnerRange(double inRange[2], double outRange[2], int inNumTicks, double base,
                                      int logAxis, int &outNumTicks, double &interval);

        // Description:
        // General method to computes font size from a representative size on the
        // viewport (given by size[2]). The method returns the font size (in points)
        // and the string height/width (in pixels). It also sets the font size of the
        // instance of vtkTextMapper provided. The factor is used when you're trying
        // to create text of different size-factor (it is usually = 1 but you can
        // adjust the font size by making factor larger or smaller).
        static int SetFontSize(vtkViewport *viewport, vtkTextMapper *textMapper, int *targetSize,
                               double factor, int *stringSize);
        static int SetMultipleFontSize(vtkViewport *viewport, vtkTextMapper **textMappers, int nbOfMappers,
                                       int *targetSize, double factor, int *stringSize);

        // Description:
        // Shallow copy of an axis actor. Overloads the virtual vtkProp method.
        void ShallowCopy(vtkProp *prop) override;

    protected:
        vtkNewAxisActor2D();
        ~vtkNewAxisActor2D() override;

        vtkSmartPointer<vtkTextProperty> TitleTextProperty;
        vtkSmartPointer<vtkTextProperty> LabelTextProperty;

        char *Title;
        double  Range[2];
        int NumberOfLabels;
        char *LabelFormat;
        int AdjustRange;
        int AdjustTicks;
        double FontFactor;
        double LabelFactor;
        int TickLength;
        int TickOffset;
        int Log;
        double Base;

        double AdjustedRange[2];
        int AdjustedNumberOfLabels;
        double TickRange[2];
        double Interval;

        int AxisVisibility;
        int TickVisibility;
        int LabelVisibility;
        int TitleVisibility;

        int LastPosition[2];
        int LastPosition2[2];

        int LastSize[2];
        int LastMaxLabelSize[2];

        virtual void BuildAxis(vtkViewport *viewport);
        static double ComputeStringOffset(double width, double height, double theta);
        static void SetOffsetPosition(double xTick[3], double theta, int stringHeight,
                                      int stringWidth, int offset, vtkActor2D *actor);
        virtual void UpdateAdjustedRange();

        vtkSmartPointer<vtkActor2D> TitleActor;

        vtkSmartPointer<vtkActor2DCollection> LabelActors;

        vtkSmartPointer<vtkPolyData> Axis;
        vtkSmartPointer<vtkPolyDataMapper2D> AxisMapper;
        vtkSmartPointer<vtkActor2D> AxisActor;

        vtkTimeStamp AdjustedRangeBuildTime;
        vtkTimeStamp BuildTime;

    private:
        vtkNewAxisActor2D(const vtkNewAxisActor2D&) = delete;
        void operator=(const vtkNewAxisActor2D&) = delete;
};
#endif

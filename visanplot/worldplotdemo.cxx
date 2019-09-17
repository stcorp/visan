#include "vtkSmartPointer.h"

#include "vtkActor.h"
#include "vtkDoubleArray.h"
#include "vtkPolyDataMapper.h"
#include "vtkRenderWindow.h"
#include "vtkRenderWindowInteractor.h"
#include "vtkRenderer.h"
#include "vtkScalarBarActor.h"
#include "vtkSphereSource.h"
#include "vtkTextProperty.h"

#include "vtkCoastLineData.h"
#include "vtkColorTable.h"
#include "vtkGeoGridData.h"
#include "vtkWorldPlotGridData.h"
#include "vtkWorldPlotPointData.h"
#include "vtkWorldPlotLineData.h"
#include "vtkWorldPlotSwathData.h"
#include "vtkInteractorStyleWorldPlot3D.h"

int main(int, char *[])
{
    double *data;
    double *latitude;
    double *longitude;
    int width = 180;
    int height = 90;
    int i, j;

    // Create a sphere
    auto sphere = vtkSmartPointer<vtkSphereSource>::New();
    sphere->SetRadius(1);
    sphere->SetPhiResolution(30);
    sphere->SetThetaResolution(60);

    // Create a mapper and actor
    auto mapper = vtkSmartPointer<vtkPolyDataMapper>::New();
    mapper->SetInputConnection(sphere->GetOutputPort());

    auto actor = vtkSmartPointer<vtkActor>::New();
    actor->SetMapper(mapper);

    // Create a renderer, render window, and interactor
    auto renderer = vtkSmartPointer<vtkRenderer>::New();
    auto renderWindow = vtkSmartPointer<vtkRenderWindow>::New();
    renderWindow->AddRenderer(renderer);
    renderWindow->SetSize(640, 480);

    auto renderWindowInteractor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
    renderWindowInteractor->SetRenderWindow(renderWindow);

    // Add the actors to the scene
    renderer->AddActor(actor);

    // Grid lines
    auto geoGridData = vtkSmartPointer<vtkGeoGridData>::New();
    renderer->AddActor(geoGridData->GetActor3D());

    // Coastlines
    auto coastLineData = vtkSmartPointer<vtkCoastLineData>::New();
    coastLineData->SetFileName(GSHHS_FILEPATH);
    coastLineData->SetMaxLevel(1);
    renderer->AddActor(coastLineData->GetActor3D());

    // Grid data
    auto gridData = vtkSmartPointer<vtkWorldPlotGridData>::New();
    auto latitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    auto longitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    auto dataArray = vtkSmartPointer<vtkDoubleArray>::New();
    latitudeArray->SetNumberOfTuples(height);
    longitudeArray->SetNumberOfTuples(width);
    dataArray->SetNumberOfTuples(width * height);
    latitude = latitudeArray->GetPointer(0);
    longitude = longitudeArray->GetPointer(0);
    data = dataArray->GetPointer(0);
    for (j = 0; j < height; j++)
    {
        latitude[j] = (j + 0.5) * 180.0 / height - 90;
    }
    for (i = 0; i < width; i++)
    {
        longitude[i] = (i + 0.5) * 360.0 / width;
    }
    for (j = 0; j < height; j++)
    {
        for (i = 0; i < width; i++)
        {
            data[j * width + i] = latitude[j] + longitude[i];
        }
    }
    gridData->AddData(latitudeArray, longitudeArray, dataArray);
    renderer->AddActor(gridData->GetActor3D());

    auto pointData = vtkSmartPointer<vtkWorldPlotPointData>::New();
    latitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    longitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    latitudeArray->SetNumberOfTuples(height);
    longitudeArray->SetNumberOfTuples(height);
    latitude = latitudeArray->GetPointer(0);
    longitude = longitudeArray->GetPointer(0);
    for (i = 0; i < height; i++)
    {
        latitude[i] = -90 + i * 180.0 / height;
        longitude[i] = i * 40.0 / height;
    }
    pointData->AddData(latitudeArray, longitudeArray, nullptr);
    renderer->AddActor(pointData->GetActor3D());

    auto lineData = vtkSmartPointer<vtkWorldPlotLineData>::New();
    for (i = 0; i < height; i++)
    {
        longitude[i] += 20;
    }
    lineData->AddData(latitudeArray, longitudeArray);
    renderer->AddActor(lineData->GetActor3D());

    auto swathData = vtkSmartPointer<vtkWorldPlotSwathData>::New();
    dataArray = vtkSmartPointer<vtkDoubleArray>::New();
    latitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    longitudeArray = vtkSmartPointer<vtkDoubleArray>::New();
    dataArray->SetNumberOfTuples(height);
    latitudeArray->SetNumberOfComponents(4);
    latitudeArray->SetNumberOfTuples(height);
    longitudeArray->SetNumberOfComponents(4);
    longitudeArray->SetNumberOfTuples(height);
    data = dataArray->GetPointer(0);
    latitude = latitudeArray->GetPointer(0);
    longitude = longitudeArray->GetPointer(0);
    for (i = 0; i < height; i++)
    {
        data[i] = i;
        for (j = 0; j < 4; j++)
        {
            latitude[i * 4 + j] = i / 2.0 + (j > 1);
            longitude[i * 4 + j] = 4.0 * i + (j == 0 || j == 3);
        }
    }
    swathData->AddData(latitudeArray, longitudeArray, dataArray);
    renderer->AddActor(swathData->GetActor3D());

    // Colorbar
    auto colorBarRenderer = vtkSmartPointer<vtkRenderer>::New();
    auto colorBarActor = vtkSmartPointer<vtkScalarBarActor>::New();
    colorBarActor->SetLookupTable(swathData->GetColorTable()->GetVTKLookupTable());
    colorBarActor->SetTitle(swathData->GetColorBarTitle());
    colorBarActor->SetNumberOfLabels(swathData->GetNumColorBarLabels());
    colorBarActor->SetOrientationToHorizontal();
    colorBarActor->SetPosition(0.1, 0.1);
    colorBarActor->SetPosition2(0.8, 0.9);
    colorBarActor->SetNumberOfLabels(5);
    colorBarActor->GetLabelTextProperty()->SetColor(1, 1, 1);
    colorBarActor->GetLabelTextProperty()->ShadowOff();
    colorBarActor->GetLabelTextProperty()->ItalicOff();
    colorBarActor->GetLabelTextProperty()->BoldOff();
    colorBarActor->GetLabelTextProperty()->SetJustificationToCentered();
    colorBarActor->GetTitleTextProperty()->SetColor(1, 1, 1);
    colorBarActor->GetTitleTextProperty()->ShadowOff();
    colorBarActor->GetTitleTextProperty()->ItalicOff();
    colorBarActor->GetTitleTextProperty()->BoldOff();
    colorBarActor->SetLabelFormat("%g");
    colorBarRenderer->AddActor2D(colorBarActor);
    colorBarRenderer->InteractiveOff();
    // use 0.375 (default) if color bar title is not empty
    colorBarActor->SetBarRatio(0.5);
    // use 60.0 if color bar title is not empty
    float relativeHeight = 40.0 / renderWindow->GetSize()[1];
    colorBarRenderer->SetViewport(0, 0, 1, relativeHeight);
    renderer->SetViewport(0, relativeHeight, 1, 1);
    renderWindow->AddRenderer(colorBarRenderer);

    // Set interactor style
    auto style = vtkSmartPointer<vtkInteractorStyleWorldPlot3D>::New();
    style->SetCurrentRenderer(renderer);
    style->SetDefaultZoom(2.5);
    style->SetDefaultView();
    renderWindowInteractor->SetInteractorStyle(style);

    // Render and interact
    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}

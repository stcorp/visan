#include "vtkSmartPointer.h"

#include "vtkDoubleArray.h"
#include "vtkProperty2D.h"
#include "vtkRenderWindow.h"
#include "vtkRenderWindowInteractor.h"
#include "vtkRenderer.h"

#include "vtkPlotActor.h"
#include "vtkXYPlotData.h"
#include "vtkInteractorStylePlot.h"

int main(int, char *[])
{
    // Create an actor
    auto actor = vtkSmartPointer<vtkPlotActor>::New();
    actor->GetProperty()->SetColor(0.0, 0.0, 0.0);

    // Create a renderer, render window, and interactor
    auto renderer = vtkSmartPointer<vtkRenderer>::New();
    auto renderWindow = vtkSmartPointer<vtkRenderWindow>::New();
    renderWindow->AddRenderer(renderer);
    renderWindow->SetSize(800, 480);

    auto renderWindowInteractor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
    renderWindowInteractor->SetRenderWindow(renderWindow);

    // Add the actor to the scene
    actor->SetTitle("Example plot");
    renderer->SetBackground(1.0, 1.0, 1.0);
    renderer->AddActor2D(actor);

    // Add plot components
    auto xdata = vtkSmartPointer<vtkDoubleArray>::New();
    auto ydata = vtkSmartPointer<vtkDoubleArray>::New();
    double *x, *y;
    int N, i;

    // Arc plot
    auto plotData = vtkSmartPointer<vtkXYPlotData>::New();
    auto plotProperty = vtkSmartPointer<vtkProperty2D>::New();
    N = 50;
    xdata->SetNumberOfTuples(N);
    ydata->SetNumberOfTuples(N);
    x = xdata->GetPointer(0);
    y = ydata->GetPointer(0);
    for (i = 0; i < N; i++)
    {
        x[i] = 2.0 + cos((6.0 * i) / N);
        y[i] = 1.0 + sin((6.0 * i) / N);
    }
    plotData->AddData(xdata, ydata);
    plotProperty->SetColor(1, 0, 0);
    actor->AddData(plotData, plotProperty);

    // Func plot
    N = 120;
    plotData = vtkSmartPointer<vtkXYPlotData>::New();
    plotProperty = vtkSmartPointer<vtkProperty2D>::New();
    xdata->SetNumberOfTuples(N);
    ydata->SetNumberOfTuples(N);
    x = xdata->GetPointer(0);
    y = ydata->GetPointer(0);
    for (i = 0; i < N; i++)
    {
        x[i] = i / 30.0;
        y[i] = sin(x[i]) * (1 + cos(x[i]));
    }
    plotData->AddData(xdata, ydata);
    plotData->PlotPointsOn();
    plotProperty->SetColor(0, 1, 0);
    actor->AddData(plotData, plotProperty);

    // Exponential plot
    N = 200;
    plotData = vtkSmartPointer<vtkXYPlotData>::New();
    plotProperty = vtkSmartPointer<vtkProperty2D>::New();
    xdata->SetNumberOfTuples(N);
    ydata->SetNumberOfTuples(N);
    x = xdata->GetPointer(0);
    y = ydata->GetPointer(0);
    for (i = 0; i < N; i++)
    {
        x[i] = 4.0 * i / (N - 1);;
        y[i] = 2 * (exp(4.0 * i / (N - 1)) - 1) / (exp(4.0) - 1);
    }
    plotData->AddData(xdata, ydata);
    plotProperty->SetColor(0, 0, 1);
    actor->AddData(plotData, plotProperty);

    // Set interactor style
    auto style = vtkSmartPointer<vtkInteractorStylePlot>::New();
    style->SetCurrentRenderer(renderer);
    renderWindowInteractor->SetInteractorStyle(style);

    // Render and interact
    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}

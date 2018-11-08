from jchart import Chart
from jchart.config import Axes, DataSet, rgba, ScaleLabel, Legend, Title
import seaborn as sns
from math import *
from  .models import *

class ExpectedLoss_Over_Time_Chart(Chart):
    chart_type = 'line'
    legend = Legend(display=False)
    title = Title(display=True, text="Expected Loss over Time")
    scales = {
        'xAxes': [Axes(type='linear', 
                       position='bottom', 
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Years From Present'))],
        'yAxes': [Axes(type='linear', 
                       position='left',
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Expected Loss ($k)'))],
    }

    def __init__(self, project):
        super(ExpectedLoss_Over_Time_Chart, self).__init__()
        building = project.model()
        im_func = project.IM.model()
        
        xlimit = im_func.plot_max()
        
        self.data = []

        rate = 0.06

        for i in range(20):
            year = (i + 1) * 5
            loss = building.E_cost(year, rate) / 1000
            self.data.append({'x': year, 'y': loss})
        
        if isnan(building.getRebuildCost().mean()):
            if isnan(building.AnnualCost().mean()):
                title = "Missing data, somewhere; cost is NAN"
            else:
                title = "EAL=${}\nDiscount rate = {}%".format(round(building.AnnualCost().mean()), 100 * rate)
        else:
            title = "EAL=${}\n({} % of rebuild cost)\nDiscount rate = {}%".format(
                round(building.AnnualCost().mean()),
                round(10000 * 
                      building.AnnualCost().mean()/building.getRebuildCost().mean()) /
                100,
                100 * rate)
        self.title['text'] = title
        
    def get_datasets(self, *args, **kwargs):
        return [
            DataSet(
                type='line',
                data=self.data,
                borderColor=rgba(0x34,0x64,0xC7,1.0),
                backgroundColor=rgba(0,0,0,0.0)
            )]


class IMCostChart(Chart):
    chart_type = 'line'
    scales = {
        'xAxes': [Axes(type='linear',
                       position='bottom')],
        'yAxes': [Axes(scaleLabel=ScaleLabel(display=True, labelString="Cost"))]
    }

    def __init__(self, project):
        super(IMCostChart, self).__init__()
        self.repair = []
        self.demolition = []
        self.collapse = []
        if project.IM:
            self.scales['xAxes'][0]['scaleLabel']=ScaleLabel(
                display=True, 
                labelString=project.IM.label())

        # This was copied from earlier code, which calculated the data,
        # then passed it to the chart. This can be cleaned up to 
        # eliminate intermediate variables and streamline the process.
        if project.IM and len(project.model().ComponentsByEDP()) > 0:
            building = project.model()
            im_func = project.IM.model()
                
            xlimit = im_func.plot_max()

            columns = ['IM', 'Repair']
            if im_func.DemolitionRate():
                columns.append('Demolition')
            if im_func.CollapseRate():
                columns.append('Collapse')

            # Suppress legend if only one line
            if (len(columns) == 2):
                self.legend = Legend(display=False)
                        
            data = [columns]

            N = 10
            for i in range(N + 1):
                im = i/N * xlimit
                new_data = [im]
                costs = building.CostsByFate(im)
                new_data.append(costs[0].mean())
                
                if im_func.DemolitionRate():
                    new_data.append(costs[1].mean())
                if im_func.CollapseRate():
                    new_data.append(costs[2].mean())
                data.append(new_data)

            headings = data[0]
            for line in data[1:]:
                line.reverse()
                im = line.pop()

                for i in range(1, len(headings)):
                    cost = line.pop()
                    heading = headings[i]
                    if heading == 'Repair':
                        self.repair.append({'x': im, 'y': cost})
                    elif heading == 'Demolition':
                        self.demolition.append({'x': im, 'y': cost})
                    elif heading == 'Collapse':
                        self.collapse.append({'x': im, 'y': cost})
                    else:
                        raise ValueError("Unknown cost type: {}".format(heading))
        
    def get_datasets(self, *args, **kwargs):
        datasets = []
        if len(self.repair) > 0:
            datasets.append(DataSet(
                type='line',
                label='Repair',
                data=self.repair,
                borderColor=rgba(255,99,132,1.0),
                backgroundColor=rgba(0,0,0,0)
            ))
        if len(self.demolition) > 0:
            datasets.append(DataSet(
                type='line',
                label='Demolition',
                data=self.demolition,
                borderColor=rgba(54, 262, 235, 1.0),
                backgroundColor=rgba(0,0,0,0)
            ))
        if len(self.collapse) > 0:
            datasets.append(DataSet(
                type='line',
                label='Collapse',
                data=self.collapse,
                borderColor=rgba(74, 192, 191, 1.0),
                backgroundColor=rgba(0,0,0,0)
            ))
        return datasets

class IMPDFChart(Chart):
    chart_type = 'line'
    legend = False
    scales = {
        'xAxes': [Axes(type='linear', position='bottom')],
    }

    def __init__(self, project):
        super(IMPDFChart, self).__init__()
        self.pdf = []

        # This was copied from earlier code, which calculated the data,
        # then passed it to the chart. This can be cleaned up to 
        # eliminate intermediate variables and streamline the process.
        if project.IM and len(project.model().ComponentsByEDP()) > 0:
            building = project.model()
            im_func = project.IM.model()
                
            xlimit = im_func.plot_max()*5

            headings = ['IM', 'PDF']

            N = 50
            for i in range(N + 1):
                im = i/N * xlimit
                self.pdf.append({'x': im, 'y': building.pdf(im)})

    def get_datasets(self, *args, **kwargs):
        datasets = [DataSet(
            type='line',
            label='PDF',
            data=self.pdf,
            borderColor=rgba(255,99,132,1.0),
            backgroundColor=rgba(0,0,0,0)
        )]
        return datasets
    


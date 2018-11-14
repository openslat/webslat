from jchart import Chart
from jchart.config import Axes, DataSet, rgba, ScaleLabel, Legend, Title
import seaborn as sns
from math import *
from .models import *
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
def Command_String_from_Chart(chart):
    try:
        html = chart.as_html()
        command = re.search("Chart\(ctx, *(\{[^;]*)", html, re.MULTILINE).groups()[0][0:-1]
        js_command = command.replace("true", "True").replace("false", "False")
        result = eval(js_command)
        return result
    except Exception as e:
        eprint("Error converting command string for chart")
        eprint(e)
        return None


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

            N = 20
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
    

class ByFloorChart(Chart):
    chart_type = 'horizontalBar'
    legend = Legend(display=False)
    title = Title(display=True, text="Mean Annual Repair Cost by Floor")
    scales = {
        'xAxes': [Axes(type='linear', 
                       position='bottom', 
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Cost ($)'))],
        'yAxes': [Axes(position='left',
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Floor'))],
    }
    
    def __init__(self, project):
        super(ByFloorChart, self).__init__()
        self.labels = []
        self.costs = []
        building = project.model()
        im_func = project.IM.model()
        
        data = []
        rate = 0.06
        xlimit = im_func.plot_max()
        levels = {}
        for l in project.levels():
            levels[l] = []
        demand_groups = EDP_Grouping.objects.filter(project=project)
        for edp in demand_groups:
            for c in Component_Group.objects.filter(demand=edp):
                levels[edp.level].append(c)
        ordered_levels = project.levels()
        ordered_levels.sort(key=lambda x: x.level, reverse=True)
        for l in ordered_levels:
            self.labels.append(l.label)
            costs = 0
            for c in levels[l]:
                costs = costs + c.model().E_annual_cost()
            self.costs.append("{:>.2f}".format(costs))
        
    def get_labels(self, **kwargs):
        return self.labels

    def get_datasets(self, **kwargs):
        return [DataSet(label='Bar Chart',
                        data=self.costs,
                        borderWidth=1,
                        borderColor=rgba(0,0,0,1.0),
                        backgroundColor=rgba(0x34,0x64,0xC7,1.0))]


class ByCompPieChart(Chart):
    chart_type = 'pie'
    legend = Legend(display=False)
    title = Title(display=True)
    
    def __init__(self, project):
        super(ByCompPieChart, self).__init__()
        data = [['Component Type', 'Cost']]
        groups = {}
        demands = EDP_Grouping.objects.filter(project=project)
        for edp in demands:
            for c in Component_Group.objects.filter(demand=edp):
                type = c.component.name
                if not groups.get(type):
                    groups[type] = 0
                groups[type] = groups[type] + c.model().E_annual_cost()

        for key in groups.keys():
            data.append([key, groups[key]])
        
        self.title['text'] = 'Mean Annual Repair Cost By Component Type'
        self.labels = []
        self.costs = []
        # Skip the first entry, which are the column labels:
        for label, costs in data[1:]:
            self.labels.append(label)
            self.costs.append("{:>.2f}".format(costs))
        #self.title['text'] = 'By Floor'

        # Assign colors
        palette = sns.color_palette(None, len(self.costs))
        colors = []
        for r, g, b in palette:
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors.append(rgba(r, g, b, 0.5))

        self._colors = colors
        self._color_map = list(zip(self.labels, self._colors, self.costs))

    def get_color_map(self):
        return self._color_map
    
    def get_labels(self, **kwargs):
        return self.labels

    def get_datasets(self, **kwargs):
        return [DataSet(label='Pie Chart',
                        data=self.costs,
                        borderWidth=1,
                        borderColor=rgba(0,0,0,1.0),
                        backgroundColor=self._colors)]


class IMDemandPlot(Chart):
    chart_type = 'line'
    legend = Legend(display=True)
    title = Title(display=True, text="Hazard Curve")
    scales = {
        'xAxes': [Axes(type='linear', 
                       position='bottom', 
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Intensity Measure'))],
        'yAxes': [Axes(type='linear', 
                       position='left',
                       scaleLabel=ScaleLabel(display=True, 
                                             labelString='Demand'))]
    }
    
    
    def __init__(self, project, demand_type, direction):
        super(IMDemandPlot, self).__init__()

        if demand_type == 'D':
            demand_label  = 'Drift (radians)'
        elif demand_type == 'A':
            demand_label  = 'Acceleration (g)'
        else:
            raise ValueError("UNKNOWN DEMAND TYPE: {}".format(demand_type))
            
        self.title['text'] = "{} {}".format(project.title_text, demand_label)
        self.scales['yAxes'][0]['scaleLabel']['labelString'] = demand_label
        xlimit = project.IM.model().plot_max()

        palette = sns.color_palette(None, len(project.levels()))
        colors = []
        for r, g, b in palette:
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors.append(rgba(r, g, b, 0.5))

        self._colors = colors
        N = 25
        self._data = []
        for level in project.levels():
            points = []
            try:
                grouping = EDP_Grouping.objects.get(project=project, 
                                                    type=demand_type,
                                                    level=level)
                if direction == 'X':
                    demand_func = grouping.demand_x.model()
                elif direction == 'Y':
                    demand_func = grouping.demand_y.model()
                else:
                    raise ValueError("UNKNOWN DIRECTION: {}".format(direction))
                
                for i in range(1,N +1):
                    x = i/N * xlimit
                    points.append({'x': x, 'y': demand_func.Median(x)})
                self._data.append({'label':level.label, 'points': points})
            except:
                continue
            
    def get_datasets(self, *args, **kwargs):
        result = []
        for d in range(len(self._data)):
            result.append(DataSet(
                type='line',
                label=self._data[d]['label'],
                data=self._data[d]['points'],
                borderColor=self._colors[d],
                backgroundColor=rgba(0,0,0,0))
            )
        return(result)

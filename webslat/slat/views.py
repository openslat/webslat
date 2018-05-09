from __future__ import print_function
import sys
import pyslat
import re
#import matplotlib.pyplot as plt
from graphos.renderers import gchart
from graphos.views import FlotAsJson, RendererAsJson
from jchart import Chart
import numpy as np
from scipy.optimize import fsolve
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory, ValidationError, HiddenInput
from django.forms.models import model_to_dict
from django.core.exceptions import PermissionDenied
from .nzs import *
from math import *
from graphos.sources.model import SimpleDataSource
from graphos.sources.model import ModelDataSource
from graphos.renderers.gchart import LineChart, AreaChart, BarChart, PieChart
from dal import autocomplete
from django.template import RequestContext

from  .models import *
from .component_models import *
from slat.constants import *
from django.contrib.auth.decorators import login_required
from registration.backends.simple.views import RegistrationView
from registration.forms import RegistrationForm
from django.forms import ModelForm
import sys
from random import randint
from datetime import datetime, timedelta

from jchart import Chart
from jchart.config import Axes, DataSet, rgba, ScaleLabel, Legend, Title
import seaborn as sns

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class Cost_IM_Chart(Chart):
    chart_type = 'line'
    scales = {
        'xAxes': [Axes(type='linear', position='bottom')],
    }

    def __init__(self, data):
        super(Cost_IM_Chart, self).__init__()
        self.repair = []
        self.demolition = []
        self.collapse = []
        for im, repair, demolition, collapse in data:
            self.repair.append({'x': im, 'y': repair})
            self.demolition.append({'x': im, 'y': demolition})
            self.collapse.append({'x': im, 'y': collapse})
        
    def get_datasets(self, *args, **kwargs):
        return [
            DataSet(
                type='line',
                label='Repair',
                data=self.repair,
                borderColor=rgba(255,99,132,1.0),
                backgroundColor=rgba(0,0,0,0)
            ),
            DataSet(
                type='line',
                label='Demolition',
                data=self.demolition,
                borderColor=rgba(54,262,235,1.0),
                backgroundColor=rgba(0,0,0,0)
            ),
            DataSet(
                type='line',
                label='Collapse',
                data=self.collapse,
                borderColor=rgba(75,192,192,1.0),
                backgroundColor=rgba(0,0,0,0)
            )]
                

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

    def __init__(self, data, title):
        super(ExpectedLoss_Over_Time_Chart, self).__init__()
        self.data = []
        for year, loss in data:
            self.data.append({'x': year, 'y': loss})
        self.title['text'] = title
        
    def get_datasets(self, *args, **kwargs):
        return [
            DataSet(
                type='line',
                data=self.data,
                borderColor=rgba(0x34,0x64,0xC7,1.0),
                backgroundColor=rgba(0,0,0,0)
            )]
                

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
    
    def __init__(self, data):
        print(data)
        super(ByFloorChart, self).__init__()
        self.labels = []
        self.costs = []
        # Skip the first entry, which are the column labels:
        for label, costs in data[1:]:
            self.labels.append(label)
            self.costs.append(costs)
        #self.title['text'] = 'By Floor'
        
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
    legend = Legend(display=True, position='bottom')
    title = Title(display=True)
    
    def __init__(self, data, title):
        print(data)
        super(ByCompPieChart, self).__init__()
        self.title['text'] = title
        self.labels = []
        self.costs = []
        # Skip the first entry, which are the column labels:
        for label, costs in data[1:]:
            self.labels.append(label)
            self.costs.append(costs)
        #self.title['text'] = 'By Floor'
        
    def get_labels(self, **kwargs):
        return self.labels

    def get_datasets(self, **kwargs):
        palette = sns.color_palette(None, len(self.costs))
        colors = []
        for r, g, b in palette:
            colors.append(rgba(int(r * 255), int(g * 255), int(b * 255), 0.5))
            
        print(colors)
        return [DataSet(label='Pie Chart',
                        data=self.costs,
                        borderWidth=1,
                        borderColor=rgba(0,0,0,1.0),
                        backgroundColor=colors)]



@login_required
def index(request):
    if request.user.is_authenticated:
        user = "User is authenticated"
    else:
        user = "User is NOT authenticated"

    project_list = []
    for permissions in ProjectPermissions.objects.filter(user=request.user):
        project = permissions.project
        if project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
            #project_list.append(permissions.project)
                project_list.append({'id': project.id,
                                 'title_text': project.title_text,
                                 'role': permissions.role})
                
    context = { 'project_list': project_list, 'user': user }
    return render(request, 'slat/index.html', context)

def make_demo(user):
    project = Project()
    setattr(project, 'title_text', "This is a demo project")
    setattr(project, 'description_text', "Describe this project...")
    setattr(project, 'rarity', 1/500)
    project.save()

    project.AssignRole(user, ProjectPermissions.ROLE_FULL)

    # Create levels:
    num_floors = 5
    for l in range(num_floors + 1):
        if l == 0:
            label = "Ground Floor"
        elif l == num_floors:
            label = "Roof"
        else:
            label = "Floor #{}".format(l + 1)
        level = Level(project=project, level=l, label=label)
        level.save()
        
    # Create an IM:
    christchurch = Location.objects.get(location='Christchurch')
    nzs = NZ_Standard_Curve(location=christchurch,
                            soil_class = NZ_Standard_Curve.SOIL_CLASS_C,
                            period = 2.0)
    nzs.save()
    hazard = IM(flavour = IM_Types.objects.get(pk=IM_TYPE_NZS), nzs = nzs)
    hazard.save()
    project.IM = hazard
    project.save()

    # Create EDPs:
    demand_params = [{'level': 5, 'accel': {'a': 5.39, 'b': 1.5}, 'drift': {'a': 0.0202, 'b': 0.5}},
                     {'level': 4, 'accel': {'a': 4.18, 'b': 1.5}, 'drift': {'a': 0.0380, 'b': 0.5}},
                     {'level': 3, 'accel': {'a': 4.10, 'b': 1.5}, 'drift': {'a': 0.0506, 'b': 0.5}},
                     {'level': 2, 'accel': {'a': 4.25, 'b': 1.5}, 'drift': {'a': 0.0633, 'b': 0.5}},
                     {'level': 1, 'accel': {'a': 4.15, 'b': 1.5}, 'drift': {'a': 0.0557, 'b': 0.5}},
                     {'level': 0, 'accel': {'a': 4.05, 'b': 1.5}}]
    for demand in demand_params:
        level = Level.objects.get(level=demand['level'], project=project)
        if demand.get('accel'):
            params = demand.get('accel')
            curve = EDP_PowerCurve(median_x_a = params['a'],
                                   median_x_b = params['b'],
                                   sd_ln_x_a = 1.5,
                                   sd_ln_x_b = 0.0)
            curve.save()
            EDP(project = project,
                level = level,
                type = EDP.EDP_TYPE_ACCEL,
                flavour = EDP_Flavours.objects.get(name_text="Power Curve"),
                powercurve = curve).save()

        if demand.get('drift'):
            params = demand.get('drift')
            curve = EDP_PowerCurve(median_x_a = params['a'],
                                   median_x_b = params['b'],
                                   sd_ln_x_a = 1.5,
                                   sd_ln_x_b = 0.0)
            curve.save()
            EDP(project = project,
                level = level,
                type = EDP.EDP_TYPE_DRIFT,
                flavour = EDP_Flavours.objects.get(name_text="Power Curve"),
                powercurve = curve).save()
            
    # Add components:
    all_floors = range(num_floors + 1)
    not_ground = range(1, num_floors+1)
    components = [{'levels': all_floors, 'id': '206', 'quantity': 10},
                  {'levels': not_ground, 'id': 'B1041.032a', 'quantity': 32},
                  {'levels': not_ground, 'id': 'B1044.023', 'quantity': 8},
                  {'levels': not_ground, 'id': 'C1011.001a', 'quantity': 32}]
    for comp in components:
        component = ComponentsTab.objects.get(ident=comp['id'])
        for l in comp['levels']:
            level = Level.objects.get(project=project, level=l)
            
            if re.compile(".*Accel").match(component.demand.name):
                demand_type='A'
            elif re.compile(".*Drift").match(component.demand.name):
                demand_type='D'
            else:
                print(component.demand.name)
                raise ValueError("UNRECOGNIZED DEMAND TYPE FOR COMPONENT")

            demand = EDP.objects.get(project=project,
                                     level=level,
                                     type=demand_type)
            group = Component_Group(demand=demand, component=component, quantity=comp['quantity'])
            group.save()
    
    return project

def make_example_2(user):
    project = Project()
    setattr(project, 'title_text', "Example #2")
    setattr(project, 'description_text', "This is based on the second example in Brendan Bradley's paper. ")
    setattr(project, 'rarity', 1/500)
    setattr(project, 'mean_im_collapse', 1.2)
    setattr(project, 'sd_ln_im_collapse', 0.47)
    setattr(project, 'mean_cost_collapse', 14E6)
    setattr(project, 'sd_ln_cost_collapse', 0.35)
    
    setattr(project, 'mean_im_demolition', 0.9)
    setattr(project, 'sd_ln_im_demolition', 0.47)
    setattr(project, 'mean_cost_demolition', 14E6)
    setattr(project, 'sd_ln_cost_demolition', 0.35)
    project.save()

    project.AssignRole(user, ProjectPermissions.ROLE_FULL)

    # Create levels:
    num_floors = 10
    for l in range(num_floors + 1):
        if l == 0:
            label = "Ground Floor"
        elif l == num_floors:
            label = "Roof"
        else:
            label = "Floor #{}".format(l + 1)
        level = Level(project=project, level=l, label=label)
        level.save()
        
    # Create an IM:
    data = np.genfromtxt('example2/imfunc.csv', comments="#", delimiter=",", invalid_raise=True)
    for d in data:
        if type(d) == list or type(d) == np.ndarray:
            for e in d:
                if isnan(e):
                    raise ValueError("Error importing data")
                else:
                    if isnan(e):
                        raise ValueError("Error importing data")

    hazard = IM()
    hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_INTERP)
    hazard.interp_method = Interpolation_Method.objects.get(method_text="Log-Log")
    hazard.save()
    project.IM = hazard
    project.save()

    # Insert new points:
    for x, y in data:
        IM_Point(hazard=hazard, im_value=x, rate=y).save()
    project.IM = hazard
    project.save()

    # Create EDPs:
    demand_params = [{'level': 10, 'accel': "RB_EDP21.csv", 'drift': "RB_EDP20.csv"},
                     {'level': 9, 'accel': "RB_EDP19.csv", 'drift': "RB_EDP18.csv"},
                     {'level': 8, 'accel': "RB_EDP17.csv" , 'drift': "RB_EDP16.csv" },
                     {'level': 7, 'accel': "RB_EDP15.csv" , 'drift': "RB_EDP14.csv" },
                     {'level': 6, 'accel': "RB_EDP13.csv" , 'drift': "RB_EDP12.csv" },
                     {'level': 5, 'accel': "RB_EDP11.csv" , 'drift': "RB_EDP10.csv" },
                     {'level': 4, 'accel': "RB_EDP9.csv" , 'drift': "RB_EDP8.csv" },
                     {'level': 3, 'accel': "RB_EDP7.csv" , 'drift': "RB_EDP6.csv" },
                     {'level': 2, 'accel': "RB_EDP5.csv" , 'drift': "RB_EDP4.csv" },
                     {'level': 1, 'accel': "RB_EDP3.csv" , 'drift': "RB_EDP2.csv" },
                     {'level': 0, 'accel': "RB_EDP1.csv"}]
    for demand in demand_params:
        level = Level.objects.get(project=project, level=demand['level'])
        
        for demand_type in ['accel', 'drift']:
            if demand.get(demand_type):
                if demand_type == 'accel':
                    EDP_demand_type = 'A'
                elif demand_type == 'drift':
                    EDP_demand_type = 'D'
                else:
                    raise ValueError("INVALID DEMAND TYPE")
                
                edp = EDP(project=project, 
                          level=level,
                          type=EDP_demand_type)

                file = demand.get(demand_type)
                
                data = np.genfromtxt('example2/{}'.format(file), comments="#", delimiter=",", invalid_raise=True)
                # Validate the data:
                for d in data:
                    if type(d) == list or type(d) == np.ndarray:
                        for e in d:
                            if isnan(e):
                                raise ValueError("Error importing data")
                            else:
                                if isnan(e):
                                    raise ValueError("Error importing data")
            
                # Create an array from the points:
                points = [{'im': 0.0, 'mu': 0.0, 'sigma': 0.0}]
                for d in data:
                    if len(d) < 2:
                        raise ValueError("Wrong number of columns")
                    im = d[0]
                    values = d[1:]
                    ln_values = []
                    nz_values = []
                    for value in values:
                        if value != 0:
                            ln_values.append(log(value))
                            nz_values.append(value)
                    median_edp = exp(np.mean(ln_values))
                    sd_ln_edp = np.std(ln_values, ddof=1)
                    points.append({'im': im, 'mu': median_edp, 'sigma': sd_ln_edp})

                edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
                edp.interpolation_method = Interpolation_Method.objects.get(method_text="Linear")
                edp.save()

                for p in points:
                    EDP_Point(demand=edp, im=p['im'], median_x=p['mu'], sd_ln_x=p['sigma']).save()
            
    # Add components:
    all_floors = range(num_floors + 1)
    not_ground = range(1, num_floors+1)
    not_roof = range(num_floors)
    components = [{'levels': not_roof, 'id': '208', 'quantity': 53},
                  {'levels': [0], 'id': '204', 'quantity': 2},
                  {'levels': not_roof, 'id': '214', 'quantity': 10},
                  {'levels': not_ground, 'id': '203', 'quantity': 693},
                  {'levels': not_ground, 'id': '211', 'quantity': 23},
                  {'levels': [1], 'id': '2', 'quantity': 20},
                  {'levels': range(2, num_floors+1), 'id': '2', 'quantity': 4},
                  {'levels': not_ground, 'id': '2', 'quantity': 18},
                  {'levels': not_ground, 'id': '3', 'quantity': 16},
                  {'levels': not_ground, 'id': '105', 'quantity': 721},
                  {'levels': not_ground, 'id': '107', 'quantity': 99},
                  {'levels': not_ground, 'id': '106', 'quantity': 721},
                  {'levels': not_ground, 'id': '108', 'quantity': 10},
                  {'levels': [num_floors], 'id': '205', 'quantity': 4}]
                  
    for comp in components:
        component = ComponentsTab.objects.get(ident=comp['id'])
        for l in comp['levels']:
            level = Level.objects.get(project=project, level=l)
            
            if re.compile(".*Accel").match(component.demand.name):
                demand_type='A'
            elif re.compile(".*Drift").match(component.demand.name):
                demand_type='D'
            else:
                print(component.demand.name)
                raise ValueError("UNRECOGNIZED DEMAND TYPE FOR COMPONENT")

            demand = EDP.objects.get(project=project,
                                     level=level,
                                     type=demand_type)
            group = Component_Group(demand=demand, component=component, quantity=comp['quantity'])
            group.save()
    
    return project

@login_required
def demo(request):
    make_demo(request.user)
    return HttpResponseRedirect(reverse('slat:index'))
    

@login_required
def project(request, project_id=None):
    chart = None
    if request.method == 'POST':
        if project_id:
            project = Project.objects.get(pk=project_id)
            form = ProjectForm(request.POST, Project.objects.get(pk=project_id), initial=model_to_dict(project))
            form.instance.id = project_id
        else:
            project = None
            form = ProjectForm(request.POST)

        if not form.is_valid():
            print("INVALID")
            print(form.errors)

        if form.is_valid():
            form.save()

            if not project_id:
                project = form.instance

                levels_form = LevelsForm(request.POST)
                levels_form.is_valid()
                levels = levels_form.cleaned_data['levels']
                for l in range(levels + 1):
                    level = Level(project=project, level=l, label="Level #{}".format(l))
                    level.save()
                
                    EDP(project=project,
                        level=level,
                        type=EDP.EDP_TYPE_ACCEL).save()
                    if l > 0:
                        EDP(project=project,
                            level=level,
                            type=EDP.EDP_TYPE_DRIFT).save()
                
            if project_id and form.has_changed() and project.IM:
                project.IM._make_model()
                for edp in EDP.objects.filter(project=project):
                    edp._make_model()
                project._make_model()
                
            project.AssignRole(request.user, ProjectPermissions.ROLE_FULL)

            return HttpResponseRedirect(reverse('slat:project', args=(form.instance.id,)))

    else:
        # If the project exists, use it to populate the form:
        if project_id:
            
            project = get_object_or_404(Project, pk=project_id)
            if not project.CanRead(request.user):
                raise PermissionDenied
                
            form = ProjectForm(instance=project, initial=model_to_dict(project))
            
            if project.IM and len(project.model().ComponentsByEDP()) > 0:
                
                building = project.model()
                im_func = project.IM.model()
                
                xlimit = im_func.plot_max()

                columns = ['IM', 'Repair']
                if im_func.DemolitionRate():
                    columns.append('Demolition')
                if im_func.CollapseRate():
                    columns.append('Collapse')
                        
                data = [columns]

                for i in range(11):
                    im = i/10 * xlimit
                    new_data = [im]
                    costs = building.CostsByFate(im)
                    new_data.append(costs[0].mean())
                        
                    if im_func.DemolitionRate():
                        new_data.append(costs[1].mean())
                    if im_func.CollapseRate():
                        new_data.append(costs[2].mean())
                    data.append(new_data)

                data_source = SimpleDataSource(data=data)
                chart = LineChart(data_source, options={'title': 'Cost | IM',
                                                        'hAxis': {'logScale': True, 'title': 'Intensity Measure (g)'},
                                                        'vAxis': {'logScale': True, 'format': 'decimal',
                                                                  'title': 'Cost ($)'},
                                                        'pointSize': 5})
                j_chart = Cost_IM_Chart(data)
                chart = j_chart
                
            levels = project.num_levels()
            levels_form = None
            users = list(ProjectPermissions.objects.filter(project=project, role=ProjectPermissions.ROLE_FULL))
        else:
            form = ProjectForm()
            levels = None
            levels_form = LevelsForm()
            users = None
    return render(request, 'slat/project.html', {'form': form, 
                                                 'levels': levels, 
                                                 'levels_form': levels_form, 
                                                 'chart': chart,
                                                 'users': users})


@login_required
def hazard(request, project_id):
    # If the project doesn't exist, generate a 404:
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    # Otherwise:
    #    - Does the project already have a hazard defined? If so, we'll
    #      redirect to the 'view' page for that type of hazard
    #    - If not, we'll redirect to the 'choose' page:
    hazard = project.IM

    if not hazard:
            form = HazardForm()
            return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id,)))
    else:        
        # Hazard exists:
        flavour = hazard.flavour
        if flavour.id == IM_TYPE_NLH:
            form = NLHForm(instance=hazard.nlh)
            return HttpResponseRedirect(reverse('slat:nlh', args=(project_id,)))
        elif flavour.id == IM_TYPE_INTERP:
            return HttpResponseRedirect(reverse('slat:im_interp', args=(project_id,)))
        elif flavour.id == IM_TYPE_NZS:
            return HttpResponseRedirect(reverse('slat:nzs', args=(project_id,)))
        else:
            raise ValueError("UNKNOWN HAZARD TYPE")
        
@login_required
def hazard_choose(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied
    
    hazard = project.IM

    if request.POST:
        if request.POST.get('cancel'):
            # If the form was CANCELled, return the user to the project page (if no hazard has been defined),
            # or to the page for the current hazard (they got here because they cancelled a change to the 
            # hazard type):
            if hazard:
                # Shouldn't get here, but if we do, just redirect to the "choose hazard" page:
                return HttpResponseRedirect(reverse('slat:hazard', args=(project_id)))
            else:
                return HttpResponseRedirect(reverse('slat:project', args=(project_id)))
        elif not hazard:
            # The form was submitted, but the project doesn't have a hazard yet. Go straight
            # to the approporite 'edit' page to let the user enter data:
            if request.POST.get('flavour'):
                flavour = IM_Types.objects.get(pk=request.POST.get('flavour'))
                if flavour.id == IM_TYPE_NLH:
                    return HttpResponseRedirect(reverse('slat:nlh_edit', args=(project_id,)))
                elif flavour.id == IM_TYPE_INTERP:
                    return HttpResponseRedirect(reverse('slat:im_interp_edit', args=(project_id,)))
                elif flavour.id == IM_TYPE_NZS:
                    return HttpResponseRedirect(reverse('slat:im_nzs_edit', args=(project_id,)))
                else:
                    raise ValueError("UNKNOWN HAZARD TYPE")
            else:
                # Shouldn't get here, but if we do, just redirect to the "choose hazard" page:
                return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id,)))
        else:        
            # Hazard exists. If the chosen type already, exists, save the change and go to the
            # 'view' page for the hazard. Otherwise, don't save the change, but go to the 'edit'
            # page.
            flavour = IM_Types.objects.get(pk=request.POST.get('flavour'))
            if flavour.id == IM_TYPE_NLH:
                if hazard.nlh:
                    hazard.flavour = flavour
                    hazard.save()
                    hazard._make_model()
                    return HttpResponseRedirect(reverse('slat:nlh', args=(project_id,)))
                else:
                    return HttpResponseRedirect(reverse('slat:nlh_edit', args=(project_id,)))
            elif flavour.id == IM_TYPE_INTERP:
                if hazard.interp_method:
                    hazard.flavour = flavour
                    hazard.save()
                    hazard._make_model()
                    return HttpResponseRedirect(reverse('slat:im_interp', args=(project_id,)))
                else:
                    return HttpResponseRedirect(reverse('slat:im_interp_edit', args=(project_id,)))
            if flavour.id == IM_TYPE_NZS:
                if hazard.nzs:
                    hazard.flavour = flavour
                    hazard.save()
                    hazard._make_model()
                    return HttpResponseRedirect(reverse('slat:nzs', args=(project_id,)))
                else:
                    return HttpResponseRedirect(reverse('slat:im_nzs_edit', args=(project_id,)))
            else:
                raise ValueError("UNKNOWN HAZARD TYPE")
    else:
        if hazard:
            form = HazardForm(instance=hazard)
        else:
            form = HazardForm(initial={'flavour': IM_TYPE_NZS})

        return render(request, 'slat/hazard_choose.html', {'form': form, 
                                                           'project_id': project_id,
                                                           'title': project.title_text })

def _plot_hazard(h):
    if h.model():
        im_func = h.model()
        xlimit = im_func.plot_max()

        data =  [
            ['IM', 'lambda'],
        ]
        for i in range(11):
            x = i/10 * xlimit
            y = im_func.getlambda(x)
            data.append([x, y])
            
        data_source = SimpleDataSource(data=data)
        chart = LineChart(data_source, options={'title': 'Intensity Measure Rate of Exceedance', 
                                                'hAxis': {'logScale': True, 'title': h.label(),
                                                          'minorGridlines': {'count': 3}},
                                                'vAxis': {'logScale': True, 
                                                          'title': 'Rate of Exceedance',
                                                          'format': 'decimal',
                                                          'gridlines': {'count': 3},
                                                          'minorGridlines': {'count': 5}},
                                                'pointSize': 5,
                                                'legend': {'position': 'none'}})
        return chart
    
        
@login_required
def nlh(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied
    
    hazard = project.IM

    if request.method == 'POST':
        return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id)))
    else:
        if hazard and hazard.nlh:
            return render(request, 'slat/nlh.html', {'nlh':hazard.nlh, 'title': project.title_text, 
                                                     'project_id': project_id, 'chart': _plot_hazard(hazard)})
        else:
            return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id)))
            

@login_required
def nlh_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        if request.POST.get('cancel'):
            if hazard:
                return HttpResponseRedirect(reverse('slat:hazard', args=(project_id)))
            else:
                return HttpResponseRedirect(reverse('slat:project', args=(project_id)))

        project = get_object_or_404(Project, pk=project_id)
        hazard = project.IM

        if not hazard or not hazard.nlh:
            form = NLHForm(request.POST)
        else:
            form = NLHForm(request.POST, instance=hazard.nlh)
        form.save()
        if not hazard:
            hazard = IM()
        hazard.nlh = form.instance
        hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_NLH)
        hazard.save()
        hazard._make_model()
        project.IM = hazard
        project.save()

        return HttpResponseRedirect(reverse('slat:nlh', args=(project_id)))
    else:
        if hazard and hazard.nlh:
            form = NLHForm(instance=hazard.nlh)
        else:
            form = NLHForm()

    return render(request, 'slat/nlh_edit.html', {'form': form, 'project_id': project_id,
                                                  'title': project.title_text})

@login_required
def im_interp(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_id)
        hazard = project.IM

        if not hazard or not hazard.interp_method:
            form = Interpolation_Method_Form(request.POST)
        else:
            form = Interpolation_Method_Form(request.POST, initial={'method': hazard.interp_method.id})
        form.save()

        if not hazard:
            hazard = IM()
        if form.is_valid():
            hazard.interp_method = Interpolation_Method.objects.get(pk=form.cleaned_data['method'])

        hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_INTERP)
        hazard.save()
        hazard._make_model()
        project.IM = hazard
        project.save()
        
        Point_Form_Set = modelformset_factory(IM_Point, can_delete=True, fields=('im_value', 'rate'), extra=3)
        formset = Point_Form_Set(request.POST, queryset=IM_Point.objects.filter(hazard=hazard).order_by('im_value'))

        instances = formset.save(commit=False)

        for instance in instances:
            instance.hazard = hazard
            if instance.im_value==0 and instance.rate==0:
                instance.delete()
            else:
                instance.save()

        # Rebuild the form from the database; this removes any deleted entries
        formset = Point_Form_Set(queryset=IM_Point.objects.filter(hazard=hazard).order_by('im_value'))
        return render(request, 'slat/im_interp.html', {'form': form, 'points': formset,
                                                       'project_id': project_id, 'title': project.title_text})
            
    # if a GET (or any other method) we'll create a blank form
    elif hazard:
        points = IM_Point.objects.filter(hazard=hazard).order_by('im_value')
        method = hazard.interp_method

        chart = _plot_hazard(hazard)

        return render(request, 'slat/im_interp.html', {'method': method, 'points': points,
                                                       'project_id': project_id, 'chart': chart,
                                                       'title': project.title_text})
    else:
        # Shouldn't get here, but if we do, just redirect to the "choose hazard" page:
        return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id,)))
        
    return render(request, 'slat/im_interp.html', {'method': method, 'points': points, 
                                                   'project_id': project_id,
                                                   'title': project.title_text})

@login_required
def im_interp_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_id)
        hazard = project.IM

        if request.POST.get('cancel'):
            if hazard:
                return HttpResponseRedirect(reverse('slat:hazard', args=(project_id)))
            else:
                return HttpResponseRedirect(reverse('slat:project', args=(project_id)))

        if not hazard or not hazard.interp_method:
            form = Interpolation_Method_Form(request.POST)
        else:
            form = Interpolation_Method_Form(request.POST, initial={'method': hazard.interp_method.id})

        if not hazard:
            hazard = IM()
        if form.is_valid():
            hazard.interp_method = Interpolation_Method.objects.get(pk=form.cleaned_data['method'])
        hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_INTERP)
        hazard.save()
        hazard._make_model()
        project.IM = hazard
        project.save()

        Point_Form_Set = modelformset_factory(IM_Point, can_delete=True, exclude=('id', 'hazard',), extra=3)
        formset = Point_Form_Set(request.POST, queryset=IM_Point.objects.filter(hazard=hazard).order_by('im_value'))

        if not formset.is_valid():
            print(formset.errors)
        instances = formset.save(commit=False)

        for f in formset.deleted_forms:
            f.instance.delete()
            
        for instance in instances:
            if instance.id and instance.DELETE:
                instance.delete()
            else:
                instance.hazard = hazard
                instance.save()

        if request.POST.get('done'):
            return HttpResponseRedirect(reverse('slat:im_interp', args=(project_id)))
        else:
            # Rebuild the form from the database; this removes any deleted entries
            formset = Point_Form_Set(queryset=IM_Point.objects.filter(hazard=hazard).order_by('im_value'))
            return render(request, 'slat/im_interp_edit.html', {'form': form, 'points': formset, 
                                                                'project_id': project_id,
                                                                'title': project.title_text})
            
    # if a GET (or any other method) we'll create a blank form
    else:
        Point_Form_Set = modelformset_factory(IM_Point, can_delete=True, exclude=('hazard',), widgets={'id': HiddenInput}, extra=3)
        if hazard and hazard.interp_method:
            form = Interpolation_Method_Form(initial={'method': hazard.interp_method.id})
            formset = Point_Form_Set(queryset=IM_Point.objects.filter(hazard=hazard).order_by('im_value'))
        else:
            form = Interpolation_Method_Form(initial={'method': INTERP_LOGLOG})
            formset = Point_Form_Set(queryset=IM_Point.objects.none())

    return render(request, 'slat/im_interp_edit.html', {'form': form, 'points': formset,
                                                        'project_id': project_id,
                                                        'title': project.title_text})

@login_required
def im_file(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        interp_form = Interpolation_Method_Form(request.POST)
        form = Input_File_Form(request.POST, request.FILES)

        try:
            # Now save the data. First make sure the database hierarchy is present:
            if not hazard:
                hazard = IM()
            if interp_form.is_valid():
                hazard.interp_method = Interpolation_Method.objects.get(pk=interp_form.cleaned_data['method'])
            else:
                hazard.interp_method = Interpolation(method=Interpolation_Method.objects.get(pk=INTERP_LOGLOG))
                
            if form.is_valid():
                if form.cleaned_data['flavour'].id == INPUT_FORMAT_CSV:
                    data = np.genfromtxt(request.FILES['path'].file, comments="#", delimiter=",", invalid_raise=True)
                    for d in data:
                        if type(d) == list or type(d) == np.ndarray:
                            for e in d:
                                if isnan(e):
                                    raise ValueError("Error importing data")
                        else:
                            if isnan(d):
                                raise ValueError("Error importing data")
                elif form.cleaned_data['flavour'].id == INPUT_FORMAT_LEGACY:
                    data = np.loadtxt(request.FILES['path'].file, skiprows=2)
                else:
                    raise ValueError("Unrecognised file format specified.")
                    
            if len(data[0]) != 2:
                raise ValueError("Wrong number of columns")


            hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_INTERP)
            hazard.save()
            project.IM = hazard
            project.save()
            # Remove any existing points:
            IM_Point.objects.filter(hazard = hazard).delete()
            
            # Insert new points:
            for x, y in data:
                IM_Point(hazard=hazard, im_value=x, rate=y).save()

            hazard._make_model()
            return HttpResponseRedirect(reverse('slat:im_interp', args=(project_id,)))
        except ValueError as e:
            data = None
            form.add_error(None, 'There was an error importing the file.')

        return render(request, 'slat/im_file.html', {'form': form,
                                                     'interp_form': interp_form,
                                                     'project_id': project_id,
                                                     'title': project.title_text,
                                                     'data': data})
            
    # if a GET (or any other method) we'll create a blank form
    else:
        form = Input_File_Form()
        if hazard and hazard.interp_method:
            interp_form = Interpolation_Method_Form(initial={'method': hazard.interp_method.id})
        else:
            interp_form = Interpolation_Method_Form()
        form.fields['path'].widget.attrs['class'] = 'normal'
        form.fields['path'].widget.attrs['title'] = 'Choose the input file'
        
        return render(request, 'slat/im_file.html', {'form': form, 
                                                     'interp_form': interp_form,
                                                     'project_id': project_id,
                                                     'title': project.title_text})
    

@login_required
def im_nzs(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        # Shouldn't get here, but if we do, just redirect to the "choose hazard" page:
        return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id,)))
    else:
        if hazard and hazard.nzs:
            if False:
                nzs = hazard.nzs
                data = [['IM', 'lambda']]
                for r in R_defaults:
                    y = 1/r
                    x =  C(hazard.nzs.soil_class,
                           hazard.nzs.period,
                           r,
                           hazard.nzs.location.z,
                           hazard.nzs.location.min_distance)
                    data.append([x, y])

                    data_source = SimpleDataSource(data=data)
                    chart = LineChart(data_source, options={'title': 'Intensity Measure Rate of Exceedance', 
                                                            'hAxis': {'logScale': True}, 'vAxis': {'logScale': True}})
            else:
                chart = _plot_hazard(hazard)
        
            return render(request, 'slat/nzs.html', {'nzs':hazard.nzs, 'title': project.title_text, 
                                                         'project_id': project_id, 'chart': chart})
        else:
            # Shouldn't get here, but if we do, just redirect to the "choose hazard" page:
            return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id,)))
            

@login_required
def im_nzs_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    hazard = project.IM

    if request.method == 'POST':
        if request.POST.get('cancel'):
            if hazard:
                return HttpResponseRedirect(reverse('slat:hazard', args=(project_id)))
            else:
                return HttpResponseRedirect(reverse('slat:project', args=(project_id)))

        if request.POST.get('edit'):
            return HttpResponseRedirect(reverse('slat:im_nzs_edit', args=(project_id)))
        
        project = get_object_or_404(Project, pk=project_id)
        hazard = project.IM

        if not hazard or not hazard.nzs:
            form = NZSForm(request.POST)
        else:
            form = NZSForm(request.POST, instance=hazard.nzs)
        form.save()

        if not hazard:
            hazard = IM()
        hazard.nzs = form.instance
        hazard.nzs.save()
        hazard.flavour = IM_Types.objects.get(pk=IM_TYPE_NZS)
        hazard.save()
        hazard._make_model()
        project.IM = hazard
        project.save()

        return HttpResponseRedirect(reverse('slat:nzs', args=(project_id)))
    
    else:
        if hazard and hazard.nzs:
            form = NZSForm(instance=hazard.nzs)
        else:
            form = NZSForm()

    return render(request, 'slat/nzs_edit.html', {'form': form, 'project_id': project_id,
                                                     'title': project.title_text})
    
def _plot_demand(edp):
    if edp.model():
        
        if edp.type == 'D':
            demand_type  = 'Drift (radians)'
        elif edp.type == 'A':
            demand_type  = 'Acceleration (g)'
        else:
            demand_type = 'Unknown'
            
        demand = "{} {}".format(edp.level.label, demand_type)
                                    
        edp_func = edp.model()
        xlimit = edp.project.IM.model().plot_max()

        data =  [['IM', 'Median', "10%", "90%"]]
        for i in range(11):
            x = i/10 * xlimit
            median = edp_func.Median(x)
            x_10 = edp_func.X_at_exceedence(x, 0.10)
            x_90 = edp_func.X_at_exceedence(x, 0.90)
            data.append([x, median, x_10, x_90])

            
        data_source = SimpleDataSource(data=data)
        chart1 = LineChart(data_source, options={'title': '{} | Intensity Measure'.format(demand), 
                                                 'hAxis': {'title': edp.project.im_label()},
                                                 'vAxis': {'title': demand},
                                                'pointSize': 5})
        
        data = [['Demand', 'Lambda']]
        xlimit = edp_func.plot_max()

        #print("{:>15.6}{:>15.6}".format("EDP", "LAMBDA"))
        for i in range(11):
            xval = i/10 * xlimit
            rate = edp_func.getlambda(xval)
            data.append([xval, rate])
            #print("{:>15.6}{:>15.6}".format(xval, rate))

        data_source = SimpleDataSource(data=data)
        chart2 = LineChart(data_source, options={'title': '{} Rate of Exceedance'.format(demand), 
                                                'hAxis': {'logScale': False, 'title': demand},
                                                 'vAxis': {'logScale': False, 'title': 'Rate of Exceedance'},
                                                 'pointSize': 5,
                                                 'legend': {'position': 'none'}})
        return [chart1, chart2]

@login_required
def edp_view(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
        
    if request.method == 'POST':
        raise ValueError("SHOULD NOT GET HERE")
    else:
        flavour = edp.flavour
        if not flavour:
            return HttpResponseRedirect(reverse('slat:edp_choose', args=(project_id, edp_id)))
        elif flavour.id == EDP_FLAVOUR_POWERCURVE:
            return HttpResponseRedirect(reverse('slat:edp_power', args=(project_id, edp_id)))
        elif flavour.id == EDP_FLAVOUR_USERDEF:
            return HttpResponseRedirect(reverse('slat:edp_userdef', args=(project_id, edp_id)))
        else:
            raise ValueError("edp_view not implemented")
    
@login_required
def edp_init(request, project_id):
    # If the project doesn't exist, generate a 404:
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    if request.method == 'POST':
        project.floors = int(request.POST.get('floors'))
        project.save()
        for f in range(int(project.floors) + 1):
            EDP(project=project,
                level=f,
                type=EDP.EDP_TYPE_ACCEL).save()
            if f > 0:
                EDP(project=project,
                    level=f,
                    type=EDP.EDP_TYPE_DRIFT).save()
        return HttpResponseRedirect(reverse('slat:edp', args=(project_id)))
    else:
        return render(request, 'slat/edp_init.html', {'project': project, 'form': FloorsForm()})
    
@login_required
def edp_choose(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    
    if request.POST:
        if request.POST.get('cancel'):
            # If the form was CANCELled, return the user to the EDP page
            return HttpResponseRedirect(reverse('slat:edp', args=(project_id)))
        
        flavour = EDP_Flavours.objects.get(pk=request.POST.get('flavour'))
        if flavour.id == EDP_FLAVOUR_USERDEF:
            return HttpResponseRedirect(reverse('slat:edp_userdef_edit', args=(project_id, edp_id)))
        elif flavour.id == EDP_FLAVOUR_POWERCURVE:
            return HttpResponseRedirect(reverse('slat:edp_power_edit', args=(project_id, edp_id)))
        else:
            raise ValueError("EDP_CHOOSE: Unrecognized choice '{}'".format(flavour))
            
    else:
        form = EDPForm()
        return render(request, 'slat/edp_choose.html', {'form': form, 
                                                        'project': project,
                                                        'edp': edp})
    raise ValueError("EDP_CHOOSE not implemented")

@login_required
def edp_power(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    charts = _plot_demand(edp)
    return render(request, 'slat/edp_power.html', {'project': project, 'edp': edp, 'charts': charts})

@login_required
def edp_power_edit(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    
    if request.POST:
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('slat:edp', args=(project_id)))

        if not edp.powercurve:
            form = EDP_PowerCurve_Form(request.POST)
        else:
            form = EDP_PowerCurve_Form(request.POST, instance=edp.powercurve)
        form.save()
        edp.powercurve = form.instance
        edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_POWERCURVE);

        edp.save()
        edp._make_model()
        
        return HttpResponseRedirect(reverse('slat:edp_power', args=(project_id, edp_id)))
    else:
        if edp.powercurve:
            form = EDP_PowerCurve_Form(instance=edp.powercurve)
        else:
            form = EDP_PowerCurve_Form()

        return render(request, 'slat/edp_power_edit.html', {'form': form,
                                                            'project': project,
                                                            'edp': edp})

@login_required
def edp_userdef(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    charts = _plot_demand(edp)
    
    return render(request, 'slat/edp_userdef.html',
                  { 'project': project, 
                    'edp': edp,
                    'charts': charts,
                    'points': EDP_Point.objects.filter(demand=edp).order_by('im')})

@login_required
def edp_userdef_edit(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    
    if request.method == 'POST':
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('slat:edp_view', args=(project.id, edp.id)))

        edp.flavour =  EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
        edp.interpolation_method = Interpolation_Method.objects.get(pk=request.POST.get('method'))
        edp.save()
        edp._make_model()
        
        Point_Form_Set = modelformset_factory(EDP_Point, can_delete=True, exclude=('demand',), widgets={'id': HiddenInput}, extra=3)
        formset = Point_Form_Set(request.POST, queryset=EDP_Point.objects.filter(demand=edp).order_by('im'))

        if not formset.is_valid():
            print(formset.errors)
        instances = formset.save(commit=False)
        
        for form in formset.deleted_forms:
            form.instance.delete()
            
        for instance in instances:
            if instance.id and instance.DELETE:
                instance.delete()
            else:
                instance.demand = edp
                instance.save()

        return HttpResponseRedirect(reverse('slat:edp_view', args=(project.id, edp.id)))
            
    # if a GET (or any other method) we'll create a blank form
    else:
        Point_Form_Set = modelformset_factory(EDP_Point, can_delete=True, exclude=('demand',), widgets={'id': HiddenInput}, extra=3)
        formset = Point_Form_Set(queryset=EDP_Point.objects.filter(demand=edp).order_by('im'))
        if edp.interpolation_method:
            form = Interpolation_Method_Form(initial={'method': edp.interpolation_method.id})
        else:
            form = Interpolation_Method_Form(initial={'method': INTERP_LINEAR})

        return render(request, 'slat/edp_userdef_edit.html',
                      {'form': form, 'points': formset,
                       'project': project, 'edp': edp})

@login_required
def edp_userdef_import(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    if request.method == 'POST':
        interp_form = Interpolation_Method_Form(request.POST)
        form = Input_File_Form(request.POST, request.FILES)

        try:
            if form.is_valid():
                if form.cleaned_data['flavour'].id == INPUT_FORMAT_CSV:
                    data = np.genfromtxt(request.FILES['path'].file, comments="#", delimiter=",", invalid_raise=True)
                    for d in data:
                        if type(d) == list or type(d) == np.ndarray:
                            for e in d:
                                if isnan(e):
                                    raise ValueError("Error importing data")
                        else:
                            if isnan(d):
                                raise ValueError("Error importing data")
                elif form.cleaned_data['flavour'].id == INPUT_FORMAT_LEGACY:
                    data = np.loadtxt(request.FILES['path'].file, skiprows=2)
                else:
                    raise ValueError("Unrecognised file format specified.")
            # Validate the data:
            points = [{'im': 0.0, 'mu': 0.0, 'sigma': 0.0}]
            for d in data:
                if len(d) < 2:
                    raise ValueError("Wrong number of columns")
                im = d[0]
                values = d[1:]
                ln_values = []
                nz_values = []
                for value in values:
                    if value != 0:
                        ln_values.append(log(value))
                        nz_values.append(value)
                median_edp = exp(np.mean(ln_values))
                sd_ln_edp = np.std(ln_values, ddof=1)
                points.append({'im': im, 'mu': median_edp, 'sigma': sd_ln_edp})

            edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
            if interp_form.is_valid():
                edp.interpolation_method = Interpolation_Method.objects.get(pk=interp_form.cleaned_data['method'])
            else:
                raise ValueError("INVALID INTERP FORM")
            edp.save()
            
            # Remove any existing points:
            EDP_Point.objects.filter(demand = edp).delete()
            
            # Insert new points:
            for p in points:
                EDP_Point(demand=edp, im=p['im'], median_x=p['mu'], sd_ln_x=p['sigma']).save()

            edp._make_model()
            return HttpResponseRedirect(reverse('slat:edp_userdef', args=(project_id, edp_id)))
        except ValueError as e:
            data = None
            form.add_error(None, 'There was an error importing the file.')

        #print(data)
        return render(request, 'slat/edp_userdef_import.html', {'form': form, 
                                                                'interp_form': interp_form,
                                                                'project': project,
                                                                'edp': edp,
                                                                'data': data})
            
    # if a GET (or any other method) we'll create a blank form
    else:
        if edp.interpolation_method:
            interp_form = Interpolation_Method_Form(initial={'method': edp.interpolation_method.id})
        else:
            interp_form = Interpolation_Method_Form()
        form = Input_File_Form()
        return render(request, 'slat/edp_userdef_import.html', {'form': form, 
                                                                'interp_form': interp_form,
                                                                'project': project,
                                                                'edp':edp})
    raise ValueError("EDP_USERDEF_IMPORT not implemented")

@login_required
def cgroup(request, project_id, floor_num, cg_id=None):
     project = get_object_or_404(Project, pk=project_id)

     if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

     if request.method == 'POST':
         if request.POST.get('cancel'):
             return HttpResponseRedirect(reverse('slat:edp', args=(project_id)))
         cg_form = CompGroupForm(request.POST)
         cg_form.save()
         cg_id = cg_form.instance.id
         
         return HttpResponseRedirect(reverse('slat:compgroup', args=(project_id, cg_id)))
     else:
         if cg_id:
             cg = get_object_or_404(Component_Group, pk=cg_id)
             cg_form = CompGroupForm(instance=cg)
         else:
             cg_form = CompGroupForm()
             
             
             
         return render(request, 'slat/cgroup.html', {'project_id': project_id,
                                                     'floor_num': floor_num, 
                                                     'cg_id': cg_id,
                                                     'cg_form': cg_form})

@login_required
def level_cgroup(request, project_id, level_id, cg_id=None):
     project = get_object_or_404(Project, pk=project_id)

     if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

     if request.method == 'POST':
         if request.POST.get('cancel'):
             return HttpResponseRedirect(reverse('slat:floor_cgroups', args=(project_id, floor_num)))

         if request.POST.get('delete'):
             cg = Component_Group.objects.get(pk=cg_id)
             project.model().RemoveCompGroup(cg.model())
             cg.delete()
             return HttpResponseRedirect(reverse('slat:level_cgroups', args=(project_id, level_id)))

         if cg_id:
             cg = Component_Group.objects.get(pk=cg_id)
             cg_form = FloorCompGroupForm(request.POST, initial=model_to_dict(cg))
         else:
             cg = Component_Group()
             cg_form = FloorCompGroupForm(request.POST)

         cg_form.is_valid()
         component = cg_form.cleaned_data['component']
         
         edp = EDP.objects.filter(project=project, level=Level.objects.get(pk=level_id))

         if re.search('^Accel(?i)', component.demand.name):
             edp = edp.filter(type='A')
         else:
             edp = edp.filter(type='D')

         cg.demand = edp[0]
         cg.component = component
         cg.quantity = cg_form.cleaned_data['quantity']
         cg.save()
         if cg_form.has_changed():
             cg._make_model()
         cg_id = cg.id
         
         return HttpResponseRedirect(reverse('slat:level_cgroups', args=(project_id, level_id)))
     else:
         if cg_id:
             cg = get_object_or_404(Component_Group, pk=cg_id)
             demand_form = ComponentForm(initial=model_to_dict(cg), level=level_id)
         else:
             demand_form = ComponentForm(level=level_id)
             
         return render(request, 'slat/level_cgroup.html', {'project': project,
                                                           'level': Level.objects.get(pk=level_id),
                                                           'cg_id': cg_id,
                                                           'demand_form': demand_form})
     

@login_required
def edp_cgroups(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
    edp = get_object_or_404(EDP, pk=edp_id)
        
    if request.method == 'POST':
         raise ValueError("SHOULD NOT GET HERE")
    else:
        return render(request, 'slat/edp_cgroups.html',
                      {'project': project,
                       'edp': edp,
                       'cgs': Component_Group.objects.filter(demand=edp)})

@login_required
def edp_cgroup(request, project_id, edp_id, cg_id=None):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edp = get_object_or_404(EDP, pk=edp_id)
    if request.method == 'POST':
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('slat:edp_cgroups', args=(project_id, edp_id)))

        if request.POST.get('delete'):
            cg = Component_Group.objects.get(pk=cg_id)
            project.model().RemoveCompGroup(cg.model())
            cg.delete()
            return HttpResponseRedirect(reverse('slat:edp_cgroups', args=(project_id, edp_id)))
             
        if cg_id:
             cg = Component_Group.objects.get(pk=cg_id)
        else:
             cg = None
        cg_form = EDPCompGroupForm(request.POST, instance=cg)
         
        cg_form.save(commit=False)
        if cg_id:
            cg_form.instance.id = int(cg_id)
        cg_form.save()
        if cg_form.has_changed():
            cg_form.instance._make_model()

        return HttpResponseRedirect(reverse('slat:edp_cgroups', args=(project_id, edp_id)))
    else:
        if cg_id:
            cg = Component_Group.objects.get(pk=cg_id)
            cg_form = EDPCompGroupForm(instance=cg)
        else:
            cg_form = EDPCompGroupForm(initial={'demand': edp})
        
        if edp.type == 'A':
            cg_form.fields['component'].queryset = ComponentsTab.objects.filter(demand=DemandsTab.objects.get(name__icontains='Accel'))
        elif edp.type == 'D':
            cg_form.fields['component'].queryset = ComponentsTab.objects.filter(demand=DemandsTab.objects.get(name__icontains='Drift'))
            
        return render(request, 'slat/edp_cgroup.html',
                      {'project': project,
                       'edp': edp,
                       'cg_form': cg_form})
    
@login_required
def cgroups(request, project_id):
     project = get_object_or_404(Project, pk=project_id)
     return render(request, 'slat/cgroups.html', {'project': project,
                                                  'cgs': Component_Group.objects.filter(demand__project=project)})
 
@login_required
def level_cgroups(request, project_id, level_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    edps = EDP.objects.filter(project=project, level=Level.objects.get(pk=level_id))
    cgs = []
    for edp in edps:
        groups = Component_Group.objects.filter(demand=edp)
        for cg in groups:
            cgs.append(cg)
            
    if request.method == 'POST':
         raise ValueError("SHOULD NOT GET HERE")
    else:
        return render(request, 'slat/level_cgroups.html',
                      {'project': project,
                       'level': Level.objects.get(pk=level_id),
                       'cgs': cgs})

@login_required
def levels(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    levels = project.levels()
    return render(request, 'slat/levels.html', 
                  {'project': project, 
                   'levels': levels})
@login_required
def demand(request, project_id, level_id, type):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    if type == 'drift':
        type = 'D'
    elif type =='acceleration':
        type = 'A'
    else:
        raise ValueError("UNKNOWN DEMAND TYPE")
        
    demand = EDP.objects.filter(project=project, level=Level.objects.get(pk=level_id), type=type)
    if len(demand) != 1:
        raise ValueError("Demand does not exist")


    demand = demand[0]
    flavour = demand.flavour
    if not flavour:
        return HttpResponseRedirect(reverse('slat:edp_choose', args=(project_id, demand.id)))
    elif flavour.id == EDP_FLAVOUR_POWERCURVE:
        return HttpResponseRedirect(reverse('slat:edp_power', args=(project_id, demand.id)))
    elif flavour.id == EDP_FLAVOUR_USERDEF:
        return HttpResponseRedirect(reverse('slat:edp_userdef', args=(project_id, demand.id)))
    else:
        raise ValueError("demand view not implemented")

    
@login_required
def analysis(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    chart = None
    jchart = None
    by_fate_chart = None
    by_floor_bar_chart = None
    by_comp_pie_chart = None

    if project.IM:
        building = project.model()
        im_func = project.IM.model()
        
        xlimit = im_func.plot_max()
        
        data = [['Year', 'Loss']]

        rate = 0.06
        for i in range(20):
            year = (i + 1) * 5
            loss = building.E_cost(year, rate) / 1000
            data.append([year, loss])
        
        data_source = SimpleDataSource(data=data)
        
        if isnan(building.getRebuildCost().mean()):
            title = "EAL=${}\nDiscount rate = {}%".format(building.AnnualCost().mean(), 100 * rate)
        else:
            title = "EAL=${}\n({} % of rebuild cost)\nDiscount rate = {}%".format(round(building.AnnualCost().mean()),
                                                                                  round(10000 * 
                                                                                        building.AnnualCost().mean()/building.getRebuildCost().mean()) /
                                                                                  100,
                                                                                  100 * rate)
        chart = LineChart(data_source, options={'title': title,
                                                'hAxis': {'logScale': False, 'title': 'Time from present (years)'},
                                                'vAxis': {'logScale': False, 'format': 'decimal',
                                                          'title': 'Expected Loss ($k)'},
                                                'pointSize': 5,
                                                'pointsVisible': False,
                                                'curveType': 'function',
                                                'legend': {'position': 'none'}})

        jchart = ExpectedLoss_Over_Time_Chart(data, title.replace("\n", "; "))
                                              
        
        if False:
            im_func = project.IM.model()
            columns = ['IM', 'Repair Costs']
            if im_func.DemolitionRate() or im_func.CollapseRate():
                columns.append('Total Costs')

            data = [columns]
            xlimit = im_func.plot_max()
            for i in range(10):
                im = i/10 * xlimit
                new_data = [im]
                costs = building.CostsByFate(im)
                new_data.append(costs[0].mean())


                if im_func.DemolitionRate() or im_func.CollapseRate():
                    non_repair_cost = new_data[1]
                    if im_func.DemolitionRate():
                        non_repair_cost = non_repair_cost + costs[1].mean()
                    if im_func.CollapseRate():
                        non_repair_cost = non_repair_cost + costs[2].mean()
                    new_data.append(non_repair_cost)
                data.append(new_data)

            data_source = SimpleDataSource(data=data)
            by_fate_chart = AreaChart(data_source, options={'title': 'Cost | IM',
                                                            'hAxis': {'logScale': True, 'title': project.im_label()},
                                                            'vAxis': {'logScale': True, 'format': 'decimal',
                                                                      'title': 'Cost ($)'},
                                                            'pointSize': 5})

        levels = {}
        for l in project.levels():
            levels[l] = []
        demands = EDP.objects.filter(project=project)
        for edp in demands:
            for c in Component_Group.objects.filter(demand=edp):
                levels[edp.level].append(c)

        if False:
            # Split repair costs by Structural and Non-Structural Components
            im_func = project.IM.model()
            columns = ['IM', 'Structural', 'Non-Structural', 'Total']

            structural_components = []
            non_structural_components = []
            demands = EDP.objects.filter(project=project)
            for edp in demands:
                for c in Component_Group.objects.filter(demand=edp):
                    floors[edp.floor].append(c)
                    if c.component.structural != 0:
                        structural_components.append(c)
                    else:
                        non_structural_components.append(c)

            data = [columns]
            xlimit = im_func.plot_max()
            for i in range(10):
                im = i/10 * xlimit
                new_data = [im]

                costs = 0
                for cg in structural_components:
                    costs = costs + cg.model().E_Cost_IM(im)
                new_data.append(costs)

                costs = 0
                for cg in non_structural_components:
                    costs = costs + cg.model().E_Cost_IM(im)
                new_data.append(costs)

                total_cost = building.Cost(im, False)
                new_data.append(total_cost.mean())
                data.append(new_data)

            data_source = SimpleDataSource(data=data)
            s_ns_chart = AreaChart(data_source, options={'title': 'Cost | IM',
                                                         'hAxis': {'logScale': True, 'title': project.im_label()},
                                                         'vAxis': {'logScale': True, 'format': 'decimal',
                                                                   'title': 'Cost ($)' ,
                                                                   'viewWindow': {'min': 1}},
                                                         'pointSize': 5})

        if False:
            columns = ['IM']
            for f in range(project.floors + 1):
                columns.append("Floor #{}".format(f))
            #columns.append('Total')
            data = [columns]

            xlimit = im_func.plot_max()
            for i in range(10):
                im = i/10 * xlimit
                new_data = [im]

                for f in range(project.floors + 1):
                    costs = 0
                    for c in floors[f]:
                        costs = costs + c.model().E_Cost_IM(im)
                    new_data.append(costs)
                data.append(new_data)

            data_source = SimpleDataSource(data=data)
            by_floor_chart = LineChart(data_source, options={'title': 'Cost | IM',
                                                             'hAxis': {'logScale': False, 'title': project.im_label()},
                                                             'vAxis': {'logScale': False, 'format': 'decimal',
                                                                       'title': 'Cost ($)'},
                                                             'pointSize': 5})

        columns = ['Floor', 'Cost']
        data = [columns]
        
        xlimit = im_func.plot_max()
        ordered_levels = project.levels()
        ordered_levels.sort(key=lambda x: x.level, reverse=True)
        for l in ordered_levels:
            costs = 0
            for c in levels[l]:
                costs = costs + c.model().E_annual_cost()
            data.append([l.label, costs])

        data_source = SimpleDataSource(data=data)
        by_floor_bar_chart = BarChart(data_source, options={'title': 'Mean Annual Repair Cost By Floor',
                                                            'hAxis': {'title': 'Cost ($)'},
                                                            'vAxis': {'title': 'Floor'}})

        j_by_floor_bar_chart = ByFloorChart(data)
        print(j_by_floor_bar_chart)

        columns = ['Component Type', 'Cost']
        data = [columns]
        groups = {}
        demands = EDP.objects.filter(project=project)
        for edp in demands:
            for c in Component_Group.objects.filter(demand=edp):
                type = c.component.name
                if not groups.get(type):
                    groups[type] = 0
                groups[type] = groups[type] + c.model().E_annual_cost()

        
        for key in groups.keys():
            data.append([key, groups[key]])

        print(data)
        data_source = SimpleDataSource(data=data)
        by_comp_pie_chart = PieChart(data_source, options={'title': 'Mean Annual Repair Cost By Component Type'})
        j_by_comp_pie_chart = ByCompPieChart(data, 'Mean Annual Repair Cost By Component Type')

    print(j_by_floor_bar_chart)
    return render(request, 'slat/analysis.html', {'project': project, 
                                                  'structure': project.model(),
                                                  'chart': chart,
                                                  'jchart': jchart,
                                                  #'by_fate_chart': by_fate_chart,
                                                  #'s_ns_chart': s_ns_chart,
                                                  #'by_floor_chart': by_floor_chart,
                                                  'by_floor_bar_chart': by_floor_bar_chart,
                                                  'j_by_floor_bar_chart': j_by_floor_bar_chart,
                                                  'by_comp_pie_chart': by_comp_pie_chart,
                                                  'j_by_comp_pie_chart': j_by_comp_pie_chart})

class ComponentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        #if not self.request.user.is_authenticated():
        #    return Country.objects.none()

        qs = ComponentsTab.objects.all()

        category = self.forwarded.get('category', None)
        floor_num = self.forwarded.get('floor', None)
        
        if category:
            qs = qs.filter(ident__regex=category)

        if floor_num and int(floor_num)==0:
            acceleration = DemandsTab.objects.filter(name__icontains='Accel')[0]
            qs = qs.filter(demand=acceleration)
            
        return qs

@login_required
def ComponentDescription(request, component_key):
    component = ComponentsTab.objects.get(pk=component_key)
    result = render(request, 'slat/component-description.html', 
                    {'component': component,
                     'fragility': FragilityTab.objects.filter(component = component).order_by('state'),
                     'costs': CostTab.objects.filter(component = component).order_by('state')})
    return(result)

@login_required
def shift_level(request, project_id, level_id, shift):
    shift = int(shift)
    print("> shift_level(..., {}, {}, {})".format(project_id, level_id, shift))
    project = Project.objects.get(pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    level_to_move = Level.objects.get(pk=level_id)
    if project != level_to_move.project:
        print("HEY--WRONG PROJECT!")
    else:
        print("Project number is correct")
        
    if shift > 0:
        print("> 0: Shifting Up")
        try:
            other_level = Level.objects.get(project=project, level=level_to_move.level + 1)
            print(other_level.id)
            level_to_move.level = level_to_move.level + 1
            other_level.level = other_level.level - 1
            level_to_move.save()
            other_level.save()
        except Level.DoesNotExist:
            print("Nowhere to go")
    elif shift < 0:
        print("< 0: Shifting Down")
        try:
            other_level = Level.objects.get(project=project, level=level_to_move.level - 1)
            print(other_level.id)
            level_to_move.level = level_to_move.level - 1
            other_level.level = other_level.level + 1
            level_to_move.save()
            other_level.save()
        except Level.DoesNotExist:
            print("Nowhere to go")
    else:
        print("??????")
    return HttpResponseRedirect(reverse('slat:levels', args=(project_id)))

@login_required
def rename_level(request, project_id, level_id):
    project = Project.objects.get(pk=project_id)

    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    level = Level.objects.get(pk=level_id)
    print("> rename_level: {} {} [{}]".format(project_id, level_id, level.label))
    if request.method == 'POST':
        form = LevelLabelForm(request.POST)
        if form.is_valid():
            level.label = form.cleaned_data['label']
            level.save()
        return HttpResponseRedirect(reverse('slat:levels', args=(project_id)))
        
    else:
        form = LevelLabelForm(initial={'label': level.label})
        return render(request, 'slat/rename_label.html', {'project': project,
                                                          'level': level,
                                                          'form': form})
    
class SLATRegistrationView(RegistrationView):
    def __init__(self, *args, **kwargs):
        self.form_class = SLATRegistrationForm
        super(SLATRegistrationView, self).__init__(*args, **kwargs)
        
    def get_success_url(self, activateduser):
        return reverse('slat:index')

class SLATRegistrationForm(RegistrationForm):
    organization = CharField()
    first_name = CharField()
    last_name = CharField()
    
    def save(self, *args, **kwargs):
        user = super(SLATRegistrationForm, self).save(*args, **kwargs)
        if user:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.save()

            profile = Profile.objects.get(user=user)
            profile.organization = self.cleaned_data['organization']
            profile.save()
        return user

class ProjectAddUserForm(Form):
    userid = CharField()
    
@login_required
def project_add_user(request, project_id):
    project = Project.objects.get(pk=project_id)
    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    if request.method == 'POST':
        print("POST")
        form = ProjectAddUserForm(request.POST)
        form.is_valid()
        print(form.cleaned_data['userid'])
        try:
            user = User.objects.get(username=form.cleaned_data['userid'])
            project.AssignRole(user, ProjectPermissions.ROLE_FULL)
            return HttpResponseRedirect(reverse('slat:project', args=(project_id,)))
        except:
            print("EXCEPTION")
            form.message = "User {} not found.".format(form.cleaned_data['userid'])
            return render(request, 'slat/project_add_user.html', context={'project_id': project_id, 'project': project, 'form': form})
            
    else:
        print("GET")
        form = ProjectAddUserForm()
        return render(request, 'slat/project_add_user.html', context={'project_id': project_id, 'project': project, 'form': form})
    
class ProjectRemoveUserForm(Form):
    userid = CharField()
    
@login_required
def project_remove_user(request, project_id):
    project = Project.objects.get(pk=project_id)
    if not project.GetRole(request.user) == ProjectPermissions.ROLE_FULL:
        raise PermissionDenied

    if request.method == 'POST':
        form = ProjectRemoveUserForm(request.POST)
        form.is_valid()
        try:
            user = User.objects.get(username=form.cleaned_data['userid'])
            project.AssignRole(user, ProjectPermissions.ROLE_NONE)
            return HttpResponseRedirect(reverse('slat:project', args=(project_id,)))
        except:
            form.message = "User {} not found.".format(form.cleaned_data['userid'])
            return render(request, 'slat/project_remove_user.html', context={'project_id': project_id, 
                                                                             'project': project, 
                                                                             'form': form})
            
    else:
        print("GET")
        form = ProjectRemoveUserForm()
        form.fields['userid'].widget = Select()
        users = []
        for permissions in ProjectPermissions.objects.filter(project=project, role=ProjectPermissions.ROLE_FULL):
            user = permissions.user
            if user != request.user:
                users.append([user.username, user.username])
        form.fields['userid'].widget.choices = users
        return render(request, 'slat/project_remove_user.html', context={'project_id': project_id,
                                                                         'project': project, 
                                                                         'form': form})

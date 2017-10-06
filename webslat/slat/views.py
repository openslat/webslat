import sys
import pyslat
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory, ValidationError, HiddenInput
from django.forms.models import model_to_dict
from .nzs import *
from math import *
from graphos.sources.model import SimpleDataSource
from graphos.sources.model import ModelDataSource
from graphos.renderers.gchart import LineChart
from dal import autocomplete

from  .models import *
from .component_models import *
from slat.constants import *

def index(request):
    project_list = Project.objects.all()
    context = { 'project_list': project_list }
    return render(request, 'slat/index.html', context)

def project(request, project_id=None):
    chart = None
    if request.method == 'POST':
        if project_id:
            project = Project.objects.get(pk=project_id)
            form = ProjectForm(request.POST, Project.objects.get(pk=project_id), initial=model_to_dict(project))
            form.instance.id = project_id
            form.instance.floors = project.floors
        else:
            project = None
            form = ProjectForm(request.POST)

        if form.is_valid():
            if project:
                form.instance.floors = project.floors
            form.save()

            if not project_id:
                project = form.instance
                
                for f in range(int(project.floors) + 1):
                    EDP(project=project,
                        floor=f,
                        type=EDP.EDP_TYPE_ACCEL).save()
                    if f > 0:
                        EDP(project=project,
                            floor=f,
                            type=EDP.EDP_TYPE_DRIFT).save()
                
            if project_id and form.has_changed() and project.IM:
                project.IM._make_model()
                if project.floors:
                    for edp in EDP.objects.filter(project=project):
                        edp._make_model()
                    project._make_model()
                        
            return HttpResponseRedirect(reverse('slat:project', args=(form.instance.id,)))

    else:
        # If the project exists, use it to populate the form:
        if project_id:
            project = Project.objects.get(pk=project_id)
            form = ProjectForm(instance=project, initial=model_to_dict(project))
            form.fields['floors'].widget = HiddenInput()
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
        else:
            form = ProjectForm()
            
    return render(request, 'slat/project.html', {'form': form, 'chart': chart})


def hazard(request, project_id):
    # If the project doesn't exist, generate a 404:
    project = get_object_or_404(Project, pk=project_id)

    # Otherwise:
    #    - Does the project already have a hazard defined? If so, we'll
    #      redirect to the 'view' page for that type of hazard
    #    - If not, we'll redirect to the 'choose' page:
    hazard = project.IM

    if not hazard:
            form = HazardForm()
            return HttpResponseRedirect(reverse('slat:hazard_choose', args=(project_id)))
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
        
def hazard_choose(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    hazard = project.IM

    if request.POST:
        if request.POST.get('cancel'):
            # If the form was CANCELled, return the user to the project page (if no hazard has been defined),
            # or to the page for the current hazard (they got here because they cancelled a change to the 
            # hazard type):
            if hazard:
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
                # Shouldn't get here!
                raise ValueError("SHOULDN'T GET HERE")
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
                                                'hAxis': {'logScale': True, 'title': 'Intensity Measure (g)'},
                                                'vAxis': {'logScale': True, 
                                                          'title': 'Rate of Exceedance',
                                                          'format': 'scientific'},
                                                'pointSize': 5,
                                                'legend': {'position': 'none'}})
        return chart
    
        
def nlh(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    hazard = project.IM

    if request.method == 'POST':
        raise ValueError("SHOULDN'T GET HERE")
    else:
        if hazard and hazard.nlh:
            return render(request, 'slat/nlh.html', {'nlh':hazard.nlh, 'title': project.title_text, 
                                                     'project_id': project_id, 'chart': _plot_hazard(hazard)})
        else:
            raise ValueError("SHOULDN'T REACH THIS")
            

def nlh_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
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

def im_interp(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
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
    else:
        points = IM_Point.objects.filter(hazard=hazard).order_by('im_value')
        method = hazard.interp_method

        if True:
            if False:
                data_source = ModelDataSource(IM_Point.objects.filter(hazard = hazard).order_by('im_value'), fields=['im_value', 'rate'])
                chart = LineChart(data_source, options={'title': 'Intensity Measure Rate of Exceedance', 
                                                        'hAxis': {'logScale': True}, 'vAxis': {'logScale': True}})
                                                        
                context = {'chart': chart}
            else:
                chart = _plot_hazard(hazard)

            return render(request, 'slat/im_interp.html', {'method': method, 'points': points,
                                                           'project_id': project_id, 'chart': chart,
                                                           'title': project.title_text})
    return render(request, 'slat/im_interp.html', {'method': method, 'points': points, 
                                                   'project_id': project_id,
                                                   'title': project.title_text})

def im_interp_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
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

def im_file(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
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
        return render(request, 'slat/im_file.html', {'form': form, 
                                                     'interp_form': interp_form,
                                                     'project_id': project_id,
                                                     'title': project.title_text})
    

def im_nzs(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    hazard = project.IM

    if request.method == 'POST':
        raise ValueError("SHOULDN'T POST THIS PAGE")
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
            raise ValueError("SHOULDN'T REACH THIS")
            

def im_nzs_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
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
            
        demand = "Floor {} {}".format(edp.floor, demand_type)
                                    
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
                                                 'hAxis': {'title': 'Intensity Measure (g)'},
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
    
def edp(request, project_id):
    # If the project doesn't exist, generate a 404:
    project = get_object_or_404(Project, pk=project_id)

    # Otherwise:
    #    - Does the project already have EDPs defined? If so, we'll
    #      redirect to the 'view' page for the EDPs
    #    - If not, we'll redirect to the 'init' page:
    if project.floors :
        # EDP has been defined exists:
        demand_table = "<demand table>"
        return render(request, 'slat/edp.html', {'project': project,
                                                 'edps': EDP.objects.filter(project=project).order_by('floor', 'type'),
                                                 'demand_table': demand_table})
    else:
        return HttpResponseRedirect(reverse('slat:edp_init', args=(project_id)))
    
def edp_view(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
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
    
def edp_init(request, project_id):
    # If the project doesn't exist, generate a 404:
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        project.floors = int(request.POST.get('floors'))
        project.save()
        for f in range(int(project.floors) + 1):
            EDP(project=project,
                floor=f,
                type=EDP.EDP_TYPE_ACCEL).save()
            if f > 0:
                EDP(project=project,
                    floor=f,
                    type=EDP.EDP_TYPE_DRIFT).save()
        return HttpResponseRedirect(reverse('slat:edp', args=(project_id)))
    else:
        return render(request, 'slat/edp_init.html', {'project': project, 'form': FloorsForm()})
    
def edp_choose(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
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

def edp_power(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
    edp = get_object_or_404(EDP, pk=edp_id)
    charts = _plot_demand(edp)
    return render(request, 'slat/edp_power.html', {'project': project, 'edp': edp, 'charts': charts})

def edp_power_edit(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
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

def edp_userdef(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
    edp = get_object_or_404(EDP, pk=edp_id)
    charts = _plot_demand(edp)
    
    return render(request, 'slat/edp_userdef.html',
                  { 'project': project, 
                    'edp': edp,
                    'charts': charts,
                    'points': EDP_Point.objects.filter(demand=edp).order_by('im')})

def edp_userdef_edit(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
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

def edp_userdef_import(request, project_id, edp_id):
    project = get_object_or_404(Project, pk=project_id)
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

def cgroup(request, project_id, floor_num, cg_id=None):
     project = get_object_or_404(Project, pk=project_id)
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

def floor_cgroup(request, project_id, floor_num, cg_id=None):
     print(" > floor_cgroup()")
     print(request)
     project = get_object_or_404(Project, pk=project_id)
     if request.method == 'POST':
         print("POST")
         if request.POST.get('cancel'):
             return HttpResponseRedirect(reverse('slat:floor_cgroups', args=(project_id, floor_num)))

         if request.POST.get('delete'):
             cg = Component_Group.objects.get(pk=cg_id)
             project.model().RemoveCompGroup(cg.model())
             cg.delete()
             return HttpResponseRedirect(reverse('slat:floor_cgroups', args=(project_id, floor_num)))

         if cg_id:
             cg = Component_Group.objects.get(pk=cg_id)
             cg_form = FloorCompGroupForm(request.POST, initial=model_to_dict(cg))
         else:
             cg = Component_Group()
             cg_form = FloorCompGroupForm(request.POST)

         cg_form.is_valid()
         component = cg_form.cleaned_data['component']
         
         edp = EDP.objects.filter(project=project).filter(floor=floor_num)

         if re.search('^Accel(?i)', component.demand.name):
             edp = edp.filter(type='A')
         else:
             edp = edp.filter(type='D')

         cg.demand = edp[0]
         cg.component = component
         cg.quantity = cg_form.cleaned_data['quantity']
         cg.save()
         cg_id = cg.id
         
         return HttpResponseRedirect(reverse('slat:floor_cgroups', args=(project_id, floor_num)))
     else:
         if cg_id:
             cg = get_object_or_404(Component_Group, pk=cg_id)
             demand_form = ComponentForm(initial=model_to_dict(cg), floor_num=floor_num)
         else:
             demand_form = ComponentForm(floor_num=floor_num)

         return render(request, 'slat/floor_cgroup.html', {'project': project,
                                                           'floor_num': floor_num, 
                                                           'cg_id': cg_id,
                                                           'demand_form': demand_form})
     

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

def edp_cgroup(request, project_id, edp_id, cg_id=None):
    project = get_object_or_404(Project, pk=project_id)
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
    
def cgroups(request, project_id):
     project = get_object_or_404(Project, pk=project_id)
     return render(request, 'slat/cgroups.html', {'project': project,
                                                  'cgs': Component_Group.objects.filter(demand__project=project)})
 
def floor_cgroups(request, project_id, floor_num):
    print(" --> floor_cgroups(", project_id, ", ", floor_num, ")")
    project = get_object_or_404(Project, pk=project_id)
    edps = EDP.objects.filter(project=project).filter(floor=floor_num)
    cgs = []
    for edp in edps:
        groups = Component_Group.objects.filter(demand=edp)
        for cg in groups:
            cgs.append(cg)
            
    if request.method == 'POST':
         raise ValueError("SHOULD NOT GET HERE")
    else:
        return render(request, 'slat/floor_cgroups.html',
                      {'project': project,
                       'floor_num': floor_num,
                       'cgs': cgs})

def floors(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    print(project.floors)
    return render(request, 'slat/floors.html', {'project': project, 
                                                'floors': range(project.floors + 1)})
def demand(request, project_id, floor_num, type):
    project = get_object_or_404(Project, pk=project_id)
    if type == 'drift':
        type = 'D'
    elif type =='acceleration':
        type = 'A'
    else:
        raise ValueError("UNKNOWN DEMAND TYPE")
        
    demand = EDP.objects.filter(project=project).filter(floor=floor_num).filter(type=type)
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

    
def analysis(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    chart = None

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
        print("{:>.2}".format(100 * building.AnnualCost().mean()/building.getRebuildCost().mean()))
    
    return render(request, 'slat/analysis.html', {'project': project, 
                                                  'structure': project.model(),
                                                  'chart': chart})
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

def ComponentDescription(request, component_key):
    component = ComponentsTab.objects.get(pk=component_key)
    result = render(request, 'slat/component-description.html', 
                    {'component': component,
                     'fragility': FragilityTab.objects.filter(component = component).order_by('state'),
                     'costs': CostTab.objects.filter(component = component).order_by('state')})
    return(result)

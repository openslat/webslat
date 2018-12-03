import pyslat
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory, ValidationError, HiddenInput
from .nzs import *
from math import *
from  .models import *
from .component_models import *
from slat.constants import *

def components(request):
    components_list = ComponentsTab.objects.all()
    context = { 'components_list': components_list }
    return render(request, 'slat/components.html', context)

def component(request, component_id):
    c = ComponentsTab.objects.get(ident=component_id)
    f = FragilityTab.objects.filter(component = c)
    costs = CostTab.objects.filter(component = c)
    context = {'component': c, 'fragility': f, 'costs': costs }
    return render(request, 'slat/component.html', context)

def edit_component(request, component_id=None):
    Cost_Form_Set = modelformset_factory(CostTab, Cost_Form, extra=0)
    Fragility_Form_Set = modelformset_factory(FragilityTab, Fragility_Form, extra=0)

    if request.method == 'GET':
        if component_id:
            c = ComponentsTab.objects.get(pk=component_id)
            f = FragilityTab.objects.filter(component = c)
            costs = CostTab.objects.filter(component = c)
            cf = Component_Form(instance=c)

            cost_form_set = Cost_Form_Set(
                queryset=CostTab.objects.filter(component = c).order_by('state'))

            eprint("cost_form_set: {}".format(cost_form_set))

            for i in cost_form_set:
                for field in ['min_cost', 'max_cost', 'lower_limit', 'upper_limit', 'dispersion']:
                    i[field].field.widget.attrs['style'] = 'text-align:right'

            fragility_form_set = Fragility_Form_Set(
                queryset=FragilityTab.objects.filter(component = c).order_by('state'))

            for i in fragility_form_set:
                for field in ['median', 'beta']:
                    i[field].field.widget.attrs['style'] = 'text-align:right'

        else:
            # Generate a blank form for creating a component
            cf = Component_Form()
            cost_form_set = None
            fragility_form_set = None
    else:
        if request.POST.get('cancel'):
            eprint("CANCEL!")
            if component_id:
                return HttpResponseRedirect(
                    reverse(
                        'slat:edit_component', 
                        args=(component_id,)))
            else:
                return HttpResponseRedirect(
                    reverse('slat:edit_component'))

        # POST request; process data
        if component_id:
            print("Change component")
            c = ComponentsTab.objects.get(key=component_id)
            f = FragilityTab.objects.filter(component = c)
            costs = CostTab.objects.filter(component = c)
            cf = Component_Form(request.POST, instance=c)

            cost_form_set = Cost_Form_Set(
                request.POST,
                queryset=CostTab.objects.filter(component = c).order_by('state'))

            eprint("[check costs]")
            eprint(cost_form_set.is_valid())
            eprint("[done checking costs]")
            
            fragility_form_set = Fragility_Form_Set(
                request.POST,
                queryset=FragilityTab.objects.filter(component = c).order_by('state'))
            
            
            if not cf.is_valid() or not cost_form_set.is_valid() or not fragility_form_set.is_valid():
                eprint("INVALID: {} {} {}".format(cf.is_valid(), cost_form_set.is_valid(), fragility_form_set.is_valid()))
            else:
                try:
                    cf.save(commit=False)
                except Exception as e:
                    eprint("EXCEPTION: {}".format(e))
                    eprint("ERRORS: {}".format(cf.errors))


                if component_id:
                    cf.instance.key = component_id
                cf.save()

                if cf.has_changed():
                    eprint("FORM CHANGED")
                    eprint(cf.changed_data)
                else:
                    eprint("No changes")


                if cost_form_set.has_changed():
                    eprint("COSTS CHANGED")
                else:
                    eprint("NO COST CHANGES")

        else:
            print("Create component")
            cf = Component_Form()
            cost_form_set = None
            fragility_form_set = None

    context = { 'component_form': cf,
                'cost_form': cost_form_set,
                'fragility_form': fragility_form_set}
    return render(request, 'slat/edit_component.html', context)


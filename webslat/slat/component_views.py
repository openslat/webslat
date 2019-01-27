import pyslat
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory, ValidationError, HiddenInput
from django.forms import formset_factory, BaseFormSet
from .nzs import *
from math import *
from  .models import *
from .component_models import *
from slat.constants import *
import os

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

class CostFormSet(BaseModelFormSet):
     def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 queryset=None, *, initial=None, **kwargs):

         if not prefix:
             prefix = "cost_form"

         self.queryset = queryset
         self.initial_extra = initial
         super(CostFormSet, self).__init__(**{'data': data, 'files': files, 
                                              'auto_id': auto_id, 
                                              'prefix': prefix,
                                              'queryset': queryset,
                                              'initial': initial, **kwargs})

     def clean(self):
         """Make sure the forms are consistent"""
         eprint("> CostFormSet::clean()")
         if any(self.errors):
             # Don't bother validating the formset unless each form is valid on its own
             eprint("< CostFormSet::clean() failing")
             return

         if len(self.forms) == 0:
             raise ValidationError('Must have at least one cost entry.')
         
         for i in range(0, len(self.forms) -1):
             eprint(i)
         eprint("< CostFormSet::clean() success")

class FragilityFormSet(BaseModelFormSet):
     def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 queryset=None, *, initial=None, **kwargs):

         if not prefix:
             prefix = "fragility_form"

         self.queryset = queryset
         self.initial_extra = initial
         super(FragilityFormSet, self).__init__(**{'data': data, 'files': files, 
                                                   'auto_id': auto_id, 
                                                   'prefix': prefix,
                                                   'queryset': queryset,
                                                   'initial': initial, **kwargs})
     def clean(self):
         """Checks that no two articles have the same title."""
         eprint("> FragilityFormSet::clean()")

         if len(self.forms) == 0:
             raise ValidationError('Must have at least one fragility entry.')
         
         if any(self.errors):
             # Don't bother validating the formset unless each form is valid on its own
             eprint("< FragilityFormSet::clean() failing")
             return
                    
         eprint("< FragilityFormSet::clean() success")
         
def edit_component(request, component_id=None):
    eprint("> edit_component({})".format(component_id))
    eprint(request)
    Cost_Form_Set = modelformset_factory(CostTab, Cost_Form, 
                                         formset=CostFormSet, extra=0)
    Fragility_Form_Set = modelformset_factory(FragilityTab, Fragility_Form, 
                                              formset=FragilityFormSet, extra=0)

    if request.method == 'GET':
        if component_id:
            eprint("GET {}".format(component_id))
            c = ComponentsTab.objects.get(pk=component_id)
            f = FragilityTab.objects.filter(component = c)
            costs = CostTab.objects.filter(component = c)
            cf = Component_Form(instance=c)

            cost_form_set = Cost_Form_Set(
                queryset=CostTab.objects.filter(component = c).order_by('state'))

            eprint(cost_form_set.forms[0])

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
            cost_form_set = Cost_Form_Set(queryset=CostTab.objects.none())
            fragility_form_set = Fragility_Form_Set(queryset=FragilityTab.objects.none())
            #eprint("cost_form_set: {}".format(dir(cost_form_set)))
            #eprint("cost_form_set.forms: {}".format(cost_form_set.forms))
            #for form in cost_form_set.forms:
            #    eprint("State: {}".format(form.instance.state))
            #eprint("-----------")
    else:
        eprint()
        eprint("POST DATA")
        keys = list(request.POST.keys())
        keys.sort()
        for key in keys:
            eprint("    {}: {}".format(key, request.POST[key]))
        keys = None
        eprint()
        
        if request.POST.get('back'):
            return HttpResponseRedirect(reverse('slat:components'))
        
        if request.POST.get('cancel'):
            if component_id:
                return HttpResponseRedirect(
                    reverse(
                        'slat:edit_component', 
                        args=(component_id,)))
            else:
                return HttpResponseRedirect(
                    reverse('slat:components'))

        # POST request; process data
        if component_id:
            eprint("POST")
            c = ComponentsTab.objects.get(key=component_id)
            f = FragilityTab.objects.filter(component = c)
            costs = CostTab.objects.filter(component = c)
            cf = Component_Form(request.POST, instance=c)

            cost_form_set = Cost_Form_Set(
                request.POST,
                queryset=CostTab.objects.filter(component = c).order_by('state'))
            #for cost_form in cost_form_set:
            #    cost_form.instance.component = c

            fragility_form_set = Fragility_Form_Set(
                request.POST,
                queryset=FragilityTab.objects.filter(component = c).order_by('state'))

            #for fragility_form in fragility_form_set:
            #    fragility_form.instance.component = c
 
            eprint("# fragility_forms: {}".format(len(fragility_form_set.forms)))
            eprint("fragility_form_set.is_valid(): {}".format(fragility_form_set.is_valid())) 
        
            if not cf.is_valid() or not cost_form_set.is_valid() or not fragility_form_set.is_valid():
                eprint("IS VALID: {} {} {}".format(cf.is_valid(), cost_form_set.is_valid(), fragility_form_set.is_valid()))
                eprint("INVALID")

                context = { 'component_form': cf,
                            'cost_form': cost_form_set,
                            'fragility_form': fragility_form_set}
                return render(request, 'slat/edit_component.html', context)
                
            else:
                for cost_form in cost_form_set:
                    eprint("state: {}".format(cost_form.cleaned_data['state']))
                    eprint("component: {}".format(cost_form.cleaned_data['component']))

                if component_id:
                    cf.instance.key = component_id

                if cf.has_changed():
                    eprint("FORM CHANGED")
                    if 'ident' in cf.changed_data:
                        eprint("ident changed")
                        old_ident = ComponentsTab.objects.get(key=cf.instance.key).ident
                        new_ident = cf.instance.ident
                        # If there is an image directory, rename it
                        try:
                            eprint("CWD: {}".format(os.getcwd()))
                            old_path = os.path.join("static/slat/images", old_ident) 
                            new_path = os.path.join("static/slat/images", new_ident)
                            if os.path.exists(old_path):
                                eprint("Renaming {} --> {}".format(old_path, new_path))
                                os.rename(old_path, new_path)
                                eprint("Renamed successfully")
                                
                                old_path = os.path.join("slat/static/slat/images", old_ident) 
                                new_path = os.path.join("slat/static/slat/images", new_ident)
                                eprint("Renaming {} --> {}".format(old_path, new_path))
                                os.rename(old_path, new_path)
                                eprint("Renamed successfully")
                            else:
                                eprint("No image directory; nothing to rename")
                        except Exception as e:
                            eprint("Caught exception {}".format(e))
                            
                else:
                    eprint("No changes")

                # Validate changes to costs and fragility before saving anything
                eprint("COST FORMS VALID: {}".format(cost_form_set.is_valid()))
                cf.save()

                eprint("cf: {}".format(cf))
                eprint("cf.instance: {}".format(cf.instance))

                for cost_form in cost_form_set:
                    cost_form.instance.component = cf.instance
                    if cost_form.has_changed():
                        cost_form.save()

                if cost_form_set.has_changed():
                    eprint("COSTS CHANGED")
                else:
                    eprint("NO COST CHANGES")

                for index, fragility_form in enumerate(fragility_form_set):
                    if fragility_form.has_changed():
                        eprint("fragility form changed: {}".format(fragility_form.changed_data))
                        eprint("State: {}".format(fragility_form.cleaned_data['state']))
                        eprint("Component: {}".format(fragility_form.cleaned_data['component']))
                        eprint("Instance: {}".format(fragility_form.instance))
                        
                        if 'image' in fragility_form.changed_data:
                            old_image = FragilityTab.objects.get(rowid=fragility_form.instance.rowid).image
                            new_image = fragility_form.instance.image

                            data = request.FILES.get("image-{}".format(index + 1))
                            data = data and data.read()
                            ident = cf.instance.ident
                            directory = os.path.join("slat/static/slat/images", ident)
                            if not os.path.exists(directory):
                                os.mkdirs(directory)
                                # Should we delete the old image?
                                if data:
                                    file.open(os.path.join(directory, new_image), "w").write(data)
                            
                            directory = os.path.join("static/slat/images", ident)
                            if not os.path.exists(directory):
                                os.mkdirs(directory)
                                # Should we delete the old image?
                                if data:
                                    file.open(os.path.join(directory, new_image), "w").write(data)
                        fragility_form.instance.component = cf.instance
                        fragility_form.save()
                        
                if fragility_form_set.has_changed():
                    eprint("FRAGILITY CHANGED")
                else:
                    eprint("NO FRAGILITY CHANGES")

        else:
            cf = Component_Form()
            # Validate the inputs:
            cf = Component_Form(request.POST)
            cost_form_set = Cost_Form_Set(request.POST)
            for cost_form in cost_form_set:
                if cost_form.is_valid():
                    eprint(cost_form.cleaned_data)
                else:
                    eprint("(cost_form is invalid)")

            fragility_form_set = Fragility_Form_Set(request.POST)
            for fragility_form in fragility_form_set:
                if fragility_form.is_valid():
                    eprint(fragility_form.cleaned_data)
                else:
                    eprint("(fragility_form is invalid)")

            if not cf.is_valid() or not cost_form_set.is_valid() or not fragility_form_set.is_valid():
                eprint("IS VALID: {} {} {}".format(cf.is_valid(), cost_form_set.is_valid(), fragility_form_set.is_valid()))
                context = { 'component_form': cf,
                            'cost_form': cost_form_set,
                            'fragility_form': fragility_form_set}
                return render(request, 'slat/edit_component.html', context)
            else:
                # All valid--save:
                cf.save()
                instance = ComponentsTab.objects.get(ident=cf.instance.ident)
                
                for cost_form in cost_form_set:
                    cost_form.instance.component = instance
                    cost_form.instance.save()

                for fragility_form in fragility_form_set:
                    fragility_form.instance.component = instance
                    fragility_form.save()
                
        if component_id:
            return HttpResponseRedirect(
                reverse(
                    'slat:edit_component', 
                    args=(component_id,)))
        else:
            return HttpResponseRedirect(
                reverse('slat:edit_component'))
    
    n = len(cost_form_set.forms)
    # cost_form_set.forms[n - 1]['state'].initial = n
    # cost_form_set.forms[n - 1]['min_cost'].initial = 0
    # cost_form_set.forms[n - 1]['max_cost'].initial = 0
    # cost_form_set.forms[n - 1]['lower_limit'].initial = 0
    # cost_form_set.forms[n - 1]['upper_limit'].initial = 0
    # cost_form_set.forms[n - 1]['dispersion'].initial = 0
    # fragility_form_set.forms[n - 1]['state'].initial = n
    # fragility_form_set.forms[n - 1]['description'].initial = ""
    # fragility_form_set.forms[n - 1]['repairs'].initial = ""
    # fragility_form_set.forms[n - 1]['median'].initial = 0
    # fragility_form_set.forms[n - 1]['beta'].initial = 0
    # fragility_form_set.forms[n - 1]['image'].initial = None

    if component_id:
        c = ComponentsTab.objects.get(pk=component_id)
        cost_form_set.forms[n - 1]['component'].initial = c
        fragility_form_set.forms[n - 1]['component'].initial = c
    

    context = { 'component_form': cf,
                'cost_form': cost_form_set,
                'fragility_form': fragility_form_set}
    return render(request, 'slat/edit_component.html', context)


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


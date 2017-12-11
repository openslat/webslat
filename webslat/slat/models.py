import pyslat
import sys
import time
from scipy.optimize import fsolve, newton
from django.db import models
from django.forms import  ModelForm, BaseModelFormSet, Select, NumberInput, Textarea, TextInput, FloatField, FileInput, FileField, Form, ModelChoiceField, IntegerField, HiddenInput, CharField
from django.forms import Form, ChoiceField, Select
from slat.constants import *
from .nzs import *
from .component_models import *
from dal import autocomplete
from django.urls import get_script_prefix
from django.utils.safestring import mark_safe
from dal import forward

# Create your models here.
class Project(models.Model):
    FREQUENCY_CHOICES = (
        (1./20, u'20'),
        (1./25, u'25'),
        (1./50, u'50'),
        (1./100, u'100'),
        (1./250, u'250'),
        (1./500, u'500'),
        (1./1000, u'1000'),
        (1./2500, u'2000'),
        (1./2500, u'2500'),
    )

    title_text = models.CharField(max_length=50)
    description_text = models.CharField(max_length=200, blank=True)
    IM = models.ForeignKey('IM', null=True, blank=True)
    rarity = models.FloatField(null=False, choices=FREQUENCY_CHOICES)
    mean_im_collapse = models.FloatField(null=True, blank=True)
    sd_ln_im_collapse = models.FloatField(null=True, blank=True)
    mean_cost_collapse = models.FloatField(null=True, blank=True)
    sd_ln_cost_collapse = models.FloatField(null=True, blank=True)
    mean_im_demolition = models.FloatField(null=True, blank=True)
    sd_ln_im_demolition = models.FloatField(null=True, blank=True)
    mean_cost_demolition = models.FloatField(null=True, blank=True)
    sd_ln_cost_demolition = models.FloatField(null=True, blank=True)

    def _make_model(self):
        structure = pyslat.structure(self.id)
        if self.mean_cost_collapse and self.sd_ln_cost_collapse:
            structure.setRebuildCost(
                pyslat.MakeLogNormalDist(
                    self.mean_cost_collapse, pyslat.LOGNORMAL_MU_TYPE.MEAN_X,
                    self.sd_ln_cost_collapse, pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X))

        if self.mean_cost_demolition and self.sd_ln_cost_demolition:
            structure.setDemolitionCost(
                pyslat.MakeLogNormalDist(
                    self.mean_cost_demolition, pyslat.LOGNORMAL_MU_TYPE.MEAN_X,
                    self.sd_ln_cost_demolition, pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X))
            
        for cg in Component_Group.objects.filter(demand__project = self):
            structure.AddCompGroup(cg.model())

    def model(self):
        if not pyslat.structure.lookup(self.id):
            self._make_model()
        return pyslat.structure.lookup(self.id)

    def levels(self):
        return list(Level.objects.filter(project=self).order_by('-level'))

    def num_levels(self):
        return length(self.levels())
            
    def __str__(self):
        if self.IM:
            im = self.IM.id
        else:
            im = "<no IM>"

        return "{}. {}: {}; {} {} {} ".format(self.id, self.title_text, 
                                              self.description_text,
                                              im,
                                              self.num_levels(),
                                              self.rarity)

    def im_label(self):
        return self.IM.label()

    def floor_label(self,floor):
        level = Level.objects.get(project=self, level=floor)
        return level.label
    
class Level(models.Model):
    project = models.ForeignKey(Project, blank=False, null=False)
    level = models.IntegerField(blank=False, null=False)
    label = models.CharField(max_length=50, blank=False, null=False)

class IM_Types(models.Model):
    name_text = models.CharField(max_length=25)

    def __str__(self):
        return self.name_text

class NonLinearHyperbolic(models.Model):
    v_assy_float = models.FloatField(default=1221)
    im_asy_float = models.FloatField(default=29.8)
    alpha_float = models.FloatField(default=62.2)

    def __str__(self):
        return "NonLinearHyperbolic: {} {} {}".format(self.v_assy_float,
                                                      self.im_asy_float,
                                                      self.alpha_float)

class Input_File_Formats(models.Model):
    format_text = models.CharField(max_length=20)

    def __str__(self):
        return self.format_text


class Interpolation_Method(models.Model):
    method_text = models.CharField(max_length=20)

    def __str__(self):
        return self.method_text

class IM_Point(models.Model):
    hazard = models.ForeignKey('IM', null=False)
    im_value = models.FloatField()
    rate = models.FloatField()

class Location(models.Model):
    location = models.CharField(max_length=128)
    z = models.FloatField()
    min_distance = models.FloatField(null = True)
    max_disstance = models.FloatField(null = True)

    def __str__(self):
        return(self.location)
    
class NZ_Standard_Curve(models.Model):
    SOIL_CLASS_A = 'A'
    SOIL_CLASS_B = 'B'
    SOIL_CLASS_C = 'C'
    SOIL_CLASS_D = 'D'
    SOIL_CLASS_E = 'E'
    SOIL_CLASS_CHOICES = (
        (SOIL_CLASS_A, 'A'),
        (SOIL_CLASS_B, 'B'),
        (SOIL_CLASS_C, 'C'),
        (SOIL_CLASS_D, 'D'),
        (SOIL_CLASS_E, 'E')
    )
    location = models.ForeignKey('Location', null=False)
    soil_class = models.CharField(max_length=1,
                                  choices=SOIL_CLASS_CHOICES,
                                  default=SOIL_CLASS_A)
    period = models.FloatField(default=1.5)

class IM(models.Model):
    flavour = models.ForeignKey(IM_Types, blank=False, null=False, default=IM_TYPE_INTERP)
    nlh = models.ForeignKey(NonLinearHyperbolic, null=True, blank=True)
    interp_method = models.ForeignKey(Interpolation_Method, null=True, blank=True)
    nzs = models.ForeignKey(NZ_Standard_Curve, null=True, blank=True)

    def label(self):
        return "Spectral Acceleration (g)"
    
    def _make_model(self):
        try:
            project = Project.objects.get(IM=self)
        except:
            # Hazard hasn't been fully specified yet; don't plot
            return None

        if self.flavour.id == IM_TYPE_NLH:
            nlh = pyslat.detfn('<nlh>', 'hyperbolic', [self.nlh.alpha_float,
                                                    self.nlh.im_asy_float,
                                                    self.nlh.v_assy_float])
            im_func = pyslat.im(self.id, nlh)
            f = lambda x: im_func.getlambda(x[0]) - project.rarity
            xlimit = fsolve(f, 0.01)[0]
            im_func.set_plot_max(xlimit)
        elif self.flavour.id == IM_TYPE_INTERP:
            #
            data = IM_Point.objects.filter(hazard = self).order_by('im_value')
            x = []
            y = []
            for d in data:
                x.append(d.im_value)
                y.append(d.rate)
            if self.interp_method.id == INTERP_LOGLOG:
                method = 'loglog'
            elif self.interp_method.id == INTERP_LINEAR:
                method = 'linear'
            else:
                raise ValueError("ILLEGAL INTERPOLATION METHOD")
            
            im_func = pyslat.im(self.id, pyslat.detfn('<interpolated>', method, [x.copy(), y.copy()]))
            if y[-1] > project.rarity:
                im_func.set_plot_max(x[-1])
            else:
                f = lambda x: im_func.getlambda(x[0]) - project.rarity
                xlimit = fsolve(f, x[-2])[0]
                im_func.set_plot_max(xlimit)
        elif self.flavour.id == IM_TYPE_NZS:
            x = []
            y = []
            for r in R_defaults:
                y.append(1/r)
                x.append(C(self.nzs.soil_class,
                           self.nzs.period,
                           r,
                           self.nzs.location.z,
                           self.nzs.location.min_distance))
            im_func = pyslat.im(self.id, pyslat.detfn('<nzs>', 'loglog', [x.copy(), y.copy()]))
            if y[-1] > project.rarity:
                im_func.set_plot_max(x[-1])
            else:
                f = lambda x: im_func.getlambda(x[0]) - project.rarity
                xlimit = fsolve(f, x[-2])[0]
                im_func.set_plot_max(xlimit)

        if project.mean_im_collapse and project.sd_ln_im_collapse:
            im_func.SetCollapse(
                pyslat.MakeLogNormalDist(
                    project.mean_im_collapse, pyslat.LOGNORMAL_MU_TYPE.MEAN_X,
                    project.sd_ln_im_collapse, pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X))

        if project.mean_im_demolition and project.sd_ln_im_demolition:
            im_func.SetDemolition(
                pyslat.MakeLogNormalDist(
                    project.mean_im_demolition, pyslat.LOGNORMAL_MU_TYPE.MEAN_X,
                    project.sd_ln_im_demolition, pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X))

    def model(self):
        if not pyslat.im.lookup(self.id):
            self._make_model()
        return pyslat.im.lookup(self.id)
            
    def __str__(self):
        return "IM: {} {} {} [{}]".format(self.flavour, self.nlh, self.interp_method, self.id)

class EDP_Flavours(models.Model):
    name_text = models.CharField(max_length=25)

    def __str__(self):
        return self.name_text

class EDP_PowerCurve(models.Model):
    median_x_a = models.FloatField(default=0.1)
    median_x_b = models.FloatField(default=1.5)
    sd_ln_x_a = models.FloatField(default=0.5)
    sd_ln_x_b = models.FloatField(default=0)

class EDP(models.Model):
    project = models.ForeignKey(Project, blank=False, null=False)
    level = models.ForeignKey(Level, blank=False, null=False)
    EDP_TYPE_DRIFT = 'D'
    EDP_TYPE_ACCEL = 'A'
    EDP_TYPE_CHOICES = (
        (EDP_TYPE_DRIFT, 'Inter-story Drift'),
        (EDP_TYPE_ACCEL, 'Acceleration'))
    type = models.CharField(max_length=1, 
                            choices=EDP_TYPE_CHOICES);
    flavour = models.ForeignKey(EDP_Flavours, blank=False, null=True)
    powercurve = models.ForeignKey(EDP_PowerCurve, null=True, blank=False)
    interpolation_method = models.ForeignKey(Interpolation_Method, null=True, blank=False)

    def __str__(self):
        return "{} {}".format(self.level.label,
                              dict(EDP.EDP_TYPE_CHOICES)[self.type])

    def _make_model(self):
        if not self.flavour:
            return None
        elif self.flavour.id == EDP_FLAVOUR_POWERCURVE:
            mu = pyslat.detfn('<powercurve-mu>', 'power law', [self.powercurve.median_x_a,
                                                               self.powercurve.median_x_b])
            sigma = pyslat.detfn('<powercurve-sigma>', 'power law', [self.powercurve.sd_ln_x_a,
                                                                     self.powercurve.sd_ln_x_b])
            prob_func = pyslat.probfn('<probfn>', 'lognormal',
                                      [pyslat.LOGNORMAL_MU_TYPE.MEDIAN_X, mu],
                                      [pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X, sigma]) 
            edp_func = pyslat.edp(self.id, self.project.IM.model(), prob_func)

            mean = edp_func.Mean(self.project.IM.model().plot_max())
            
            sigma =  edp_func.SD(self.project.IM.model().plot_max())
            f = lambda x: edp_func.getlambda(x[0]) - self.project.rarity
            xlimit = fsolve(f, edp_func.Mean(self.project.IM.model().plot_max())/2)[0]
            edp_func.set_plot_max(xlimit)
            
        elif self.flavour.id == EDP_FLAVOUR_USERDEF:
            #
            data = EDP_Point.objects.filter(demand = self).order_by('im')
            x = []
            mu = []
            sigma = []
            for d in data:
                x.append(d.im)
                mu.append(d.median_x)
                sigma.append(d.sd_ln_x)

            if self.interpolation_method.id == INTERP_LOGLOG:
                method = 'loglog'
            elif self.interpolation_method.id == INTERP_LINEAR:
                method = 'linear'
            else:
                raise ValueError("ILLEGAL INTERPOLATION METHOD")
            
            mu = pyslat.detfn('<interpolated-mu>', method, [x.copy(), mu.copy()])
            sigma = pyslat.detfn('<interpolated-sigma>', method, [x.copy(), sigma.copy()])

            prob_func = pyslat.probfn('<probfn>', 'lognormal',
                                      [pyslat.LOGNORMAL_MU_TYPE.MEDIAN_X, mu],
                                      [pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X, sigma]) 
            edp_func = pyslat.edp(self.id, self.project.IM.model(), prob_func)

            mean = edp_func.Mean(self.project.IM.model().plot_max())
            sigma =  edp_func.SD(self.project.IM.model().plot_max())

            epsilon = 1E-2
            counter = 0
            low_x = 0
            low_y = edp_func.getlambda(low_x)


            high_x = edp_func.Median(self.project.IM.model().plot_max())
            high_y = edp_func.getlambda(high_x)
            old_high_y = None
            while high_y > self.project.rarity:
                high_x = high_x * 2
                old_high_y = high_y
                high_y = edp_func.getlambda(high_x)

                rate = (edp_func.getlambda(high_x) - edp_func.getlambda(high_x * (1.0 + epsilon)))/(epsilon * high_x)
                if rate < 1E-6:
                    break

            mid_x = high_x/2
            mid_y = edp_func.getlambda(mid_x)

            while counter < 100:
                counter = counter + 1
                xlimit = mid_x

                error = self.project.rarity - mid_y
                if abs(error) < self.project.rarity/10:
                    xlimit = mid_x
                    break
                elif error > 0:
                    high_x = mid_x
                    high_y = mid_y
                else:
                    low_x = mid_x
                    low_y = mid_y

                mid_x = (low_x + high_x)/2
                mid_y = edp_func.getlambda(mid_x)
                    
            edp_func.set_plot_max(xlimit)

    def model(self):
        if not pyslat.edp.lookup(self.id):
            self._make_model()
        return pyslat.edp.lookup(self.id)


class EDP_Point(models.Model):
    demand = models.ForeignKey('EDP', null=False)
    im = models.FloatField()
    median_x = models.FloatField()
    sd_ln_x = models.FloatField()

    def __str__(self):
        return("an EDP_Point: [{}]".format(self.id))

class Component_Group(models.Model):
    demand = models.ForeignKey('EDP', null=False)
    component = models.ForeignKey('ComponentsTab', null=False)
    quantity = models.IntegerField(blank=False, null=False)

    def _make_model(self):
        frags = []
        for f in FragilityTab.objects.filter(component = self.component).order_by('state'):
            frags.append([f.median, f.beta])
        fragility = pyslat.fragfn_user(self.id, {'mu': pyslat.LOGNORMAL_MU_TYPE.MEDIAN_X,
                                                 'sd': pyslat.LOGNORMAL_SIGMA_TYPE.SD_LN_X},
                                       frags)

        costs = []
        for c in CostTab.objects.filter(component = self.component).order_by('state'):
            costs.append(pyslat.MakeBiLevelLoss(c.lower_limit, c.upper_limit,
                                                c.max_cost, c.min_cost,
                                                c.dispersion))
        cost = pyslat.bilevellossfn(self.id, costs)
        pyslat.compgroup(self.id, self.demand.model(), fragility, cost, None, self.quantity)

    def model(self):
        if not pyslat.compgroup.lookup(self.id):
            self._make_model()
        return pyslat.compgroup.lookup(self.id)
    

    def __str__(self):
        result = str(self.demand) + " "
        if self.component:
            result = result + str(self.component)
        else:
            result = result + "NO COMPONENT"
        result = result + " " + str(self.quantity)
        return result

    
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'description_text': Textarea(attrs={'cols': 50, 'rows': 4, 'title': "Enter the description"}),
            'IM': HiddenInput,
            'title_text': TextInput(attrs={'title': 'Enter the title text here.'}),
            'rarity': Select(attrs={'title': "The rate-of-exceedence of the rarest event we are interested in displaying."}),
            'floors': NumberInput(attrs={'title': "The number of floors in the structure."}),
            'mean_im_collapse': NumberInput(attrs={'title': 'The mean IM value at which collapse occurs.'}),
            'sd_ln_im_collapse': NumberInput(attrs={'title': 'The standard deviation of log(IM) at which collapse occurs.'}),
            'mean_cost_collapse': NumberInput(attrs={'title': 'The mean cost of collapse.'}),
            'sd_ln_cost_collapse': NumberInput(attrs={'title': 'The standard deviation of log(cost) of collapse.'}),
            'mean_im_demolition': NumberInput(attrs={'title': 'The mean IM value at which demolition occurs.'}),
            'sd_ln_im_demolition': NumberInput(attrs={'title': 'The standard deviation of log(IM) at which demolition occurs.'}),
            'mean_cost_demolition': NumberInput(attrs={'title': 'The mean cost of demolition.'}),
            'sd_ln_cost_demolition': NumberInput(attrs={'title': 'The standard deviation of log(cost) of demolition.'}),
            }
        
class HazardForm(ModelForm):
    def __init__(self, instance=None, initial=None):
        super(HazardForm, self).__init__(instance=instance, initial=initial)
        self.fields['flavour'].label='Hazard Definition Type'
        self.fields['flavour'].widget.attrs['title'] ='Choose how to specify the hazard curve.'
        
    class Meta:
        model = IM
        fields = '__all__'
        widgets = {
            'nlh': HiddenInput,
            'interp_method': HiddenInput,
            'nzs': HiddenInput
            }

class NLHForm(ModelForm):
    def __init__(self, request=None, instance=None):
        super(NLHForm, self).__init__(request, instance=instance)
        self.fields['v_assy_float'].widget.attrs['class'] = 'normal'
        self.fields['im_asy_float'].widget.attrs['class'] = 'normal'
        self.fields['alpha_float'].widget.attrs['class'] = 'normal'
        self.fields['v_assy_float'].widget.attrs['title'] = "v_assy"
        self.fields['im_asy_float'].widget.attrs['title'] = 'im_asy'
        self.fields['alpha_float'].widget.attrs['title'] = 'alpha'

    class Meta:
        model = NonLinearHyperbolic
        fields = '__all__'

class Interpolation_Method_Form(Form):
    def __init__(self, request=None, initial=None):
        super(Interpolation_Method_Form, self).__init__(request, initial=initial)
        self.fields['method'].widget.attrs['class'] = 'normal'
        self.fields['method'].widget.attrs['title'] = 'Choose the interpolation method.'

    def choices():
        objects = []
        for method in Interpolation_Method.objects.all():
            objects.append([method.id, method.method_text])
        return objects

    method = ChoiceField(choices=choices, label='Interpolation Method')
    
class EDPForm(ModelForm):
    class Meta:
        model = EDP
        fields = ['flavour']

class EDP_PowerCurve_Form(ModelForm):
    class Meta:
        model = EDP_PowerCurve
        fields = '__all__'
        
class Input_File_Form(Form):
    def __init__(self, post=None, files=None):
        super(Input_File_Form, self).__init__(post, files)
        self.fields['path'].widget.attrs['class'] = 'normal'
        self.fields['path'].widget.attrs['title'] = 'Choose the data file to read.'
        self.fields['flavour'].widget.attrs['class'] = 'normal'
        self.fields['flavour'].widget.attrs['title'] = 'Select the file format.'
        self.fields['flavour'].label = 'File Format'

    path = FileField()
    flavour = ModelChoiceField(queryset=Input_File_Formats.objects, empty_label=None)

class NZSForm(ModelForm):
    class Meta:
        model = NZ_Standard_Curve
        fields = '__all__'

class FloorsForm(Form):
    floors = IntegerField(initial=4)

class CompGroupForm(ModelForm):
    class Meta:
        model = Component_Group
        fields = '__all__'

class EDPCompGroupForm(ModelForm):
    class Meta:
        model = Component_Group
        fields = '__all__'
        widgets = {
            'demand': HiddenInput
        }

class FloorCompGroupForm(Form):
    component = ModelChoiceField(queryset=ComponentsTab.objects)
    quantity = IntegerField(initial=1)
        
def ListOfComponentCategories():
    demands = [[r"", "All"], ["^[0-9]", "SLAT"], ["^[A-Z]", "PACT"]]
    for d in PACT_CatsTab.objects.all():
        #if len(ComponentsTab.objects.filter(ident__regex=d.ident)) > 0:
        demands.append((d.ident, mark_safe(len(d.ident) * "&nbsp;" + str(d))))
    return demands
    

class ComponentForm(Form):
    def __init__(self, initial=None, level=None):
        super(ComponentForm, self).__init__(initial)
        if initial:
            self.fields['component'].initial = initial['component']
        self.fields['component'].widget.forward.append(forward.Const(level, 'level'))
        self.fields['quantity'].widget.attrs['class'] = 'normal'
        self.fields['category'].widget.attrs['class'] = 'normal'
        self.fields['component'].widget.attrs['class'] = 'normal'
        self.fields['quantity'].widget.attrs['title'] = 'How many of this component are in the group?'
        self.fields['category'].widget.attrs['title'] = 'Narrow the component search by category.'
        self.fields['component'].widget.attrs['title'] = 'Choose the type of component.'
        
    quantity = IntegerField()
    category = ChoiceField(ListOfComponentCategories, required=False)
    component = ModelChoiceField(
        queryset=ComponentsTab.objects.all(),
        widget=autocomplete.Select2(url='/slat/component-autocomplete/',
                                    forward=['category']))


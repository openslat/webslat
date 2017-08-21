import pyslat
from scipy.optimize import fsolve, newton
from django.db import models
from django.forms import  ModelForm, BaseModelFormSet, Textarea, FloatField, FileField, Form, ModelChoiceField, IntegerField, HiddenInput
from django.forms import Form, ChoiceField
from slat.constants import *
from .nzs import *
from .component_models import *

# Create your models here.
class Project(models.Model):
    title_text = models.CharField(max_length=50)
    description_text = models.CharField(max_length=200, blank=True)
    IM = models.ForeignKey('IM', null=True, blank=True)
    floors = models.IntegerField(null=True, blank=True)
    rarity = models.FloatField(null=False, default=1E-4)
    

    def __str__(self):
        if self.IM:
            im = self.IM.id
        else:
            im = "<no IM>"

        if self.floors:
            floors = self.floors
        else:
            floors = "<no floors>"

        return "{}. {}: {}; {} {} {} ".format(self.id, self.title_text, 
                                              self.description_text,
                                              im,
                                              floors,
                                              self.rarity)
    
    
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

    def model(self):
        if not pyslat.im.lookup(self.id):
            self._make_model()
        return pyslat.im.lookup(self.id)
            
    def __str__(self):
        return "I M: {} {} {} [{}]".format(self.flavour, self.nlh, self.interp_method, self.id)

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
    floor = models.IntegerField()
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
        if self.floor == 0:
            floor = "Ground Floor"
        else:
            floor = "Floor #" + str(self.floor)
        for c in self.EDP_TYPE_CHOICES:
            if c[0] == self.type:
                return floor + ' ' + c[1]
        return floor + "????"

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

            if False:
                #f = lambda x: edp_func.getlambda(max(x[0], 0)) - self.project.rarity
                #xlimit = fsolve(f, x[1])[0]
                f = lambda x: (edp_func.getlambda(x) - self.project.rarity)
                xlimit = newton(f, x[1], tol=self.project.rarity/2)

            else:
                epsilon = 1E-2
                counter = 0
                low_x = 0
                low_y = edp_func.getlambda(low_x)


                high_x = edp_func.Median(self.project.IM.model().plot_max())
                high_y = edp_func.getlambda(high_x)
                while high_y > self.project.rarity:
                    high_x = high_x * 2
                    high_y = edp_func.getlambda(high_x)
                
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

    def __str__(self):
        result = str(self.demand) + " "
        #if self.component:
        #    result = result + str(self.component)
        #else:
        #    result = result + "NO COMPONENT"
        result = result + " " + str(self.quantity)
        return result

    
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'description_text': Textarea(attrs={'cols': 50, 'rows': 4}),
            'IM': HiddenInput,
            'floors': HiddenInput
            }
        
class HazardForm(ModelForm):
    class Meta:
        model = IM
        fields = '__all__'
        widgets = {
            'nlh': HiddenInput,
            'interp_method': HiddenInput,
            'nzs': HiddenInput
            }

class NLHForm(ModelForm):
    class Meta:
        model = NonLinearHyperbolic
        fields = '__all__'

class Interpolation_Method_Form(Form):
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

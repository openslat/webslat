# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from django.forms import ValidationError, formset_factory
from django.forms.utils import ErrorList
import sys
import numpy as np

from django.db import models
from django.forms import ModelForm, TextInput, NumberInput, HiddenInput

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class ComponentsTab(models.Model):
    key = models.IntegerField(blank=True, null=False, primary_key=True)
    ident = models.TextField(unique=True)  # This field type is a guess.
    name = models.TextField(blank=True, null=True)  # This field type is a guess.
    system = models.TextField(blank=True, null=True)  # This field type is a guess.
    units = models.ForeignKey('UnitsTab', models.DO_NOTHING, db_column='units', blank=True, null=True)
    demand = models.ForeignKey('DemandsTab', models.DO_NOTHING, db_column='demand', blank=True, null=True)
    structural = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'components_tab'

    def __str__(self):
        if self.ident:
            return self.ident + ": " + self.name
        else:
            return "<new ComponentsTab entry>"

class CostTab(models.Model):
    rowid = models.IntegerField(blank=True, null=False, primary_key=True)
    component = models.ForeignKey(ComponentsTab, models.DO_NOTHING, db_column='component')
    state = models.IntegerField(blank=True, null=True)
    min_cost = models.FloatField(blank=True, null=True)
    max_cost = models.FloatField(blank=True, null=True)
    dispersion = models.FloatField(blank=True, null=True)
    lower_limit = models.IntegerField(blank=True, null=True)
    upper_limit = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cost_tab'

    def __str__(self):
        try:
            result =  "CostTab: {:4} {:4} {:10} {:4} {:5.3f} {:4} {:5.3f} {:5.3f}".format(
                self.rowid or "<none>",
                self.state or "<none>",
                self.component.ident or "<none>", 
                self.lower_limit or np.nan, 
                self.max_cost or np.nan,
                self.upper_limit or np.nan,
                self.min_cost or np.nan,
                self.dispersion or np.nan)
        except:
            result =  "CostTab: {:4} {:4} {:10} {:4} {:5.3f} {:4} {:5.3f} {:5.3f}".format(
                self.rowid or "<none>",
                self.state or "<none>",
                "<none>", 
                self.lower_limit or np.nan, 
                self.max_cost or np.nan,
                self.upper_limit or np.nan,
                self.min_cost or np.nan,
                self.dispersion or np.nan)
        return result


class DemandsTab(models.Model):
    key = models.IntegerField(blank=True, null=False, primary_key=True)
    name = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'demands_tab'

    def __str__(self):
        return self.name


class DjangoMigrations(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class FragilityTab(models.Model):
    rowid = models.IntegerField(blank=True, null=False, primary_key=True)
    component = models.ForeignKey(ComponentsTab, models.DO_NOTHING, db_column='component')
    state = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    repairs = models.TextField(blank=True, null=True)
    median = models.FloatField(blank=True, null=True)
    beta = models.FloatField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fragility_tab'

    def __str__(self):
        try:
            return "FragilityTab: {:4} {:4} {:10}".format(
                self.rowid or "<none>",
                self.state or "<none>",
                self.component.ident or "<none>")
        except:
            return "FragilityTab: {:4} {:4} {:10}".format(
                self.rowid or "<none>",
                self.state or "<none>",
                "<none>")

class UnitsTab(models.Model):
    key = models.IntegerField(blank=True, null=False, primary_key=True)
    name = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'units_tab'

    def __str__(self):
        return self.name

class PACT_CatsTab(models.Model):
    rowid = models.IntegerField(blank=True, null=False, primary_key=True)
    ident = models.TextField(blank=True, null=False)
    description = models.TextField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pact_cats_tab'

    def __str__(self):
        return self.ident + ": " + self.description

class CompRouter(object):
    """
    A router to control all database operations on models in the
    comp application.
    """
    def __init__(self):
        self.tables = ['components_tab', 'cost_tab', 'demands_tab', 'fragility_tab', 'units_tab', 'pact_cats_tab']

    def db_for_read(self, model, **hints):
        """
        Attempts to read comp models go to comp_db.
        """
        if model._meta.db_table in self.tables:
            return 'components_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write comp models go to comp_db.
        """
        if model._meta.db_table in self.tables:
            return 'components_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the comp app is involved.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the comp app only appears in the 'comp_db'
        database.
        """
        return None
        
class Component_Form(ModelForm):
    class Meta:
        model = ComponentsTab
        fields = '__all__'

        widgets = {
            'ident': TextInput(attrs={'title': 'Enter the component identifier.'}),
            'key': HiddenInput,
        }

        def __init(self, **args):
            super(ModelForm, self).__init__(args)
            self.fields['component'].widget.attrs['onchange'] = 'change_component()'

    def clean(self):
        """Basic validation"""
        # Use the parent's handling of required fields, etc.
        #super(Component_Form, self).clean()        
        cleaned_data = self.cleaned_data

        errors = {}
        # Make sure that the identifier hasn't been changed to one that's
        # already in use:
        if self.instance.ident != cleaned_data['ident']:
            if len(ComponentsTab.objects.filter(ident=cleaned_data['ident'])) > 0:
                if ComponentsTab.objects.get(ident=cleaned_data['ident']) != self:
                   errors['ident'] = 'Identifier must be unique'

        if len(errors) > 0:
            raise ValidationError(errors)

class Cost_Form(ModelForm):
    class Meta:
        model = CostTab
        fields = '__all__'

        widgets={'state': HiddenInput,
                 'component': HiddenInput,
                 'rowid': HiddenInput}

    # Full set of options form BaseModelForm class:
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, use_required_attribute=None,
                 renderer=None):
        super(ModelForm, self).__init__(data, files, auto_id, prefix, initial,
                                        error_class, label_suffix,
                                        empty_permitted, instance,
                                        use_required_attribute, renderer)
        self.fields['component'].required= False

    def clean(self):
        """Basic validation"""
        # Use the parent's handling of required fields, etc.
        cleaned_data = self.cleaned_data
        if self.is_valid():
            errors = {}

            if cleaned_data['min_cost'] and cleaned_data['min_cost'] < 0:
                errors['min_cost'] = 'Min cost must be >= $0.00'
            if cleaned_data['max_cost'] and cleaned_data['max_cost'] < 0:
                errors['max_cost'] = 'Max cost must be >= $0.00'

            if cleaned_data['lower_limit'] < 0:
                errors['lower_limit'] = 'Lower limit must be >= 0'
            if cleaned_data['upper_limit'] < 0:
                errors['upper_limit'] = 'Upper limit must be >= 0'
            if cleaned_data['dispersion'] < 0:
                errors['dispersion'] = 'Dispersion must be >= 0'

            if len(errors) > 0:
                raise ValidationError(errors)
        else:
            eprint("Cost_Form errors: {}".format(self.errors))
            eprint("cost_form cleaned_data: {}".format(cleaned_data))
            #eprint("form: {}".format(self))
            raise ValidationError(self.errors)

class Fragility_Form(ModelForm):
    class Meta:
        model = FragilityTab
        fields = '__all__'
        

        widgets={'state': HiddenInput,
                 'component': HiddenInput,
                 'rowid': HiddenInput,
                 'image': HiddenInput}

    # Full set of options form BaseModelForm class:
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, use_required_attribute=None,
                 renderer=None):
        super(ModelForm, self).__init__(data, files, auto_id, prefix, initial,
                                        error_class, label_suffix,
                                        empty_permitted, instance,
                                        use_required_attribute, renderer)
        self.fields['component'].required= False
        
    def clean(self):
        """Basic validation"""
        # Use the parent's handling of required fields, etc.
        cleaned_data = self.cleaned_data
        #eprint("> Fragility_Form::clean()")

        if self.is_valid():
            errors = {}

            if cleaned_data['description'] == "":
                errors['description'] = "Description required."
            if cleaned_data['repairs'] == "":
                errors['repairs'] = "Repairs required."
            if cleaned_data['median'] <= 0:
                errors['median'] = "Median must be > 0."
            if cleaned_data['beta'] <= 0:
                errors['beta'] = "Beta must be > 0."

            if len(errors) > 0:
                eprint("fragility_form errors: {}".format(errors))
                raise ValidationError(errors)
        else:
            eprint("Fragility_Form errors: {}".format(self.errors))
            eprint("fragility_form cleaned_data: {}".format(cleaned_data))
            #eprint("form: {}".format(self))
            raise ValidationError(self.errors)
        #eprint("< Fragility_Form::clean()")

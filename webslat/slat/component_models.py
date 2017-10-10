# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class ComponentsTab(models.Model):
    key = models.IntegerField(blank=True, null=False, primary_key=True)
    ident = models.TextField()  # This field type is a guess.
    name = models.TextField(blank=True, null=True)  # This field type is a guess.
    system = models.TextField(blank=True, null=True)  # This field type is a guess.
    units = models.ForeignKey('UnitsTab', models.DO_NOTHING, db_column='units', blank=True, null=True)
    demand = models.ForeignKey('DemandsTab', models.DO_NOTHING, db_column='demand', blank=True, null=True)
    structural = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'components_tab'

    def __str__(self):
        return self.ident + ": " + self.name


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
        return "CostTab: {} {}".format(self.rowid, self.component)


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
        return "FragilityTab: {} {}".format(self.rowid, self.component)

class UnitsTab(models.Model):
    key = models.IntegerField(blank=True, null=False, primary_key=True)
    name = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'units_tab'

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
        

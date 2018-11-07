from celery import shared_task,current_task,task
from numpy import random
from scipy.fftpack import fft
from django.urls import reverse
from django.contrib.auth.models import User
from .etabs import *
import numpy as np
from functools import reduce
#from .models import *
from .models import *
import pandas as pd
import os
import time
import logging
from jchart import Chart
from jchart.config import Axes, DataSet, rgba, ScaleLabel, Legend, Title
import seaborn as sns
from math import *
from django.utils.safestring import mark_safe

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

@task
def ImportETABS(user_id, preprocess_data_id):
    logger = ImportETABS.get_logger()
    eprint("> ImportETABS()")

    preprocess_data = ETABS_Preprocess.objects.get(id=preprocess_data_id)
    title = preprocess_data.title
    description = preprocess_data.description
    strength = preprocess_data.strength
    location = preprocess_data.location
    soil_class = preprocess_data.soil_class
    return_period = preprocess_data.return_period
    frame_type_x = preprocess_data.frame_type_x
    frame_type_y = preprocess_data.frame_type_y
    drift_case_x = preprocess_data.drift_case_x
    drift_case_y = preprocess_data.drift_case_y
    accel_case_x = preprocess_data.accel_case_x
    accel_case_y = preprocess_data.accel_case_y
    Tx = preprocess_data.period_x
    Ty = preprocess_data.period_y

    start_time = time.time()
    messages = []
    current_task.update_state(meta={'message': "\n".join(messages) + "\nStarting"})
    project = Project()
    xl_workbook = pd.ExcelFile(io.BytesIO(preprocess_data.file_contents))
    sheet = munge_data_frame(
        xl_workbook.parse("Modal Participating Mass Ratios", 
                          skiprows=(1)))
    mpms = sheet
    sheet = munge_data_frame(xl_workbook.parse(
        "Diaphragm Center of Mass Displa",
        skiprows=1))
    sheet = munge_data_frame(xl_workbook.parse(
        "Story Drifts", 
        skiprows=1))
    sheet = munge_data_frame(xl_workbook.parse(
        "Story Accelerations", 
        skiprows=1))
    end_time = time.time()
    
    eprint("Load Time: {}".format(end_time - start_time))
    
    setattr(project, 'title_text', title)
    setattr(project, 'description_text', description)
    setattr(project, 'rarity', 1.0/float(return_period))
    project.save()

    messages.append("Source: {}".format(preprocess_data.hazard_period_source))
    current_task.update_state(meta={'message': "\n".join(messages)})
    
    if preprocess_data.hazard_period_source == 'TX':
        fundamental_period = Tx
    elif preprocess_data.hazard_period_source == 'TY':
        fundamental_period = Ty
    elif preprocess_data.hazard_period_source == 'AVERAGE':
        fundamental_period = (Tx + Ty)/2.0
    elif preprocess_data.hazard_period_source == 'MANUAL':
        fundamental_period = preprocess_data.hazard_manual_period
    else:
        raise ValueError

    messages.append("Periods: {}, {}; {}".format(Tx, Ty, fundamental_period))
    current_task.update_state(meta={'message': "\n".join(messages) + 
                                    "\nCreating hazard curve"})

    # Create the hazard curve, using the selected period:
    nzs = NZ_Standard_Curve(location=Location.objects.get(location=location),
                            soil_class = soil_class,
                            period = fundamental_period)
    nzs.save()
    hazard = IM(flavour = IM_Types.objects.get(pk=IM_TYPE_NZS), nzs = nzs)
    hazard.save()
    project.IM = hazard
    project.save()

    messages.append("Created hazard curve for {}, soil class {}".format(
        location, soil_class))
    current_task.update_state(meta={ 'message': "\n".join(messages) + 
                                    "\nDetermining design hazard."})
    # Figure out the design IM:
    guess = hazard.model().plot_max()
    design_im = fsolve(lambda x: 
                       hazard.model().getlambda(x[0]) - 1.0/return_period,
                       guess)[0]
    messages.append("Design IM: {:>5.3}".format(design_im))
    current_task.update_state(meta={ 'message': "\n".join(messages) + 
                                    "\nReading data."})
    # Get the names and heights of the stories from the ~Diaphragm Center of Mass
    # Displa~ tab:
    sheet = munge_data_frame(xl_workbook.parse(
        "Diaphragm Center of Mass Displa",
        skiprows=1))
    height_df = sheet.loc[lambda x: 
                          x['Load Case/Combo'] == 'Dead'].\
                          filter(['Story', 'Z']).sort_values('Z')
    height_df = height_df.rename(index=str, columns={'Z': 'Height'})
    messages.append("Structure has {} stories.".format(len(height_df)))
    current_task.update_state(meta={ 'message': "\n".join(messages) + 
                                    "\nCreating levels."})

    # Create levels for the project:
    level = Level(project=project, level=0, label="Ground Floor")
    level.save()
    l = 1;
    for story in height_df["Story"]:
        level = Level(project=project, level=l, label=story)
        level.save()
        l = l + 1

    # Get the drift at each story from the ~Story Drifts~ tab:
    sheet = munge_data_frame(xl_workbook.parse(
        "Story Drifts", 
        skiprows=1))
    drifts_df = pd.DataFrame(columns=['Story', 'X', 'Y'])

    for i in height_df['Story'].index:
        story = height_df.at[i, 'Story']

        x = sheet.loc[lambda x: map(lambda a, b, c: a == story and\
                                    b == drift_case_x and\
                                    c == 'X', \
                                    sheet['Story'],\
                                    sheet['Load Case/Combo'],
                                    sheet['Direction'])
        ]['Drift'].values[0]
        y = sheet.loc[lambda x: map(lambda a, b, c: a == story and\
                                     b == drift_case_y and\
                                     c == 'Y', \
                                     sheet['Story'],\
                                     sheet['Load Case/Combo'],
                                     sheet['Direction'])
        ]['Drift'].values[0]
        drifts_df = drifts_df.append(
            pd.DataFrame(data=[[story, x, y]],
                         columns=['Story', 'X', 'Y']))
    
    # Get the acceleration at each story from the ~Story Accelerations~ tab:
    sheet = munge_data_frame(xl_workbook.parse(
        "Story Accelerations", 
        skiprows=1))
    accels_df = pd.DataFrame(columns=['Story', 'X', 'Y'])
    
    for i in  height_df['Story'].index:
        story = height_df.at[i, 'Story']

        x = sheet.loc[lambda x: map(lambda a, b: a == story and \
                                    b == accel_case_x, \
                                    sheet['Story'], sheet['Load Case/Combo'])]['UX'].values[0]
        y = sheet.loc[lambda x: map(lambda a, b: a == story and \
                                    b == accel_case_y, \
                                    sheet['Story'], sheet['Load Case/Combo'])]['UY'].values[0]
        
        # Convert form mm/sec^2 to g:
        x = x / 9810
        y = y / 9810
        
        accels_df = accels_df.append(pd.DataFrame(
            data=[[story, x, y]], 
            columns=['Story', 'X', 'Y']))

    num_floors = len(height_df)  # Number of stories
    H = max(height_df['Height'])  # Building height

    # Define the range IM values for the table:
    im_range = np.linspace(0.0, design_im * 2, 12)

    # Allocate a blank table for the results:
    curves = pd.DataFrame(columns=['Story', 'IM', 'Drift_X', 'Drift_Y', 'Accel_X', 'Accel_Y'])

    dispersions = pd.DataFrame(columns=['IM', 'βsd', 'βfa', 'βfv'])

    # Get the drift and acceleration coefficients from the table:
    drift_coefficients_x = get_correction_factors(num_floors,
                                                frame_type_x,
                                                "Story Drift Ratio")
    drift_coefficients_y = get_correction_factors(num_floors,
                                                frame_type_y,
                                                "Story Drift Ratio")
    accel_coefficients_x = get_correction_factors(num_floors,
                                                frame_type_x, 
                                                "Floor Acceleration")
    accel_coefficients_y = get_correction_factors(num_floors,
                                                frame_type_y, 
                                                "Floor Acceleration")
    current_task.update_state(meta={ 'message': "\n".join(messages) + 
                                    "\nCalculating dispersions."})
    for im in im_range:
        # Calculate the dispersion values for each demand:
        scale = im / design_im
        
        # Get dispersion factors:
        dispersion = get_dispersion(fundamental_period, scale)
        dispersions = dispersions.append(
            pd.DataFrame(data=[[im, 
                                float(dispersion[0]),
                                float(dispersion[1]),
                                float(dispersion[2])]],
                         columns=['IM', 'βsd', 'βfa', 'βfv']),
            ignore_index=True)

    for story in height_df['Story']:
        for im in im_range:
            current_task.update_state(
                meta={ 'message': "\n".join(messages) + 
                      "\nCalculating demads for story {} at {}.".format(
                          story, im)})
            # Calculate the linear (uncorrected) values for
            # each demand:
            scale = im / design_im

            dx = drifts_df.loc[lambda d: d['Story'] == story]['X'][0] * scale
            dy = drifts_df.loc[lambda d: d['Story'] == story]['Y'][0] * scale
            ax = accels_df.loc[lambda d: d['Story'] == story]['X'][0] * scale
            ay = accels_df.loc[lambda d: d['Story'] == story]['Y'][0] * scale
            #
            # If the strength ratio is at least 1.0, apply the 
            # correction factors:
            s = max(scale * strength, 1.0)
            if (s >= 1.0):
                # Apply non-linear correction factors
                h = height_df.loc[lambda x: x['Story'] == story]["Height"][0]
                #
                # For X drift
                k = sum(([1, Tx, s, h/H, (h/H)**2, (h/H)**3] * drift_coefficients_x).values[0])
                dx = dx * np.exp(k)
                #
                # For Y drift
                k = sum(([1, Ty, s, h/H, (h/H)**2, (h/H)**3] * drift_coefficients_y).values[0])
                dy = dy * np.exp(k)
                #
                # For X acceleration
                k = sum(([1, Tx, s, h/H, (h/H)**2, (h/H)**3] * accel_coefficients_x).values[0])
                ax = ax * np.exp(k)
                #
                # For Y acceleration
                k = sum(([1, Ty, s, h/H, (h/H)**2, (h/H)**3] * accel_coefficients_y).values[0])
                ay = ay * np.exp(k)
            # Add the data for this story and IM to the table:
            curves = curves.append(pd.DataFrame(data=[[story, im, dx, dy, ax, ay]], columns=['Story', 'IM', 'Drift_X', 'Drift_Y', 'Accel_X', 'Accel_Y']), ignore_index=True)

    messages.append("Created hazard curves.")
    current_task.update_state(
        meta={ 'message': "\n".join(messages) + 
              "\nCreating EDP: Ground level acceleration."})
    
    # Ground level acceleration is calculated using NZS 1170, using a period of 0:
    level = Level.objects.get(level=0, project=project)
    ground_accel_x = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                         interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
    ground_accel_x.save()
    ground_accel_y = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                         interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
    ground_accel_y.save()
    EDP_Grouping(project=project, 
                 level=Level.objects.get(level=0, project=project),
                 type='A',
                 demand_x=ground_accel_x,
                 demand_y=ground_accel_y).save()
    
    location_data = Location.objects.get(location=location)
    for r in R_defaults:
        im = C(soil_class,
               fundamental_period, 
               r, 
               location_data.z,
               location_data.min_distance)
        accel = C(soil_class,
                  0.0, 
                  r, 
                  location_data.z,
                  location_data.min_distance)
        dispersion = float(get_dispersion(fundamental_period, im / design_im)[0])
        EDP_Point(demand=ground_accel_x, im=im, median_x=accel, sd_ln_x=dispersion).save()
        EDP_Point(demand=ground_accel_y, im=im, median_x=accel, sd_ln_x=dispersion).save()

    # Add drift and accelerations for above-ground levels:    
    for l in range(1, num_floors+1):                               
        level = Level.objects.get(level=l, project=project)
        current_task.update_state(
            meta={ 'message': "\n".join(messages) + 
                  "\nCreating EDP: {} drift.".format(level.label)})
        edp_x = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                    interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
        edp_x.save()
        edp_y = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                    interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
        edp_y.save()
        EDP_Grouping(project=project, 
                     level=Level.objects.get(level=l, project=project),
                     type='D',
                     demand_x=edp_x,
                     demand_y=edp_y).save()

        for im in im_range:
            drift = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Drift_X'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βsd']
            EDP_Point(demand=edp_x, im=im, median_x=drift, sd_ln_x=dispersion).save()
            drift = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Drift_Y'])
            EDP_Point(demand=edp_y, im=im, median_x=drift, sd_ln_x=dispersion).save()
            
        edp_x = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                    interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
        edp_x.save()
        edp_y = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                    interpolation_method=Interpolation_Method.objects.get(method_text="Linear"))
        edp_y.save()
        EDP_Grouping(project=project, 
                     level=Level.objects.get(level=l, project=project),
                     type='A',
                     demand_x=edp_x,
                     demand_y=edp_y).save()
        current_task.update_state(
            meta={ 'message': "\n".join(messages) + 
                  "\nCreating EDP: {} acceleration.".format(level.label)})
        for im in im_range:
            accel = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Accel_X'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βfa']
            EDP_Point(demand=edp_x, im=im, median_x=accel, sd_ln_x=dispersion).save()
            
            accel = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Accel_Y'])
            EDP_Point(demand=edp_y, im=im, median_x=accel, sd_ln_x=dispersion).save()
            
    project.AssignRole(
        User.objects.get(id=user_id),
        ProjectUserPermissions.ROLE_FULL)
    messages.append("Done")
    current_task.update_state(
        meta={ 'message': "\n".join(messages)})
    
    preprocess_data.delete()
    eprint("< ImportETABS()")
    return(reverse('slat:levels', args=(project.id,)))
    #return project.id

    

@task
def Project_Annual_Cost(project_id):
    logger = Project_Annual_Cost.get_logger()
    logger.info("> Project_Annual_Cost({})".format(project_id))
    eprint("> Project_Annual_Cost({})".format(project_id))
    for c in Cached_Result.objects.all():
        eprint("C: {}".format(c))
    project = Project.objects.get(pk=project_id)
    cr = Cached_Result.objects.get(identifier="Project::Annual_Cost",
                                   project=project)
    eprint("CR: {}".format(cr))
    annual_cost = project.model().AnnualCost()
    cr.result = pickle.dumps({'mean': annual_cost.mean(), 'sd_ln': annual_cost.sd_ln()})
    cr.save()
    eprint("< Project_Annual_Cost({})".format(project_id))
    logger.info("< Project_Annual_Cost({})".format(project_id))
    return None

@task
def Incremental_Test(project_id):
    s = time.time()
    eprint("> Incremental_Test(): Projects: {}".format(pyslat.structure.defs))
    value = {'slat_id_status': 'Calculating...'}
    
    project = Project.objects.get(pk=project_id)

    groups = Component_Group.objects.filter(demand__project=project)
    for c in groups:
        models = c.model().Models()
        value['slat_comp_id_{}_x'.format(c.id)] = models['X'].E_annual_cost()
        current_task.update_state(meta=value)

        value['slat_comp_id_{}_y'.format(c.id)] = models['Y'].E_annual_cost()
        current_task.update_state(meta=value)

        value['slat_comp_id_{}_u'.format(c.id)] = models['U'].E_annual_cost()
        current_task.update_state(meta=value)

    c = ExpectedLoss_Over_Time_Chart(project).as_html()

    d = re.search("Chart\(ctx, *(\{[^;]*)", c, re.MULTILINE).groups()[0][0:-1]
    e = d.replace("true", "True").replace("false", "False")
    value['slat_id_chart'] = eval(e)
    value['slat_id_status'] = 'Done'
    
    eprint(project.model().AnnualCost())
    eprint(time.time() - s)
    eprint("< Incremental_Test(): Projects: {}".format(pyslat.structure.defs))
    return value
        
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

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
from .project_charts import *
from  webslat.settings import SINGLE_USER_MODE
from django.db import transaction


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

    
@task
def ImportETABS(user_id, preprocess_data_id):
    logger = ImportETABS.get_logger()

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
    with transaction.atomic():
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
    with transaction.atomic():
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
    location_data = Location.objects.get(location=location)
    ground_points = []
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
        ground_points.append({'im': im, 'accel': accel, 'sd_ln':dispersion})
        
    with transaction.atomic():
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
        
        for point in ground_points:
            EDP_Point(demand=ground_accel_x,
                      im=point['im'],
                      median_x=point['accel'],
                      sd_ln_x=point['sd_ln']).save()
            EDP_Point(demand=ground_accel_y,
                      im=point['im'],
                      median_x=point['accel'],
                      sd_ln_x=point['sd_ln']).save()

    # Add drift and accelerations from ETABS data:    
    for l in range(1, num_floors+1): 
        # Drift calculations
        current_task.update_state(
            meta={ 'message': "\n".join(messages) + 
                  "\nCreating EDP: {} drift.".format(
                      Level.objects.get(
                          level=l-1, 
                          project=project).label)})

        src_label = Level.objects.get(level=l, project=project).label
        drift_points = []
        for im in im_range:
            drift_x = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b==src_label,
                    x['IM'], x['Story']
                )]['Drift_X'])
            drift_y = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b==src_label,
                    x['IM'], x['Story']
                )]['Drift_Y'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βsd']
            drift_points.append({'im': im, 'x': drift_x, 'y': drift_y,
                                     'dispersion': dispersion})
        with transaction.atomic():
            edp_x = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                        interpolation_method=
                        Interpolation_Method.objects.get(method_text="Linear"))
            edp_x.save()
            edp_y = EDP(flavour=EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF),
                        interpolation_method=
                        Interpolation_Method.objects.get(method_text="Linear"))
            edp_y.save()
            EDP_Grouping(project=project, 
                         level=Level.objects.get(level=l-1, project=project),
                         type='D',
                         demand_x=edp_x,
                         demand_y=edp_y).save()
            
            for point in drift_points:
                EDP_Point(demand=edp_x, 
                          im=point['im'],
                          median_x=point['x'],
                          sd_ln_x=point['dispersion']
                ).save()
                EDP_Point(demand=edp_y, 
                          im=point['im'],
                          median_x=point['y'],
                          sd_ln_x=point['dispersion']
                ).save()

        current_task.update_state(
            meta={ 'message': "\n".join(messages) + 
                  "\nCreating EDP: {} acceleration.".format(level.label)})

        accel_points = []
        for im in im_range:
            accel_x = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b==src_label,
                    x['IM'], x['Story']
                )]['Accel_X'])
            
            accel_y = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b==src_label,
                    x['IM'], x['Story']
                )]['Accel_Y'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βfa']

            accel_points.append({'im': im,
                                 'x': accel_x,
                                 'y': accel_y,
                                 'dispersion': dispersion})

        with transaction.atomic():
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
            
            for point in accel_points:
                EDP_Point(demand=edp_x,
                          im=point['im'],
                          median_x=point['x'],
                          sd_ln_x=point['dispersion']
                ).save()

                EDP_Point(demand=edp_y,
                          im=point['im'],
                          median_x=point['y'],
                          sd_ln_x=point['dispersion']
                ).save()

    if not SINGLE_USER_MODE:
        project.AssignRole(
            User.objects.get(id=user_id),
            ProjectUserPermissions.ROLE_FULL)
    messages.append("Done")
    current_task.update_state(
        meta={ 'message': "\n".join(messages)})
    
    preprocess_data.delete()
    return(reverse('slat:levels', args=(project.id,)))

    

@task
def Project_Basic_Stats(project_id):
    logger = Project_Basic_Stats.get_logger()
    project = Project.objects.get(pk=project_id)
    values = {'slat_id_status': 'Calculating annual cost.'}
    current_task.update_state(meta=values)
    annual_cost = project.model().AnnualCost()
    values['slat_id_mean_annual_cost'] = "{:>.2f}".format(annual_cost.mean())
    values['slat_id_sd_ln_annual_cost'] = "{:>.2f}".format(annual_cost.sd_ln())
    values['slat_id_status'] = 'Plotting Cost vs. IM.'
    current_task.update_state(meta=values)
    
    before = time.time()
    values['slat_id_cost_chart'] = Command_String_from_Chart(IMCostChart(project))
    after = time.time()
    values['slat_id_status'] = 'Plotting PDF'
    current_task.update_state(meta=values)

    before = after
    values['slat_id_pdf_chart'] = Command_String_from_Chart(IMPDFChart(project))
    after = time.time()
    
    values['slat_id_status'] = 'Done'
    current_task.update_state(meta=values)
    return values

@task
def Project_Basic_Analysis(project_id):
    project = Project.objects.get(pk=project_id)
    if project.IM:
        values = {'slat_id_status': 'Calculating annual cost.'}
        current_task.update_state(meta=values)
        annual_cost = project.model().AnnualCost()
        values['slat_id_mean_annual_cost'] = "{:>.2f}".format(annual_cost.mean())
        values['slat_id_sd_ln_annual_cost'] = "{:>.2f}".format(annual_cost.sd_ln())
        values['slat_id_status'] = 'Expected Annual Losses'
        current_task.update_state(meta=values)
        
        values['slat_id_cost_chart'] = Command_String_from_Chart(ExpectedLoss_Over_Time_Chart(project))
        values['slat_id_status'] = 'Plotting Loss by Floor'
        current_task.update_state(meta=values)

        values['slat_id_by_floor_chart'] = Command_String_from_Chart(ByFloorChart(project))
        values['slat_id_status'] = 'Plotting Loss by Component'
        current_task.update_state(meta=values)

        by_comp_chart = ByCompPieChart(project)
        values['slat_id_by_comp_chart'] = Command_String_from_Chart(by_comp_chart)
        values['slat_id_by_comp_chart_color_map'] = by_comp_chart.get_color_map()
        values['slat_id_status'] = 'Done'
    else:
        values = {'slat_id_status': 'Error: No hazard defined.'}
    return values

@task
def Project_Detailed_Analysis(project_id):
    project = Project.objects.get(pk=project_id)
    if project.IM:
        s = time.time()
        value = {'slat_id_status': 'Calculating...'}


        groups = Component_Group.objects.filter(demand__project=project)
        level_totals = {}
        for l in project.levels():
            level_totals[l.id] = {'X': 0, 'Y': 0, 'U': 0, 'Total': 0}

        for c in groups.order_by('?'):
            models = c.model().Models()
            level_id = c.demand.level.id

            value['slat_id_status'] = "Calculating X cost for group #{} ({}).".format(c.id, c.demand.level.label)
            current_task.update_state(meta=value)

            cost = models['X'].E_annual_cost()
            current_cost = cost
            value['slat_comp_id_{}_x'.format(c.id)] = cost
            value['slat_comp_id_{}_total'.format(c.id)] = current_cost
            level_totals[level_id]['X'] = level_totals[level_id]['X'] + cost
            level_totals[level_id]['Total'] = level_totals[level_id]['Total'] + cost
            value['slat_comp_id_flr_{}_x'.format(level_id)] = level_totals[level_id]['X']
            value['slat_comp_id_flr_{}_total'.format(level_id)] = level_totals[level_id]['Total']

            value['slat_id_status'] = "Calculating Y cost for group #{} ({}).".format(c.id, c.demand.level.label)
            current_task.update_state(meta=value)

            cost = models['Y'].E_annual_cost()
            current_cost += cost
            value['slat_comp_id_{}_y'.format(c.id)] = cost
            value['slat_comp_id_{}_total'.format(c.id)] = current_cost
            level_totals[level_id]['Y'] = level_totals[level_id]['Y'] + cost
            level_totals[level_id]['Total'] = level_totals[level_id]['Total'] + cost
            value['slat_comp_id_flr_{}_y'.format(level_id)] = level_totals[level_id]['Y']
            value['slat_comp_id_flr_{}_total'.format(level_id)] = level_totals[level_id]['Total']
            value['slat_id_status'] = "Calculating U cost for group #{} ({}).".format(c.id, c.demand.level.label)
            current_task.update_state(meta=value)

            cost = models['U'].E_annual_cost()
            current_cost += cost
            value['slat_comp_id_{}_total'.format(c.id)] = current_cost
            value['slat_comp_id_{}_u'.format(c.id)] = models['U'].E_annual_cost()
            value['slat_comp_id_{}_total'.format(c.id)] = current_cost
            level_totals[level_id]['U'] = level_totals[level_id]['U'] + cost
            value['slat_comp_id_flr_{}_u'.format(level_id)] = level_totals[level_id]['U']
            value['slat_comp_id_flr_{}_total'.format(level_id)] = level_totals[level_id]['Total']
            level_totals[level_id]['Total'] = level_totals[level_id]['Total'] + cost
            current_task.update_state(meta=value)
            value['slat_level_contrib_id_{}'.format(level_id)] = level_totals[level_id]['Total']

        value['slat_id_status'] = 'Calculating annual cost.'
        current_task.update_state(meta=value)
        annual_cost = project.model().AnnualCost()
        value['slat_id_mean_annual_cost'] = annual_cost.mean()
        value['slat_id_sd_ln_annual_cost'] = annual_cost.sd_ln()
        for l in project.levels():
            value['slat_level_pct_id_{}'.format(l.id)] = 100 * level_totals[l.id]['Total']/annual_cost.mean()

        value['slat_id_status'] = 'Expected Annual Losses'
        current_task.update_state(meta=value)

        value['slat_id_status'] = "Plotting Expected Loss Over Time."
        current_task.update_state(meta=value)

        value['slat_id_chart'] = Command_String_from_Chart(ExpectedLoss_Over_Time_Chart(project))
        value['slat_id_status'] = 'Done'

    else:
        value = {'slat_id_status': 'Error: No hazard defined.'}
    return value
        
@task
def Incremental_Test(project_id):
    s = time.time()
    value = {'slat_id_status': 'Calculating...'}
    
    project = Project.objects.get(pk=project_id)

    groups = Component_Group.objects.filter(demand__project=project)
    for c in groups:
        models = c.model().Models()
        value['slat_id_status'] = "Calculating X cost for group #{} ({}).".format(c.id, c.demand.level.label)
        current_task.update_state(meta=value)
        
        value['slat_comp_id_{}_x'.format(c.id)] = models['Y'].E_annual_cost()
        value['slat_id_status'] = "Calculating X cost for group #{} ({}).".format(c.id, c.demand.level.label)
        current_task.update_state(meta=value)

        value['slat_id_status'] = "Calculating U cost for group #{} ({}).".format(c.id, c.demand.level.label)
        value['slat_comp_id_{}_y'.format(c.id)] = models['Y'].E_annual_cost()
        current_task.update_state(meta=value)

        value['slat_comp_id_{}_u'.format(c.id)] = models['U'].E_annual_cost()
        current_task.update_state(meta=value)

    value['slat_id_status'] = "Plotting Expected Loss Over Time."
    value['slat_comp_id_{}_y'.format(c.id)] = models['Y'].E_annual_cost()
    current_task.update_state(meta=value)
  
    value['slat_id_chart'] = Command_String_from_Chart(ExpectedLoss_Over_Time_Chart(project))
    value['slat_id_status'] = 'Done'
    
    return value
        


@task
def Project_Demand_Plots(project_id):
    project = Project.objects.get(pk=project_id)
    values = {'slat_id_status': 'Plotting X Drifts.'}
    current_task.update_state(meta=values)

    values['slat_id_chart_drift_x'] = Command_String_from_Chart(IMDemandPlot(project, 'D', 'X'))
    values['slat_id_status'] = 'Plotting Y Drifts.'
    current_task.update_state(meta=values)
    
    values['slat_id_chart_drift_y'] = Command_String_from_Chart(IMDemandPlot(project, 'D', 'Y'))
    values['slat_id_status'] = 'Plotting X Accelerations.'
    current_task.update_state(meta=values)

    values['slat_id_chart_accel_x'] = Command_String_from_Chart(IMDemandPlot(project, 'A', 'X'))
    values['slat_id_status'] = 'Plotting Y Accelerations.'
    current_task.update_state(meta=values)

    values['slat_id_chart_accel_y'] = Command_String_from_Chart(IMDemandPlot(project, 'A', 'Y'))
    values['slat_id_status'] = 'Done'
    return values

@task
def HandleChange(object_class, object_id):
    logger = HandleChange.get_logger()
    #logger.info("> HandleChange({}, {})".format(object_class, object_id))
    #eprint("> HandleChange({}, {})".format(object_class, object_id))
    
    if object_class == "<class 'slat.models.Project'>":
        object = Project.objects.get(pk=object_id)
        object.model().Clear_Cache()
        object._make_model()
        if object.IM:
            old_mean_im_collapse = object.IM.model()._collapse and \
                                   object.IM.model()._collapse.get_mean_X()
            old_sd_ln_im_collapse = object.IM.model()._collapse and \
                                    object.IM.model()._collapse.get_sigma_lnX()
            new_mean_im_collapse = object.mean_im_collapse
            new_sd_ln_im_collapse = object.sd_ln_im_collapse

            old_mean_im_demolition = object.IM.model()._demolition and \
                                     object.IM.model()._demolition.get_mean_X()
            old_sd_ln_im_demolition = object.IM.model()._demolition and \
                                      object.IM.model()._demolition.get_sigma_lnX()
            new_mean_im_demolition = object.mean_im_demolition
            new_sd_ln_im_demolition = object.sd_ln_im_demolition

            if (old_mean_im_collapse != new_mean_im_collapse) or \
               (old_sd_ln_im_collapse != new_sd_ln_im_collapse) or \
               (old_mean_im_demolition != new_mean_im_demolition) or \
               (old_sd_ln_im_demolition != new_sd_ln_im_demolition):
                logger.info("REMODELING IM")
                object.IM._make_model() # In case collapse or demolition values changed
    elif object_class == "<class 'slat.models.IM'>":
        object = IM.objects.get(pk=object_id)
        object._make_model()
    elif object_class == "<class 'slat.models.IM'>":
        object = EDP.objects.get(pk=object_id)
        object._make_model()
    elif object_class == "<class 'slat.models.Component_Group'>":
        object = Component_Group.objects.get(pk=object_id)
        object._make_model({'X': True, 'Y': True, 'U':True})
        project = object.demand.project
        project._make_model()
    else:
        logger.info("**** I DON'T KNOW WHAT IT IS ****")




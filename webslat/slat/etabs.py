from  .models import *
import pandas as pd
import numpy as np
from  .models import *
from functools import reduce

def munge_data_frame(df):
    column = df.columns[0]
    # Remove rows from the top:
    while type(df.at[df.index[0], column])==float \
          and \
          np.isnan(df.at[df.index[0], column]):
        df = df.drop(df.index[0])
        
    # Remove rows from the bottom:
    while type(df.at[df.index.values[-1], column])==float \
          and \
          np.isnan(df.at[df.index.values[-1], column]):
        df = df.drop(df.index.values[-1])
        
    # Remove empty columns:
    for col in df.columns:
        if reduce(lambda x, y: x and y, 
                  (df[col].map(lambda x: 
                               type(x)==float and
                               np.isnan(x), False))):
            df = df.drop(col, 1)
            
    return df

def get_correction_factors(floors, 
                           structure_frame_type, 
                           structure_demand):
    return correction_factors.loc[
        lambda x: map(lambda demand, minf, maxf, frame:
                      demand == structure_demand and
                      minf <= floors and
                      maxf >= floors and
                      frame == structure_frame_type, 
                      x['Demand'], 
                      x['Min Floors'],
                      x['Max Floors'],
                      x['Frame Type'])].filter(
                          ['a0', 'a1', 'a2', 'a3','a4', 'a5'])

correction_factors = pd.DataFrame(
    data= np.array([['Story Drift Ratio', 2, 9, 'Braced', 0.9, -0.12, 0.012, -2.65,
                     2.09, 0.0],
       ['Story Drift Ratio', 2, 9, 'Moment', 0.75, -0.044, -0.01, -2.58,
        2.3, 0.0],
       ['Story Drift Ratio', 2, 9, 'Wall', 0.92, -0.036, -0.058, -2.56,
        1.39, 0.0],
       ['Floor Velocity', 2, 9, 'Braced', 0.15, -0.1, 0.0, -0.408, 0.47,
        0.0],
       ['Floor Velocity', 2, 9, 'Moment', 0.025, -0.068, 0.032, -0.53,
        0.54, 0.0],
       ['Floor Velocity', 2, 9, 'Wall', -0.033, -0.085, 0.055, -0.52, 0.47,
        0.0],
       ['Floor Acceleration', 2, 9, 'Braced', 0.66, -0.027, -0.089, 0.075,
        0.0, 0.0],
       ['Floor Acceleration', 2, 9, 'Moment', 0.66, -0.25, -0.08, -0.039,
        0.0, 0.0],
       ['Floor Acceleration', 2, 9, 'Wall', -0.66, -0.15, -0.084, -0.26,
        0.57, 0.0],
       ['Story Drift Ratio', 10, 15, 'Braced', 1.19, -0.12, -0.077, -3.78,
        6.43, -3.42],
       ['Story Drift Ratio', 10, 15, 'Moment', 0.67, -0.044, -0.098, -1.37,
        1.71, -0.57],
       ['Story Drift Ratio', 10, 15, 'Wall', 0.86, -0.036, -0.076, -4.58,
        6.88, -3.24],
       ['Floor Velocity', 10, 15, 'Braced', 0.086, -0.1, 0.041, 0.45,
        -2.89, 2.57],
       ['Floor Velocity', 10, 15, 'Moment', -0.02, -0.068, 0.034, 0.32,
        -1.75, 1.53],
       ['Floor Velocity', 10, 15, 'Wall', -0.11, -0.085, 0.11, 0.87, -4.07,
        3.27],
       ['Floor Acceleration', 10, 15, 'Braced', 0.44, -0.27, -0.052, 3.24,
        -9.71, 6.83],
       ['Floor Acceleration', 10, 15, 'Moment', 0.34, -0.25, -0.062, 2.86,
        -7.43, 5.1],
       ['Floor Acceleration', 10, 15, 'Wall', -0.13, -0.15, -0.1, 7.79,
        -17.52, 11.04]], dtype=object),
    columns=['Demand', 'Min Floors', 'Max Floors', 'Frame Type',
             'a0', 'a1', 'a2', 'a3', 'a4', 'a5'])

def get_dispersion_factors(period, strength_ratio):
    periods = set(dispersion_factors["T1"])
    t = max(0.2, min(period, 2.0))
    s = max(1.0, min(strength_ratio, 8.0))
    
    if t in periods:
        strengths = set(dispersion_factors[lambda x: x["T1"] == t]["S"])
        if s in strengths:
            return dispersion_factors.loc[
                lambda a: map(lambda x, y: x == 0.35 and y == 2, 
                              a['T1'], a['S'])].filter(
                                  ['βaΔ', 'βaa', 'βav', 'βm'])
        else:
            low_s = max([x for x in strengths if x <= s])
            high_s = min([x for x in strengths if x >= s])
            low = get_dispersion_factors(t, low_s)
            high = get_dispersion_factors(t, high_s)
            
            result = low
            for i in ["βaΔ", "βaa", "βav", "βm"]:
                result[i] = low[i] + (s - low_s)/(high_s - low_s) * (high[i] - low[i])
                return result
    else:
        low_t = max([x for x in periods if x <= t])
        high_t = min([x for x in periods if x >= t])
        low = get_dispersion_factors(low_t, s)
        high = get_dispersion_factors(high_t, s)
        result = low
        for i in ["βaΔ", "βaa", "βav", "βm"]:
            result[i] = low[i] + (t - low_t)/(high_t - low_t) * (high[i] - low[i])
            return result
        
def get_dispersion(period, strength_ratio):
    factors = get_dispersion_factors(period, strength_ratio)
    βaΔ = factors["βaΔ"]
    βaa = factors["βaa"]
    βav = factors["βav"]
    βm = factors["βm"]
    
    βsd = np.sqrt(βaΔ**2 + βm**2)
    βfa = np.sqrt(βaa**2 + βm**2)
    βfv = np.sqrt(βav**2 + βm**2)
    
    return [βsd, βfa, βfv]
      
dispersion_factors = pd.DataFrame(
    data = np.array([[ 0.2 ,  1.  ,  0.05,  0.1 ,  0.5 ,  0.25],
       [ 0.2 ,  2.  ,  0.35,  0.1 ,  0.51,  0.25],
       [ 0.2 ,  4.  ,  0.4 ,  0.1 ,  0.4 ,  0.35],
       [ 0.2 ,  6.  ,  0.45,  0.1 ,  0.37,  0.5 ],
       [ 0.2 ,  8.  ,  0.45,  0.05,  0.24,  0.5 ],
       [ 0.35,  1.  ,  0.1 ,  0.15,  0.32,  0.25],
       [ 0.35,  2.  ,  0.35,  0.15,  0.38,  0.25],
       [ 0.35,  4.  ,  0.4 ,  0.15,  0.43,  0.35],
       [ 0.35,  6.  ,  0.45,  0.15,  0.38,  0.5 ],
       [ 0.35,  8.  ,  0.45,  0.15,  0.34,  0.5 ],
       [ 0.5 ,  1.  ,  0.1 ,  0.2 ,  0.31,  0.25],
       [ 0.5 ,  2.  ,  0.35,  0.2 ,  0.35,  0.25],
       [ 0.5 ,  4.  ,  0.4 ,  0.2 ,  0.41,  0.35],
       [ 0.5 ,  6.  ,  0.45,  0.2 ,  0.36,  0.5 ],
       [ 0.5 ,  8.  ,  0.45,  0.2 ,  0.32,  0.5 ],
       [ 0.75,  1.  ,  0.1 ,  0.25,  0.3 ,  0.25],
       [ 0.75,  2.  ,  0.35,  0.25,  0.33,  0.25],
       [ 0.75,  4.  ,  0.4 ,  0.25,  0.39,  0.35],
       [ 0.75,  6.  ,  0.45,  0.25,  0.35,  0.5 ],
       [ 0.75,  8.  ,  0.45,  0.25,  0.3 ,  0.5 ],
       [ 1.  ,  1.  ,  0.15,  0.3 ,  0.27,  0.25],
       [ 1.  ,  2.  ,  0.35,  0.3 ,  0.29,  0.25],
       [ 1.  ,  4.  ,  0.4 ,  0.3 ,  0.37,  0.35],
       [ 1.  ,  6.  ,  0.45,  0.3 ,  0.36,  0.5 ],
       [ 1.  ,  8.  ,  0.45,  0.25,  0.34,  0.5 ],
       [ 1.5 ,  1.  ,  0.15,  0.35,  0.25,  0.25],
       [ 1.5 ,  2.  ,  0.35,  0.35,  0.26,  0.25],
       [ 1.5 ,  4.  ,  0.4 ,  0.3 ,  0.33,  0.35],
       [ 1.5 ,  6.  ,  0.45,  0.3 ,  0.34,  0.5 ],
       [ 1.5 ,  8.  ,  0.45,  0.25,  0.33,  0.5 ],
       [ 2.  ,  1.  ,  0.25,  0.5 ,  0.28,  0.25],
       [ 2.  ,  2.  ,  0.35,  0.45,  0.21,  0.25],
       [ 2.  ,  4.  ,  0.4 ,  0.45,  0.25,  0.35],
       [ 2.  ,  6.  ,  0.45,  0.4 ,  0.26,  0.5 ],
       [ 2.  ,  8.  ,  0.45,  0.35,  0.26,  0.5 ]]),
    columns=['T1', 'S', 'βaΔ', 'βaa', 'βav', 'βm'])

def ImportETABS(title, description, strength, path, location, soil_class, return_period, frame_type):
    project = Project()
    xl_workbook = pd.ExcelFile(path)
    setattr(project, 'title_text', title)
    setattr(project, 'description_text', description)
    setattr(project, 'rarity', 1.0/return_period)
    project.save()

    # Get the fundamental frequencies from the ~Modal Participating Mass Ratios~
    # tab:
    sheet = munge_data_frame(
        xl_workbook.parse("Modal Participating Mass Ratios", 
                          skiprows=(1)))
    Tx = list(sheet.sort_values('UX', ascending=False)['Period'])[0]
    Ty = list(sheet.sort_values('UY', ascending=False)['Period'])[0]

    # Create the hazard curve, using the X period:
    nzs = NZ_Standard_Curve(location=Location.objects.get(location=location),
                            soil_class = soil_class,
                            period = Tx)
    nzs.save()
    hazard = IM(flavour = IM_Types.objects.get(pk=IM_TYPE_NZS), nzs = nzs)
    hazard.save()
    project.IM = hazard
    project.save()

    # Figure out the design IM:
    guess = hazard.model().plot_max()
    design_im = fsolve(lambda x: 
                       hazard.model().getlambda(x[0]) - 1.0/return_period,
                       guess)[0]
    print("Design IM: {}".format(design_im))

    # Get the names and heights of the stories from the ~Diaphragm Center of Mass
    # Displa~ tab:
    sheet = munge_data_frame(xl_workbook.parse(
        "Diaphragm Center of Mass Displa",
        skiprows=1))
    height_df = sheet.loc[lambda x: 
                          x['Load Case/Combo'] == 'Dead'].\
                          filter(['Story', 'Z']).sort_values('Z')
    height_df = height_df.rename(index=str, columns={'Z': 'Height'})

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
    drifts = sheet.loc[
        lambda x: map(lambda a: a == 'MRS EQX mu=4 Max' or 
                      a == 'MRS EQY mu=4 Max', 
                      x['Load Case/Combo'])].filter(
                          ['Story', 'Direction', 'Drift'])
    drifts_df = pd.DataFrame(columns=['Story', 'X', 'Y'])
    for story in height_df['Story'].values:
        x = drifts.loc[lambda x: map(lambda a, b: a == story and\
                                     b == 'X', x['Story'], x['Direction'])
        ]['Drift'].values[0]
        y = drifts.loc[lambda x: map(lambda a, b: a == story and\
                                     b == 'Y', x['Story'], x['Direction'])
        ]['Drift'].values[0]
        drifts_df = drifts_df.append(
            pd.DataFrame(data=[[story, x, y]],
                         columns=['Story', 'X', 'Y']))
    
    # Get the acceleration at each story from the ~Story Drifts~ tab:
    sheet = munge_data_frame(xl_workbook.parse(
        "Story Accelerations", 
        skiprows=1))
    accels = sheet.loc[
        lambda x: map(lambda a: a == 'MRS EQX mu=4 Max' or 
                      a == 'MRS EQY mu=4 Max', 
                      x['Load Case/Combo'])].filter(['Story', 'UX', 'UY'])
    accels_df = pd.DataFrame(columns=['Story', 'X', 'Y'])
    
    for story in height_df['Story'].values:
        x = accels.loc[lambda x: x['Story'] == story]['UX'].values[0]
        y = accels.loc[lambda x: x['Story'] == story]['UY'].values[0]
        
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
    drift_coefficients = get_correction_factors(num_floors,
                                                frame_type,
                                                "Story Drift Ratio")
    accel_coefficients = get_correction_factors(num_floors,
                                                frame_type, 
                                                "Floor Acceleration")
    for im in im_range:
        # Calculate the linear (uncorrected) values for
        # each demand:
        scale = im / design_im
        
        # Get dispersion factors:
        dispersion = get_dispersion(Tx, scale)
        dispersions = dispersions.append(
            pd.DataFrame(data=[[im, 
                                float(dispersion[0]),
                                float(dispersion[1]),
                                float(dispersion[2])]],
                         columns=['IM', 'βsd', 'βfa', 'βfv']),
            ignore_index=True)

    for story in height_df['Story']:
        for im in im_range:
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
                k = sum(([1, Tx, s, h/H, (h/H)**2, (h/H)**3] * drift_coefficients).values[0])
                dx = dx * np.exp(k)
                #
                # For Y drift
                k = sum(([1, Ty, s, h/H, (h/H)**2, (h/H)**3] * drift_coefficients).values[0])
                dy = dy * np.exp(k)
                #
                # For X acceleration
                k = sum(([1, Tx, s, h/H, (h/H)**2, (h/H)**3] * accel_coefficients).values[0])
                ax = ax * np.exp(k)
                #
                # For Y acceleration
                k = sum(([1, Ty, s, h/H, (h/H)**2, (h/H)**3] * accel_coefficients).values[0])
                ay = ay * np.exp(k)
            # Add the data for this story and IM to the table:
            curves = curves.append(pd.DataFrame(data=[[story, im, dx, dy, ax, ay]], columns=['Story', 'IM', 'Drift_X', 'Drift_Y', 'Accel_X', 'Accel_Y']), ignore_index=True)

    # Ground level acceleration matches the IM:
    level = Level.objects.get(level=0, project=project)
    edp = EDP(project=project, level=level, type='A')
    edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
    edp.interpolation_method = Interpolation_Method.objects.get(method_text="Linear")
    edp.save()
    for im in im_range:
        accel = im                                   
        dispersion = dispersions.loc[lambda x: x['IM']==im]['βsd']
        EDP_Point(demand=edp, im=im, median_x=accel, sd_ln_x=dispersion).save()

    # Add drift and accelerations for above-ground levels:    
    for l in range(1, num_floors+1):                               
        level = Level.objects.get(level=l, project=project)
        edp = EDP(project=project, level=level, type='D')
        edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
        edp.interpolation_method = Interpolation_Method.objects.get(method_text="Linear")
        edp.save()
        for im in im_range:
            drift = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Drift_X'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βsd']
            EDP_Point(demand=edp, im=im, median_x=drift, sd_ln_x=dispersion).save()
    
        edp = EDP(project=project, level=level, type='A')
        edp.flavour = EDP_Flavours.objects.get(pk=EDP_FLAVOUR_USERDEF);
        edp.interpolation_method = Interpolation_Method.objects.get(method_text="Linear")
        edp.save()
        for im in im_range:
            accel = float(curves.loc[
                lambda x: map(
                    lambda a, b: a==im and b=='Story1', 
                    x['IM'], x['Story']
                )]['Accel_X'])
            dispersion = dispersions.loc[lambda x: x['IM']==im]['βfa']
            EDP_Point(demand=edp, im=im, median_x=accel, sd_ln_x=dispersion).save()
    print(curves)
    return project

    


from  .models import *
import pandas as pd
import numpy as np
from  .models import *
from functools import reduce
import io
import pickle

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

def ETABS_preprocess(title, description,
                     constant_R, constant_I, constant_Omega,
                     file_data, file_path,
                     location, soil_class, return_period,
                     frame_type_x, frame_type_y, user_id):
    preprocess_data = ETABS_Preprocess()
    preprocess_data.title = title
    preprocess_data.description = description
    preprocess_data.constant_R = constant_R
    preprocess_data.constant_I = constant_I
    preprocess_data.constant_Omega = constant_Omega
    preprocess_data.location = location
    preprocess_data.soil_class = soil_class
    preprocess_data.return_period = return_period
    preprocess_data.frame_type_x = frame_type_x
    preprocess_data.frame_type_y = frame_type_y
    preprocess_data.file_name = file_path
    preprocess_data.file_contents = file_data

    start_time = time.time()
    project = Project()
    xl_workbook = pd.ExcelFile(io.BytesIO(file_data))
    sheet  = xl_workbook.parse("Mass Summary by Diaphragm", skiprows=(1))
    msby = munge_data_frame(sheet)
    weight_units = sheet['Mass X'][0]
    preprocess_data.weight_units = weight_units
    if weight_units == 'kg':
        weight_mutliplier = 1.0
    elif weight_units == 'N-s²/mm':
        weight_mutliplier = 1000.0
    else:
        preprocess_data.weight_units_message = "Units not recognised; assuming they are equivalent to kg"
        weight_mutliplier = 1.0
        
    preprocess_data.weight = msby['Mass X'].sum() * weight_mutliplier
    preprocess_data.min_yield_strength = round(1.5 * preprocess_data.weight) / \
                                         (preprocess_data.constant_R /
                                          preprocess_data.constant_I)
    preprocess_data.max_yield_strength = round(preprocess_data.constant_Omega *
                                          preprocess_data.weight) / \
                                          (preprocess_data.constant_R / \
                                           preprocess_data.constant_I)
    preprocess_data.yield_strength = round((preprocess_data.min_yield_strength + 
                                      preprocess_data.max_yield_strength) / 2)
    
    
    sheet  = xl_workbook.parse("Modal Participating Mass Ratios", skiprows=(1))
    preprocess_data.period_units = sheet['Period'][0]
    if preprocess_data.period_units != 'sec':
        preprocess_data.period_units_message = "WebSLAT doesn't recognise this units string. If these values are not in seconds, your results will be incorrect."

    mpms = munge_data_frame(sheet)

    cases = set(mpms['Case'])
    period_choices = []
    for case in cases:
        for row in mpms[mpms['Case'] == case].iterrows():
            mode = int(row[1]['Mode'])
            period =  float(row[1]['Period'])
            period_choices.append(
                { 'case' : case,
                  'mode': mode,
                  'period': period,
                  'ux': row[1]['UX'], 
                  'uy': row[1]['UY']})
        period_choices.append(
            { 'case' : "",
              'mode': "",
              'period': 'Manual',
              'ux': np.nan,
              'uy': np.nan})
    preprocess_data.period_choices = pickle.dumps(period_choices)
    sheet = xl_workbook.parse("Diaphragm Center of Mass Displa",
                              skiprows=1)
    height_unit = sheet['Z'][0]
    preprocess_data.height_units = height_unit
    if preprocess_data.height_units != 'm' and preprocess_data.height_units != 'mm':
        preprocess_data.height_units_message = "WebSLAT doesn't recognise this units string. If these values are not in metres, your results will be incorrect."
        
    dcomd = munge_data_frame(sheet)
    height_df = dcomd.loc[lambda x: 
                          x['Load Case/Combo'] == 'Dead'].\
                          filter(['Story', 'Z']).sort_values('Z')
    height_df = height_df.rename(index=str, columns={'Z': 'Height'})
    heights = []
    for level in height_df.iterrows():
        heights.append({'Story': level[1]['Story'],
                        'Height': level[1]['Height']})
    preprocess_data.stories = pickle.dumps(heights)

    sd = munge_data_frame(xl_workbook.parse(
        "Story Drifts", 
        skiprows=1))
    drift_choices = list(set(sd['Load Case/Combo']))
    drift_choices.sort()
    preprocess_data.drift_choices = pickle.dumps(drift_choices)

    sheet = xl_workbook.parse("Story Accelerations", 
                              skiprows=1)

    preprocess_data.accel_units_x = sheet['UX'][0]
    preprocess_data.accel_units_y = sheet['UY'][0]
    if preprocess_data.accel_units_x != 'mm/sec²' or \
       preprocess_data.accel_units_y != 'mm/sec²':
        preprocess_data.accel_units_message = "WebSLAT doesn't recognise these units strings. If these values are not in mm/sec², your results will be incorrect."
    sa = munge_data_frame(sheet)
    accel_choices = list(set(sa['Load Case/Combo']))
    accel_choices.sort()
    preprocess_data.accel_choices = pickle.dumps(accel_choices)
    end_time = time.time()
    
    preprocess_data.save()
    eprint("Load Time: {}".format(end_time - start_time))
        
    return preprocess_data.id
    

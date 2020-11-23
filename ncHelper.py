#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 16:13:53 2020
Run on distributed model of Gisburn Forest 
@author: jimmy
"""
import os
from datetime import datetime
import xarray as xr 
import pandas as pd 
import numpy as np 
from tqdm import tqdm 

#%% functions 
def timestamp2dt(strings,delimiter='-',reverse=False):
    """Parse a list of strings into python datetime instances. Format of
    dates can be yyyy-mm-dd 00:00:00.0000 or dd-mm-yyyy 00:00:00.0000. 
    
    Parameters
    ----------
    strings: list
        Each list entry is a string which defines the date. The format of
        the string is flexible. 
    delimiter: string, optional
        Default == "-" (dash). Character which seperates the date numbers. 
    reverse: bool, optional
        if format is dd-mm-yyyy set reverse = True
    
    Returns
    ----------
    serial_num: list
        Each entry in list is python datetime instance. 
    """
    #go through each date string and convert to datetime, doesnt deal with american times
    dates = [datetime.now()] * len(strings)
    yr_idx = 0 # index of the year in string 
    dy_idx = 2 # index of the day in string 
    if reverse:
        yr_idx = 2
        dy_idx = 0 # nb: month should always be 1
        
    for i in range(len(strings)):
        entry = strings[i].split()
        temp = entry[0].split(delimiter)
        time = entry[1].split(':')
        try:
            second = time[2].split('.')[0] # not always possible to get seconds 
        except:
            second = 0 
        dates[i] = datetime(int(temp[yr_idx]),
                             int(temp[1]),
                             int(temp[dy_idx]),
                             int(time[0]),
                             int(time[1]),
                             int(second))
    return dates 

#%% pepare weather data 
def cosmos2nc(fname, lat, long, elev, nhru):   
    """
    Parse COSMOS data into xrray dataset. Returns the forcing file needed for
    running SUMMA. See here for further details:
    https://github.com/NCAR/summa/blob/master/docs/input_output/SUMMA_input.md
    
    note: adapt this for generic weather data? 

    Parameters
    ----------
    fname : string
        Full path to cosmos weather file.
    lat : float 
        Latitude of cosmos station.
    long : float 
        Longitude of cosmos station 
    elev : float
        Elevaion (mOAD) of cosmos station  
    nhru : int
        Number of HRUs in the study, we assume that fluxes are the same across 
        the entire catchment here (could improve on this in future)

    Returns
    -------
    DataSet: xarray dataset 
        Data organised into the xarray format and converted in the correct 
        units needed by SUMMA  

    """
    
    df = pd.read_csv(fname) # read in pandas dataframe 
    
    # def SHcalc(t,pa,rh):
    #     #compute Specific humidity
    #     #equation taken from here: 
    #     # https://earthscience.stackexchange.com/questions/5076/how-to-calculate-specific-humidity-with-relative-humidity-temperature-and-pres
    #     T0 = 273.15
    #     Rv = 461 
    #     Rd = 287
    #     es0 = 0.6113
    #     Lv = 2.5e6
    #     T = t+273.15
    #     es = es0 * np.exp((Lv/Rv) * ((1/T0)-(1/T))) #saturation vapor pressure
    #     RH = rh/100 # fractional relative humidity 
    #     p = pa*100 # transfer hPa into Pa
    #     e = es*RH
    #     w = (e*Rd)/(Rv*(p-e))
    #     q = w/(w+1)
    #     return q 
    
    def SHcalc(temp,pa,rh):
        #from https://cran.r-project.org/web/packages/humidity/vignettes/humidity-measures.html 
        Tdp = (temp - ((100-rh)/5))+273.16 # dew point (approx) in kelvin
        p = pa*100 # transfer hPa into Pa
        a = 17.2693882
        b = 35.86
        tmp = (a*(Tdp-273.16))/(Tdp-b)
        e = 6.1078*np.exp(tmp)
        q = 0.622/(p - (0.378*e))
        return q
    
    #'fix' data by interpolating missing values 
    columns = ['PRECIP','TA','SWIN','LWIN','Q','RH','PA','WS']
    x = np.arange(0,len(df))
    for c in columns:
        idxnan = df[c] == -9999 # nan values 
        idxval = df[c] != -9999
        xnan = x[idxnan]
        if len(xnan)>0: # if nan values present 
            xp = x[idxval]
            yp = df[c].values[idxval]
            ynan = np.interp(xnan,xp,yp)
            df.loc[idxnan,c] = ynan 
    
    #min SW values must be capped at -1 
    idx = df['SWIN'] < -1 
    df.loc[idx,'SWIN'] = -0.99 
    
    #coordinates 
    hru = np.arange(0,nhru)+1 # hru id 
    times = timestamp2dt(df['DATE_TIME'].values)
    coords = {'time':times}
    
    tdelta = times[1] - times[0] # time delta object 
    tstep = abs(tdelta.seconds) 
    
    sh = SHcalc(df['TA'].values, # compute sensitive humidity 
                df['PA'].values,
                df['RH'].values)
    
    # weather arrays, arrays which are nsteps and nhru in dimensions 
    # (assumes fluxes are valid across the catchment)    
    pptrate = np.zeros((len(times),len(hru)))
    airtemp = np.zeros((len(times),len(hru)))
    SWRadAtm  = np.zeros((len(times),len(hru)))
    LWRadAtm = np.zeros((len(times),len(hru)))
    spechum = np.zeros((len(times),len(hru)))
    airpres = np.zeros((len(times),len(hru)))
    windspd = np.zeros((len(times),len(hru)))
    
    for i in tqdm(range(len(hru)),ncols=100,desc='prepping'):
        pptrate[:,i] = df['PRECIP'].values/tstep # precipiation rate in kg/m2/s
        airtemp[:,i] = df['TA'].values + 273.15 #(temp in kelvin )
        SWRadAtm[:,i] = df['SWIN'].values 
        LWRadAtm[:,i] = df['LWIN'].values 
        spechum[:,i] = sh
        airpres[:,i] = df['PA'].values * 100 #Pa
        windspd[:,i] = df['WS'].values # m/s
        
    data = {'data_step':float(tstep),
            'lat':(('hru'),lat),
            'lon':(('hru'),long),
            'hruId':(('hru'),hru),
            'pptrate':(('time','hru'),pptrate),
            'airtemp':(('time','hru'),airtemp),
            'SWRadAtm':(('time','hru'),SWRadAtm),
            'LWRadAtm':(('time','hru'),LWRadAtm),
            'spechum':(('time','hru'),spechum),
            'airpres':(('time','hru'),airpres),
            'windspd':(('time','hru'),windspd)}
    
    weather = xr.Dataset(data,coords=coords) # xarray dataset 
    weather.assign_attrs({'Author':os.getlogin()})
    
    return weather #nb: use weather.to_netcdf to write out in netcdf format 

#%% prepare basin attributes 
def attributes2nc(data):
    """
    Prepare basin attributes file 

    Parameters
    ----------
    data : dict, pandas dataframe 
        Columns (must be same length) refering to basin parameters, see here: 
        https://github.com/NCAR/summa/blob/master/docs/input_output/SUMMA_input.md

    Raises
    ------
    Exception
        If a column is missing.

    Returns
    -------
    DataSet: xarray dataset 
        Data organised into the xarray format read for SUMMA 

    """
    
    columns = ['hruId',
               'gruId',          
               'hru2gruId',       
               'downHRUindex',    
               'longitude',      
               'latitude',       
               'elevation',      
               'HRUarea',         
               'tan_slope',      
               'contourLength',   
               'slopeTypeIndex',  
               'soilTypeIndex',   
               'vegTypeIndex',   
               'mHeight']
  
    missing = []
    for c in columns:
        # print(c)
        if c not in data.keys():
            missing.append(c)
    
    if len(missing)>0:
        for c in missing:
            print('Column "%s" is missing from basin attributes!'%c)
        raise Exception('Missing columns found in basin attributes')
    
    netc = {'hruId':(('hru'), data['hruId']),
            'gruId':(('gru'), data['gruId']),
            'hru2gruId':(('hru'), data['hru2gruId']),
            'downHRUindex':(('hru'), data['downHRUindex']),
            'longitude':(('hru'), data['longitude']),
            'latitude':(('hru'), data['latitude']),
            'elevation':(('hru'), data['elevation']), 
            'HRUarea':(('hru'), data['HRUarea']),
            'tan_slope':(('hru'), data['tan_slope']),
            'contourLength':(('hru'), data['contourLength']),
            'slopeTypeIndex':(('hru'), data['slopeTypeIndex']),
            'soilTypeIndex':(('hru'), data['soilTypeIndex']), 
            'vegTypeIndex':(('hru'), data['vegTypeIndex']), 
            'mHeight':(('hru'), data['mHeight'])}
    
    attributes = xr.Dataset(netc)
    attributes.assign_attrs({'Author':os.getlogin()})
    
    return attributes


#%% init conditions file - this will be most tricky 
def initCond2nc(data={}, nhru=1):
    """Creates initial conditions for SUMMA. Calling function returns dataset
    with default values. 

    Parameters
    ----------
    data : dict, optional
        Dictionary containing the data arrays needed for SUMMA. The default is {}.
    nhru : int, optional
        Number of HRUs. 1.

    Returns
    -------
    DataSet: xarray dataset 
        Data organised into the xarray format needed by SUMMA  

    """
    
    columns = ['scalarCanopyLiq', 'scalarCanairTemp', 'scalarSnowAlbedo', 
               'scalarSnowDepth', 'scalarCanopyIce', 'scalarSfcMeltPond', 
               'scalarAquiferStorage', 'scalarSWE', 'scalarCanopyTemp', 
               'mLayerMatricHead', 'iLayerHeight', 'mLayerTemp', 
               'mLayerVolFracLiq', 'mLayerVolFracIce','mLayerDepth', 
               'dt_init', 'nSnow', 'nSoil'] #all the parameters needed by SUMMA 
    
    midTotoC = ['mLayerTemp','mLayerVolFracLiq','mLayerVolFracIce',
                'mLayerDepth'] # parameters which discretise by layer depth
    midSoilC = ['mLayerMatricHead'] # parameters which discretise by mid soil depth
    ifcTotoC = ['iLayerHeight'] # parameters which discretise by layer height 
    
    if not isinstance(nhru, int):
        raise ValueError('Number of HRUs needs to be an integer')
    
    def val1d(x,dtype=float): # creat default array 
        return np.full((1,nhru),x, dtype=dtype)
    
    def val2d(x, xdim, dtype=float):
        return np.full((xdim,nhru),x,dtype=dtype)
    
    ## default layering ## 
    if 'mLayerDepth' not in data.keys():
        tmp = np.asarray([0.025, 0.075, 0.15, 0.25, 0.5, 0.5, 1, 1.5])#m
        layerDepth = np.zeros((len(tmp),nhru),dtype=float)
        for i in range(nhru):
            layerDepth[:,i] = tmp
        data['mLayerDepth'] = layerDepth
    else:
        layerDepth = data['mLayerDepth']
        
    if 'iLayerHeight' not in data.keys(): # calculate automatically 
        nlayers = layerDepth.shape[0]+1
        tmp = np.zeros(nlayers)
        r = 0
        for i in range(nlayers-1):
            r += layerDepth[:,0][i]
            tmp[i+1] = r 
       # print(tmp)
        layerHeight = np.zeros((nlayers,nhru),dtype=float)
        for i in range(nhru):
            layerHeight[:,i] = tmp
        data['iLayerHeight'] = layerHeight
    else:
        layerHeight = data['iLayerHeight']
    

        
    #setup default values (feel free to edit this)
    defaults = {'scalarCanopyLiq'     :0,
                'scalarCanairTemp'    :286,
                'scalarSnowAlbedo'    :0.16,
                'scalarSnowDepth'     :0,
                'scalarCanopyIce'     :0,
                'scalarSfcMeltPond'   :0,
                'scalarAquiferStorage':0,
                'scalarSWE'           :0,
                'scalarCanopyTemp'    :286,
                'mLayerMatricHead'    :-1,
                'iLayerHeight'        :layerHeight,
                'mLayerTemp'          :273,
                'mLayerVolFracLiq'    :1,
                'mLayerVolFracIce'    :0.1,
                'mLayerDepth'         :layerDepth,
                'dt_init'             :1800,
                'nSnow'               :0,
                'nSoil'               :layerHeight.shape[0]}
            
    netc = {}
    for c in columns:
        # define state dimensions 
        d = 1
        if c in midTotoC:
            dim = ('midToto', 'hru')
            d = 2
            xdim = layerDepth.shape[0] 
        elif c in midSoilC:
            dim = ('midSoil', 'hru')
            d = 2
            xdim = layerDepth.shape[0]
        elif c in ifcTotoC:
            dim = ('ifcToto', 'hru')
            d = 2
            xdim = layerHeight.shape[0]
        else:
            dim = ('scalarv', 'hru')
                
        if c not in data.keys():
            #then defualt to a value 
            if c[0] == 'n':
                dtype=int
            else:
                dtype=float
            if d == 1:    
                arr = val1d(defaults[c], dtype)
            else:
                arr = val2d(defaults[c],xdim,dtype)
        else:
            arr = data[c]
            
        #add to dictionary used as input into xarray dataset
        netc[c] = (dim,arr)
  
    initCond = xr.Dataset(netc)
    initCond.assign_attrs({'Author':os.getlogin()})
    
    return initCond

#%% prepare trial param file, no need to do much here, basically an empty file 
def emptyTrailParam(nhru=1):
    """Return empty trail parameters DataSet

    Parameters
    ----------
    nhru : int, optional
        Number of HRUs. The default is 1.

    """
    hru = np.arange(0,nhru)+1
    data = {'hruId':(('hru'),hru)}
    trailParam = xr.Dataset(data)
    return trailParam

#%% nb: how jimmy originally created initial condition file 
    # data = {'scalarCanopyLiq'     :(('scalarv', 'hru'), val(0)),
    #         'scalarCanairTemp'    :(('scalarv', 'hru'), val(15.73+273)),
    #         'scalarSnowAlbedo'    :(('scalarv', 'hru'), val(0)),
    #         'scalarSnowDepth'     :(('scalarv', 'hru'), val(1)),
    #         'scalarCanopyIce'     :(('scalarv', 'hru'), val(0)),
    #         'scalarSfcMeltPond'   :(('scalarv', 'hru'), val(0)),
    #         'scalarAquiferStorage':(('scalarv', 'hru'), val(1)),
    #         'scalarSWE'           :(('scalarv', 'hru'), val(0)),
    #         'scalarCanopyTemp'    :(('scalarv', 'hru'), val(15.73+273)),
    #         'mLayerMatricHead'    :(('midSoil', 'hru'), np.ones((8,1))*-1),
    #         'iLayerHeight'        :(('ifcToto', 'hru'), layerHeight),
    #         'mLayerTemp'          :(('midToto', 'hru'), np.ones((8,1))*273.15),
    #         'mLayerVolFracLiq'    :(('midToto', 'hru'), np.ones((8,1))*0.5),
    #         'mLayerVolFracIce'    :(('midToto', 'hru'), np.ones((8,1))*0.1),
    #         'mLayerDepth'         :(('midToto', 'hru'), layerDepth),
    #         'dt_init'             :(('scalarv', 'hru'), val(30*60)),
    #         'nSnow'               :(('scalarv', 'hru'), val(1,dtype=int)),
    #         'nSoil'               :(('scalarv', 'hru'), val(7,dtype=int))}
    
#%% uk landcover to usgs table lookup 
# lookup = {'Deciduous woodland':(1,11)}
lookup = {'1':13,#Deciduous woodland
          '2':11,#Coniferous woodland
          '3':4,
          '4':5,
          '5':7,
          '6':8,
          '7':9,
          '8':17,
          '9':8,
          '10':9,
          '11':17,
          '12':19,
          '13':16,
          '14':16}

def UKCEH2NOAH(coverId):
    out = [0]*len(coverId)
    for i in range(len(coverId)):
        li = str(int(coverId[i]))
        out[i] = lookup[li]
    return out 
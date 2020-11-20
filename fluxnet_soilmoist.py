'''
Read site soil moisture fields form FLUXNET-FULLSET '.csv' file and save it into '.nc' file
Todo: Transform into function; add Quality flag columns;
@aelkouk 11202020

'''
import numpy as np
import xarray as xr
import pandas as pd
import os

flx_fullset_csv = '../0_data/FLX_NL-Loo_FLUXNET2015_FULLSET_HH_1996-2014_1-4.csv'
df = pd.read_csv(flx_fullset_csv)
datevar = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
swc = np.full((3, datevar.size), -9999.)
for i in range(3):
    swc_lv1 = df['SWC_F_MDS_{}'.format(i+1)].values
    swc[i] = swc_lv1

ds = xr.Dataset(data_vars={'SWC':(('layer', 'time'), swc, {'long_name':'Soil water content',
    'missing_value':-9999., 'units':'[%]'})},
    coords={'layer':[1,2,3], 'time':datevar.values})
    #{'long_name':'Soil layer index, 1 is shallowest'}

outnc = 'SWC_'+os.path.basename(flx_fullset_csv).replace('.csv', '.nc')
ds.to_netcdf(outnc)





#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 17:31:25 2020
read and write soil parameters for SUMMA 
@author: jimmy
"""
import pandas as pd 
def parseSoilTBL(fname):
# fname = '/home/jimmy/phd/Extra/HydroCourse/Week03/code/pbhmCourse_student/2_process_based_modelling/settings/plumber/UniMich/SOILPARM.TBL'
    fh = open(fname,'r')
    lines = fh.readlines()
    fh.close()
    
    header_lines = []
    model_type = [] # eg rosetta or stars 
    ntypes = []
    data = {}
    
    for i in range(len(lines)):
        l = lines[i].strip()
        if l == 'Soil Parameters':
            header_lines.append(i)
            model_type.append(lines[i+1].strip())
            tmp = lines[i+2].strip().split()[0]
            ntypes.append(int(tmp.split(',')[0]))
            d = {}
            headers = lines[i+2].strip().split()
    
            for h in headers:
                d[h] = []
            
            for j in range(ntypes[-1]):
                ln = i+3+j 
                info = lines[ln].split(',')
                if model_type[-1]=='ROSETTA': #special case in rosetta frame work 
                    info = lines[ln].split()
                    if len(info) != len(headers):
                        delta = len(info) - len(headers)
                        for k in range(delta):
                            info[len(headers)-1] += ' ' 
                            info[len(headers)-1] += info[len(headers)+k] 
                
                for k in range(len(headers)):
                    h = headers[k]
                    tmp = info[k]
                    if tmp.isdigit():
                        val = int(tmp)
                    else:
                        try:
                            val = float(tmp)
                        except ValueError:
                            val = tmp.strip()
                    d[h].append(val)
            df = pd.DataFrame()
            for h in headers:
                df[h] = d[h]
            data[model_type[-1]]=df 
    
    return data 

def writeTbl(fname,data):
    fh = open(fname,'w')
    tables = ['STAS', 'STAS-RUC', 'ROSETTA']
    
    for t in tables: 
        df = data[t]
        fh.write('Soil Parameters\n')
        fh.write('%s\n'%t)
        #write table headers 
        for key in df.keys():
            fh.write('{:>16} '.format(key))
        fh.write('\n')
        for i in range(len(df)):
            c = 0 
            for key in df.keys():
                c+=1 
                if c == 1:
                    fmt = '{:<16d},'
                elif c == len(df.keys()):
                    fmt = ' {:<16}'
                else:
                    fmt = '{:>16.8e},'
                fh.write(fmt.format(df[key][i]))
            fh.write('\n')
    fh.close()
       
import sys
sys.path.insert(0, '..')
import os
from traceback import print_exc
from pprint import pprint
from sir.sir import SIR
from sir.ensemblesir import EnsembleSIR
from sir.easir import EnsembleAdjustmentSIR
from sir.basssir import BassSIR
from sir.pfsir import ParticleSIR
from readparams import read_params
from time import time
from numpy import mean

def write_file(path, year, sir, out_str):
    directory = 'outs%s/%s' % (year, path)
    if not os.path.exists(directory): os.makedirs(directory)

    with open('%s/%s_%s_en_out' % (directory, ens, year), 'ab') as f:
        f.write('%s\n' % out_str)
    with open('%s/%s_%s_en_out_par' % (directory, ens, year), 'ab') as f:
        f.write('%f,%f\n' % (mean(sir.alphas), mean(sir.betas)))
    return sir.score

def sim_sir():
    params = read_params('../data/params/params2013-14-sir.csv')
    sir = SIR(params)

    sir.predict()
    print ','.join(map(str, sir.Is)) 
    print sir.scores
    return sir.scores

def sim_sir_filtered():
    params = read_params('../data/params/params.csv')
    params['filtering'] = True
    sir = SIR(params)

    sir.predict_with_filter()

    print ','.join(map(str, sir.Is))
    pprint(sir.scores)
    return sir.score

def sim_ensir_filtered(ens, year, cov_type, params=False):
    if not params:
        params = read_params('../data/params/params%s.csv' % year)
    params['filtering'] = True
    params['filter_type'] = 'EnKF'
    sir = EnsembleSIR(ens, params)

    sir.filter.cov_type = cov_type
    sir.predict_with_filter()
 
    out_str = ','.join(map(str, sir.IS))
    path = 'centered_enkf' if cov_type == 'c' else 'uncentered_enkf'
    pprint(sir.scores)
    write_file(path, year, sir, out_str)
    return sir.score

def sim_basssir_filtered(ens, year, cov_type, params=None):
    if not params:
        params = read_params('../data/params/params%s.csv' % year)
    params['filtering'] = True
    params['time_varying'] = False
    sir = BassSIR(ens, params)

    sir.err_bnd = 0.00001
    sir.filter.cov_type = cov_type
    sir.predict_with_filter()
 
    out_str = ','.join(map(str, sir.IS))
    print out_str
    pprint(sir.scores)
    path = 'centered_bass' if cov_type == 'c' else 'uncentered_bass'

    pprint(sir.scores)
    write_file(path, year, sir, out_str)
    return sir.score

def sim_easir_filtered(ens, year, cov_type, params):
    if not params:
        params = read_params('../data/params/params%s.csv' % year)
    params['filtering'] = True
    params['time_varying'] = False
    sir = EnsembleAdjustmentSIR(ens, params)

    sir.filter.cov_type = cov_type
    sir.predict_with_filter()
 
    out_str = ','.join(map(str, sir.IS))
    path = 'centered_eakf' if cov_type == 'c' else 'uncentered_eakf'
    write_file(path, year, sir, out_str)
    pprint(sir.scores)
    return sir.score

def sim_psir_filtered(ens, year, params=None):
    if not params:
        params = read_params('../data/params/params%s.csv' % year)
    params['filtering'] = True
    params['time_varying'] = False
    sir = ParticleSIR(ens, params)

    sir.predict_with_filter()
 
    out_str = ','.join(map(str, sir.IS))
    print out_str
    pprint(sir.scores)
    path = 'centered_pkf_set1'
    write_file(path, year, sir, out_str)

###### Main function #####
if __name__ == '__main__':
    s = time()

    for year in ['2011-12', '2012-13', '2013-14', '2014-15']:     
        for i in xrange(50):
            for ens in xrange(500, 501, 50):
                try:
                    sim_ensir_filtered(ens, year, 'c', params)
                    sim_ensir_filtered(ens, year, 'u', params)
                except:
                    print_exc() 
        for i in xrange(50):
            for ens in xrange(500, 501, 50):
                try:
                    sim_psir_filtered(ens, year, params)
                except:
                    from traceback import print_exc
                    print_exc()
        for i in xrange(50):
            for ens in xrange(500, 501, 50):
                try:
                    sim_easir_filtered(ens, year, 'c', params)
                    sim_easir_filtered(ens, year, 'u', params)
                except:
                    from traceback import print_exc
                    print_exc()
                    pass

        params = None
        for ens in xrange(50, 451, 50):
            for i in xrange(50):
                try:
                    sim_basssir_filtered(ens, year, 'c', params)
                    sim_basssir_filtered(ens, year, 'u', params)
                except:
                    from traceback import print_exc
                    print_exc()
                    pass

    print '%f seconds cost' % (time() - s)

import sys
sys.path.append('..')
from kalmanfilter import KalmanFilter
from numpy import cov, array
from common.linalg import uncentered_cov 

class EnsembleKalmanFilter(KalmanFilter):

    def __init__(self, num_enbs, num_states, num_obs, A, B, V, W, P=None):
        super(EnsembleKalmanFilter, self).__init__(num_states, num_obs, 
                                                   A, B, V, W, P)
        self.weights = array([1.0/num_enbs] * num_enbs)
        self.num_enbs = num_enbs

        self.cov_type = None

    def fit(self, x, P=None):
        self.x_prior = x.copy()
    
        if P:
            self.P_prior = P
        else:
            if self.cov_type == 'c':
                self.P_prior = cov(self.x_prior)        
            elif self.cov_type == 'u':
                self.P_prior = uncentered_cov(x)
            else:
                raise Exception('Covariance type errors')

import sys
sys.path.insert(0, '..')
from sir import SIR
from common.maths import as_array, as_matrix, data_type, init_weights
from common.stats import RSS, MSPE, RMSE
from numpy.random import normal, uniform
from numpy import *
from filtering.ensemblekalmanfilter import EnsembleKalmanFilter


class EnsembleAdjustmentSIR(SIR):
    
    def __init__(self, num_enbs, params):
        self.num_enbs = num_enbs
        super(EnsembleAdjustmentSIR, self).__init__(params)

        del self.alpha
        del self.beta

        self.inflate = 1.001
        self.current_Is = uniform(0, self.i * 2, num_enbs)
        self.current_Ss = ones(num_enbs) - self.current_Is
        self.alphas = uniform(0, .5, num_enbs)
        self.betas = uniform(0, .5, num_enbs)

        self.weights = [as_array([1.0/num_enbs] * num_enbs)]

        for i in xrange(num_enbs):
            if self.alphas[i] < self.betas[i]:
                self.alphas[i], self.betas[i] = self.betas[i], self.alphas[i]  
        self.Is = [self.current_Is.tolist()]
        self.Ss = [self.current_Ss.tolist()]

    def update_states(self):
        for j in xrange(self.num_enbs):
            s = self.current_Ss[j]
            i = self.current_Is[j]
            s += self._delta_s(self.current_Ss[j], self.current_Is[j], 
                               self.alphas[j])
            i += self._delta_i(self.current_Ss[j], self.current_Is[j], 
                               self.alphas[j], self.betas[j])

            s = self.check_bounds(s)
            i = self.check_bounds(i)

            self.current_Is[j] = i
            self.current_Ss[j] = s

        self.Is.append(self.current_Is.tolist())
        self.Ss.append(self.current_Ss.tolist())

    def _init_filter(self):
        num_states = 4
        num_obs = 1

        A = None
        B = None

        V = as_matrix(eye(num_states, dtype=data_type)) * 0.00001
        W = as_matrix(eye(num_obs, dtype=data_type)) * 0.00001

        self.filter = EnsembleKalmanFilter(self.num_enbs, num_states, num_obs, A, B, V, W)

    def predict_with_filter(self):
        F = self.filter

        while self.epoch < self.epochs - 1:
            X = as_matrix([self.current_Ss, self.current_Is, 
                           self.alphas, self.betas])
        
            F.fit(X)
            y = tile(as_matrix(self.CDC_obs[self.epoch]), 
                     self.num_enbs)
            F.step(y, predict_P=False, verbose=False)
            self.weights.append(F.weights)

            x_post = F.x_post
            x_mean = mean(X, axis=1)
            x_post_mean = mean(x_post, axis=1)
            x_post = self.inflate * (X - tile(x_mean, self.num_enbs)) + \
                     tile(x_post_mean, self.num_enbs)
            for j in xrange(self.num_enbs):
                self.current_Ss[j] = self.check_bounds(x_post[0, j])
                self.current_Is[j] = self.check_bounds(x_post[1, j])
                self.alphas[j] = self.check_bounds(x_post[2, j], inf)
                self.betas[j] = self.check_bounds(x_post[3, j], inf)

            self.update_states()
            self.epoch += 1

        self.get_score()

    def _delta_s(self, s, i, alpha):
        return - alpha * s * i

    def _delta_i(self, s, i, alpha, beta):
        return alpha * s * i - beta * i

    def check_par_bounds(self, par):
        if par < 0: par = 0
        return par

    def get_score(self):
        I_mat = as_array(self.Is)
        for i, w in enumerate(self.weights):
            I_mat[i] *= w 

        self.IS = sum(I_mat, axis=1)

        time_gap = self.epochs / 52
        idx = [x for x in xrange(self.epochs) if not x % time_gap]

        self.score = RSS(self.CDC_obs, self.IS[idx])
        self.scores = {}
        self.scores['SSE'] = self.score
        self.scores['RMSE'] = RMSE(self.CDC_obs, self.IS[idx])
        self.scores['MSPE'] = MSPE(self.CDC_obs, self.IS[idx])
        self.scores['CORR'] = corrcoef(self.CDC_obs, self.IS[idx])[0, 1]
        print mean(self.alphas), mean(self.betas)
        print max(self.alphas), min(self.alphas), max(self.betas), min(self.betas)
        return self.score
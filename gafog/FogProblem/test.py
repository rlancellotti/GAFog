#!/usr/bin/python3
import unittest
import sys
import math

from ..FogProblem.problem import Problem
from ..FogProblem.solution import Solution

sample_problem={"fog": {"F1": {"capacity": 1.0}, "F2": {"capacity": 1.5}},
                "sensor": {"S1": {"servicechain": "SC1", "lambda": 0.4},
                           "S2": {"servicechain": "SC1", "lambda": 0.4},
                           "S3": {"servicechain": "SC2", "lambda": 0.5}},
                "servicechain": {"SC1": {"services": ["MS1_1", "MS1_2"]},
                                 "SC2": {"services": ["MS2_1"]}},
                "microservice": {"MS1_1": {"meanserv": 0.2, "stddevserv": 0.2},
                                 "MS1_2": {"meanserv": 0.1, "stddevserv": 0.01},
                                 "MS2_1": {"meanserv": 0.1, "stddevserv": 0.01}},
                "network":{"F1-F2": {"delay": 0.1}}}

epsilon=0.00001

class TestProblem(unittest.TestCase):
    # Service chains
    def test_chains(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_servicechain_list(), ['SC1', 'SC2'])

    # Microservices
    def test_nservice(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_nservice(), 3)

    def test_ms(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_microservice_list(), ['MS1_1', 'MS1_2', 'MS2_1'])

    def test_ms_in_chain(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_microservice_list(sc='SC1'), ['MS1_1', 'MS1_2'])
        self.assertEqual(p.get_microservice_list(sc='SC2'), ['MS2_1'])

    def test_ms_entry(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_microservice('MS1_1'), sample_problem['microservice']['MS1_1'])
        self.assertEqual(p.get_microservice('MS1_2'), sample_problem['microservice']['MS1_2'])
        self.assertEqual(p.get_microservice('MS2_1'), sample_problem['microservice']['MS2_1'])

    # Fog nodes
    def test_nfog(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_nfog(), 2)

    def test_fog(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_fog_list(), ['F1', 'F2'])

    def test_fog_entry(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_fog('F1'), sample_problem['fog']['F1'])
        self.assertEqual(p.get_fog('F2'), sample_problem['fog']['F2'])

    # Sensors
    def test_sens(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_sensor_list(), ['S1', 'S2', 'S3'])

    def test_sens_in_chain(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_chain_for_sensor('S1'), 'SC1')
        self.assertEqual(p.get_chain_for_sensor('S2'), 'SC1')
        self.assertEqual(p.get_chain_for_sensor('S3'), 'SC2')

    def test_sens_in_ms(self):
        p=Problem(sample_problem)
        self.assertEqual(p.get_service_for_sensor('S1'), 'MS1_1')
        self.assertEqual(p.get_service_for_sensor('S2'), 'MS1_1')
        self.assertEqual(p.get_service_for_sensor('S3'), 'MS2_1')
    
    # Network
    def test_net(self):
        p=Problem(sample_problem)
        self.assertEqual(p.network_as_matrix(), [[0.0, 0.1], [0.1, 0.0]])

class TestSolution(unittest.TestCase):
    def test_no_placement(self):
        s=Solution([None, None, None], Problem(sample_problem))
        self.assertEqual(s.obj_func(), 0)

    def test_placement_MS1_1_on_F1(self):
        s=Solution([0, None, None], Problem(sample_problem))
        #print(s.dump_solution())
        lam=sample_problem['sensor']['S1']['lambda']+sample_problem['sensor']['S2']['lambda']
        ts=sample_problem['microservice']['MS1_1']['meanserv']/sample_problem['fog']['F1']['capacity']
        sd=sample_problem['microservice']['MS1_1']['stddevserv']/sample_problem['fog']['F1']['capacity']
        lam_tot=sum(map(lambda x: sample_problem['sensor'][x]['lambda'], sample_problem['sensor'].keys()))
        tw=ts*((1+(sd/ts)**2)/2)*((lam*ts)/(1-(lam*ts)))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), lam, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), lam*ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), sd, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw+ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam/lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw+ts)* (lam/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F2(self):
        s=Solution([1, None, None], Problem(sample_problem))
        #print(s.dump_solution())
        lam=sample_problem['sensor']['S1']['lambda']+sample_problem['sensor']['S2']['lambda']
        ts=sample_problem['microservice']['MS1_1']['meanserv']/sample_problem['fog']['F2']['capacity']
        sd=sample_problem['microservice']['MS1_1']['stddevserv']/sample_problem['fog']['F2']['capacity']
        lam_tot=sum(map(lambda x: sample_problem['sensor'][x]['lambda'], sample_problem['sensor'].keys()))
        tw=ts*((1+(sd/ts)**2)/2)*((lam*ts)/(1-(lam*ts)))
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), lam, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), lam*ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw+ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam/lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw+ts)* (lam/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F1_MS1_2_on_F2(self):
        s=Solution([0, 1, None], Problem(sample_problem))
        #print(s.dump_solution())
        lam1=sample_problem['sensor']['S1']['lambda']+sample_problem['sensor']['S2']['lambda']
        #lam2=sample_problem['sensor']['S3']['lambda']
        ts11=sample_problem['microservice']['MS1_1']['meanserv']/sample_problem['fog']['F1']['capacity']
        ts12=sample_problem['microservice']['MS1_2']['meanserv']/sample_problem['fog']['F2']['capacity']
        sd11=sample_problem['microservice']['MS1_1']['stddevserv']/sample_problem['fog']['F1']['capacity']
        sd12=sample_problem['microservice']['MS1_2']['stddevserv']/sample_problem['fog']['F2']['capacity']
        tn1=sample_problem['network']['F1-F2']['delay']
        lam_tot=sum(map(lambda x: sample_problem['sensor'][x]['lambda'], sample_problem['sensor'].keys()))
        tw1=ts11*((1+(sd11/ts11)**2)/2)*((lam1*ts11)/(1-(lam1*ts11)))
        tw2=ts12*((1+(sd12/ts12)**2)/2)*((lam1*ts12)/(1-(lam1*ts12)))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), lam1*ts11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), lam1*ts12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), ts11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), sd11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), tw1, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw2, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw1+tw2+ts11+ts12+tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw1+tw2, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts11+ts12, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam1/lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw1+tw2+ts11+ts12+tn1)* (lam1/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F2_MS1_2_on_F2(self):
        s=Solution([1, 1, None], Problem(sample_problem))
        #print(s.dump_solution())
        lam1=sample_problem['sensor']['S1']['lambda']+sample_problem['sensor']['S2']['lambda']
        #lam2=sample_problem['sensor']['S3']['lambda']
        ts11=sample_problem['microservice']['MS1_1']['meanserv']/sample_problem['fog']['F2']['capacity']
        ts12=sample_problem['microservice']['MS1_2']['meanserv']/sample_problem['fog']['F2']['capacity']
        ts2=(ts11+ts12)/2
        sd11=sample_problem['microservice']['MS1_1']['stddevserv']/sample_problem['fog']['F2']['capacity']
        sd12=sample_problem['microservice']['MS1_2']['stddevserv']/sample_problem['fog']['F2']['capacity']
        sd2=math.sqrt(0.5*(sd11**2+ts11**2+sd12**2+ts12**2)-ts2**2)
        tn1=0
        rho2=2*lam1*ts2
        lam_tot=sum(map(lambda x: sample_problem['sensor'][x]['lambda'], sample_problem['sensor'].keys()))
        tw2=ts2*((1+(sd2/ts2)**2)/2)*((rho2)/(1-(rho2)))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), 2*lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), rho2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw2, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw2+tw2+ts11+ts12+tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw2+tw2, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts11+ts12, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam1/lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw2+tw2+ts11+ts12+tn1)* (lam1/(lam_tot)), delta=epsilon)

if __name__ == '__main__':
    unittest.main()
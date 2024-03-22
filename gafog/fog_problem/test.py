import unittest
import math
from pprint import pprint
from ..fog_problem.problem import load_problem

sample_problem_perf = {
    "type:": "perf",
    "fog": {"F1": {"capacity": 1.0}, "F2": {"capacity": 1.5}},
    "sensor": {
        "S1": {"servicechain": "SC1", "lambda": 0.4},
        "S2": {"servicechain": "SC1", "lambda": 0.4},
        "S3": {"servicechain": "SC2", "lambda": 0.5},
    },
    "servicechain": {
        "SC1": {"services": ["MS1_1", "MS1_2"]},
        "SC2": {"services": ["MS2_1"]},
    },
    "microservice": {
        "MS1_1": {"meanserv": 0.2, "stddevserv": 0.2},
        "MS1_2": {"meanserv": 0.1, "stddevserv": 0.01},
        "MS2_1": {"meanserv": 0.1, "stddevserv": 0.01},
    },
    "network": {"F1-F2": {"delay": 0.1}},
}

epsilon = 0.00001


class TestProblem(unittest.TestCase):

    def test_problem_type_perf(self):
        from gafog.fog_problem.problem_perf import ProblemPerf
        p=load_problem(sample_problem_perf)
        self.assertEqual(type(p), ProblemPerf)

    # Service chains
    def test_chains(self):
        """ Tests if there is the right list of servicechain. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_servicechain_list(), ['SC1', 'SC2'])

    # Microservices
    def test_nservice(self):
        """ Tests if there is the right number of microservices. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_nservice(), 3)

    def test_ms(self):
        """ Tests if there is the right list of microservices. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_microservice_list(), ['MS1_1', 'MS1_2', 'MS2_1'])

    def test_ms_in_chain(self):
        """ Tests if there are the right list in the servicechains. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_microservice_list(sc='SC1'), ['MS1_1', 'MS1_2'])
        self.assertEqual(p.get_microservice_list(sc='SC2'), ['MS2_1'])

    def test_ms_entry(self):
        """ Tests if there are the right params for all the microservices. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_microservice('MS1_1'), sample_problem_perf['microservice']['MS1_1'])
        self.assertEqual(p.get_microservice('MS1_2'), sample_problem_perf['microservice']['MS1_2'])
        self.assertEqual(p.get_microservice('MS2_1'), sample_problem_perf['microservice']['MS2_1'])

    # Fog nodes
    def test_nfog(self):
        """ Tests if there is the right number of fog nodes. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_nfog(), 2)

    def test_fog(self):
        """ Tests if there is the right list of fog nodes. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_fog_list(), ['F1', 'F2'])

    def test_fog_entry(self):
        """ Tests there are the right params for the fog node. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_fog('F1'), sample_problem_perf['fog']['F1'])
        self.assertEqual(p.get_fog('F2'), sample_problem_perf['fog']['F2'])

    # Sensors
    def test_sens(self):
        """ Tests if there is the right list of sensors. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_sensor_list(), ['S1', 'S2','S3'])

    def test_sens_in_chain(self):
        """ Tests if the function get_chain_for_sensor returns the right servicechain for a certain sensor. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_chain_for_sensor('S1'), 'SC1')
        self.assertEqual(p.get_chain_for_sensor('S2'), 'SC1')
        self.assertEqual(p.get_chain_for_sensor('S3'), 'SC2')

    def test_sens_in_ms(self):
        """ Tests that the function get_service_for_sensor returns the right microservice for a certain sensor. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.get_service_for_sensor('S1'), 'MS1_1')
        self.assertEqual(p.get_service_for_sensor('S2'), 'MS1_1')
        self.assertEqual(p.get_service_for_sensor('S3'), 'MS2_1')

    # Network
    def test_net(self):
        """ Tests if the function network_as_matrix gives the right delay for the fog nodes in the problem. """

        p = load_problem(sample_problem_perf)
        self.assertEqual(p.network_as_matrix(), [[0.0, 0.1], [0.1, 0.0]])


class TestSolution(unittest.TestCase):

    def test_solution_type_perf(self):
        p = load_problem(sample_problem_perf)
        s = p.get_solution([None, None, None])
        from gafog.fog_problem.solution_perf import SolutionPerf
        self.assertEqual(type(s), SolutionPerf)

    def test_no_placement(self):
        """ Tests if all the microservices are not placed in any nodes have 0 in the object function. """
        p = load_problem(sample_problem_perf)
        s = p.get_solution([None, None, None])
        self.assertEqual(s.obj_func(), 0)

    def test_placement_MS1_1_on_F1(self):
        """ 
            Tests all the performance on nodes and services if there is only the first microservice
            on the first node.
        """
        p = load_problem(sample_problem_perf)
        s = p.get_solution([0, None, None])
        # print(s.dump_solution())
        lam = (sample_problem_perf['sensor']['S1']['lambda'] + sample_problem_perf['sensor']['S2']['lambda'])
        ts  = (sample_problem_perf['microservice']['MS1_1']['meanserv'] / sample_problem_perf['fog']['F1']['capacity'])
        sd  = (sample_problem_perf['microservice']['MS1_1']['stddevserv'] / sample_problem_perf['fog']['F1']['capacity'])
        lam_tot = sum(map(lambda x: sample_problem_perf['sensor'][x]['lambda'],sample_problem_perf['sensor'].keys(),))
        tw = ts * ((1 + (sd / ts) ** 2) / 2) * ((lam * ts) / (1 - (lam * ts)))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), lam, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), lam * ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), sd, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw + ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam / lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw+ts) * (lam/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F2(self):
        """ 
            Tests all the performance on nodes and services if there is only the first microservice
            on the second node.
        """
        p = load_problem(sample_problem_perf)
        s = p.get_solution([1, None, None])
        #pprint(s.dump_solution())
        lam = (sample_problem_perf['sensor']['S1']['lambda'] + sample_problem_perf['sensor']['S2']['lambda'])
        ts  = (sample_problem_perf['microservice']['MS1_1']['meanserv'] / sample_problem_perf['fog']['F2']['capacity'])
        sd  = (sample_problem_perf['microservice']['MS1_1']['stddevserv'] / sample_problem_perf['fog']['F2']['capacity'])
        lam_tot = sum(map(lambda x: sample_problem_perf['sensor'][x]['lambda'], sample_problem_perf['sensor'].keys(),))
        tw = ts * ((1 + (sd / ts) ** 2) / 2) * ((lam * ts) / (1 - (lam * ts)))
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), lam, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), lam * ts, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw + ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam / lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw+ts) * (lam/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F1_MS1_2_on_F2(self):
        """ 
            Tests all the performance on nodes and services if there is the first microservice on 
            the first node and the second microservice on the second fog.
        """
        p = load_problem(sample_problem_perf)
        s = p.get_solution([0, 1, None])
        # print(s.dump_solution())
        lam1 = (sample_problem_perf['sensor']['S1']['lambda'] + sample_problem_perf['sensor']['S2']['lambda'])
        # lam2=sample_problem['sensor']['S3']['lambda']
        ts11 = (sample_problem_perf['microservice']['MS1_1']['meanserv'] / sample_problem_perf['fog']['F1']['capacity'])
        ts12 = (sample_problem_perf['microservice']['MS1_2']['meanserv'] / sample_problem_perf['fog']['F2']['capacity'])
        sd11 = (sample_problem_perf['microservice']['MS1_1']['stddevserv'] / sample_problem_perf['fog']['F1']['capacity'])
        sd12 = (sample_problem_perf['microservice']['MS1_2']['stddevserv'] / sample_problem_perf['fog']['F2']['capacity'])
        tn1  = sample_problem_perf['network']['F1-F2']['delay']
        lam_tot = sum(map(lambda x: sample_problem_perf['sensor'][x]['lambda'], sample_problem_perf['sensor'].keys()))
        tw1 = (ts11 * ((1 + (sd11 / ts11) ** 2) / 2) * ((lam1 * ts11) / (1 - (lam1 * ts11))))
        tw2 = (ts12 * ((1 + (sd12 / ts12) ** 2) / 2) * ((lam1 * ts12) / (1 - (lam1 * ts12))))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), lam1 * ts11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), lam1 * ts12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), ts11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), sd11, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd12, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), tw1, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw2, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw1 + tw2 + ts11 + ts12 + tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw1 + tw2, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts11 + ts12, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam1 / lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw1+tw2+ts11+ts12+tn1) * (lam1/(lam_tot)), delta=epsilon)

    def test_placement_MS1_1_on_F2_MS1_2_on_F2(self):
        """ 
            Tests all the performance on nodes and services if there are the first and the second microservice
            on the second node.
        """
        p = load_problem(sample_problem_perf)
        s = p.get_solution([1, 1, None])
        # print(s.dump_solution())
        lam1 = (sample_problem_perf['sensor']['S1']['lambda'] + sample_problem_perf['sensor']['S2']['lambda'])
        # lam2 = sample_problem['sensor']['S3']['lambda']
        ts11 = (sample_problem_perf['microservice']['MS1_1']['meanserv'] / sample_problem_perf['fog']['F2']['capacity'])
        ts12 = (sample_problem_perf['microservice']['MS1_2']['meanserv'] / sample_problem_perf['fog']['F2']['capacity'])
        ts2  = (ts11 + ts12) / 2
        sd11 = (sample_problem_perf['microservice']['MS1_1']['stddevserv'] / sample_problem_perf['fog']['F2']['capacity'])
        sd12 = (sample_problem_perf['microservice']['MS1_2']['stddevserv'] / sample_problem_perf['fog']['F2']['capacity'])
        sd2  = math.sqrt(0.5 * (sd11**2 + ts11**2 + sd12**2 + ts12**2) - ts2**2)
        tn1  = 0
        rho2 = 2 * lam1 * ts2
        lam_tot = sum(map(lambda x: sample_problem_perf["sensor"][x]["lambda"], sample_problem_perf["sensor"].keys()))
        tw2  = ts2 * ((1 + (sd2 / ts2) ** 2) / 2) * ((rho2) / (1 - (rho2)))
        self.assertAlmostEqual(s.get_fog_param('F1', 'lambda'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'lambda'), 2 * lam1, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'rho'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'rho'), rho2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'tserv'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'tserv'), ts2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'stddev'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F2', 'stddev'), sd2, delta=epsilon)
        self.assertAlmostEqual(s.get_fog_param('F1', 'twait'), 0, delta=epsilon) 
        self.assertAlmostEqual(s.get_fog_param('F2', 'twait'), tw2, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'resptime'), tw2 + tw2 + ts11 + ts12 + tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'resptime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'waittime'), tw2 + tw2, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'waittime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'servicetime'), ts11 + ts12, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'servicetime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.get_chain_param('SC1', 'networktime'), tn1, delta=epsilon) 
        self.assertAlmostEqual(s.get_chain_param('SC2', 'networktime'), 0, delta=epsilon)
        self.assertAlmostEqual(s.problem.servicechain['SC1']['weight'], lam1 / lam_tot, delta=epsilon)
        self.assertAlmostEqual(s.obj_func(), (tw2+tw2+ts11+ts12+tn1) * (lam1/(lam_tot)), delta=epsilon)

if __name__ == "__main__":
    unittest.main()
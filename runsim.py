#!/usr/bin/env python
#
# Dan Levin <dlevin@net.t-labs.tu-berlin.de>

import argparse
import logging
import logging.config
from math import log
#import plot #automatically plot selected ouputs directly after running
from sim.simulation import LinkBalancerSim
from sim.workload import dual_offset_workload, sawtooth, wave, expo_workload
import sys
from test.test_helper import two_ctrls, two_separate_state_ctrls, two_random_ctrls, two_greedy_ctrls, two_switch_topo, strictly_local_ctrls

parser = argparse.ArgumentParser()
parser.add_argument('--demand', '-d',
                    help="max demand values",
                    action="store",
                    nargs='+',
                    default=[32,64,128],
                    dest="demands")
parser.add_argument('--staleness', '-s',
                    help="staleness values",
                    action="store",
                    nargs='+',
                    default=[0,1],
                    dest="stalenesses")
parser.add_argument('--syncperiods', '-p',
                    help="staleness values",
                    action="store",
                    nargs='+',
                    default=[0,1,2,4,8,16],
                    dest="syncperiods")
parser.add_argument('--timesteps', '-t',
                    help="number of simulation timesteps",
                    action="store",
                    type=int,
                    default=256,
                    dest="timesteps")
parser.add_argument('--alpha-sslbc', '-a',
                    help="sslbc alpha parameter",
                    action="store",
                    type=float,
                    default=0.3,
                    dest="sslbc_alpha")

#parser.add_argument('--workloads', '-w',

#                    help="workload function",
#                    action="store",
#                    nargs='+',
#                    default=[expo_workload, dual_offset_workload]
#                    dest="timesteps")
args = parser.parse_args()




logging.config.fileConfig('setup.cfg')
logger= logging.getLogger(__name__)

def main():
    sp = args.syncperiods
    timesteps = args.timesteps
    sa = float(args.sslbc_alpha)
    print "Timesteps = %d" % (timesteps)
    print "Sync Periods = %s" % (str(sp))
    print "SSLBC Alpha = %f\n" % (sa)
    for demand in args.demands:
        demand = int(demand)
        for staleness in args.stalenesses:
            staleness = float(staleness)
            sync_improves_metric(max_demand=demand, sa=sa, sync_periods=sp, timesteps=timesteps, workload_name='expo', ctrl_name='separate', staleness=staleness)
            sync_improves_metric(max_demand=demand, sa=sa, sync_periods=sp, timesteps=timesteps, workload_name='expo', ctrl_name='lbc', staleness=staleness)
            sync_improves_metric(max_demand=demand, sa=sa, sync_periods=sp, timesteps=timesteps, workload_name='wave', ctrl_name='lbc', staleness=staleness)
            sync_improves_metric(max_demand=demand, sa=sa, sync_periods=sp, timesteps=timesteps, workload_name='wave', ctrl_name='separate', staleness=staleness)
#        for greedylimit in [0,0.25,0.5,0.75,1]:
#            compare_greedy_dist_to_centralized(max_demand=demand, greedylimit=greedylimit)
#    synced_dist_equals_central()
#    compare_random_dist_to_centralized()
#    demo_strictly_local_ctrls()


def sync_improves_metric(max_demand, sync_periods, timesteps, workload_name,
        ctrl_name, name=None, sa=0.3, ia=10, shape=0.5,  show_graph=False, staleness=0):
    """Evalute the value of synchronization for a LinkBalanerCtrl by showing
    its effect on performance metric. We expect that for a workload which
    imparts server link imbalance across multiple domains, syncing will help
    improve the rmse_server metric.
    
    sa: the sslbc fractional load-balancing scale factor (0,1]. Controls what
    fraction of the imbalance we re-balance at each handle_request

    ia: the mean parameter for the expnentially distributed inter-arrival times
    of the expo workflow (value of x leads to mean of 1/x). Gets passed to
    random.expovariate(ia)

    shape: the weibull distribution shape parameter for flow duration
    """

    if name == None:
        name = sys._getframe().f_code.co_name + "_" + ctrl_name + "_" + workload_name

    #for sync_period in [0] + [2**(x) for x in range(0, int(log(timesteps,2)))]:
    for sync_period in sync_periods:

        sync_period = float(sync_period)
        myname = '%(a)s_%(b)d_%(c)02d_%(d)01d' % {"a": name,
                                               "b": max_demand,
                                               "c": sync_period,
                                               "d": staleness}

        logger.info("starting %s", myname)

        if workload_name == 'expo':
            wave_period = timesteps/4
            old_style=False
            workload = expo_workload(switches=['sw1', 'sw2'],
                                     period=wave_period, interarrival_alpha=ia,
                                     duration_shape=shape, timesteps=timesteps)
        elif workload_name == 'wave':
            old_style=True
            wave_period = timesteps/4
            workload = dual_offset_workload(switches=['sw1', 'sw2'],
                                            period=wave_period, offset=wave_period/2.0,
                                            max_demand=max_demand, size=1,
                                            duration=2, timesteps=timesteps,
                                            workload_fcn=wave, y_shift=(1.0/3))
        else: 
            assert "No Valid Workload Specified"

        if ctrl_name == 'separate':
            ctrls = two_separate_state_ctrls(alpha=sa)
        elif ctrl_name == 'lbc':
            ctrls = two_ctrls()
        else:
            assert "No Valid Controller Specified"

        sim = LinkBalancerSim(two_switch_topo(), ctrls)
        sim.run_and_trace(myname, workload, old=old_style, sync_period=sync_period,
                          show_graph=show_graph, staleness=staleness,
                          ignore_remaining=True)
        logger.info("ending %s", myname)



#def sync_improves_metric(max_demand, timesteps, workload, name=None, ia=10, shape=5, show_graph=False, staleness=0):
#    """Evalute the value of synchronization for a LinkBalanerCtrl by showing
#    its effect on performance metric. We expect that for a workload which
#    imparts server link imbalance across multiple domains, syncing will help
#    improve the rmse_server metric."""
#
#    if name == None:
#        name = sys._getframe().f_code.co_name
#
#    for sync_period in [0] + [2**x for x in range(0, int(log(timesteps,2)))]:
#        myname = '%(a)s_%(b)d_%(c)02d_%(d)' % {"a": name,
#                                               "b": max_demand,
#                                               "c": sync_period,
#                                               "d": staleness}
#
#        logger.info("starting %s", myname)
#
#        if workload == 'expo':
#            workload = expo_workload(switches=['sw1', 'sw2'], interarrival_alpha=ia,
#                                     duration_shape=shape, timesteps=timesteps)
#        elif workload == 'wave':
#            wave_period = timesteps/4
#            workload = dual_offset_workload(switches=['sw1', 'sw2'],
#                                            period=wave_period, offset=wave_period/2.0,
#                                            max_demand=max_demand, size=1,
#                                            duration=2, timesteps=timesteps,
#                                            workload_fcn=wave, y_shift=(1.0/3))
#
#        ctrls = two_ctrls()
#        sim = LinkBalancerSim(two_switch_topo(), ctrls)
#        sim.run_and_trace(myname, workload, old=True, sync_period=sync_period,
#                          show_graph=show_graph, staleness=staleness,
#                          ignore_remaining=True)
#        logger.info("ending %s", myname)
#
#
#def sync_separate_improves_metric(max_demand, timesteps, workload, name=None, ia=10, shape=5, show_graph=False, staleness=0):
#    """ """
#
#    if name == None:
#        name = sys._getframe().f_code.co_name + "_" + workload
#
#    for sync_period in [0] + [2**x for x in range(0, int(log(timesteps,2)))]:
#        myname = '%(a)s_%(b)d_%(c)02d_%(d)' % {"a": name,
#                                               "b": max_demand,
#                                               "c": sync_period,
#                                               "d": staleness}
#
#        logger.info("starting %s", myname)
#
#        if workload == 'expo':
#            workload = expo_workload(switches=['sw1', 'sw2'], interarrival_alpha=ia,
#                                     duration_shape=shape, timesteps=timesteps)
#        elif workload == 'wave':
#            wave_period = timesteps/4
#            workload = dual_offset_workload(switches=['sw1', 'sw2'],
#                                            period=wave_period, offset=wave_period/2.0,
#                                            max_demand=max_demand, size=1,
#                                            duration=2, timesteps=timesteps,
#                                            workload_fcn=wave, y_shift=(1.0/3))
#
#        ctrls = two_separate_state_ctrls()
#        sim = LinkBalancerSim(two_switch_topo(), ctrls)
#        sim.run_and_trace(myname, workload, old=False, sync_period=sync_period,
#                          show_graph=show_graph, staleness=staleness,
#                          ignore_remaining=True)
#        logger.info("ending %s", myname)
#


#def sync_expo_improves_metric(max_demand, timesteps, workload ia=10, shape=5, show_graph=False, staleness=0):
#    """ Same as sync_improves_metric, but using an exponential inter-arrival
#    distribution workload """
#
#    if name == None:
#        name = sys._getframe().f_code.co_name
#
#    for sync_period in [0] + [2**x for x in range(0, int(log(timesteps,2)))]:
#        myname = '%(a)s_%(b)d_%(c)02d_%(d)' % {"a": name,
#                                                "b": max_demand,
#                                                "c": sync_period,
#                                                "d": staleness}
#        logger.info("starting %s", myname)
#        workload = expo_workload(switches=['sw1', 'sw2'], interarrival_alpha=ia,
#                duration_shape=shape, timesteps=timesteps)
#                
#        ctrls = two_ctrls()
#        #ctrls = two_separate_state_ctrls()
#        sim = LinkBalancerSim(two_switch_topo(), ctrls)
#        sim.run_and_trace(myname, workload, old=False, sync_period=sync_period,
#                          show_graph=show_graph, staleness=staleness,
#                          ignore_remaining=True)
#        logger.info("ending %s", myname)
#

#def sync_separate_improves_metric(max_demand, period=64, name=None, show_graph=False, staleness=0):
#    """ Same as above, except using separate state tracking controllers which keep
#    synchronization-shared state from extra-domain links sepatate from
#    locally-originating inferred "contributed" extra-domain link utilization """
#
#    if name == None:
#        name = sys._getframe().f_code.co_name
#
#    timesteps = period * 4
#    for sync_period in [0] + [2**x for x in range(0, int(log(period,2)))]:
#        myname = '%(a)s_%(b)d_%(c)02d_%(d)' % {"a": name,
#                                                "b": max_demand,
#                                                "c": sync_period,
#                                                "d": staleness}
#
#        logger.info("starting %s", myname)
#        workload = dual_offset_workload(switches=['sw1', 'sw2'],
#                                        period=period, offset=period/2.0,
#                                        max_demand=max_demand, size=1,
#                                        duration=2, timesteps=timesteps,
#                                        workload_fcn=wave, y_shift=(1.0/3))
#
#        ctrls = two_separate_state_ctrls()
#        sim = LinkBalancerSim(two_switch_topo(), ctrls)
#        sim.run_and_trace(myname, workload, old=True, sync_period=sync_period,
#                          show_graph=show_graph, staleness=staleness,
#                          ignore_remaining=True)
#        logger.info("ending %s", myname)
#
#######################################

def synced_dist_equals_central(period=64, max_demand=4, show_graph=False):
    """Ensure that a distributed controller simulation run with sync_period=0
    yields exactly the same result as the same toplology and workload with a
    single controller."""

    timesteps = period * 4
    for sync_period in [0] + [2**x for x in range(0, int(log(period,2)))]:
        myname = '%(fname)s_%(num)02d' % {"fname": sys._getframe().f_code.co_name, "num": sync_period}
        logger.info("starting %s", myname)
        workload = dual_offset_workload(switches=['sw1', 'sw2'],
                                        period=period, offset=0,
                                        max_demand=max_demand, size=1,
                                        duration=1, timesteps=timesteps,
                                        workload_fcn=wave)

        ctrls = two_ctrls()
        sim = LinkBalancerSim(two_switch_topo(), ctrls)
        sim.run_and_trace(myname+str(sync_period), workload, old=True, sync_period=sync_period,
                          show_graph=show_graph)
        logger.info("ending %s", myname)

def compare_random_dist_to_centralized(period=64, max_demand=8, show_graph=False):
    """ """
    timesteps = period * 4
    for sync_period in [0] + [2**x for x in range(0, int(log(period,2)))]:
        myname = '%(fname)s_%(num)02d' % {"fname": sys._getframe().f_code.co_name, "num": sync_period}
        logger.info("starting %s", myname)
        workload = dual_offset_workload(switches=['sw1', 'sw2'],
                                        period=period, offset=period/2.0,
                                        max_demand=max_demand, size=1,
                                        duration=2, timesteps=timesteps,
                                        workload_fcn=wave)

        ctrls = two_random_ctrls()
        sim = LinkBalancerSim(two_switch_topo(), ctrls)
        sim.run_and_trace(myname, workload, old=True, sync_period=sync_period,
                          show_graph=show_graph)
        logger.info("ending %s", myname)

   


def compare_greedy_dist_to_centralized(period=64, max_demand=30,
                                       greedylimit=0.5, show_graph=False):
    """Ensure that a distributed controller simulation run with sync_period=0
    yields exactly the same result as the same toplology and workload with a
    single controller."""
    timesteps = period * 4
    for sync_period in [0] + [2**x for x in range(0, int(log(period,2)))]:
        myname = '%(fname)s_%(demand)d_%(gl)s_%(num)02d' % {"fname": sys._getframe().f_code.co_name,
                                                     "demand": max_demand,
                                                     "gl": str(greedylimit),
                                                     "num": sync_period}

        logger.info("starting %s", myname)
        workload = dual_offset_workload(switches=['sw1', 'sw2'],
                                        period=period, offset=period/2.0,
                                        max_demand=max_demand, size=1,
                                        duration=2, timesteps=timesteps,
                                        workload_fcn=wave)

        ctrls = two_greedy_ctrls(greedylimit=greedylimit)
        sim = LinkBalancerSim(two_switch_topo(), ctrls)
        sim.run_and_trace(myname, workload, old=True, sync_period=sync_period,
                          show_graph=show_graph)
        logger.info("ending %s", myname)



def compare_greedy_dist_to_sync_dist(max_demand=8, show_graph=False):
    """Understand what improvement synchronization gives us over a greedy
    algorithm in a dynamic, discrete loadbalancing environment"""
    pass


def demo_strictly_local_ctrls(max_demand=8, show_graph=False):
    """Demonstrate synchronization across domains makes no difference when
    LinkBalanerCtrl only handles requests within its own domain"""

    #TODO: demonstrate with more than 1 srv per controller domain
    period = 32
    timesteps = period * 4
    for sync_period in [0] + [2**x for x in range(0, int(log(period,2)))]:
        myname = '%(fname)s_%(num)02d' % {"fname": sys._getframe().f_code.co_name, "num": sync_period}
        logger.info("starting %s", myname)
        workload = dual_offset_workload(switches=['sw1', 'sw2'],
                                        period=period, offset=period/2.0,
                                        max_demand=max_demand, size=1,
                                        duration=1, timesteps=timesteps,
                                        workload_fcn=wave)

        ctrls = strictly_local_ctrls()
        sim = LinkBalancerSim(two_switch_topo(), ctrls)
        sim.run_and_trace(myname, workload, old=True, sync_period=sync_period,
                          show_graph=show_graph)
        logger.info("ending %s", myname)


#Not enough brainpower left tonight to implement these, but I have been
#looking through the code and tests.  Here are some thoughts for regression
#test-ish graphs to generate.
#
#(1) Line topology w/3 controllers, each responsible for one server.   Let's
#say all requests go to the center controller first.  If the main parameter
#to vary is the relative size of requests, this should expose the effect of
#bins on our load-packing metric, plus ensure that LinkBalancerCtrl properly
#handles shortest-path ties in a reasonable way.
#
#(2) Line topology w/N controllers, N servers.  I have to think more about
#this one, but it seems like the nearest servers are always a better choice
#on a restricted topology where the demand is at one location, because
#they'd yield strictly less link usage.  But when demands are more spread
#out I could see a model solver in a central node doing a better job.
#
#(3) Ring topology w/N controllers, N servers.  Like 2.  Faster sync should
#yield closer-to-optimal balancing.
#
#(4) Ring topology w/N servers and varying number of controllers C, each
#commanding N / C servers.  With more controllers do we see crappier
#balancing for random workloads?
#
#-b


if __name__ == "__main__":
    main()

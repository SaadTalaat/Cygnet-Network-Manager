from cygnet_network_manager.client import Client
from cygnet_network_manager.clusterState import ClusterState
from autobahn.twisted.wamp import ApplicationRunner
from cygnet_common.NetworkInterface import NetworkInterface
from cygnet_common import strtypes

from threading import Thread
from cygnet_network_manager.components.plugin import docker

class Helper(object):

    # get the address of br1 supposed that ovs ifaces are up
    def __init__(self, **kwargs):
        # Obtain network information
        self.args = dict()
        for arg, value in list(kwargs.items()):
            self.args[arg] = value
        print(self.args)
        empty_setup = {'interfaces': [],
                       'containers': [],
                       'endpoints': [],
                       'interface_class': self.args['internal-network'],
                       'internal_ip': self.args['internal-addr'],
                       'external_iface': self.args['external-iface']
                       }
        t = Thread(target=docker.start, args=(empty_setup,))
        t.setDaemon(True)
        interface = NetworkInterface(**empty_setup)
    # address is returned as a 2-tuple of strings addr,mask
        self.address = interface.initalize()
        ClusterState.address1 = self.address
        ClusterState.interface = interface
        ClusterState.etcd_addr = self.args['etcd-server-addr']
        t.start()

    # simply run the client
    def connect(self):
        print(self.args['router-addr'])
        runner = ApplicationRunner(u"ws://" + self.args['router-addr'] + "/ws", strtypes.cast_unicode(self.args['router-realm']))
        runner.run(Client)

import etcd
from cygnet_common.generic.Network import Network

class EtcdClusterClient(etcd.Client):
    '''
    Etcd cluster client is a client used to manage
    the service information stored in etcd. Information
    stored in etcd match the same information stored in
    the clusterState object
    '''
    def __init__(self, host, nodeId, port=7001, protocol='http'):
        print(host)
        etcd.Client.__init__(self, host=host, port=port, protocol=protocol)
        print("INIT")
        self.nodeId = str(nodeId)
        print("NODE")

    def initStore(self):
        try:
            self.write("nodes", None, dir=True)
            return True
        except etcd.EtcdNotFile:
            try:
                self.read("nodes")
                return True
            except etcd.EtcdKeyNotFoud:
                return False

    def _lockNode(self, nodePath):
        # traverse node path - check any parent nodes are locked.
        free = False
        for i in range(len(nodePath.split("/")), 0):
            try:
                lock = self.get("/".join(nodePath.split("/")[:i])+"/lock")
                if lock.value and lock.value != self.nodeId:
                    free &= False
                elif lock.value is None:
                    lock.value = self.nodeId
                    self.update(lock)
                    free &= True
                elif lock.value == self.nodeId:
                    free &= True
            except:
                if i == len(nodePath.split("/")):
                    self.write(nodePath + "/lock", self.nodeId, dir=False)
                else:
                    free &= True
                    continue
        return free

    def _unlockNode(self, nodePath):
        try:
            lock = self.get(nodePath+"/lock")
            lock.value = None
            self.update(lock)
        except:
            return

    def addNode(self):
        node_key = "nodes/" + self.nodeId
        try:
            self.write(node_key, None, dir=True)
            self.write(node_key+"/state", ttl=60)
        except etcd.EtcdNotFile:
            self.write(node_key+"/state", 1, ttl=60)

        try:
            self.write(node_key+"/networks",None, dir=True)
        except etcd.EtcdNotFile:
            pass

        networks = self.get(node_key+"/networks/")
        read_networks = []
        if networks._children:
            for network in networks.children:
                network = self.get(network.key)
                empty = {"Id": None,
                         "Name": None,
                         "Address":None,
                         "Config": None
                         }
                for leaf in network.children:
                    for foo in leaf.children:
                        print(foo)
                    empty[leaf.key.split("/")[-1]] = leaf.value
                network = Network(empty['Id'], config=empty['Config'])
                network.name = empty['Name']
                read_networks.append(network)
        return read_networks

    def addNetwork(self, network):
        network_key = "nodes/" + self.nodeId + "/networks/" + network.id
        print("adding iface "+ network_key)
        try:
            self.write(network_key, None, dir=True)
            for key, value in network.items():
                current_key = network_key+ "/" + key
                self.write(current_key, value, dir=False)
            return True
        except:
            return False

    def removeNetwork(self, network):
        network_key = "nodes/" + self.nodeId + "/networks/" + network.id
        try:
            self.delete(network_key, recursive=True)
            return True
        except:
            True

    def updateContainer(self, container, key=None):
        container_key = "/".join(["nodes", self.nodeId, container.id])
        if key:
            current_key = container_key + '/' + key
        try:
            if key:
                node = self.get(current_key)
                node.value = container[key]
                self.update(node)
                return True
            else:
                for key2, value in list(container.items()):
                    current_key = container_key + '/' + key2
                    node = self.get(current_key)
                    node.value = container[key]
                    self.update(node)
                return True
        except:
            return False

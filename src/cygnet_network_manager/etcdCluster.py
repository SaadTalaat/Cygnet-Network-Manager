import etcd


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
            self.write(node_key+"/interfaces",None, dir=True)
        except etcd.EtcdNotFile:
            pass

        interfaces = self.get(node_key+"/interfaces/")
        read_interfaces = []
        if interfaces:
            for interface in interfaces.children:
                interface = self.get(interface.key)
                empty = {"Id": None,
                         "Name": None,
                         "Address":None
                         }
                for leaf in interface.children:
                    empty[leaf.key.split("/")[-1]] = leaf.value
                read_interfaces.append(empty)
        return read_interfaces

    def addInterface(self, interface):
        interface_key = "nodes/" + self.nodeId + "/interfaces/" + interface['Id']
        print("adding iface "+interface_key)
        try:
            self.write(interface_key, None, dir=True)
            for key, value in interface.items():
                current_key = interface_key+ "/" + key
                self.write(current_key, value, dir=False)
            return True
        except:
            return False

    def removeInterface(self, interface):
        interface_key = "nodes/" + self.nodeId + "/interfaces/" + interface['Id']
        try:
            self.delete(interface_key, recursive=True)
            return True
        except:
            True

    def updateContainer(self, container, key=None):
        container_key = "/".join(["nodes", self.nodeId, container["Id"]])
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

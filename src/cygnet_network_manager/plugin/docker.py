from twisted.web import resource, server
import json
from cygnet_network_manager.clusterState import ClusterState
## remove
from twisted.internet import reactor

class Plugin(resource.Resource):
    isLeaf = True

    def __init__(self):
        resource.Resource.__init__(self)

    def render_POST(self, request):
        op = request.uri.decode('utf-8')[len('/Plugin.'):]
        return {
                'Activate': self.activate,
                }.get(op)(request)

    def activate(self, request):
        # Activate expects no request payload
        payload = {
                   "implements":["NetworkDriver"]
                   }
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        print('done')
        return server.NOT_DONE_YET

class NetworkDriver(resource.Resource):
    isLeaf = True

    def __init__(self, setup):
        resource.Resource.__init__(self)
        self.setup = setup
        self.cluster_state = ClusterState(None)
    def render_POST(self, request):
        op = request.uri.decode('utf-8')[len('/NetworkDriver.'):]
        print(request.uri)
        print(op)
        return {
                'GetCapabilities': self.getCapabilities,
                'CreateNetwork': self.createNetwork,
                'DeleteNetwork': self.deleteNetwork
                }.get(op)(request)

    def getCapabilities(self, request):
        # GetCapabilities expects no request payload
        payload = {
                    "Scope":"local"
                    }
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def createNetwork(self, request):
        specs = request.content.read().decode('utf-8')
        specs = json.loads(specs)
        network_id = specs['NetworkID']
        self.cluster_state.addInterface(network_id, specs['IPv4Data'][0])
        response = json.dumps({}).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def deleteNetwork(self, request):
        body = request.content.read().decode('utf-8')
        body = json.loads(body)
        print(body)
        network_id = body["NetworkID"]
        self.cluster_state.removeInterface(network_id)
        response = json.dumps({}).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET


class CygnetDockerPlugin(resource.Resource):
    isLeaf = False

    def __init__(self, setup):
        resource.Resource.__init__(self)
        self.setup = setup
    def getChild(self, name, request):
        rsrc404 = resource.NoResource()
        name = name.decode('utf-8')
        if '.' in name:
            name = name.split('.')[0]
        print(name)
        rsrc = {'Plugin': Plugin(),
                'NetworkDriver': NetworkDriver(self.setup),
                '': self
                }.get(name, rsrc404)
        return rsrc
def start(setup):
    root = CygnetDockerPlugin(setup)
    r = server.Site(root)
    reactor.listenUNIX('/run/docker/plugins/cygnet/cygnet.sock', r)

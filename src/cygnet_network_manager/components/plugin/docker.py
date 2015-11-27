from twisted.web import resource, server
import json
from cygnet_network_manager.clusterState import ClusterState
from cygnet_common.generic.Container import Container
from cygnet_common.generic.Network import Network
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
                'DeleteNetwork': self.deleteNetwork,
                'CreateEndpoint': self.createEndpoint,
                'DeleteEndpoint': self.deleteEndpoint,
                'Join': self.join,
                'EndpointOperInfo': self.endpointInfo
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
        payload = {}
        specs = request.content.read().decode('utf-8')
        specs = json.loads(specs)
        print(specs)
        print("DONEEEE!!")
        network = Network(specs['NetworkID'], specs['IPv4Data'][0])
        try:
            self.cluster_state.addInterface(network_id, specs['IPv4Data'][0])
        except Exception as e:
            error = str(e)
            payload = {"Err":error}
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def deleteNetwork(self, request):
        payload = {}
        body = request.content.read().decode('utf-8')
        body = json.loads(body)
        print(body)
        network_id = body["NetworkID"]
        try:
            self.cluster_state.removeInterface(network_id)
        except Exception as e:
            error = str(e)
            payload = {"Err":error}
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def createEndpoint(self, request):
        payload = {}
        specs = request.content.read().decode('utf-8')
        specs = json.loads(specs)
        network_id = specs["NetworkID"]
        try:
            assert 1==2
        except Exception as e:
            error = str(e)
            payload= {"Err": error}
            raise e
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def deleteEndpoint(self, request):
        payload = {}
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def join(self, request):
        payload = {}
        print(request.content.read().decode('utf-8'))
        response = json.dumps(payload).encode('utf-8')
        request.write(response)
        request.finish()
        return server.NOT_DONE_YET

    def endpointInfo(self, request):
        payload = {'Value':{}}
        print(request.content.read().decode('utf-8'))
        response = json.dumps(payload).encode('utf-8')
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

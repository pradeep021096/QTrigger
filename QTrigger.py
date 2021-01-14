
import ssl
import json
from websocket import create_connection

# Qlik JSON-RPC 2.0 API
# {
#   MEMBERS     REQUIRED
#   -------     --------
#   jsonrpc     Yes
#   id          No
#   method      Yes
#   handle      Yes
#   delta       No
#   params      No
# }

#Request
# {
#     "jsonrpc" : self.jsonrpc,
#     "handle" : self.handle,
#     "method" : self.method,
#     "params" : self.params
# }
 

# Qlik Document Info
class QDoc:

    def __init__(self, qDoc):

        self.docName = qDoc["qDocName"]
        self.docTitle = qDoc["qTitle"]
        self.docId = qDoc["qDocId"]
    
    def _openDoc(self, webSocket):

        request = {"jsonrpc": "2.0", "method": "OpenDoc", "handle": -1, "params": [self.docId] }
        # print(request)
        webSocket.send(json.dumps(request))
        response = webSocket.recv()
        # print(response)
        handle = json.loads(response)["result"]["qReturn"]["qHandle"]

        return handle

    def reloadDoc(self,webSocket):
        
        handle = self._openDoc(webSocket)

        # print(handle)
        request = { "handle": handle, "method": "DoReload", "params": {}}
        # print(request)
        webSocket.send(json.dumps(request))
        response = webSocket.recv()
        # print(response)
        status = json.loads(response)["result"]["qReturn"]

        if(status):
            status = self.saveDoc(webSocket,handle)
        else:
            print("Reload error")
            status = False

        return status
    
    def saveDoc(self,webSocket,handle):

        request = { "handle": handle, "method": "DoSave", "params": [] }
        # print(request)
        webSocket.send(json.dumps(request))
        response = webSocket.recv()

        return True
        # print(response)


#All Qlik Document 
#Store All Doc Info
class QDocFactory:

    def __init__(self, socket):

        self.webSocket = socket.webSocket
        self.qDocList = self._generate_Qlik_Docs()
    
    def _generate_Qlik_Docs(self):

        request = {"jsonrpc": "2.0", "handle": -1, "method": "GetDocList", "params": [] }
        self.webSocket.send(json.dumps(request))
        response_list = json.loads(self.webSocket.recv())["result"]["qDocList"]

        return [ QDoc(doc)  for doc in response_list ]
    
    
    def isPresent(self, docId):

        for doc in self.qDocList:
            if doc.docId == docId:
                return True, doc

        return False, None


#WebSocket for Qlik Engine JSON API
# Add param in create_connection if using header AUTH
# default settings for Qlik Sense Desktop
class QWebSocket:

    def __init__(self, url = "ws://localhost:4848/app/engineData", sslopt={"cert_reqs": ssl.CERT_NONE} ):

        self.webSocket = create_connection(url, sslopt = sslopt)
        self.status = json.loads(self.webSocket.recv())["params"]["qSessionState"]
        # print(self.status) 

    def __del__(self):
        self.webSocket.close()


def main():

    socket = QWebSocket()
    qFactory = QDocFactory(socket)

    # print(qFactory.qDocList[3].reloadDoc(socket.webSocket))

    reloadListPath = './ReloadList.json'

    with open(reloadListPath) as json_file:
        for app in json.load(json_file)["Apps"]:
            docId = app["AppId"]
            present, doc =  qFactory.isPresent(docId)
            if(present):
                doc.reloadDoc(socket.webSocket)
            


if __name__ == "__main__":
    
    main()

    


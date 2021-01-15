
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


# Qlik Document and fucntions
class QDoc:

    def __init__(self, qDoc):

        self.docName = qDoc["qDocName"]
        self.docTitle = qDoc["qTitle"]
        self.docId = qDoc["qDocId"]
    
    def _openDoc(self, webSocket):

        request = {"jsonrpc": "2.0", "method": "OpenDoc", "handle": -1, "params": [self.docId] }
               
        handle = webSocket.request(request)["result"]["qReturn"]["qHandle"]

        return handle

    def reloadDoc(self,webSocket):
        
        handle = self._openDoc(webSocket)

        request = { "handle": handle, "method": "DoReload", "params": {}}
 
        status = webSocket.request(request)["result"]["qReturn"]

        if(status):
            status = self.saveDoc(webSocket,handle)

        return status
    
    def saveDoc(self,webSocket,handle):

        request = { "handle": handle, "method": "DoSave", "params": [] }
        webSocket.request(request)
        return True
        


#All Qlik Document 
#Store All Doc Info
class QDocFactory:

    def __init__(self, socket):

        self.webSocket = socket
        self.qDocList = self._generate_Qlik_Docs()
    
    def _generate_Qlik_Docs(self):

        request = {"jsonrpc": "2.0", "handle": -1, "method": "GetDocList", "params": [] }
        response_list = self.webSocket.request(request)["result"]["qDocList"]
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

    def __del__(self):
        self.webSocket.close()
    
    def request(self,req):
        self.webSocket.send(json.dumps(req))
        return json.loads(self.webSocket.recv())


def main():

    socket = QWebSocket()
    qFactory = QDocFactory(socket)

    reloadListPath = './ReloadList.json'

    with open(reloadListPath) as json_file:
        for app in json.load(json_file)["Apps"]:
            docId = app["AppId"]
            present, doc =  qFactory.isPresent(docId)
            if(present):
                doc.reloadDoc(socket)
            

if __name__ == "__main__":
    
    main()

    


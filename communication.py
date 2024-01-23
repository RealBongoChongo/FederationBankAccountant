import socketio
import asyncio
from threading import Thread

class WebsocketClient(socketio.Client):
    def __init__(self, loop, connectionCallback, updateTransaction, updateTransactionAdmin):
        super().__init__(
            logger=True, 
            reconnection_attempts=10
        )

        self.connectionCallback = connectionCallback
        self.updateTransaction = updateTransaction
        self.updateTransactionAdmin = updateTransactionAdmin
        self.loop = loop
        self.callbackDictionary = {}

    def invoke_callback(self, data):
        self.callbackDictionary[data["processID"]](data["data"])
        self.callbackDictionary.pop(data["processID"])
        
    def on_connection(self):
        asyncio.run_coroutine_threadsafe(self.connectionCallback(), self.loop)
        print("Connected")

    def server_response(self, data):
        print(data)

    def ping_packet(self):
        while True:
            asyncio.run(asyncio.sleep(10))
            self.emit("ping_packet", "Ping", "/")

    def returnData(self, data):
        asyncio.run_coroutine_threadsafe(self.updateTransactionAdmin(data), self.loop)

    def returnData2(self, data):
        asyncio.run_coroutine_threadsafe(self.updateTransaction(data), self.loop)

    def start(self):
        def start_task():
            self.on("connect", self.on_connection, "/")
            self.on("heartbeat", self.server_response, "/")
            self.on("newTransactionAdmin", self.returnData, "/")
            self.on("newTransaction", self.returnData2, "/")
            #Thread(target=self.ping_packet).start()
            self.connect("https://bank.federationfleet.xyz", namespaces=["/"])
            self.wait()
        
        Thread(target=start_task).start()
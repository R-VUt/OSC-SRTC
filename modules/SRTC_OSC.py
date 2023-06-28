from pythonosc import udp_client, osc_server, dispatcher
import threading


class SRTC_OSC:
    def __init__(self, settings: dict, log: callable):
        self._OSC_Send_IP = settings.get("osc_ip") or "127.0.0.1"
        self._OSC_Send_Port = settings.get("osc_port") or 9000
        self._OSC_Recv_IP = settings.get("osc_serv_ip") or "127.0.0.1"
        self._OSC_Recv_Port = settings.get("osc_serv_port") or 9001
        self._log = log
        self._log("[OSC][Info] Initializing OSC Interface...")

        self._disp = dispatcher.Dispatcher()

        self._OSC_Server: osc_server.ThreadingOSCUDPServer = None
        self._OSC_Client: udp_client.SimpleUDPClient = udp_client.SimpleUDPClient(
            self._OSC_Send_IP, self._OSC_Send_Port
        )

    def send(self, address: str, *args):
        """Send OSC message to the specified address"""
        self._OSC_Client.send_message(address, args)

    def recv_callback(self, address: str, callback: callable):
        """Register callback function for the specified address"""
        self._disp.map(address, callback)

    def start_server(self):
        """Start OSC server"""
        self._OSC_Server = osc_server.ThreadingOSCUDPServer(
            (self._OSC_Recv_IP, self._OSC_Recv_Port), self._disp
        )
        threading.Thread(target=self._OSC_Server.serve_forever).start()

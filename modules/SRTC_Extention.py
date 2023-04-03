# 양방향 http 기반 익스텐션 메인 서버
# http://main-server-ip:port/extention/register?name=(name)&ip=(extention-server-ip)&port=(port) (등록)
# 결과: 200 only
# 200: 성공

# http://main-server-ip:port/extention/forward?name=(name) (익스텐션 순서 변경 -> 앞으로)
# http://main-server-ip:port/extention/backward?name=(name) (익스텐션 순서 변경 -> 뒤로)
# 결과: 200, 400, 404
# 200: 성공
# 400: 이미 가장 앞에 있음
# 404: 해당 이름의 익스텐션이 없음

# http://extention-server-ip:port/extention/execute?message=(message) (익스텐션 실행)
# 결과: 200, 400
# 200: 성공
# 400: 실패

# http://extention-server-ip:port/extention/heartbeat?num=(num) (하트비트)
# 200 신호가 2번 이상 돌아오지 않으면 메인 측 서버에서 제거
# 서버는 5초마다 하트비트를 보낸다.
# num은 해당 익스텐션의 순서를 나타낸다.
# 결과: 200, 400
# 200: 성공
# 400: num이 없거나 숫자가 아님

# 음성 인식시 익스텐션 사이드 서버로 결과 전달
# 익스텐션 사이드 서버는 메인 서버로 결과 전달 (처리된 메시지 혹은 "{Sended-Already}")
# {Sended-Already}는 이미 VRChat으로 전송되었음을 의미한다. -> 더 이상 메인 서버는 해당 메시지를 처리하지 않는다.

import threading
import time
import requests
from flask import Flask, request

class Extention_MainServer:

    def __send_heartbeat(self):
        i=0
        while i < len(self.__extention_list):
            self.__extention_list_lock.acquire()
            try:
                heartbeat_res = requests.get(f"http://{self.__extention_list[i]['ip']}:{self.__extention_list[i]['port']}/extention/heartbeat?num={i}")

                if heartbeat_res.status_code != 200:
                    self.__extention_list[i]["heartbeat-fail"] += 1
                else:
                    self.__extention_list[i]["heartbeat-fail"] = 0
            except:
                    self.__extention_list[i]["heartbeat-fail"] += 1
            finally:
                if self.__extention_list[i]["heartbeat-fail"] >= 2:
                    self.__log(f"[Extention] {self.__extention_list[i]['name']} heartbeat failed. Removing extention.")
                    del self.__extention_list[i]
                else:
                    i += 1
                self.__extention_list_lock.release()

    def __heartbeat_check(self):
        while True:
            self.__send_heartbeat()
            time.sleep(5)

    def __init__(self, server_ip: str, port: int, log: callable):
        self.__server_ip = server_ip
        self.__port = port
        self.__extention_list = []
        self.__extention_list_lock = threading.Lock()

        self.__server = Flask(__name__)

        self.__server.add_url_rule("/extention/register", view_func=self.__register_extention, methods=["GET"])
        self.__server.add_url_rule("/extention/forward", view_func=self.__forward_extention, methods=["GET"])
        self.__server.add_url_rule("/extention/backward", view_func=self.__backward_extention, methods=["GET"])
        self.__server.add_url_rule("/extention/test", view_func=self.__extention_test, methods=["GET"])
        self.__log = log

    def __extention_test(self):
        msg = request.args.get("message")
        self.__log(f"[Extention] testing [{msg}]")
        msg = self.execute_extention(msg)
        return msg


    def __register_extention(self):
        name = request.args.get("name")
        ip = request.args.get("ip")
        port = request.args.get("port")
        self.__log(f"[Extention] {name} registering. [{ip}:{port}]")

        self.__extention_list_lock.acquire()

        for i in range(len(self.__extention_list)):
            if self.__extention_list[i]["name"] == name:
                self.__extention_list[i]["ip"] = ip
                self.__extention_list[i]["port"] = port
                self.__extention_list_lock.release()
                return str(i)
        
        self.__extention_list.append({"name": name, "ip": ip, "port": port, "heartbeat-fail": 0})
        self.__extention_list_lock.release()
        return str(len(self.__extention_list) - 1)
    
    def __forward_extention(self):
        name = request.args.get("name")
        self.__log(f"[Extention] {name} moving forward.")

        self.__extention_list_lock.acquire()
        for i in range(len(self.__extention_list)):
            if self.__extention_list[i]["name"] == name:
                if i == 0:
                    self.__extention_list_lock.release()
                    return "Already first extention", 400
                self.__extention_list[i], self.__extention_list[i - 1] = self.__extention_list[i - 1], self.__extention_list[i]
                self.__extention_list_lock.release()
                self.__send_heartbeat()
                return str(i - 1)
        self.__extention_list_lock.release()
        return "Not found extention", 404
    
    def __backward_extention(self):
        name = request.args.get("name")
        self.__log(f"[Extention] {name} moving backward.")

        self.__extention_list_lock.acquire()
        for i in range(len(self.__extention_list)):
            if self.__extention_list[i]["name"] == name:
                if i == len(self.__extention_list) - 1:
                    self.__extention_list_lock.release()
                    return "Already last extention", 400
                self.__extention_list[i], self.__extention_list[i + 1] = self.__extention_list[i + 1], self.__extention_list[i]
                self.__extention_list_lock.release()
                self.__send_heartbeat()
                return str(i + 1)
        self.__extention_list_lock.release()
        return "Not found extention", 404
    
    def execute_extention(self, message: str):
        self.__extention_list_lock.acquire()
        extention_len = len(self.__extention_list)

        execute_result = message
        i = 0
        while i < extention_len:
            try:
                req_data = requests.get(f"http://{self.__extention_list[i]['ip']}:{self.__extention_list[i]['port']}/extention/execute?message={execute_result}")
                if req_data.status_code == 200:
                    execute_result = req_data.text
                    if execute_result == "{Sended-Already}":
                        break
                    i += 1

                else:
                    # 익스텐션 서버가 응답하지 않는다면 제거
                    del self.__extention_list[i]
                    extention_len -= 1
            except:
                pass
        
        self.__extention_list_lock.release()
        return execute_result
    
    def start_server(self):
        threading.Thread(target=self.__heartbeat_check).start()
        #threaded
        t1 = threading.Thread(target=self.__server.run, kwargs={"host": self.__server_ip, "port": self.__port})
        t1.daemon= True
        t1.start()

    


        
        
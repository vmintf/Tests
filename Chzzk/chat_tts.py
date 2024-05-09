import os
import time
import requests
import websocket
import json
import threading

from playsound import playsound
from gtts import gTTS


class ChnConnect(websocket.WebSocketApp):
    def __init__(self, url: str, acc_token, cht_id):
        super().__init__(url,
                         on_open=self.on_open,
                         on_error=self.on_error,
                         on_close=self.on_close,
                         on_message=self.on_message)
        self.acc_token = acc_token
        self.cht_id = cht_id
        self.pinged = False
        websocket.enableTrace(False)

    def data_case(self, x):
        match x:
            case 1:  # 초기 진입 데이터
                data = {"ver": "2", "cmd": 100, "svcid": "game", "cid": self.cht_id,
                        "bdy": {"uid": None, "devType": 2001,
                                "accTkn": self.acc_token,
                                "auth": "READ"}, "tid": 1}
                print(json.dumps(data))
                return json.dumps(data)
            case 2:  # 핑퐁 1
                data = {"ver": "2", "cmd": 10000}
                return json.dumps(data)

            case 3:  # 핑퐁 2
                data = {"ver": "2", "cmd": 0}
                return json.dumps(data)


    def unplayable_letters(self, x):
        match x:
            case "?":
                return "물음표"
            case "ㅏ":
                return "아"
            case "ㅓ":
                return "어"
            case "ㅜ":
                return "우"
            case "ㅔ":
                return "에"
            case "ㅐ":
                return "애"

    def on_open(self, ws):
        print("connected")
        ws.send(data=self.data_case(1))
        time.sleep(1)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_message(self, ws, message):
        # print(json.loads(message))
        # print("bdy" in json.loads(message))
        if "bdy" in json.loads(message):
            # print(json.loads(message)["bdy"][0]['msg'])
            # print("msg" in json.loads(message)["bdy"][0])
            if "msg" in json.loads(message)["bdy"][0]:
                # print("msg" in json.loads(message)["bdy"][0])
                self.tts(json.loads(message)["bdy"][0]["msg"])
        elif {"ver": "2", "cmd": 0} == json.loads(message):
            print("[핑] 서버 연결 유지를 위해, 핑을 전송합니다.")
            self.send(data=self.data_case(2))

    def tts(self, msg):
        print(f"[TTS 플레이] {msg}")
        if msg[0] in ["ㅏ", "ㅓ", "ㅔ", "ㅐ", "?", "ㅜ"]:
            g = gTTS(text=f"{self.unplayable_letters(msg[0])}, {msg[1] if len(msg) == 1 else None}", lang="ko", slow=False)
            urd = os.urandom(16)
            urd_str = str(int.from_bytes(urd, 'little'))[:4]
            g.save(f"./tmp/tmp_{urd_str}.mp3")
            playsound(sound=f"./tmp/tmp_{urd_str}.mp3")
            os.remove(f"./tmp/tmp_{urd_str}.mp3")
            return
        else:
            g = gTTS(text=str(msg), lang="ko", slow=False)
            urd = os.urandom(16)
            urd_str = str(int.from_bytes(urd, 'little'))[:4]
            g.save(f"./tmp/tmp_{urd_str}.mp3")
            playsound(sound=f"./tmp/tmp_{urd_str}.mp3")
            os.remove(f"./tmp/tmp_{urd_str}.mp3")
            return

    # def ping(self):
    #     set_interval: int = 20
    #     while True:
    #         if self.pinged is False:
    #             time.sleep(set_interval)
    #             self.send(self.data_case(3))
    #             self.pinged = True
    #             print("서버 연결 유지를 위해 데이터를 전송합니다.")

    def connect(self):
        try:
            # t = threading.Thread(target=self.ping)
            # t.start()
            self.run_forever(origin="https://chzzk.naver.com", reconnect=1)
        except websocket.WebSocketConnectionClosedException:
            exit(0)


def __api_url(x: int):
    """
    케이스 아이디 목록\n
    1: comm-api.game.naver.com\n
    2: api.chzzk.naver.com\n
    3: wss://kr-ss4.chat.naver.com

    :param x: 케이스 아이디 입니다.
    :return: url 주소
    """
    match x:
        case 1:
            return "https://comm-api.game.naver.com"  # 치지직 알림 등을 다루는 주소
        case 2:
            return "https://api.chzzk.naver.com"  # 치지직 기본 api 주소
        case 3:
            return "wss://kr-ss5.chat.naver.com/chat"  # 치지직 채팅창 웹 소켓 주소


def get_live_status(chnid) -> dict:
    urls = __api_url(2)
    post_url = f"/polling/v2/channels/{chnid}/live-status"
    headers = {"Origin": "https://chzzk.naver.com"}
    with requests.get(f"{urls}{post_url}", headers=headers) as r:
        return r.json()


def get_chat_access_token(chnid) -> dict:
    urls = __api_url(1)
    chatChnId = get_live_status(chnid)["content"]["chatChannelId"]
    post_url = f"/nng_main/v1/chats/access-token?channelId={chatChnId}&chatType=STREAMING"
    headers = {"Origin": "https://chzzk.naver.com"}
    with requests.get(f"{urls}{post_url}", headers=headers) as r:
        return r.json()


if __name__ == "__main__":
    for i in os.listdir("./tmp/"):
        os.remove(f"./tmp/{i}")

    gls = get_live_status("4fa8d17010a569f7739b611da4a6edd2")["content"]["chatChannelId"]
    gcat = get_chat_access_token("4fa8d17010a569f7739b611da4a6edd2")["content"]["accessToken"]

    c = ChnConnect(url=__api_url(3), acc_token=gcat, cht_id=gls)
    c.connect()

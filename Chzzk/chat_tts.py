import os
import time
import requests
import websocket
import json
import random

from playsound import playsound
from gtts import gTTS


class ChnConnect(websocket.WebSocketApp):
    def __init__(self, url: str, acc_token, cht_id):
        super().__init__(url,
                         on_open=self.on_open,
                         on_error=self.on_error,
                         on_close=self.on_close,
                         on_message=self.on_message,
                         on_data=self.on_data)
        self.acc_token = acc_token
        self.cht_id = cht_id

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

            case 2:  # 핑퐁 2
                data = {"ver": "2", "cmd": 0}
                return json.dumps(data)

    def on_open(self, ws):
        print("connected")
        ws.send(data=self.data_case(1))
        time.sleep(1)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_message(self, ws, message):
        print(message)
        match json.loads(message):
            case {"ver": "2", "cmd": 0}:
                return ws.send(self.data_case(2))

            case {"ver": "2", "cmd": 10000}:
                return ws.send(self.data_case(3))

    def on_data(self, ws, message, flags, opcode):
        if json.loads(message)["bdy"][0]["msg"]:
            g = gTTS(
                text=json.loads(message)["bdy"][0]["msg"],
                lang="ko",
                slow=False
            )
            rand = str(int.from_bytes(os.urandom(16), "little"))[:5]
            g.save(f"./tmp/tmp_{rand}.mp3")
            playsound(f'{os.getcwd()}/tmp/tmp_{rand}.mp3')
            os.remove(f"./tmp/tmp_{rand}.mp3")


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
        os.remove(i)

    gls = get_live_status("0441c4d35b2668ebaa0906302665adfc")["content"]["chatChannelId"]
    gcat = get_chat_access_token("0441c4d35b2668ebaa0906302665adfc")["content"]["accessToken"]

    c = ChnConnect(url=__api_url(3), acc_token=gcat, cht_id=gls)
    c.run_forever(origin="https://chzzk.naver.com")

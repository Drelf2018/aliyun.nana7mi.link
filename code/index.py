import httpx
import uvicorn
from bilibili_api.tools.parser import get_fastapi
from fastapi import FastAPI
from fastapi.responses import FileResponse

fastapp = FastAPI()
fastapp.get("/favicon.ico")(lambda: FileResponse("favicon.ico"))
fastapp.get("/getLoginUrl")(lambda: httpx.get("https://passport.bilibili.com/qrcode/getLoginUrl").json())

@fastapp.get("/getLoginInfo")
def getLoginInfo(oauthKey: str):
    js = httpx.post('https://passport.bilibili.com/qrcode/getLoginInfo', data={'oauthKey': oauthKey}).json()
    if js['status']:
        url: str = js['data']['url']
        url = url.replace('https://passport.biligame.com/crossDomain?', '')
        cookies = url.split('&')
        return {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies if cookie.split('=')[0] in ['DedeUserID', 'SESSDATA', 'bili_jct']}
    else:
        return {'DedeUserID': -1}

fastapp.mount("/", get_fastapi())

if __name__ == "__main__":
    uvicorn.run(fastapp, host="0.0.0.0", port=9000)
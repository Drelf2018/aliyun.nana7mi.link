import httpx
import uvicorn
from bilibili_api.tools.parser import get_fastapi
from fastapi import FastAPI
from fastapi.responses import FileResponse
from weibo_poster import get_content, parse_text

app = FastAPI()

@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")

@app.get("/getLoginUrl")
def getLoginUrl():
    return httpx.get("https://passport.bilibili.com/qrcode/getLoginUrl").json()

@app.get("/getLoginInfo")
def getLoginInfo(oauthKey: str):
    js = httpx.post("https://passport.bilibili.com/qrcode/getLoginInfo", data={'oauthKey': oauthKey}).json()
    if js['status']:
        url: str = js['data']['url']
        url = url.replace('https://passport.biligame.com/crossDomain?', '')
        cookies = url.split('&')
        return {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies if cookie.split('=')[0] in ['DedeUserID', 'SESSDATA', 'bili_jct']}
    else:
        return {'DedeUserID': -1}

@app.get("/content")
def content(text: str):
    ts, _ = parse_text(text)
    return get_content(ts)

app.mount("/", get_fastapi())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
import httpx
import uvicorn
from fastapi import FastAPI
from lxml import etree
import bilibili_api
from inspect import iscoroutinefunction as isAsync

# weibo.cn COOKIES
headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'cookie': '_T_WM=4f424bc33be0d62a2d75deaea7663a7e; SUB=_2A25OYyC6DeRhGeFJ6FoX8SjNzjqIHXVtrEDyrDV6PUJbkdAKLUTYkW1NfB9c4mX8iDOuMuRJjRhusVSksNkPl5Az; SCF=AjTyISCkRlwIyYTl4s8fHOI4utjEYr3jQbVCaQ3YIXWD4Bm52DNP72ago_zCTbpsLVpzwTBINAhovOAq7oM4owc.; SSOLoginState=1667715306'
}

app = FastAPI()

@app.get("/weibo/{uid}")
def weibo(uid: str):
    try:
        resp = httpx.get(f'https://weibo.cn/u/{uid}', headers=headers)
        data = etree.HTML(resp.text.encode('utf-8'))
        return {"code": 0, "data": [post[2:] for post in data.xpath('//div[@class="c"]/@id')]}
    except Exception as e:
        return {"code": 1, "error": str(e)}

@app.get("/comment/{mid}")
def comment(mid: str, uid: int):
    try:
        resp = httpx.get(f'https://m.weibo.cn/api/comments/show?id={mid}', headers=headers)
        return {"code": 0, "data": [d for d in resp.json()['data'].get('data', []) if d['user']['id'] == uid]}
    except Exception as e:
        return {"code": 1, "error": str(e)}
    
@app.get("/getLoginUrl")
def getLoginUrl():
    return httpx.get("https://passport.bilibili.com/qrcode/getLoginUrl").json()

@app.get("/getLoginInfo")
def getLoginInfo(oauthKey: str):
    js = httpx.post('https://passport.bilibili.com/qrcode/getLoginInfo', data={'oauthKey': oauthKey}).json()
    if js['status']:
        url: str = js['data']['url']
        url = url.replace('https://passport.biligame.com/crossDomain?', '')
        cookies = url.split('&')
        return {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies if cookie.split('=')[0] in ['DedeUserID', 'SESSDATA', 'bili_jct']}
    else:
        return {'DedeUserID': -1}

@app.get("/{path}")
async def bilibili_api_web(path: str, SESSDATA: str = None, bili_jct: str = None, buvid3: str = None, DedeUserID: str = None):
    pos = bilibili_api
    attr = path.split(".")
    while attr:
        func = attr.pop(0)
        kwargs = None
        if func.endswith(")"):
            func, kwargs = tuple(func.split("("))
            if kwargs != ")":
                kwargs = {k.split("=")[0]: k.split("=")[1] for k in kwargs[:-1].split(",")}
                if "credential" in kwargs:
                    kwargs["credential"] = bilibili_api.Credential(
                        sessdata=SESSDATA,
                        bili_jct=bili_jct,
                        buvid3=buvid3,
                        dedeuserid=DedeUserID
                    )
                    if await kwargs["credential"].check_valid() is False:
                        return {"code": 1, "error": "Cookies Error"}
            else:
                kwargs = None
        pos = getattr(pos, func)
        if kwargs is not None:
            pos = await pos(**kwargs) if isAsync(pos) else pos(**kwargs)
        if pos is None:
            break
    else:
        return {"code": 0, "data": pos if kwargs is not None else await pos() if isAsync(pos) else pos()}
    return {"code": 1, "error": "Path Error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

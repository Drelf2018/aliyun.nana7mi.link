import re
from enum import Enum
from inspect import iscoroutinefunction as isAsync, isfunction as isFn, isclass
from typing import List, Tuple

import bilibili_api
import httpx
import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from lxml import etree

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
pattern = re.compile(r'(?:([:\$\w]+(?:=\w+)?),?)')
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

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

class Parser:
    def __init__(self, var: str):
        self.valid = True
        self.varDict = dict(v.split("<") for v in var.split(",")) if var else dict()

    async def __aenter__(self):
        for key in list(self.varDict.keys()):
            obj, err = await self.parse(self.varDict[key])
            if not err:
                if isinstance(obj, bilibili_api.Credential):
                    self.valid = await obj.check_valid()
                self.varDict["$"+key] = obj
        return self

    async def __aexit__(self, type, value, trace): ...

    async def parse(self, path: str) -> Tuple[any, bool]:
        "分析指令"

        sentences = path.split(".")  # 指令列表
        position: any = bilibili_api  # 起始点

        async def inner() -> bool:
            "递归取值"

            nonlocal position
            if len(sentences) == 0:
                return position is None  # 判断是否取得具体对象

            sentence = sentences.pop(0)
            # 分解执行的函数名、参数、指名参数
            flags: List[str] = pattern.findall(sentence)
            func = flags.pop(0)
            args, kwargs = list(), dict()

            for flag in flags:
                # 假设分为键值形式 利用列表特性从 -1 读取值
                # 即使没有键也能读到值
                arg = flag.split("=")
                # 类型装换
                if arg[-1].endswith(":int"):
                    arg[-1] = int(arg[-1][:-4])
                # 将值与储存的变量替换
                arg[-1] = self.varDict.get(arg[-1], arg[-1])
                # 存入对应的参数、指名参数
                if len(arg) == 1:
                    args.append(arg[0])
                else:
                    kwargs[arg[0]] = arg[1]

            # 开始转移
            if isinstance(position, dict):
                position = position.get(func, None)
            else:
                position = getattr(position, func, None)

            # 赋值参数
            if isAsync(position):
                position = await position(*args, **kwargs)
            elif isFn(position):
                position = position(*args, **kwargs)
            elif isclass(position) and not issubclass(position, Enum):
                position = position(*args, **kwargs)

            # 递归
            return await inner()

        err = await inner()
        return position, err


@app.get("/{path}")
async def bilibili_api_web(response: Response, path: str, var: str = "", max_age: int = -1):
    # 返回头设置
    response.headers["Access-Control-Allow-Origin"] = "*"
    if max_age != -1:
        response.headers["Cache-Control"] = f"max-age={max_age}"
    
    # 先判断是否有效 再分析
    async with Parser(var) as parser:
        if not parser.valid:
            return {"code": 1, "error": "Cookies Error"}
        obj, err = await parser.parse(path)  # 什么 golang 写法
        if not err:
            return {"code": 0, "data": obj}
        else:
            return {"code": 2, "error": "Path Error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

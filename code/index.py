import httpx
import uvicorn
from fastapi import FastAPI
from lxml import etree
from bilibili_api import user, Credential

# weibo.cn COOKIES
headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'cookie': 'SUB=_2A25P9OE_DeRhGeFM7lQU8i7PyjmIHXVtFo93rDV6PUJbktAKLVrskW1NQNxRT3IFuL3bXA569DreXZlw2TSGQXb_; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWsM7qnLH5XXeUsRC8WX5b75NHD95QNeo-cSKz7e02fWs4DqcjPi--RiKnXiKnci--4i-zEi-2ReKzpe0nt; _T_WM=4f424bc33be0d62a2d75deaea7663a7e'
}

app = FastAPI()

@app.get("/weibo/{uid}")
def weibo(uid: str):
    try:
        resp = httpx.get(f'https://weibo.cn/u/{uid}', headers=headers)
        data = etree.HTML(resp.text.encode('utf-8'))
        return {"code": 1, "data": [post[2:] for post in data.xpath('//div[@class="c"]/@id')]}
    except Exception as e:
        return {"code": 0, "error": str(e)}
    

@app.get("/comment/{mid}")
def comment(mid: str, uid: int):
    try:
        resp = httpx.get(f'https://m.weibo.cn/api/comments/show?id={mid}', headers=headers)
        return {"code": 1, "data": [d for d in resp.json()['data'].get('data', []) if d['user']['id'] == uid]}
    except Exception as e:
        return {"code": 0, "error": str(e)}

@app.get("/info")
async def info(DedeUserID: str, SESSDATA: str, bili_jct: str):
    if await Credential(sessdata=SESSDATA, bili_jct=bili_jct).check_valid():
        return await user.User(DedeUserID).get_user_info()
    else:
        return {'mid': -1}
    
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

@app.get('/get_list')
async def get_list():
    data = etree.HTML(httpx.get('https://acrnm.com/?sort=default&filter=txt').text)
    Products = dict()
    for tr in data.xpath('.//tbody/tr'):
        for td in tr.xpath('./td'):
            tag = td.xpath("./@class")[0][39:-5]
            if tag == "title":
                name = td.xpath('.//span/text()')[0]
                if name not in Products:
                    Products[name] = dict()
                    Products[name]["price"] = dict()
            elif tag == "variant":
                variant = dict()
                for span in td.xpath('./div/span'):
                    color = '/'.join(span.xpath("./div/span/text()"))
                    size = '/'.join(span.xpath("./span/text()"))       
                    variant[color] = size
            elif tag == "price":
                val = td.xpath('.//span/text()')
                if val and val[0] != "0.00 EUR":
                    Products[name]["price"][val[0]] = variant

    imgs = etree.HTML(httpx.get("https://acrnm.com/").text)
    for name in Products:
        try:
            img = "https://acrnm.com/" + imgs.xpath(f'.//span[text()="{name}"]/../img/@src')[0]
            Products[name]['img'] = img
        except:
            ...

    return Products

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

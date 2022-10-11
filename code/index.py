import httpx
import uvicorn
from fastapi import FastAPI
from fastapi import Body
from lxml import etree
from bilibili_api import user, Credential

app = FastAPI()

@app.get("/self")
async def self(sessdata: str, bili_jct: str, buvid3: str):
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
    if await credential.check_valid():
        return await user.get_self_info(credential)
    else:
        return {'mid': -1}
    
@app.get("/info")
async def self(uid: str, sessdata: str, bili_jct: str, buvid3: str):
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
    if await credential.check_valid():
        return await user.User(uid, credential).get_user_info()
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
        return {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies}
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

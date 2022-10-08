import uvicorn
import httpx
from lxml import etree
from fastapi import FastAPI

app = FastAPI()

@app.get('/get_list')
async def get_list():
    data = etree.HTML(httpx.get('https://acrnm.com/?sort=default&filter=txt').text)
    Products = dict()
    for tr in data.xpath('.//tbody/tr'):
        for td in tr.xpath('./td'):
            match td.xpath("./@class")[0][39:-5]:
                case "title":
                    name = td.xpath('.//span/text()')[0]
                    if name not in Products:
                        Products[name] = dict()
                        Products[name]["price"] = dict()
                case "variant":
                    variant = dict()
                    for span in td.xpath('./div/span'):
                        color = '/'.join(span.xpath("./div/span/text()"))
                        size = '/'.join(span.xpath("./span/text()"))       
                        variant[color] = size
                case "price":
                    if val := td.xpath('.//span/text()'):
                        if val[0] != "0.00 EUR":
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

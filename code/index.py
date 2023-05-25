import uvicorn
from bilibili_api.tools.parser import get_fastapi
from fastapi import FastAPI
from fastapi.responses import FileResponse
from weibo_poster import get_content, parse_text

app = FastAPI()


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


@app.get("/content")
def parse_content(text: str):
    ts, _ = parse_text(text)
    return get_content(ts)


app.mount("/", get_fastapi())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
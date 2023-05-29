import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from weibo_poster import get_content, parse_text

app = FastAPI()


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


@app.get("/content")
def parse(text):
    ts, _ = parse_text(text)
    return get_content(ts)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
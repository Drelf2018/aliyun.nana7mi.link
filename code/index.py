import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from bilibili_api.tools.parser import get_fastapi
import httpx
app = FastAPI()


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


@app.get("/laplace")
def _(roomid: int):
    return httpx.get(f"https://workers.meta48.live/api/bilibili/room-conn-info/{roomid}", params={"builtInAuth": 1}).json()
    

app.mount("/", get_fastapi())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
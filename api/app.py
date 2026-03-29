from fastapi import FastAPI
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 프로젝트 루트를 path에 두어 pipeline import 가능하게 함
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.jbexport_daily import run_daily

app = FastAPI()

@app.get("/")
def home():
    return {"message": "JBEXPORT API Server Running"}

@app.get("/test")
def test():
    return {"status": "ok"}

@app.get("/files")
def files():
    if not os.path.exists("data"):
        return {"files": []}
    return {"files": os.listdir("data")}

@app.get("/crawl")
def crawl():
    url = "https://example.com"  # 크롤링할 사이트
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.title.text
    return {"title": title}

@app.get("/download")
def download():
    if not os.path.exists("data"):
        os.makedirs("data")

    file_url = "https://example.com"
    res = requests.get(file_url)

    with open("data/sample.html", "wb") as f:
        f.write(res.content)

    return {"result": "downloaded"}


@app.post("/api/jbexport/run")
def run_jbexport_pipeline():
    return run_daily()
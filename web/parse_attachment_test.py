import requests
import re
from bs4 import BeautifulSoup

session = requests.Session()

detail_url = "https://www.jbexport.or.kr/other/spWork/spWorkSupportBusiness/detail1.do"
params = {
    "menuUUID": "402880867c8174de017c819251e70009",
    "spSeq": "b563bbbb46824cedb07adca8455f00af"
}

res = session.get(detail_url, params=params, verify=False)
print("상태:", res.status_code)

soup = BeautifulSoup(res.text, "html.parser")

files = []
for tag in soup.find_all(onclick=True):
    onclick = tag.get("onclick", "")
    m = re.search(r"fn_fileDown\(['\"](.+?)['\"]\)", onclick)
    if m:
        files.append({"fileUUID": m.group(1), "pathNum": "6"})

if files:
    print("첨부파일:", files)
else:
    print("첨부파일 없음")
import os
import urllib3
urllib3.disable_warnings()

os.makedirs("downloads", exist_ok=True)

download_url = "https://www.jbexport.or.kr/downloadFile.do"

for f in files:
    params = {"pathNum": f["pathNum"], "fileUUID": f["fileUUID"]}
    r = session.get(download_url, params=params, verify=False)
    fname = f"downloads/{f['fileUUID']}.bin"
    with open(fname, "wb") as out:
        out.write(r.content)
    print(f"저장: {fname} ({len(r.content)} bytes)")
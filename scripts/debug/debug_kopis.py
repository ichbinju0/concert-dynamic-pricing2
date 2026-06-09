"""KOPIS API 응답 필드 확인용 스크립트"""
from dotenv import load_dotenv
import pathlib, os, requests
from xml.etree import ElementTree as ET

load_dotenv(dotenv_path=pathlib.Path(".env"), override=True)
KEY = os.getenv("KOPIS_API_KEY", "")

# 1) 공연 목록 검색 (장르: 대중음악 = CC)
resp = requests.get(
    "http://www.kopis.or.kr/openApi/restful/pblprfr",
    params={"service": KEY, "rows": 3, "cpage": 1, "shcate": "CCCD",
            "stdate": "20250101", "eddate": "20251231"},
    timeout=10,
)
print("=== 공연 목록 ===")
content = resp.content.decode("utf-8", errors="replace")
print("raw:", content[:500])
root = ET.fromstring(content)
for db in root.findall("db"):
    mt20id = db.findtext("mt20id", "")
    name   = db.findtext("prfnm", "")
    state  = db.findtext("prfstate", "")
    dates  = f"{db.findtext('prfpdfrom','')} ~ {db.findtext('prfpdto','')}"
    print(f"  {mt20id} | {name} | {state} | {dates}")

# 2) 공연 상세 (첫 번째 공연)
first_id = root.find("db/mt20id")
if first_id is not None:
    resp2 = requests.get(
        f"http://www.kopis.or.kr/openApi/restful/pblprfr/{first_id.text}",
        params={"service": KEY},
        timeout=10,
    )
    root2 = ET.fromstring(resp2.text)
    print(f"\n=== 상세 필드 ({first_id.text}) ===")
    for child in root2.find("db") or []:
        print(f"  {child.tag}: {child.text}")

"""KOPIS 공연장 API - 좌석 배치도 이미지 확인"""
from dotenv import load_dotenv
import pathlib, os, requests
from xml.etree import ElementTree as ET

load_dotenv(dotenv_path=pathlib.Path(".env"), override=True)
KEY = os.getenv("KOPIS_API_KEY", "")

# 1) BTS 공연에서 나온 mt10id: FC001169 로 공연장 상세 조회
mt10id = "FC001169"
resp = requests.get(
    f"http://www.kopis.or.kr/openApi/restful/prfplc/{mt10id}",
    params={"service": KEY},
    timeout=10,
)
content = resp.content.decode("utf-8", errors="replace")
root = ET.fromstring(content)
db = root.find("db")

print("=== 공연장 상세 필드 ===")
if db is not None:
    for child in db:
        print(f"  {child.tag}: {child.text}")

# 2) 공연장 목록에서 KSPO돔 검색
resp2 = requests.get(
    "http://www.kopis.or.kr/openApi/restful/prfplc",
    params={"service": KEY, "rows": 5, "cpage": 1, "shprfnm": "KSPO"},
    timeout=10,
)
content2 = resp2.content.decode("utf-8", errors="replace")
root2 = ET.fromstring(content2)
print("\n=== KSPO 공연장 검색 ===")
for db2 in root2.findall("db"):
    mt10id2 = db2.findtext("mt10id", "")
    name2   = db2.findtext("fcltynm", "")
    print(f"  {mt10id2} | {name2}")
    for child in db2:
        if child.text and "http" in str(child.text):
            print(f"    → 이미지 URL 발견! {child.tag}: {child.text}")

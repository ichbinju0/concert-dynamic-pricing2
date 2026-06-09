"""official_price 없이 WTP 기반 floor/ceiling 테스트"""
from dotenv import load_dotenv
import pathlib
load_dotenv(dotenv_path=pathlib.Path(".env"), override=True)

from main import run_agent

result = run_agent({
    "artist":           "DAY6",
    "followers_in_10k": 281.8,
    "concert_index":    0,
    "venue_image_path": "data/venue.png",
})

kpi  = result.get("kpi", {})
cons = result.get("constraints", {})
lp   = result.get("pricing_result", {})

print(f"\n{'='*50}")
print(f"Floor   : {cons.get('floor', 0):,}원  (WTP 자동)")
print(f"Ceiling : {cons.get('ceiling', 0):,}원  (WTP 자동)")
print(f"Revenue Gain: +{kpi.get('revenue_gain_pct', 0):.1f}%")
print(f"\nD-day별 구역별 추천 가격:")
for interval, v in lp.items():
    print(f"\n  [{interval}] 기준가 {int(v['price']):,}원")
    for zone, price in v.get("zone_prices", {}).items():
        print(f"    {zone:<20}: {price:>10,}원")
if result.get("errors"):
    print(f"\nErrors: {result['errors']}")

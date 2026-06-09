from dotenv import load_dotenv
import pathlib
load_dotenv(dotenv_path=pathlib.Path(".env"), override=True)
from tools.kopis_tool import list_concerts
from datetime import date
print(f"오늘: {date.today()}")
for c in list_concerts("DAY6"):
    print(f"[{c['index']}] {c['date']}  {c['name']}  @ {c['venue']}")

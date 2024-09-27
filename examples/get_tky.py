import datetime
from yfjpscraper import get_data

tick_id = 8951
start_dt = datetime.date(2024, 9, 26)
end_dt = datetime.date(2024, 9, 27)
resp = get_data(tick_id, start_dt, end_dt)

for data in resp:
    print(data)

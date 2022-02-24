import datetime
from yfjpscraper import get_data

tick_id = 3496
start_dt = datetime.date(2021, 1, 1)
end_dt = datetime.date(2021, 3, 1)
resp = get_data(tick_id, start_dt, end_dt)

for data in resp:
    print(data)

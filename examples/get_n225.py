import datetime
from yfjpscraper import get_data

tick_id = 998407
start_dt = datetime.date(2017, 1, 1)
end_dt = datetime.date(2017, 2, 1)
resp = get_data(tick_id, start_dt, end_dt)

for data in resp:
    print(data)

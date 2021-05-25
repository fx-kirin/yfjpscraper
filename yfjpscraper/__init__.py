# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 fx-kirin <fx.kirin@gmail.com>
#
# Distributed under terms of the MIT license.

"""

"""
import datetime
import json
import logging
import re
from urllib.parse import urlencode

import bs4
import kanirequests

from .parser import parse_html, parse_json, parse_json_split

logger = logging.getLogger("yf_parser")
page_url = "http://info.finance.yahoo.co.jp/history/"


def get_data_stock(
    tick_id: str,
    start_dt: datetime.date,
    end_dt: datetime.date,
):

    from kanirequests import KaniRequests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    session = kanirequests.KaniRequests(
        headers=headers,
    )
    root_url = f"https://finance.yahoo.co.jp/quote/{tick_id}/history"
    result = session.get(root_url)
    jwtToken = re.search(r"\"jwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text).group(1)
    stockJwtToken = re.search(
        r"\"stocksJwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text
    ).group(1)
    page = 1
    result.url
    from_date = start_dt.strftime("%Y%m%d")
    to_date = end_dt.strftime("%Y%m%d")
    code = re.search(r"\d{4}\.T", result.url).group(0)
    page_url = "https://finance.yahoo.co.jp/web-pc-stocks/ajax"
    headers = {
        "x-z-jwt-token": stockJwtToken,
        "Accept": "*/*",
        "Origin": "https://finance.yahoo.co.jp",
        "Content-Type": "application/json",
        "Referer": result.url,
    }
    get_split = False
    while True:
        params = {
            "id": "priceHistory",
            "params": {
                "code": code,
                "fromDate": from_date,
                "toDate": to_date,
                "timeFrame": "daily",
                "page": page,
            },
        }
        logger.info(page_url)
        resp = session.post(
            page_url, data=json.dumps(params).replace(" ", ""), headers=headers
        )
        json_data = resp.json()
        if get_split is False:
            yield from parse_json_split(json_data)
            get_split = True
        stop = yield from parse_json(json_data)
        if stop:
            break
        page = page + 1


def get_data_futures(
    tick_id: str,
    start_dt: datetime.date,
    end_dt: datetime.date,
):
    session = kanirequests.HTMLSession()
    page = 1
    while True:
        params = {
            "code": tick_id,
            "sy": start_dt.year,
            "sm": start_dt.month,
            "sd": start_dt.day,
            "ey": end_dt.year,
            "em": end_dt.month,
            "ed": end_dt.day,
            "tm": "d",
            "p": page,
        }
        logger.info(page_url + "?" + urlencode(params))
        resp = session.get(page_url, params=params)
        if not resp.ok:
            break
        html_soup = bs4.BeautifulSoup(resp.text, "html.parser")
        kanirequests.open_html_in_browser(resp.content)
        stop = yield from parse_html(html_soup)
        if stop:
            break
        page = page + 1


def get_data(tick_id: str, start_dt: datetime.date, end_dt: datetime.date):
    tick_id = str(tick_id)
    if len(tick_id) > 4:
        return get_data_futures(tick_id, start_dt, end_dt)
    else:
        return get_data_stock(tick_id, start_dt, end_dt)

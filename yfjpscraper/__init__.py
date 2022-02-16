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
from pathlib import Path
from urllib.parse import urlencode

import bs4
import kanirequests
from kanirequests import KaniRequests

from .parser import parse_html, parse_json, parse_json_split

logger = logging.getLogger("yf_parser")
page_url = "http://info.finance.yahoo.co.jp/history/"


def get_data_stock(
    session,
    result,
    tick_id: str,
    start_dt: datetime.date,
    end_dt: datetime.date,
):
    from_date = start_dt.strftime("%Y%m%d")
    to_date = end_dt.strftime("%Y%m%d")
    code = re.search(r"\d{4}\.\w", result.url).group(0)
    jwtToken = re.search(r"\"jwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text).group(1)
    if "stocksJwtToken" in result.text:
        stockJwtToken = re.search(
            r"\"stocksJwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text
        ).group(1)
        query_name = "priceHistory"
        page_url = "https://finance.yahoo.co.jp/web-pc-stocks/ajax"
        inner_params = {
                "code": code,
                "fromDate": from_date,
                "toDate": to_date,
                "timeFrame": "daily",
        }
    elif "etfJwtToken" in result.text:
        stockJwtToken = re.search(
            r"\"etfJwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text
        ).group(1)
        query_name = "etfHistory"
        page_url = "https://finance.yahoo.co.jp/web-etf/ajax"
        inner_params = {
                "stockCode": code,
                "fromDate": from_date,
                "toDate": to_date,
                "timeFrame": "d",
        }
    Path("/tmp/sssresult.txt").write_text(result.text)

    page = 1
    headers = {
        "x-z-jwt-token": stockJwtToken,
        "Accept": "*/*",
        "Origin": "https://finance.yahoo.co.jp",
        "Content-Type": "application/json",
        "Referer": result.url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    get_split = False
    while True:
        inner_params["page"] = page
        params = {
            "id": query_name,
            "params": inner_params
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
    session = KaniRequests()
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
        if "該当する期間のデータはありません。" in resp.text:
            break
        if "該当する銘柄はありません。" in resp.text:
            logger.info("Target stock was not found.")
            break
        html_soup = bs4.BeautifulSoup(resp.text, "html.parser")
        stop = yield from parse_html(html_soup)
        if stop:
            break
        page = page + 1


def get_data(tick_id: str, start_dt: datetime.date, end_dt: datetime.date):
    tick_id = str(tick_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    session = kanirequests.KaniRequests(
        headers=headers, proxy={"http": "192.168.100.108:8888", "https": "192.168.100.108:8888"}
    )
    root_url = f"https://finance.yahoo.co.jp/quote/{tick_id}/history"
    result = session.get(root_url)
    if "指定されたページまたは銘柄は存在しません。" in result.text:
        return get_data_futures(tick_id, start_dt, end_dt)
    else:
        return get_data_stock(session, result, tick_id, start_dt, end_dt)

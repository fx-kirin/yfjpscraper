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
from requests.models import HTTPError

from .parser import parse_html, parse_json, parse_json_split, parse_json_of_future

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
    else:
        raise NotImplementedError(f"jwt token doen't found url:{result.url}")
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
    session,
    result,
    tick_id: str,
    start_dt: datetime.date,
    end_dt: datetime.date,
):
    from_date = start_dt.strftime("%Y%m%d")
    to_date = end_dt.strftime("%Y%m%d")
    code = re.search(r"\d{4}\.\w", result.url).group(0)
    
    if "indicesJwtToken" in result.text:
        indeciesJwtToken = re.search(
            r"\"indicesJwtToken\":\"([0-9a-zA-Z\._\-]*)\"", result.text
        ).group(1)
        query_name = "priceHistory"
    else:
        raise NotImplementedError(f"jwt token doen't found url:{result.url}")
    page = 1
    while True:
        page_url = f"https://finance.yahoo.co.jp/bff-pc-indices/v1/main/index/price/history/{tick_id}.T?fromDate={from_date}&page={page}&size=20&timeFrame=d&toDate={to_date}"
        headers = {
            "jwt-token": indeciesJwtToken,
            "Accept": "*/*",
            "Origin": "https://finance.yahoo.co.jp",
            "Content-Type": "application/json",
            "Referer": result.url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        resp = session.get(
            page_url, headers=headers
        )
        json_data = resp.json()
        stop = yield from parse_json_of_future(json_data)
        if stop:
            break
        page = page + 1


def get_data(tick_id: str, start_dt: datetime.date, end_dt: datetime.date, proxy=None):
    tick_id = str(tick_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    session = kanirequests.KaniRequests(
        headers=headers, proxy=proxy
    )
    root_url = f"https://finance.yahoo.co.jp/quote/{tick_id}/history"
    result = session.get(root_url)
    if result.status_code != 200:
        raise HTTPError(f"status code is {result.status_code} url:{root_url}")
    if len(tick_id) == 4:
        return get_data_stock(session, result, tick_id, start_dt, end_dt)
    else:
        return get_data_futures(session, result, tick_id, start_dt, end_dt)

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 fx-kirin <fx.kirin@gmail.com>
#
# Distributed under terms of the MIT license.

"""

"""
import datetime
from typing import List, Dict
import bs4
import re

fmt = "%Y年%m月%d日"


def _parse_fund(data: List[str]) -> Dict:
    return {
        "date": datetime.datetime.strptime(data[0], fmt).date(),
        "share_value": float(data[1]),
        "total_value": float(data[2]),
    }


def _parse_index(data: List[str]) -> Dict:
    return {
        "date": datetime.datetime.strptime(data[0], fmt).date(),
        "open_v": float(data[1]),
        "high_v": float(data[2]),
        "low_v": float(data[3]),
        "close_v": float(data[4]),
    }


def _parse_stock(data: List[str]) -> Dict:
    return {
        "date": datetime.datetime.strptime(data[0], fmt).date(),
        "open_v": float(data[1]),
        "high_v": float(data[2]),
        "low_v": float(data[3]),
        "close_v": float(data[4]),
        "volume": float(data[5]),
        "final_v": float(data[6]),
    }


def _parse_stock_division(data: List[str]) -> Dict:
    matched = re.search(u"分割: (.+)株 -> (.+)株", data[1])
    return {
        "date": datetime.datetime.strptime(data[0], fmt).date(),
        "division": "division",
        "division_from": float(matched.group(1)),
        "division_to": float(matched.group(2)),
    }


def parse_json(json_data) -> bool:
    if "priceHistory" in json_data:
        json_data = json_data["priceHistory"]
    data_rows = json_data["history"]["histories"]
    if len(data_rows) == 0:
        return True
    for row in data_rows:
        yield {
            "date": datetime.datetime.strptime(row["baseDate"], fmt).date(),
            "open_v": float(row["openPrice"].replace(",", "")),
            "high_v": float(row["highPrice"].replace(",", "")),
            "low_v": float(row["lowPrice"].replace(",", "")),
            "close_v": float(row["closePrice"].replace(",", "")),
            "volume": float(row["volume"].replace(",", "")),
            "final_v": float(row["adjustedClosePrice"].replace(",", "")),
        }
    if "splitHistories" in json_data["history"]:
        split = json_data["history"]["splitHistories"]
    return False


def parse_json_split(json_data):
    if "priceHistory" in json_data:
        json_data = json_data["priceHistory"]
    if "splitHistories" in json_data["history"]:
        splits = json_data["history"]["splitHistories"]

        for split in splits:
            yield {
                "date": datetime.datetime.strptime(split["splitDate"], fmt).date(),
                "division": "division",
                "division_from": float(1),
                "division_to": float(split["splitRate"].replace(",", "")),
            }


def parse_html(html_soup: bs4.BeautifulSoup) -> bool:
    table = html_soup.find("table", {"class": "boardFin yjSt marB6"})
    table_rows = table.find_all("tr")
    header = table_rows[0]
    data_rows = table_rows[1:]
    if len(data_rows) == 0:
        return True
    n_cols = len(header.find_all("th"))
    if n_cols == 3:
        _parse_f = _parse_fund
    elif n_cols == 5:
        _parse_f = _parse_index
    elif n_cols > 5:
        _parse_f = _parse_stock
    else:
        raise ValueError("invalid table, n_cols = {}".format(n_cols))

    for row in data_rows:
        data = [t.text.replace(",", "") for t in row.find_all("td")]
        if len(data) == 2:
            yield _parse_stock_division(data)
        else:
            try:
                yield _parse_f(data)
            except Exception as e:
                print("Error occured", e)
    return False

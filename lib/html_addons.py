#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 13:35:19 2016

@author: mints
"""
from lxml import html
from astropy.coordinates import SkyCoord


def replace_empty(table, values):
    for value in values:
        for cell in table.xpath('//td[contains(., "%s")]' % value):
            cell.text = ''
    return table


def add_distance_column(table, ra_column, de_column, center,
                        has_head=False, has_body=False,
                        new_location=None):
        head = table.getchildren()[0]
        if has_head:
            head = head.getchildren()[0]
        if new_location is not None:
            head.getchildren()[new_location].text = 'Distance'
        else:
            th = html.Element('th')
            th.text = 'Distance'
            head.append(th)
        if has_body:
            rows = table.getchildren()[1].getchildren()
        else:
            rows = table.getchildren()[1:]
        for row in rows:
            ra = float(row.getchildren()[ra_column].text)
            de = float(row.getchildren()[de_column].text)
            c = SkyCoord(ra, de, unit="deg")
            separation = (c.separation(center)*3600).to_string(decimal=True)
            if new_location is not None:
                cell = row.getchildren()[new_location]
                cell.text = separation
                cell.remove(cell.getchildren()[0])
            else:
                td = html.Element('td')
                td.text = separation
                row.append(td)
        return table



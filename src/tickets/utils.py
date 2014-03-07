# -*- coding: utf-8 -*-
from datetime import date, timedelta

def today():
    return date.today()

def tomorrow():
    return date.today() + timedelta(days=1)

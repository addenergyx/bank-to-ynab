# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 10:28:50 2021

@author: david
"""

from returns import returns
from live_portfolio import live_portfolio
from helpers import get_portfolio, get_summary

def updates():
    get_portfolio()
    returns()
    get_summary()
    live_portfolio()
    
#updates()
# -*- coding: utf-8 -*-
"""
Created on Sun May  3 16:53:31 2020

@author: david
"""

import os
import pandas as pd
from sqlalchemy import create_engine

def get_tokens():

    db_URI = os.getenv('AWS_DATABASE_URL')
    
    engine = create_engine(db_URI)
    
    data = pd.read_sql_table("banking", con=engine, index_col='index')

    return data

def update_database():
    db_URI = os.getenv('AWS_DATABASE_URL')
    engine = create_engine(db_URI)
        
    data = pd.read_csv(r"C:\Users\david\OneDrive\Desktop\banktoks.csv")   
    data.to_sql('banking', engine, if_exists='replace')
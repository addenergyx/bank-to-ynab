# -*- coding: utf-8 -*-
"""
Created on Mon May 25 15:22:43 2020

@author: david
"""
import pandas as pd
import os
import psycopg2

"""
The psycopg2 is over 2x faster than SQLAlchemy on small table. 
This behavior is expected as psycopg2 is a database driver for postgresql while SQLAlchemy is general ORM library.
"""

## table hosted in AWS RDS

#connect to db
def connect():
    return psycopg2.connect(os.getenv('AWS_DATABASE_URL'))

def get_all_bank_accounts(connection):
    ## use with statement to ensure connection closes after
    with connection:
        cur = connection.cursor()
        cur.execute("SELECT * FROM banking")
        rows = cur.fetchall()
        cur.close()
        return rows

def get_all_ynab_linked_accounts(connection):
    with connection:
        cur = connection.cursor()
        cur.execute("SELECT * FROM banking WHERE ynab_account_id IS NOT NULL")
        rows = cur.fetchall()
        cur.close()
        return rows


def add_bank_account(connection, bank, access_token, ynab_account_id):
    with connection:
        cur = connection.cursor()
        cur.execute("INSERT INTO banking (bank, access_token, ynab_account_id) VALUES (%s, %s, %s);", 
                    (bank, access_token, ynab_account_id))
        connection.commit()
        cur.close()


# #connect to db
# con = psycopg2.connect(os.getenv('AWS_DATABASE_URL'))
# # con = psycopg2.connect(
# #         host="",
# #         database="",
# #         user="",
# #         password="")

# #cursor
# cur = con.cursor()
# cur.execute("INSERT INTO banking (index, bank, access_token, ynab_account_id) VALUES (DEFAULT, %s, %s, %s);", (1,2,3))

# ## can cur.execute(insert new bank info from plaid) use values(%s, %s) , (input, input) to prevent sql injection
# ## must commit edit after
# #commit the transaction
# ## con.commit()


# #execute sql query
# cur.execute("SELECT * FROM banking")

# rows = cur.fetchall() #returns tuples (bank, access_token, ynab_account_id)

# for r in rows:
#     print(f"bank: {r[1]} token: {r[2]} ynab: {r[3]}")


# #close connections to prevent leaks

# #close cursor
# cur.close()

# #close connection
# con.close()






















        
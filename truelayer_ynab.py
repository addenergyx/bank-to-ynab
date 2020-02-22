#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 00:53:49 2020

@author: ubu
"""
import requests
#import pandas as pd
from pprint import pprint

url = "https://auth.truelayer.com/connect/token"

payload = "grant_type=refresh_token&client_id=personalfinance-3bc1a1&client_secret=8b5c5190-ea17-4b38-9a4f-2f808a1d8fe6&refresh_token=4xUi8khL5-K8duy3Y2HfECvP9zxMpFRKEdMvhhtVfCw"
headers = {
    'User-Agent': "PostmanRuntime/7.20.1",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Postman-Token': "f280117f-5de2-461c-bfb0-0f683c2401d4,0171e387-217d-436b-a5b4-57e0d23a4654",
    'Host': "auth.truelayer.com",
    'Content-Type': "application/x-www-form-urlencoded",
    'Accept-Encoding': "gzip, deflate",
    'Content-Length': "166",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
    }

response = requests.request("POST", url, data=payload, headers=headers)

url = "https://api.truelayer.com/data/v1/accounts/c0c191726d09ce9c64aaaa41477a1b39/transactions"

headers = {
    'Authorization': "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjE0NTk4OUIwNTdDOUMzMzg0MDc4MDBBOEJBNkNCOUZFQjMzRTk1MTAiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJGRm1Kc0ZmSnd6aEFlQUNvdW15NV9yTS1sUkEifQ.eyJuYmYiOjE1ODA3MzcxOTgsImV4cCI6MTU4MDczODkzNywiaXNzIjoiaHR0cHM6Ly9hdXRoLnRydWVsYXllci5jb20iLCJhdWQiOlsiaHR0cHM6Ly9hdXRoLnRydWVsYXllci5jb20vcmVzb3VyY2VzIiwiaW5mb19hcGkiLCJhY2NvdW50c19hcGkiLCJ0cmFuc2FjdGlvbnNfYXBpIiwiYmFsYW5jZV9hcGkiLCJjYXJkc19hcGkiLCJkaXJlY3RfZGViaXRzX2FwaSIsInN0YW5kaW5nX29yZGVyc19hcGkiXSwiY2xpZW50X2lkIjoicGVyc29uYWxmaW5hbmNlLTNiYzFhMSIsInN1YiI6Im9pa0xKbjE0RmxOV1cvT1VUakY0WmIvb3V3cDRPUXBQRDJmSDlmR0ZKRkk9IiwiYXV0aF90aW1lIjoxNTgwNzI1MTUyLCJpZHAiOiJsb2NhbCIsImNvbm5lY3Rvcl9pZCI6Im9iLWJhcmNsYXlzIiwiY3JlZGVudGlhbHNfa2V5IjoiMzE0NGQ1ZGRiNWViNzI5YzJhOWE1NDM1YjNmNzFiODU5M2IxMDczOWU2Yzc1YzkyYjdjYjc3MWFjZjQyODdjNSIsInByaXZhY3lfcG9saWN5IjoiRmViMjAxOSIsImNvbnNlbnRfaWQiOiIwZWUyM2JhYy05MzdjLTQ0NzMtYmU0Yi0yYmVkN2RjYzFhMjQiLCJwcm92aWRlcl9hY2Nlc3NfdG9rZW5fZXhwaXJ5IjoiMjAyMC0wMi0wM1QxNDowOTo1Ny44OTUwMDAwKzAwOjAwIiwicHJvdmlkZXJfcmVmcmVzaF90b2tlbl9leHBpcnkiOiIyMDIwLTA1LTAzVDA5OjE4OjExLjAwMDAwMDArMDA6MDAiLCJzb2Z0d2FyZV9zdGF0ZW1lbnRfaWQiOiIyTnVnNFBXRE52SGJCUjFrSkQ5aERhIiwiYWNjb3VudF9yZXF1ZXN0X2lkIjoiQkFSQ0xBWVMtQS0xMDAwMDAwMjM2NDc1NSIsInNjb3BlIjpbImluZm8iLCJhY2NvdW50cyIsInRyYW5zYWN0aW9ucyIsImJhbGFuY2UiLCJjYXJkcyIsImRpcmVjdF9kZWJpdHMiLCJzdGFuZGluZ19vcmRlcnMiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsicHdkIl19.Y_RtdOapJ_2qj2L5mSan1lIM1M-F-Kpht-26cU2QNUR5RthEwipL4BmgbahSotkSI4BdPXkrzgAeGvH0CWRCRjU_NGAgROCyFBRp92qUWN5fM4iMWpe64kcz-qV2o2CWoIiCGaqhzDlcFQbR064LrbMtzd8hGWMX8kNO81TIHcgTUg4YqIsZExdCOOnxF0m7Q7WZBh1ivtRe-wv9tmuOTS3a3OtfN1cyQIxLUiHyQKx5f6xx_kEEKrLtnoZ-DvtcdK3Um532yI2_XSN3xCfWYT41B1gw0EAZ2Ew1CZAhRtcEGslURTkVHhACfH6csOQy2p1UEOEyQ8dEnUuiX1dEfw",
    'User-Agent': "PostmanRuntime/7.20.1",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Postman-Token': "d23766b1-df58-4b76-b918-b8e89b89e97b,e8cae90a-81c9-43a2-95bb-fed6d926559d",
    'Host': "api.truelayer.com",
    'Accept-Encoding': "gzip, deflate",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
    }

response = requests.request("GET", url, headers=headers)

#if response.json()['status'] successful

j = response.json()['results']
for a in j:
    a['date'] = a.pop('timestamp')
    a['payee_name'] = a.pop('description')
    a['account_id'] = '89d72a49-07de-47f9-8f26-c6c68fef75d3'
    a['import_id'] = a['transaction_id'] # Pervent duplications in ynab
    a['amount'] = int(a['amount'] * 1000) # YNAB uses milliunits, 1,000 milliunits equals "one" unit
    a['cleared'] = 'cleared'

#barclays_df = pd.DataFrame(j)

import ynab
from ynab.rest import ApiException

configuration = ynab.Configuration()

configuration.api_key['Authorization'] = 'f274ed018ba18c0600c6fbc00a9e59fbd78118374504ab5c2de543824c33b116'
configuration.api_key_prefix['Authorization'] = 'Bearer'

api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
budget_id = '11bf1cd1-469c-4c21-9436-65bc652932cd'

transactions = ynab.BulkTransactions(j)

try:
    # Bulk create transactions
    api_response = api_instance.bulk_create_transactions(budget_id, transactions)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e)




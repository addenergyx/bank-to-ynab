#!/bin/sh
source /etc/profile

cd /
cd home/pi/bank-to-ynab
python3 bank_to_ynab.py &
python3 coop_transactions_notification.py &
cd /

from cs50 import SQL
import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, transform, transform_single, minus

db = SQL("sqlite:///finance.db")

#purchase_row = db.execute("SELECT * FROM purchase WHERE username = :username", username='Gilson' )

#symbols = {}

#master = []
#for i in purchase_row:
#  dic = i
#  """ Clean up the Dictionary"""
 # del dic['id']
 # del dic['username']

 # """ Retrieve the company name """
  #symbol = dic['symbol']
 # symbol=symbol.upper()
#  api_response = lookup(symbol)
#  company_name = api_response['name']

  
  #if symbol not in symbols:
    #symbols[symbol] = 1
 # elif symbol in symbols:
 #   symbols[symbol] += 1

  
#  print(symbol, company_name, dic["quantity"], dic["price"], dic["total"])

#print(symbols)


#username = db.execute("SELECT username FROM users WHERE id=:id", id = 1)
#username = username[0]['username']
user_purchased_data = db.execute("SELECT * FROM purchase WHERE username=:username", username='hash')
user_sold_data = db.execute("SELECT symbol, quantity, price, date FROM sold WHERE username=:username", username='hash')

"""purchased_stocks = transform_single(user_purchased_data, 'symbol')
purchased_prices = transform_single(user_purchased_data, 'price')
purchased_qtys = transform_single(user_purchased_data, 'quantity')
purchased_date = transform_single(user_purchased_data, 'date')

sold_stocks = transform_single(user_sold_data, 'symbol')
sold_prices = transform_single(user_sold_data, 'price')
sold_qtys = transform_single(user_sold_data, 'quantity')
sold_date = transform_single(user_sold_data, 'date')

p_data = []
s_data = []

i = 0
while i < len(purchased_stocks):
    p_data.append((purchased_stocks[i], purchased_qtys[i], usd(purchased_prices[i]), purchased_date[i]))
    i=i+1

i = 0
while i < len(sold_stocks):
    s_data.append((sold_stocks[i], minus(sold_qtys[i]), usd(sold_prices[i]), sold_date[i]))
    i=i+1

data = p_data + s_data

data.sort(key=lambda L: datetime.strptime(L[3], '%Y-%m-%d %H:%M:%S'))

print(data)"""

print(user_purchased_data)

print()
print()

for data in user_purchased_data:
  print(data.id)

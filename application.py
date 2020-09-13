import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import apology, login_required, lookup, usd, transform, transform_single, minus

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control{{ i[4] }}"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    username = db.execute("SELECT username FROM users WHERE id=:id", id = session["user_id"])
    username = username[0]['username']
    purchased_symbols = db.execute("SELECT symbol, SUM(quantity) FROM purchase WHERE username = :username GROUP BY symbol", username = username)
    sold_symbols = db.execute("SELECT symbol, SUM(quantity) FROM sold WHERE username = :username GROUP BY symbol", username= username)
    purchased_data = transform(purchased_symbols, 'symbol', 'SUM(quantity)')
    sold_data = transform(sold_symbols, 'symbol', 'SUM(quantity)')

    print(purchased_data)
    print(sold_data)

    index = {}
    clean = {}

    for key, value in purchased_data.items():
        if key in sold_data:
            purchased_qty = purchased_data[key]
            sold_qty = sold_data[key]
            actual_amt = purchased_qty-sold_qty
            index[key] = actual_amt
        else:
            index[key]=purchased_data[key]


    for key, value in index.items():
        if index[key] != 0:
            clean[key] = value

    
    symbols = []
    shares = []
    price = []
    total = []
    company_name = []
    data = []

    for i in clean.keys():
        symbols.append(i)
    
    
    for i in clean.values():
        shares.append(i)
    
    
    for i in symbols:
        response = lookup(i)
        name = response['name']
        current_price = response['price']
        company_name.append(name)
        price.append(current_price)
        
    t = 0
    while t < len(symbols):
        tot = shares[t] * price [t]
        total.append(tot)
        t+=1


    cash_row = db.execute("SELECT cash FROM users where id=:id", id = session["user_id"])
    cash = cash_row[0]["cash"]

    asset = (sum(total) + cash)

    i = 0
    while i < len(symbols):
        data.append((symbols[i], company_name[i], shares[i], usd(price[i]), usd(total[i])))
        i=i+1

    return render_template("index.html", data = data, balance = usd(cash), asset= usd(asset), name=username)




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    # Returns the buy page of the request method is get
    if request.method == "GET":
        return render_template("buy.html")
    else:
        # Get the users inputs in the html form and store them in a variable for easy reference
        symbol = (request.form.get("symbol").upper())
        shares = int(request.form.get("shares"))

        # Ensures the shares qty to be bought is an integer and is greater or equals to 1
        if type(shares) != int and shares < 1:
            return apology("Shares amount must be a number", 302)
       
        # Look up the unit price for the stock the user wants to buy
        API_RESPONSE = (lookup(symbol))
        stock_unit_price = API_RESPONSE["price"]
        
        # This just makes it easier to refer to the user id anywhere in this function
        # I can`t think of anything more strenious than having to hard code "user_id" everytime :)
        id = session["user_id"]

        # Here we get the cash balance of the user from the database for vetting purposes
        rows = db.execute("SELECT * FROM users WHERE id = :id",id=id)
        balance = rows[0]['cash']
        username = rows[0]['username']
        
        # Calculate the total expense by multiplying the unit price with the number of shares to be bought
        total_expense = stock_unit_price * shares
        
        # Date of Transaction
        now = datetime.now()
        date = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # Processing of the transaction if conditions are satisfied
        if balance >= total_expense:
            # Send the details of the purchase to the PURCHASE TABLE
            db.execute("INSERT INTO PURCHASE (username, symbol, price, quantity, date, total) VALUES(:username, :symbol, :price, :quantity, :date, :total)",
            username=username, symbol=symbol, price=stock_unit_price, quantity=shares, date=date, total=total_expense)
            
            # Substact the expenditure from the existing balance
            balance -= total_expense

            # Insert the new balance into the users cash balance in the USERS TABLE
            db.execute("UPDATE users SET cash= (:balance) WHERE id= (:id)", balance=balance, id=id)

            # Render this page if all was succesful
            render_template("bought.html", shares=shares, symbol=symbol, amount=total_expense)

            # Take to user back to the home page i.e Dashboard in this case
            return redirect("/")
            
        else:
            # Return this page if the user lacks funds sufficient enough to purchase this stock
            return apology("You lack sufficient funds to perfom this transaction", 302)
    


@app.route("/history")
@login_required
def history():
    id = session["user_id"]

    rows = db.execute("SELECT * FROM users WHERE id = :id",id=id)
    username = rows[0]['username']

    user_purchased_data = db.execute("SELECT symbol, quantity, price, date FROM purchase WHERE username=:username", username=username)
    user_sold_data = db.execute("SELECT symbol, quantity, price, date FROM sold WHERE username=:username", username=username)

    purchased_stocks = transform_single(user_purchased_data, 'symbol')
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

    data = p_data+s_data
    data.sort(key=lambda L: datetime.strptime(L[3], '%Y-%m-%d %H:%M:%S'))
    
    return render_template("history.html", data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    # This just returns the quote`s page
    if request.method == "GET":
        return render_template("quote.html")
    else:
         # Send a request through the API to get the stock symbol data through API response
         response = lookup(request.form.get("quote"))
         return render_template("quoted.html", response=response)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Returns the register page if request is a GET method
    if request.method == "GET":
        return render_template("register.html")
    
    # If request method is POST
    else:
        # Storing user credentials in  variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # Ensures the username field is not blank
        if not username:
            return apology("must provide a username", 403)
        
        # Ensures the password field is not blank
        elif not password:
            return apology("must provide a password", 403)  

        # Ensures the confirmation field is not blank  
        elif not confirm:
            return apology("Please confirm your password", 403)
        
        # Ensures the the password matches with the confirmation field
        if password != confirm:
            return apology("Password does not match", 403)

        # Generates a hash for password to facilitate storage in the database
        password_hash = generate_password_hash(password)        

        #Inserts the new user credentials into the database
        db.execute("INSERT INTO USERS (username, hash) VALUES(:username, :hash)", username=username, hash=password_hash)
        
        # Takes user back to the homepage i.e Login in this case
        return redirect("/")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "GET":
            return render_template("change.html")
    if request.method == "POST":
        # If the request method is a post method

        # Extract the inputed data and make a variable of each of them
        old_password = request.form.get("old")
        new_password = request.form.get("new")
        confirmation = request.form.get("confirm")
        
        # Get the users old password from the database 
        row = db.execute("SELECT * FROM users WHERE id=:id", id = session["user_id"])
        users_hash = row[0]["hash"]

        # Ensure the old password is correct
        if not check_password_hash(users_hash, old_password):
            return apology("Wrong old password", 100)

        # Ensure the password is the same with its confirmation
        if new_password != confirmation:
            return apology("Your passwords does not match", 102)

        # Hash the new password
        new_hash = generate_password_hash(new_password)

        # insert into the database
        db.execute("UPDATE users SET hash = :hash WHERE id=:id", hash=new_hash, id=session["user_id"])

        return redirect("/") 


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Extracting necesary parameters from database to clean inputed data"""
    # Extract the users username from database
    rows = db.execute("SELECT * FROM users WHERE id = :id",id= session["user_id"])
    username = rows[0]['username']

    # Extract the user`s owned stock symbols and their respective qty
    symbol_qty_row = db.execute("SELECT symbol, SUM(quantity) FROM purchase WHERE username=:username GROUP BY SYMBOL", username=username)
    symbol_qty = transform(symbol_qty_row, 'symbol', 'SUM(quantity)')#Transforms the fetched complex list to a simple dictionary
    owned_symbols = []

    # Iterates over the symbol/qty dictionary keys to isolate just the owned stock symbols 
    for i in symbol_qty.keys():
        owned_symbols.append(i)

    # Returns the "sell" page with its the stock symbols as options in a select element
    if request.method == "GET":
        return render_template("sell.html", symbols = owned_symbols)
    
    # If the request method is a POST request then do the following 
    else:
        # Extract the inputs and make a variable of them
        symbol_input = (request.form.get("symbol").upper())
        shares_input = int(request.form.get("shares"))

        # Ensures the stock symbol field is not empty
        if not symbol_input:
            return apology("No symbol", 404)

        # Ensures the user has the very stock symbol he/she is trying to sell
        if symbol_input not in owned_symbols:
            return apology("You don`t own that stock", 404)

        # Ensures the shares qty field is not empty
        if not shares_input:
            return apology("Shares cannot be empty", 404)

        # Confirm that the shares qty inputed by user is a number and an int.
        if type(shares_input) != int:
            return apology("Shares must be a number", 302)
        
        # Confirm that the user owns a sufficient qty of the inputed shares to sell
        if shares_input > symbol_qty[symbol_input]:
            return apology("Insufficient shares", 302)

        # If the above conditions are satisfied, Please proceed with processing the transaction.

        # Fetch the unit price for the inputed stock symbol from the API
        stock_data = lookup(symbol_input)
        stock_price = stock_data["price"]
        
        # Calculate the selling price that is incured by multiplying the stock unit price by the qty to be sold
        price_recovered = stock_price * shares_input
        
        # Get the users existing cash balance from the users table,
        # so as to increment(Update) it by the sold price as income
        user_data = db.execute("SELECT cash FROM users  WHERE id=:id", id=session["user_id"])
        cash = user_data[0]["cash"]
        income = cash + price_recovered
        db.execute("UPDATE users SET cash = :cash WHERE id=:id", cash=income, id=session["user_id"])
       
        # Get the date of the transaction for posterity sake
        now = datetime.now()
        date = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # Send the details of this transaction to the PURCHASE table
        db.execute("INSERT INTO sold (username, symbol, price, quantity, date, total) VALUES(:username, :symbol, :price, :quantity, :date, :total)",
            username = username, symbol = symbol_input, price = stock_price, quantity=shares_input, date=date, total= income)

        # Takes user back to the homepage i.e dashboard in this case        
        return redirect("/")
    
        
        






def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run()

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import re

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Checks user's stocks and shares
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # Checks the cash balance in the user's account
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]

    # These variables get the total value
    total_value = cash
    grand_total = cash

    # itetating over stocks to add price/total value
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["value"] = stock["price"] * stock["total_shares"]
        total_value += stock["value"]
        grand_total += stock["value"]

    return render_template(
        "index.html",
        stocks=stocks,
        cash=usd(cash),
        total_value=usd(total_value),
        grand_total=usd(grand_total),
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        # Checks if a symbol was provided and if the number was positive.
        if not symbol:
            return apology("Please provide a symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive number of shares")

        # Checks if the symbol exists
        quote = lookup(symbol)
        if quote is None:
            return apology("Symbol not found.")
        # Checks the price and calculates the total cost to then check the cash in the user account.
        price = quote["price"]
        total_cost = int(shares) * price

        cash = db.execute(
            "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
        )[0]["cash"]
        if cash < total_cost:
            return apology("Not enough funds.")

        # Updates user's table
        db.execute(
            "UPDATE users SET cash = cash - :total_cost WHERE id = :user_id",
            total_cost=total_cost,
            user_id=session["user_id"],
        )

        # Adds purchase to the purchases history
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
            user_id=session["user_id"],
            symbol=symbol,
            shares=shares,
            price=price,
        )

        flash(f"bought {shares} shares of {symbol} for{usd(total_cost)}!")
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # query for user's transactions (AGAIN)
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = :user_id ORDER BY timestamp DESC",
        user_id=session["user_id"],
    )

    return render_template("history.html", transactions=transactions)
    return apology("TODO")


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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        if not quote:
            return apology("Invalid Symbol.", 400)
        return render_template("quote.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user ID
    session.clear()

    # Declares the regex needed standards
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pat = re.compile(reg)

    if request.method == "POST":
        # Makes sure the user SUBMITTED AN USERNAME
        if not request.form.get("username"):
            return apology("Sorry, please provide an username", 400)

        # Makes sure the user submitted a password
        if not request.form.get("password"):
            return apology("Sorry, please provide a password", 400)

        # Makes sure the confirmation field was correctly submited
        if not request.form.get("confirmation"):
            return apology("Please confirm your password", 400)

        if re.search(pat, request.form.get("password")) == None:
            return apology(
                "Please add special characters such as /, *, @, ?, #... to your password and upper case letters",
                400,
            )

        # Makes sure the password and confirmation fields are the same and match.
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("The passwords do not match.", 400)

        # Makes sure the email fields are filled and the emails are the same and match
        if request.form.get("email") != request.form.get("email-confirmation"):
            return apology("Fields don't match", 400)

        # Makes sure the email is not used
        emailrows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        if len(emailrows) != 0:
            return apology("email already taken", 400)

        # Queries through the username database
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Makes sure a similar username does not exist
        if len(rows) != 0:
            return apology("Username already taken", 400)

        # Insert user into the database
        db.execute(
            "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
            request.form.get("username"),
            request.form.get("email"),
            generate_password_hash(request.form.get("password")),
        )

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # searches on the DB for a new inserted user
        session["user_id"] = rows[0]["id"]

        # Redurect to homepage
        return redirect("/", 200)

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # gets user's stocks
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # form gets submitted
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if not symbol:
            return apology("Must provide a symbol.")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("Must provide a positive number of shares")
        else:
            shares = int(shares)

        # iterates through the stocks.
        for stock in stocks:
            if stock["symbol"] == symbol:
                if stock["total_shares"] < shares:
                    return apology("Not Enough Shares.")
                else:
                    # get quote
                    quote = lookup(symbol)
                    if quote is None:
                        return apology("symbol not found")
                    price = quote["price"]
                    total_sale = shares * price

                    # Now lets update the user's table
                    db.execute(
                        "UPDATE users SET cash = cash + :total_sale WHERE id = :user_id",
                        total_sale=total_sale,
                        user_id=session["user_id"],
                    )

                    # adds the sale to the sales history
                    db.execute(
                        "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                        user_id=session["user_id"],
                        symbol=symbol,
                        shares=-shares,
                        price=price,
                    )

                    flash(f"sold {shares} shares of {symbol} for {usd(total_sale)}!")
                    return redirect("/")

            return apology("Symbol not found")

    else:
        return render_template("sell.html", stocks=stocks)


@app.route("/passwordreset", methods=["GET", "POST"])
@login_required
def reset():
    """Resets user's password (Must be logged in)"""
    # Declares the regex needed standards
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pat = re.compile(reg)

    # Resets the password if the user is logged in
    if request.method == "POST":
        # Makes sure the user submitted a password
        if not request.form.get("password"):
            return apology("Sorry, please provide a password", 400)

        # Makes sure the confirmation field was correctly submited
        if not request.form.get("confirmation"):
            return apology("Please confirm your password", 400)

        if re.search(pat, request.form.get("password")) == None:
            return apology(
                "Please add special characters such as /, *, @, ?, #... to your password and upper case letters",
                400,
            )

        # Makes sure the password and confirmation fields are the same and match.
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("The passwords do not match.", 400)

        db.execute(
            "UPDATE users SET hash = :new_hash WHERE id = :user_id",
            user_id=session["user_id"],
            new_hash=generate_password_hash(request.form.get("password")),
        )
        return redirect("/", 200)
    else:
        return render_template("passwordreset.html")

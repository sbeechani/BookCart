from flask import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cartdata.db'

db = SQLAlchemy(app)

class userdetails(db.Model):    
    __tablename__="users"
    user_id = db.Column(db.Integer, autoincrement=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String(30))
    phone = db.Column(db.String)

    def __init__(self,name,email,password,phone):
        self.name=name
        self.email=email
        self.password=password
        self.phone=phone

class cartdetails(db.Model):
    __tablename__="items"
    cid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email=db.Column(db.String)
    bookname = db.Column(db.String(100))
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __init__(self,email,bookname,qty,price):
        self.email=email
        self.bookname=bookname
        self.qty=qty
        self.price=price

class allorders(db.Model):
    __tablename__="orders"
    inc = db.Column(db.Integer, primary_key=True, autoincrement=True)
    oid = db.Column(db.Integer)
    email=db.Column(db.String)
    bookname = db.Column(db.String(100))
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __init__(self,oid,email,bookname,qty,price):
        self.oid=oid
        self.email=email
        self.bookname=bookname
        self.qty=qty
        self.price=price
    

class bookdetails(db.Model):    
    __tablename__="books"
    bookid = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50))
    price = db.Column(db.Float)

    def __init__(self,bookid,name,price):
        self.bookid=bookid
        self.name=name
        self.price=price

def addbooks():
    alldata = bookdetails.query.all()
    if(len(alldata)==0):
        data = json.load(open("books.json"))
        books=data["items"]
        for i in range(10):
            bid= "b"+str(i)
            if(books[i]["saleInfo"]["saleability"]== "FOR_SALE"):
                price=books[i]["saleInfo"]["listPrice"]["amount"]
            else:
                price=0
            newbook = bookdetails(bid,books[i]["volumeInfo"]["title"],price)
            db.session.add(newbook)
            db.session.commit()

def buildstring(result):
    booklist =[]
    blist = []
    totalprice = 0 
    for book in result:
        blist = []
        blist.append(str(book.bookname))
        blist.append(str(book.qty))
        totalprice+=book.price
        blist.append(str(book.price))
        booklist.append(blist)
    booklist.append(totalprice)
    return booklist  
    
@app.route("/")
def main():
    return render_template('welcome.html')

@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/show_books")
def display():
    global current_email
    cartbooks = cartdetails.query.filter_by(email = current_email)
    su=0
    bookstring =[]
    if(cartbooks):
        bookstring = buildstring(cartbooks)
        for b in cartbooks:
            su+=b.qty
    data = json.load(open("books.json"))
    return render_template('cart.html',books=data["items"], sum=su, cartbooks=bookstring)

@app.route("/addbook/<title>")
def addbook(title):
    global current_email
    book = cartdetails.query.filter_by(email = current_email).filter_by(bookname = title).first()    
    if(book):
        j = book.qty
        if(j==3):
            flash("Cant add more items of this book",'danger')
        else:
            book.qty = j+1
            thisbook = bookdetails.query.filter_by(name = title).first()
            thisprice = thisbook.price
            book.price = thisprice*(j+1)            
            db.session.commit()
    else:
        thisbook = bookdetails.query.filter_by(name = title).first()
        thisprice = thisbook.price
        newentry = cartdetails(current_email,title,1,thisprice)
        db.session.add(newentry)
        db.session.commit()
    return redirect(url_for('display'))

@app.route("/removebook/<title>")
def removebook(title):
    global current_email
    book = cartdetails.query.filter_by(email = current_email).filter_by(bookname = title).first()
    if(book):
        j = book.qty
        if(j>0):
            book.qty = j-1
            if(j-1 > 0):
                thisbook = bookdetails.query.filter_by(name = title).first()
                thisprice = thisbook.price
                book.price = thisprice*(j-1)
            else:
                db.session.delete(book)
            db.session.commit()
        else:
            flash("No items of this book to remove",'danger') 
    else:
        flash("No items of this book to remove",'danger')        
    return redirect(url_for('display'))

@app.route("/checkout")
def checkout():
        global current_email
        booksincart = cartdetails.query.filter_by(email = current_email)
        if(booksincart.count()== 0):
            flash("No books in your cart to checkout!",'danger')
            return redirect(url_for('display'))
        user = userdetails.query.filter_by(email = current_email).first()
        name = user.name
        phone = user.phone
        bookstring = buildstring(booksincart)
        price = round(bookstring[-1],2)
        tax = round(0.1*price,2)
        totalprice = round(price+tax,2)
        return render_template('checkoutpage.html', cartbooks=bookstring, price=price, tax=tax, totalprice=totalprice, name=name, phone=phone)

@app.route("/placeorder")
def placeorder():
        global current_email
        booksincart = cartdetails.query.filter_by(email = current_email)
        previd = allorders.query.first()
        if(previd):
            previd = allorders.query.order_by(allorders.oid.desc()).first()
            currentid = previd.oid+1
        else:
            currentid=1
        for book in booksincart:
            newentry = allorders(currentid,current_email,book.bookname,book.qty,book.price)
            db.session.add(newentry)
        cartdetails.query.filter_by(email = current_email).delete()
        db.session.commit()
        return redirect(url_for('main'))

@app.route("/vieworders",methods=['POST'])
def vieworders():
    current_email = request.form['name'] 
    phoneno = request.form['phone']
    pastorders = allorders.query.filter_by(email = current_email)
    if(pastorders.count()==0):
        flash("Sorry, no previous orders to display",'danger')
        return redirect(url_for('display'))
    orderarray = []
    if(pastorders):
        currentid = (allorders.query.filter_by(email = current_email).first()).oid
        neworder=[]
        tprice = 0
        for book in pastorders:
            if book.oid==currentid:
                blist = []
                blist.append(str(book.bookname))
                blist.append(str(book.qty))
                tprice+=book.price
                blist.append(str(book.price))
                neworder.append(blist)
            else:
                neworder.append(["totalprice including tax:","",round(1.1*tprice,2)])
                tprice=0
                orderarray.append(neworder)
                neworder=[]
                currentid = book.oid
                blist = []
                blist.append(str(book.bookname))
                blist.append(str(book.qty))
                blist.append(str(book.price))
                neworder.append(blist)
        neworder.append(["totalprice including tax:","",round(1.1*tprice,2)])
        orderarray.append(neworder)
    return render_template('vieworder.html',cartbooks=orderarray, email=current_email, phone=phoneno)
    

@app.route("/",methods=['POST'])
def validate():
    global current_name
    global current_email
    userid = request.form['email']
    userpwd = request.form['password']
    thisuser = userdetails.query.filter_by(email = userid).first()
    if (thisuser):
        if(thisuser.password == userpwd):
            current_name=thisuser.name
            current_email=userid
            return redirect(url_for('display'))
        else:
            errormsg="Invalid password"       
            return render_template('welcome.html',errormsg=errormsg)
        
    else:
        errormsg="No such entry! Please signup"       
        return render_template('welcome.html',errormsg=errormsg)

@app.route("/signup",methods=['POST'])
def add():
    global current_name
    global current_email
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    allusers = userdetails.query.all()
    for u in allusers:
        if (u.email == email):
           errormsg="Email already registered!"       
           return render_template('signup.html',errormsg=errormsg) 
    else:
        current_name=name
        current_email=email
        newuser = userdetails(name,email,password,phone)
        db.session.add(newuser)
        db.session.commit()
        return redirect(url_for('display'))
    

if __name__ == "__main__":
    current_name ="sneha"
    current_email="sneha@email"
    addbooks()
    app.secret_key='sneha'
    app.run(debug=True)

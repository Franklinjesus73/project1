import os
import json
import requests


from flask import Flask, session, render_template, url_for, request, flash, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import jsonify
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#INDEX
@app.route("/")
def index():
    return render_template('index.html')

#REGISTRO DE USUARIO
@app.route("/add_contact", methods=['GET','POST'])
def add_contact():
    if request.method == 'POST':
            #VERIFICANDO EL NOMBRE DE USUARIO
        userCheck = db.execute("SELECT * FROM registro WHERE username = :username",
                                {"username":request.form.get("username")}).fetchone()
            #SI EL USUARIO ESTA EN USO
        if userCheck:
            flash("user in use", "danger")
            return render_template("registro.html")

             #VERIFICANDO EL email
        userCheck1 = db.execute("SELECT * FROM registro WHERE email = :email",
                                {"email":request.form.get("email")}).fetchone()
            #SI EL email ESTA EN USO
        if userCheck1:
            flash("email in use", "danger")
            return render_template("registro.html")

     #INSERTANDO EN LA BASE DE DATOS
        name = request.form['name']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        secure_password = sha256_crypt.encrypt(str(password))

       #SI LAS CONTRASENAS COINCIDEN
        if password == confirm:
            db.execute('INSERT INTO registro (name, lastname, username, email, password) VALUES (:name, :lastname, :username, :email, :password)',
                         {"name": name, "lastname": lastname, "username": username, "email": email, "password": secure_password})
            #ENVIAR A LA BASE DE DATOS
            db.commit()
            print('done')
            flash('Account created', 'success')
            return redirect("login") 
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("registro.html")

    #INICIAR SESION

#INICIO DE SESION
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        usernamedata=db.execute('SELECT username from registro WHERE username=:username',{'username':username}).fetchone()
        passwordata=db.execute('SELECT password from registro WHERE username=:username',{'username':username}).fetchone()       
        
        if passwordata is None:
            flash('Must provide a PASSWORD', "danger")
            return render_template("login.html")

        if usernamedata is None:
            flash("Must provide a USERNAME", "danger")
            return render_template("login.html")
     
        else:
            for password_data in passwordata:
                if sha256_crypt.verify(password, password_data):
                    session['log'] = True
                    session["user_id"] = id
                    session["user_name"] = username

                    flash('You are now login', "success")
                    return render_template('results.html')
                else:
                    flash('Incorrect password', "danger")
                    return render_template("login.html") 

    else:
        return render_template("login.html") 

#CERRAR SESION
@app.route("/logout", methods=["GET"])
def logout():

    if request.method == 'GET':
        if not session.get("log"):
            flash("You are not logged in", 'danger')
            return redirect("/login")
        else:
            session["log"] = False
            session["user_id"] = None
            flash("Logout successful", "success")
            return redirect("/")

#BUSQUEDA  
@app.route("/search", methods=["GET"])
def search():

    if request.method == 'GET':
        if not session.get("log"):
            flash("You are not logged in", 'danger')
            return render_template("login.html")
        else:
                return render_template("results.html")  
@app.route("/results", methods=["GET"])

def results():

    if not session.get("log"):
        flash("You are not logged in", 'danger')
        return render_template("login.html")

    if not request.args.get("book"):
        flash('you must provide a book', 'danger')
        return render_template("results.html")

    busqueda = "%" + request.args.get("book") + "%"

    busqueda = busqueda.title()
    
    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :busqueda OR \
                        title LIKE :busqueda OR \
                        author LIKE :busqueda LIMIT 15",
                        {"busqueda": busqueda})
                        
    
    # Books not founded
    if rows.rowcount == 0:
        flash("we can't find books with that description", 'danger')
        return render_template("results.html")
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)

@app.route("/author", methods=["GET"])
def author():


    if not session.get("log"):
        flash("You are not logged in", 'danger')
        return render_template("login.html")

    if not request.args.get("book"):
        flash('you must provide a book', 'danger')
        return render_template("results.html")

    busqueda = "%" + request.args.get("book") + "%"

    busqueda = busqueda.title()
    
    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        author LIKE :busqueda LIMIT 10",
                        {"busqueda": busqueda})
                        
    
    # Books not founded
    if rows.rowcount == 0:
        flash("we can't find books with that description", 'danger')
        return render_template("results.html")
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)

@app.route("/isbn", methods=["GET"])
def isbn():


    if not session.get("log"):
        flash("You are not logged in", 'danger')
        return render_template("login.html")

    if not request.args.get("book"):
        flash('you must provide a book', 'danger')
        return render_template("results.html")

    busqueda = "%" + request.args.get("book") + "%"

    busqueda = busqueda.title()
    
    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :busqueda LIMIT 10",
                        {"busqueda": busqueda})
                        
    
    # Books not founded
    if rows.rowcount == 0:
        flash("we can't find books with that description", 'danger')
        return render_template("results.html")
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)
#Busqueda

@app.route('/book/<string:isbn>', methods = ['GET', 'POST'])
def singleBook(isbn):

    isbn = isbn
    username = session['user_name']
    
    apiCall = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "D0WReQQIG0vNma5L4g", "isbns": isbn })
    apidata = apiCall.json()
    dbdata = db.execute(" SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    dbreviews = db.execute('SELECT * FROM reviews WHERE isbn = :isbn', {'isbn': isbn}).fetchall()

    Review = db.execute('SELECT * FROM public.reviews WHERE isbn = :isbn and username = :username ', {'isbn': isbn, 'username': username}).fetchall()
    if request.method == 'POST':
        if Review: 
            flash('You alreaddy submitted a review on this book', 'danger')
        else: 
            rating = int(request.form['rating'])
            comment = request.form['comment']
            username = session['user_name']
            fisbn = request.form['isbn']
            db.execute("INSERT into reviews (username, rating, comment, isbn) Values (:username, :rating, :comment, :isbn)", {'username': username, 'rating': rating, 'comment': comment, 'isbn': fisbn})
            db.commit()
            flash('Awesome, Your review added successfully', 'success')
            return render_template('results.html')
    
    if apiCall:
        return render_template('book.html', apidata = apidata, dbdata = dbdata, dbreviews = dbreviews, isbn = isbn )
    else:
        flash('Data fetch failed')
        return render_template('book.html')

@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):     
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if data==None:
        return render_template('error.html')

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "D0WReQQIG0vNma5L4g", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']

    x = {
    "title": data.title,
    "author": data.author,
    "year": data.year,
    "isbn": isbn,
    "review_count": work_ratings_count,
    "average_rating": average_rating
    }
        # api=json.dumps(x)
        # return render_template("api.json",api=api)
    return  jsonify(x)



if __name__ == '__main__':
    app.run(debug =True)

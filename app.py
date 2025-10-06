from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import sys

app = Flask(__name__)
app.secret_key = 'abcd2123445'

# Configuration for MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'library-system'

# Initialize MySQL
mysql = MySQL(app)

# Utility Functions
def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

# Authentication Functions
def login_user(email, password):
    cursor = get_cursor()
    cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password,))
    user = cursor.fetchone()
    return user

def logout_user():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)

# Route Definitions
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))

    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        user = login_user(email, password)
        if user:
            session['loggedin'] = True
            session['userid'] = user['id']
            session['name'] = user['first_name']
            session['email'] = user['email']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))
# Manage Books   
@app.route("/books", methods=['GET', 'POST'])
def books():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("""
        SELECT 
            book.bookid, book.picture, book.name, book.status, 
            book.isbn, book.no_of_copy, book.updated_on, 
            author.name as author_name, category.name AS category_name, 
            rack.name As rack_name, publisher.name AS publisher_name 
        FROM 
            book 
        LEFT JOIN 
            author ON author.authorid = book.authorid 
        LEFT JOIN 
            category ON category.categoryid = book.categoryid 
        LEFT JOIN 
            rack ON rack.rackid = book.rackid 
        LEFT JOIN 
            publisher ON publisher.publisherid = book.publisherid
    """)
    books = cursor.fetchall()

    cursor.execute("SELECT authorid, name FROM author")
    authors = cursor.fetchall()

    cursor.execute("SELECT publisherid, name FROM publisher")
    publishers = cursor.fetchall()

    cursor.execute("SELECT categoryid, name FROM category")
    categories = cursor.fetchall()

    cursor.execute("SELECT rackid, name FROM rack")
    racks = cursor.fetchall()

    return render_template("books.html", books=books, authors=authors, publishers=publishers, categories=categories, racks=racks)
# Manage Users
@app.route("/users", methods=['GET', 'POST'])
def users():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute('SELECT * FROM user')
    users = cursor.fetchall()

    return render_template("users.html", users=users)

@app.route("/save_user", methods=['POST'])
def save_user():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        role = request.form['role']
        action = request.form['action']

        if action == 'updateUser':
            user_id = request.form['userid']
            cursor.execute('UPDATE user SET first_name = %s, last_name = %s, email = %s, role = %s WHERE id = %s',
                           (first_name, last_name, email, role, user_id,))
        else:
            password = request.form['password']
            cursor.execute('INSERT INTO user (first_name, last_name, email, password, role) VALUES (%s, %s, %s, %s, %s)',
                           (first_name, last_name, email, password, role))

        mysql.connection.commit()

    return redirect(url_for('users'))

@app.route("/edit_user", methods=['GET'])
def edit_user():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = request.args.get('userid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    return render_template("edit_user.html", user=user)

@app.route("/view_user", methods=['GET'])
def view_user():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = request.args.get('userid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    return render_template("view_user.html", user=user)

@app.route("/password_change", methods=['GET', 'POST'])
def password_change():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    message = ''
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']
        confirm_pass = request.form['confirm_pass']

        if not password or not confirm_pass:
            message = 'Please fill out the form !'
        elif password != confirm_pass:
            message = 'Confirm password is not equal!'
        else:
            cursor = get_cursor()
            cursor.execute('UPDATE user SET password = %s WHERE id = %s', (password, user_id,))
            mysql.connection.commit()
            message = 'Password updated !'

    return render_template("password_change.html", message=message)
# Delete User
@app.route("/delete_user", methods=['GET'])
def delete_user():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = request.args.get('userid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM user WHERE id = %s', (user_id,))
    mysql.connection.commit()

    return redirect(url_for('users'))

# Manage Books
@app.route("/edit_book", methods=['GET'])
def edit_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    book_id = request.args.get('bookid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM book WHERE bookid = %s', (book_id,))
    book = cursor.fetchone()

    return render_template("edit_book.html", book=book)

@app.route("/save_book", methods=['POST'])
def save_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        book_name = request.form['name']
        isbn = request.form['isbn']
        no_of_copy = request.form['no_of_copy']
        author = request.form['author']
        publisher = request.form['publisher']
        category = request.form['category']
        rack = request.form['rack']
        status = request.form['status']
        action = request.form['action']

        if action == 'updateBook':
            book_id = request.form['bookid']
            cursor.execute('UPDATE book SET name = %s, status = %s, isbn = %s, no_of_copy = %s, categoryid = %s, authorid = %s, rackid = %s, publisherid = %s WHERE bookid = %s',
                           (book_name, status, isbn, no_of_copy, category, author, rack, publisher, book_id,))
        else:
            cursor.execute('INSERT INTO book (name, status, isbn, no_of_copy, categoryid, authorid, rackid, publisherid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                           (book_name, status, isbn, no_of_copy, category, author, rack, publisher))

        mysql.connection.commit()

    return redirect(url_for('books'))

@app.route("/delete_book", methods=['GET'])
def delete_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    book_id = request.args.get('bookid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM book WHERE bookid = %s', (book_id,))
    mysql.connection.commit()

    return redirect(url_for('books'))

# Manage Issue Book
@app.route("/list_issue_book", methods=['GET', 'POST'])
def list_issue_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("SELECT * FROM issued_book")
    issue_books = cursor.fetchall()

    return render_template("issue_book.html", issue_books=issue_books)

@app.route("/save_issue_book", methods=['POST'])
def save_issue_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        book_id = request.form['book']
        user_id = request.form['users']
        expected_return_date = request.form['expected_return_date']
        return_date = request.form['return_date']
        status = request.form['status']
        action = request.form['action']

        if action == 'updateIssueBook':
            issue_book_id = request.form['issueBookId']
            cursor.execute('UPDATE issued_book SET bookid = %s, userid = %s, expected_return_date = %s, return_date_time = %s, status = %s WHERE issuebookid = %s',
                           (book_id, user_id, expected_return_date, return_date, status, issue_book_id,))
        else:
            cursor.execute('INSERT INTO issued_book (bookid, userid, expected_return_date, return_date_time, status) VALUES (%s, %s, %s, %s, %s)',
                           (book_id, user_id, expected_return_date, return_date, status))

        mysql.connection.commit()

    return redirect(url_for('list_issue_book'))

@app.route("/edit_issue_book", methods=['GET'])
def edit_issue_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    issue_book_id = request.args.get('issuebookid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM issued_book WHERE issuebookid = %s', (issue_book_id,))
    issue_book = cursor.fetchone()

    return render_template("edit_issue_book.html", issue_book=issue_book)

@app.route("/delete_issue_book", methods=['GET'])
def delete_issue_book():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    issue_book_id = request.args.get('issuebookid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM issued_book WHERE issuebookid = %s', (issue_book_id,))
    mysql.connection.commit()

    return redirect(url_for('list_issue_book'))

# Manage Category
@app.route("/category", methods=['GET', 'POST'])
def category():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("SELECT * FROM category")
    categories = cursor.fetchall()

    return render_template("category.html", categories=categories)
# Manage Category
@app.route("/save_category", methods=['POST'])
def saveCategory():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        category_name = request.form['name']
        action = request.form['action']

        if action == 'updateCategory':
            category_id = request.form['categoryId']
            cursor.execute('UPDATE category SET name = %s WHERE categoryid = %s', (category_name, category_id,))
        else:
            cursor.execute('INSERT INTO category (name) VALUES (%s)', (category_name,))

        mysql.connection.commit()

    return redirect(url_for('category'))

@app.route("/edit_category", methods=['GET'])
def editcategory():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    category_id = request.args.get('categoryid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM category WHERE categoryid = %s', (category_id,))
    category = cursor.fetchone()

    return render_template("edit_category.html", category=category)

@app.route("/delete_category", methods=['GET'])
def delete_category():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    category_id = request.args.get('categoryid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM category WHERE categoryid = %s', (category_id,))
    mysql.connection.commit()

    return redirect(url_for('category'))

# Manage Author
@app.route("/author", methods=['GET', 'POST'])
def author():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("SELECT * FROM author")
    authors = cursor.fetchall()

    return render_template("author.html", authors=authors)

@app.route("/saveauthor", methods=['POST'])
def saveAuthor():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        author_name = request.form['name']
        action = request.form['action']

        if action == 'updateAuthor':
            author_id = request.form['authorId']
            cursor.execute('UPDATE author SET name = %s WHERE authorid = %s', (author_name, author_id,))
        else:
            cursor.execute('INSERT INTO author (name) VALUES (%s)', (author_name,))

        mysql.connection.commit()

    return redirect(url_for('author'))

@app.route("/editauthor", methods=['GET'])
def editAuthor():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    author_id = request.args.get('authorid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM author WHERE authorid = %s', (author_id,))
    author = cursor.fetchone()

    return render_template("edit_author.html", author=author)

@app.route("/delete_author", methods=['GET'])
def delete_author():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    author_id = request.args.get('authorid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM author WHERE authorid = %s', (author_id,))
    mysql.connection.commit()

    return redirect(url_for('author'))

# Manage Publisher
@app.route("/publisher", methods=['GET', 'POST'])
def publisher():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("SELECT * FROM publisher")
    publishers = cursor.fetchall()

    return render_template("publisher.html", publishers=publishers)

@app.route("/savepublisher", methods=['POST'])
def savePublisher():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        publisher_name = request.form['name']
        action = request.form['action']

        if action == 'updatePublisher':
            publisher_id = request.form['publisherId']
            cursor.execute('UPDATE publisher SET name = %s WHERE publisherid = %s', (publisher_name, publisher_id,))
        else:
            cursor.execute('INSERT INTO publisher (name) VALUES (%s)', (publisher_name,))

        mysql.connection.commit()

    return redirect(url_for('publisher'))

@app.route("/editpublisher", methods=['GET'])
def editPublisher():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    publisher_id = request.args.get('publisherid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM publisher WHERE publisherid = %s', (publisher_id,))
    publisher = cursor.fetchone()

    return render_template("edit_publisher.html", publisher=publisher)

@app.route("/delete_publisher", methods=['GET'])
def delete_publisher():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    publisher_id = request.args.get('publisherid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM publisher WHERE publisherid = %s', (publisher_id,))
    mysql.connection.commit()

    return redirect(url_for('publisher'))

# Manage Rack
@app.route("/rack", methods=['GET', 'POST'])
def rack():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("SELECT * FROM rack")
    racks = cursor.fetchall()

    return render_template("rack.html", racks=racks)

@app.route("/saverack", methods=['POST'])
def saveRack():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = get_cursor()
    if request.method == 'POST':
        rack_name = request.form['name']
        action = request.form['action']

        if action == 'updateRack':
            rack_id = request.form['rackId']
            cursor.execute('UPDATE rack SET name = %s WHERE rackid = %s', (rack_name, rack_id,))
        else:
            cursor.execute('INSERT INTO rack (name) VALUES (%s)', (rack_name,))

        mysql.connection.commit()

    return redirect(url_for('rack'))

@app.route("/editrack", methods=['GET'])
def editRack():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    rack_id = request.args.get('rackid')
    cursor = get_cursor()
    cursor.execute('SELECT * FROM rack WHERE rackid = %s', (rack_id,))
    rack = cursor.fetchone()

    return render_template("edit_rack.html", rack=rack)

@app.route("/delete_rack", methods=['GET'])
def delete_rack():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    rack_id = request.args.get('rackid')
    cursor = get_cursor()
    cursor.execute('DELETE FROM rack WHERE rackid = %s', (rack_id,))
    mysql.connection.commit()

    return redirect(url_for('rack'))
if __name__ == "__main__":
    app.run()
    os.execv(__file__, sys.argv)





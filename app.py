#Import Flask Library
from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time
from datetime import datetime
from werkzeug.utils import secure_filename

now = datetime.now()
timestamp = now.strftime('%Y-%m-%d %H:%M:%S')


#Initialize the app from Flask
app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")




#Configure MySQL
conn = pymysql.connect(host='127.0.0.1',
                       port=8889,
                       user='root',
                       password='root',
                       db='finsta',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       autocommit=True)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec


#Define a route to index function
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

#Define route for login
@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

#Define route for register
@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

#Authenticates the login
@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

        with conn.cursor() as cursor:
            query = "SELECT * FROM Person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)

#Authenticates the register
@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]

        try:
            with conn.cursor() as cursor:
                query = "INSERT INTO Person (username, password, fname, lname) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (username, hashedPassword, firstName, lastName))
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)


#home page once user logs in
@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT groupName, groupOwner FROM Belong WHERE username = %s'
    cursor.execute(query, (username))
    cfg = cursor.fetchall()

    #get visible posts
    query = 'SELECT photoID, photoOwner, timestamp, filePath, caption FROM Photo WHERE ' \
            'photoID IN (SELECT photoID FROM Share NATURAL JOIN CloseFriendGroup WHERE groupOwner=%s) ' \
            'OR photoID IN (SELECT photoID FROM Belong NATURAL JOIN Share NATURAL JOIN CloseFriendGroup WHERE username=%s) ' \
            'OR photoID IN (SELECT photoID FROM Tag WHERE username=%s AND acceptedTag=1) ' \
            'OR photoOwner=%s ' \
            'OR photoOwner IN (SELECT DISTINCT photoOwner FROM follow JOIN Photo ON Photo.photoOwner=follow.followeeUsername ' \
            'WHERE followerUsername=%s AND acceptedfollow=1 AND allFollowers=1) ' \
            'ORDER BY timestamp DESC'
    cursor.execute(query, (username, username, username, username, username))
    posts = cursor.fetchall()


    # get tags
    query = 'SELECT username, photoID FROM Tag WHERE photoID IN (SELECT photoID FROM Photo WHERE allFollowers=1) OR photoID ' \
            'IN (SELECT photoID FROM Share NATURAL JOIN Belong WHERE username=%s)'
    cursor.execute(query, (username))
    tags = cursor.fetchall()

    #proposed tags
    query = 'SELECT photoID FROM Tag WHERE username = %s AND acceptedTag = 0'
    cursor.execute(query, (username))
    proptags = cursor.fetchall()

    #get follows
    query ='SELECT followerUsername FROM Follow WHERE followeeUsername=%s and acceptedfollow=0'
    cursor.execute(query,(username))
    propfollows=cursor.fetchall()

    cursor.close()
    return render_template('home.html', username=username, cfg=cfg, posts=posts, tags=tags, proptags=proptags, propfollows=propfollows)


#to post
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']

    if request.files:

        cursor = conn.cursor()

        caption = request.form['caption']
        all_followers = 0
        image_file = request.files["upload"]
        image_name = secure_filename(image_file.filename)
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)

        if request.form.get('all_followers'):
            all_followers = 1
            query = "INSERT INTO Photo (photoOwner, timestamp, caption ,allFollowers,filePath) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (username, timestamp, caption, all_followers, image_name))

        # if not, get the friend group, and insert data in photo and share
        else:
            cfg = request.form['closefriendg']
            q = "SELECT groupOwner FROM CloseFriendGroup WHERE groupName=%s"
            cursor.execute(q,(cfg))
            owner = cursor.fetchone().get('groupOwner')

            queryToPhoto = "INSERT INTO Photo (photoOwner, timestamp, caption ,allFollowers, filePath) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(queryToPhoto, (username, timestamp, caption, all_followers, image_name))
            cfg= request.form['closefriendg']
            queryToShare = "INSERT INTO Share (photoID, groupOwner, groupName) VALUES (%s,%s,%s)"
            cursor.execute(queryToShare, (cursor.lastrowid, owner, cfg))

        cursor.close()
        return redirect(url_for('home'))
    else:
        error = "Failed to upload image."
        return render_template("post_error.html", error=error)


#when users want more info about the post
@app.route('/detailed_info', methods=['GET', 'POST'])
def detailed_info():

    photoid = request.form['photoid']
    cursor = conn.cursor()

    #select approved tags
    query = "SELECT fname,lname FROM Tag NATURAL JOIN Person WHERE photoID = %s AND acceptedTag=1"
    cursor.execute(query,(photoid))
    tags = cursor.fetchall()

    #select photos
    query="SELECT * FROM Photo WHERE photoID=%s"
    cursor.execute(query,(photoid))
    images=cursor.fetchall()


    cursor.close()
    return render_template('detailed_info.html', tags=tags,images=images)


#to tag someone
@app.route('/tag', methods=['GET', 'POST'])
def tag():
    tagger = session['username']
    taggee = request.form['taggee']
    photoid = request.form['photoid']

    cursor = conn.cursor()

    check_group = cursor.execute('SELECT username FROM Belong WHERE username = %s AND groupName IN '
                                 '(SELECT groupName from Share WHERE photoID = %s)', (taggee, photoid))
    check_all = cursor.execute('SELECT * FROM Photo WHERE allFollowers = 1 and photoID = %s', (photoid))

    #check if the user is part of the friend group or if the post opens to all
    if (not check_group and not check_all):
        error = "This user is not allowed to view this photo or does not exist."
        cursor.close()
        return render_template('tag_error.html', error=error)

    already = cursor.execute('SELECT * FROM Tag WHERE username = %s AND photoID = %s', (taggee, photoid))
    #check if user was already tagged
    if (already):
        error = "You already tagged this user on this photo."
        cursor.close()
        return render_template('tag_error.html', error=error)

    # if the user is tagging oneself
    if taggee == tagger:
        acceptedTag = 1
    # if the user tagged someone (valid).
    else:
        acceptedTag = 0

    #insert into database
    query = 'INSERT INTO Tag (photoID, username, acceptedTag) VALUES(%s, %s, %s)'
    cursor.execute(query, (photoid, taggee, acceptedTag))
    cursor.close()
    return redirect(url_for('home'))

#to accept tags from others
@app.route('/accepttag', methods=['GET','POST'])
def accepttags():
    username = session['username']
    cursor = conn.cursor();
    photoid = request.form['photoid']
    query = 'UPDATE Tag SET acceptedTag = 1 WHERE photoID = %s AND username = %s'
    cursor.execute(query, (photoid, username))
    cursor.close()
    return redirect(url_for('home'))


# to reject tags from others
@app.route('/declinetag', methods=['GET', 'POST'])
def declinetags():
    username = session['username']
    cursor = conn.cursor();
    photoid = request.form['photoid']
    query = 'DELETE FROM Tag WHERE photoID = %s AND username = %s'
    cursor.execute(query, (photoid, username))
    cursor.close()
    return redirect(url_for('home'))


#for creating a friend group
@app.route('/createfg', methods=['GET', 'POST'])
def createfg():
    username = session['username']
    cfg_name = request.form['name']

    cursor = conn.cursor()

    #check if the owner already has a friendgroup with the same name
    check_cfg = cursor.execute('SELECT * FROM CloseFriendGroup WHERE groupOwner = %s AND groupName = %s', (username, cfg_name))
    if check_cfg:
        error = "You already created a Close Friend Group with this name."
        cursor.close()
        return render_template('tag_error.html', error=error)

    query = 'INSERT INTO CloseFriendGroup (groupName, groupOwner) VALUES (%s, %s)'
    cursor.execute(query, (cfg_name, username))
    query = 'INSERT INTO Belong (username, groupName, groupOwner) VALUES (%s, %s, %s)'
    cursor.execute(query, (username, cfg_name, username))
    cursor.close()
    return redirect(url_for('home'))


#to add someone to a friend group
@app.route('/addtocfg', methods=['GET', 'POST'])
def addtocfg():
    username = session['username']
    cfg = request.form["group"]
    user_toadd= request.form['username_toadd']

    cursor = conn.cursor()
    #check if the username exists
    exist = 'SELECT * FROM Person WHERE username=%s'
    if (not cursor.execute(exist, (user_toadd))):
        error = "This name does not exist."
        cursor.close()
        return render_template('addfg_error.html', error=error)

    #check if the username already in closefriendgroup, if not return error
    query = 'SELECT * FROM Belong WHERE username = %s AND groupName=%s '
    if (cursor.execute(query, (user_toadd,cfg))):
        error = "This friend is already in this close friend group."
        cursor.close()
        return render_template('addfg_error.html', error=error)

    query = 'INSERT INTO Belong(username, groupOwner, groupName) VALUES (%s , %s, %s)'
    cursor.execute(query, (user_toadd, username, cfg))
    cursor.close()

    return redirect(url_for('home'))

#to manage follow request
@app.route('/follow', methods=['GET','POST'])
def follow():
    follower=session['username']
    followee = request.form['followee']

    cursor = conn.cursor()

    #check if followee exists
    exist=cursor.execute('SELECT username FROM Person WHERE username=%s',(followee))
    if (not exist):
        error= "This user does not exist"
        cursor.close()
        return render_template('follow_error.html', error=error)

    query='INSERT INTO Follow (followerUsername, followeeUsername, acceptedfollow) VALUES (%s,%s,%s)'
    cursor.execute(query,(follower,followee,0))
    cursor.close()

    return redirect(url_for('home'))

#to accept follows
@app.route('/acceptfollow',methods=['GET','POST'])
def acceptfollows():
    username = session['username']
    cursor = conn.cursor()
    followername = request.form['followername']
    query = 'UPDATE Follow SET acceptedfollow = 1 WHERE followeeUsername = %s AND followerUsername=%s'
    cursor.execute(query, (username, followername))
    cursor.close();
    return redirect(url_for('home'))

#to dedcline follows
@app.route('/declinefollow',methods=['GET','POST'])
def delinefollows():
    username = session['username']
    cursor = conn.cursor()
    followername = request.form['followername']
    query = 'DELETE FROM Follow WHERE followeeUsername = %s AND followerUsername=%s'
    cursor.execute(query, (username, followername))
    cursor.close();
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('127.0.0.1', 5000, debug = True)

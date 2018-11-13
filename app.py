######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64
#used in tag recommendation functions
from collections import Counter

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460iscool' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('home.html', message='Logged out', photos=getAllPhotos(), comments=getComments(), logo=getLogo())

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('improved_register.html', supress='True', logo=getLogo())

@app.route('/friends/', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		cursor = conn.cursor()
		if(cursor.execute("SELECT user_id from users WHERE fname = '{0}' and lname = '{1}'".format(fname, lname))):
			cursor.execute("SELECT user_id from users WHERE fname = '{0}' and lname = '{1}'".format(fname, lname))
			friend_id = cursor.fetchall()[0][0]
			cursor.execute("INSERT INTO friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, friend_id))
			conn.commit()
			return render_template('friends.html', message="Friend added!", friends=getUserFriends(uid), logo=getLogo())
	return render_template('friends.html', message="Find your friends!", friends=getUserFriends(uid), logo=getLogo())

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		birthday=request.form.get('birthday')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		bio=request.form.get('bio')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		if (request.files['photo'].filename == ''):
			cursor.execute("INSERT INTO Users (email, password, fname, lname, DoB, hometown, gender, bio) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, firstname, lastname, birthday, hometown, gender, bio))
			conn.commit()
		else:
			prof_pic = request.files['photo']
			photo_data = base64.standard_b64encode(prof_pic.read())
			cursor.execute("INSERT INTO Users (email, password, fname, lname, DoB, hometown, gender, bio, prof_pic) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}')".format(email, password, firstname, lastname, birthday, hometown, gender, bio, photo_data))
			conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=firstname, message='Account Created!', bio=getUserBio(email), prof_pic=getUserProfPic(email), logo=getLogo())
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def userHasProfPic(uid):
	cursor = conn.cursor()
	bool = cursor.execute("SELECT prof_pic FROM users WHERE user_id = '{0}'".format(uid))
	bool = cursor.fetchall()
	if(bool[0][0] != None):
		print True
		return True
	else:
		return False

def getUserProfPic(email):
	uid = getUserIdFromEmail(email)
	if(userHasProfPic(uid)):
		print "not using default"
		cursor = conn.cursor()
		cursor.execute("SELECT prof_pic FROM users WHERE user_id = '{0}'".format(uid))
		photo = cursor.fetchall()
		return photo[0][0]
	else:
		print "using default"
		with open('default.png') as imageFile:
			str = base64.b64encode(imageFile.read())
		return (str)
def getLogo():
	with open('photoshare.png') as imageFile:
		str = base64.b64encode(imageFile.read())
	return (str)

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name, album_id FROM album_id_name WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUsersAlbumID(uid, name):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM album_id_name WHERE user_id = '{0}' and name='{1}'".format(uid,name))
	return cursor.fetchall()[0]

def getAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT name, album_id FROM album_id_name")
	return cursor.fetchall()

def getTags():
	cursor = conn.cursor()
	cursor.execute("SELECT word, tag_id FROM tag_id_word")
	return cursor.fetchall()

def getTopTags():
	tags = []
	cursor = conn.cursor()
	cursor.execute("SELECT word, count(*) FROM tags GROUP BY word ORDER BY count(*) DESC LIMIT 3;")
	tags = cursor.fetchall()
	return tags

def getTopUsers():
	users = []
	names = []
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, U.count	FROM (SELECT Us.user_id, count(*) AS count FROM (SELECT user_id FROM photos UNION ALL SELECT user_id FROM comments) AS Us GROUP BY Us.user_id) AS U ORDER BY U.count DESC LIMIT 10")
	users = cursor.fetchall()
	for user in users:
		if(user[0] != 0):
			cursor.execute("SELECT fname, lname from users where user_id = '{0}'".format(user[0]))
			name = cursor.fetchone()
			names.append(name)
	return names

def getComments():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos")
	photos = cursor.fetchall()
	all = []
	res = []
	for photo in photos:
		if(cursor.execute("SELECT comment_id FROM comments WHERE photo_id = '{0}'".format(photo[0]))):
			cursor.execute("SELECT users.fname, users.lname, comments.photo_id, comments.text, comments.date, comments.user_id FROM users, comments WHERE comments.photo_id = '{0}' and comments.user_id = users.user_id".format(photo[0]))
			all = cursor.fetchall()
			for item in all:
				res.append(item)
			if(cursor.execute("SELECT comments.photo_id, comments.text, comments.date, comments.user_id FROM comments WHERE comments.photo_id = '{0}' and comments.user_id = 0".format(photo[0]))):
				cursor.execute("SELECT comments.photo_id, comments.text, comments.date, comments.user_id FROM comments WHERE comments.photo_id = '{0}' and comments.user_id = 0".format(photo[0]))
				all = cursor.fetchall()
				for item in all:
					result = [' ', ' ']
					result.append(item)
					flat_result = [item for r in result for item in r]
					res.append(flat_result)
	print "resulting comments: " + str(res)
	return res

def getUserLikes():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos WHERE user_id = '{0}'".format(uid))
	photos = cursor.fetchall()
	res = []
	all = []
	for photo in photos:
		if(cursor.execute("SELECT photo_id FROM likes WHERE photo_id = '{0}'".format(photo[0]))):
			cursor.execute("SELECT likes.user_id, likes.photo_id, users.fname, users.lname FROM users, likes WHERE photo_id = '{0}' and likes.user_id = users.user_id".format(photo[0]))
			all = cursor.fetchall()
			for item in all:
				res.append(item)
	print "likes: " + str(res)
	return res

def getLikes():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos")
	photos = cursor.fetchall()
	res = []
	all = []
	for photo in photos:
		if(cursor.execute("SELECT photo_id FROM likes WHERE photo_id = '{0}'".format(photo[0]))):
			cursor.execute("SELECT likes.user_id, likes.photo_id, users.fname, users.lname FROM users, likes WHERE photo_id = '{0}' and likes.user_id = users.user_id".format(photo[0]))
			all = cursor.fetchall()
			for item in all:
				res.append(item)
	print "likes: " + str(res)
	return res

def alreadyLiked(uid, pid):
	cursor = conn.cursor()
	if(cursor.execute("SELECT user_id, photo_id FROM likes WHERE user_id = '{0}' and photo_id = '{1}'".format(uid, pid))):
		return True
	else:
		return False

def getCaption(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT caption FROM photos WHERE photo_id = '{0}'".format(photo_id))
	return cursor.fetchall()

def getUserComments():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos WHERE user_id = '{0}'".format(uid))
	photos = cursor.fetchall()
	all = []
	res = []
	for photo in photos:
		if(cursor.execute("SELECT comment_id FROM comments WHERE photo_id = '{0}'".format(photo[0]))):
			cursor.execute("SELECT users.fname, users.lname, comments.photo_id, comments.text, comments.date, comments.user_id  FROM users, comments WHERE comments.photo_id = '{0}' and comments.user_id = users.user_id".format(photo[0]))
			all = cursor.fetchall()
			for item in all:
				res.append(item)
			if(cursor.execute("SELECT comments.photo_id, comments.text, comments.date, comments.user_id FROM comments WHERE comments.photo_id = '{0}' and comments.user_id = 0".format(photo[0]))):
				cursor.execute("SELECT comments.photo_id, comments.text, comments.date, comments.user_id FROM comments WHERE comments.photo_id = '{0}' and comments.user_id = 0".format(photo[0]))
				all = cursor.fetchall()
				for item in all:
					result = [' ', ' ']
					result.append(item)
					flat_result = [item for r in result for item in r]
					res.append(flat_result)
	return res

def insertAlbums(uid, name, imgdata):
	cursor = conn.cursor()
	photo_id = cursor.execute("SELECT photo_id FROM photos WHERE imgdata ='{0}' AND user_id = '{1}'".format(imgdata, uid))
	photo_id = cursor.fetchone()[0]
	if(cursor.execute("SELECT album_id FROM album_id_name WHERE name = '{0}' and user_id = '{1}'".format(name, uid))):
			cursor.execute("SELECT album_id, date_created FROM album_id_name WHERE name = '{0}' and user_id = '{1}'".format(name, uid))
			res = cursor.fetchone()
			album_id = res[0]
			date_created = res[1]
			cursor.execute("INSERT INTO albums (name, album_id, user_id, date_created, photo_id) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(name, album_id, uid, date_created, photo_id))
	else:
			cursor.execute("INSERT INTO album_id_name (name, user_id) VALUES ('{0}', '{1}')".format(name, uid))
			cursor.execute("SELECT album_id, date_created FROM album_id_name WHERE name = '{0}' and user_id = '{1}'".format(name, uid))
			res = cursor.fetchone()
			album_id = res[0]
			date_created = res[1]
			cursor.execute("INSERT INTO albums (name, user_id, date_created, photo_id, album_id) VALUES ('{0}', '{1}',  '{2}','{3}','{4}')".format(name, uid, date_created, photo_id, album_id))

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserBio(email):
	cursor = conn.cursor()
	cursor.execute("SELECT bio FROM users WHERE email = '{0}'".format(email))
	return cursor.fetchall()

def getUserNameFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT fname FROM users WHERE email = '{0}'".format(email))
	return cursor.fetchall()

def getUserTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT word, tag_id FROM tag_id_word WHERE user_id = '{0}'".format(uid))
	# print cursor.fetchall()
	return cursor.fetchall()

def getTaggedImages(tag):
	cursor = conn.cursor()
	img_ids = cursor.execute("SELECT photo_id FROM tags WHERE word = '{0}'".format(tag))
	res = []
	for id in img_ids:
		cursor.execute("SELECT photos.imgdata, photos.caption, photos.photo_id FROM photos WHERE photos.photo_id = '{0}'".format(id))
		res.append(cursor.fetchall()[0])
	return cursor.fetchall()

def getAlbumImages(album_id):
	cursor = conn.cursor()
	print "aid: " + album_id
	cursor.execute("SELECT photos.imgdata, photos.caption, photos.photo_id, albums.photo_id, albums.album_id FROM photos, albums WHERE albums.album_id = '{0}' and albums.photo_id = photos.photo_id".format(album_id))
	res = cursor.fetchall()
	return res

def getTaggedImages(tag):
	cursor = conn.cursor()
	print "tag: " + tag
	cursor.execute("SELECT photos.imgdata, photos.photo_id, tags.photo_id, tags.word FROM photos, tags WHERE tags.word = '{0}' and tags.photo_id = photos.photo_id".format(tag))
	res = cursor.fetchall()
	return res

def getUsersTaggedImages(tag):
	cursor = conn.cursor()
	print "tag: " + tag
	cursor.execute("SELECT photos.imgdata, photos.photo_id, tags.photo_id, tags.tag_id FROM photos, tags WHERE tags.tag_id = '{0}' and tags.photo_id = photos.photo_id".format(tag))
	res = cursor.fetchall()
	return res

def getUserFriends(uid):
		cursor = conn.cursor()
		names = cursor.execute("SELECT users.fname, users.lname from USERS, FRIENDS where users.user_id = friends.friend_id and friends.user_id = '{0}'".format(uid))
		return cursor.fetchall()

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, caption, photo_id FROM photos")
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def insertTags(uid, oldtags, imgdata):
	print oldtags
	tags = [x.strip() for x in oldtags.split(',')]
	cursor = conn.cursor()
	photo_id = cursor.execute("SELECT photo_id FROM photos WHERE imgdata ='{0}' AND user_id = '{1}'".format(imgdata, uid))
	photo_id = cursor.fetchone()[0]
	for tag in tags:
		if(cursor.execute("SELECT tag_id FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))):
			tag_id = cursor.execute("SELECT tag_id  FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))
			tag_id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO tags (word, photo_id, user_id, tag_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(tag, photo_id, uid,tag_id))
		else:
			if(tag != ""):
				cursor.execute("INSERT INTO tag_id_word (word, user_id) VALUES ('{0}', '{1}')".format(tag, uid))
				tag_id = cursor.execute("SELECT tag_id  FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))
				tag_id = cursor.fetchone()[0]
				cursor.execute("INSERT INTO tags (word, photo_id, user_id, tag_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(tag, photo_id, uid,tag_id))

#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Welcome to your profile", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo())

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	email = flask_login.current_user.id
	if request.method == 'POST':
		uid = getUserIdFromEmail(email)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album = request.form.get('album')
		tags = request.form.get('tag')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO photos (imgdata, user_id, caption) VALUES ('{0}', '{1}', '{2}')".format(photo_data, uid, caption))
		insertTags(uid, tags, photo_data)
		insertAlbums(uid, album, photo_data)
		conn.commit()
		return render_template('hello.html', name=getUserNameFromEmail(email)[0][0], message='Photo uploaded!', photos=getUsersPhotos(uid),albums=getUsersAlbums(uid), bio=getUserBio(email)[0], tags=getUserTags(uid), comments=getComments(), prof_pic=getUserProfPic(email), likes=getLikes(), logo=getLogo())
		#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('upload.html', albums=getUsersAlbums(uid), tags=getUserTags(uid), logo=getLogo())

@app.route('/prof_pic', methods=['GET', 'POST'])
@flask_login.login_required
def prof_pic():
	email = flask_login.current_user.id
	uid = getUserIdFromEmail(email)
	imgfile = request.files['new_prof']
	photo_data = base64.standard_b64encode(imgfile.read())
	cursor = conn.cursor()
	cursor.execute("UPDATE users SET prof_pic = '{0}' WHERE user_id = '{1}'".format(photo_data, uid))
	conn.commit()
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getUsersPhotos(uid),albums=getUsersAlbums(uid), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(uid), comments=getComments(), prof_pic=getUserProfPic(email), logo=getLogo())

#end photo uploading code
@app.route('/comment', methods=['GET', 'POST'])
def comment():
	if(flask_login.current_user.is_anonymous()):
		comment = request.form.get('comment')
		photo_id = request.form.get('photo_id')
		print "photo_id: " + str(photo_id)
		cursor = conn.cursor()
		cursor.execute("INSERT INTO comments (text, photo_id) VALUES ('{0}', '{1}')".format(comment, photo_id))
		# comment_id = cursor.execute("SELECT comment_id FROM comments WHERE photo_id ='{0}' and user_id = '{1}' and text = '{2}'".format(photo_id, uid, text))
		# cursor.execute("UPDATE photos SET comment_id = '{0}' WHERE photo_id ='{1}' and user_id = '{2}')".format(comment_id, photo_id, uid))
		conn.commit()
		return render_template('home.html', message="Comment posted", photos=getAllPhotos(), comments=getComments(), logo=getLogo())
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		comment = request.form.get('comment')
		photo_id = request.form.get('photo_id')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO comments (user_id, text, photo_id) VALUES ('{0}', '{1}', '{2}')".format(uid, comment, photo_id))
		# comment_id = cursor.execute("SELECT comment_id FROM comments WHERE photo_id ='{0}' and user_id = '{1}' and text = '{2}'".format(photo_id, uid, text))
		# cursor.execute("UPDATE photos SET comment_id = '{0}' WHERE photo_id ='{1}' and user_id = '{2}')".format(comment_id, photo_id, uid))
		conn.commit()
		return render_template('home.html', message="Comment posted", name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), likes=getLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), logo=getLogo())


@app.route('/like', methods=['GET', 'POST'])
@flask_login.login_required
def like():
		uid = getUserIdFromEmail(flask_login.current_user.id)
		# comment = request.form.get('comment')
		photo_id = request.form.get('photo_id')
		if (alreadyLiked(uid, photo_id)):
			return render_template('home.html', message="You already liked this photo!", name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), likes=getLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), logo=getLogo())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO likes (user_id, photo_id) VALUES ('{0}', '{1}')".format(uid, photo_id))
		# comment_id = cursor.execute("SELECT comment_id FROM comments WHERE photo_id ='{0}' and user_id = '{1}' and text = '{2}'".format(photo_id, uid, text))
		# cursor.execute("UPDATE photos SET comment_id = '{0}' WHERE photo_id ='{1}' and user_id = '{2}')".format(comment_id, photo_id, uid))
		conn.commit()
		likes = getLikes()
		return render_template('home.html', message="Liked added!", name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), likes=getLikes(), logo=getLogo())


#default page
@app.route("/", methods=['GET', 'POST'])
def home():
	if(flask_login.current_user.is_anonymous()):
		return render_template('home.html', message='Welcome to Photoshare', photos=getAllPhotos(), likes=getLikes(), comments=getComments(), albums=getAlbums(), tags=getTags(), toptags=getTopTags(), topusers=getTopUsers(), logo=getLogo())
	else:
		email = flask_login.current_user.id
		return render_template('home.html', message='Welcome to Photoshare', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), likes=getLikes(), comments=getComments(), albums=getAlbums(), tags=getTags(), prof_pic=getUserProfPic(email), toptags=getTopTags(), topusers=getTopUsers(), logo=getLogo())


@app.route('/albumPhotos', methods=['GET', 'POST'])
def albumPhotos():
	# photo_id = request.form.get('photo_id')
	album_id = request.form.get('album_id')
	photos = getAlbumImages(album_id)
	return render_template('album.html', photos=getAlbumImages(album_id),logo=getLogo())

@app.route('/taggedPhotos', methods=['GET', 'POST'])
def taggedPhotos():
	# photo_id = request.form.get('photo_id')
	tag = request.form.get('tag_word')
	print "passed:" + tag
	photos = getTaggedImages(tag)
	return render_template('tags.html', photos=photos,logo=getLogo())

@app.route('/usersTaggedPhotos', methods=['GET', 'POST'])
@flask_login.login_required
def usersTaggedPhotos():
	# photo_id = request.form.get('photo_id')
	tag = request.form.get('tag_id')
	photos = getUsersTaggedImages(tag)
	return render_template('userTags.html', photos=photos, logo=getLogo())


@app.route('/deleteAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def deleteAlbum():
	album_id = request.form.get('album_id')
	print "passed aid:" + album_id
	photos = getAlbumImages(album_id)
	cursor = conn.cursor()
	for photo in photos:
		print photo[3]
		cursor.execute("DELETE FROM photos WHERE photo_id = '{0}'".format(photo[3]))
		conn.commit()
	cursor.execute("DELETE FROM albums WHERE album_id = '{0}'".format(album_id))
	cursor.execute("DELETE FROM album_id_name WHERE album_id = '{0}'".format(album_id))
	conn.commit()
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Welcome to your profile", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo())

@app.route('/deletePhoto', methods=['GET', 'POST'])
@flask_login.login_required
def deletePhoto():
	photo_id = request.form.get('photo_id')
	print "passed pid:" + photo_id
	cursor = conn.cursor()
	cursor.execute("DELETE FROM photos WHERE photo_id = '{0}'".format(photo_id))
	cursor.execute("DELETE FROM albums WHERE photo_id = '{0}'".format(photo_id))
	conn.commit()
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Welcome to your profile", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo())


@app.route('/deleteTag', methods=['GET', 'POST'])
@flask_login.login_required
def deleteTag():
	photo_id = request.form.get('photo_id')
	print "passed pid:" + photo_id
	cursor = conn.cursor()
	cursor.execute("DELETE FROM tags WHERE photo_id = '{0}'".format(photo_id))
	conn.commit()
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Tag Removed", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo())

@app.route('/addTag', methods=['GET', 'POST'])
@flask_login.login_required
def addTag():
	photo_id = request.form.get('photo_id')
	tag = request.form.get('tag')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	print "passed pid:" + photo_id
	print "passed tag:" + tag
	cursor = conn.cursor()
	if(cursor.execute("SELECT tag_id FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))):
		tag_id = cursor.execute("SELECT tag_id FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))
		tag_id = cursor.fetchone()[0]
		cursor.execute("INSERT INTO tags (word, photo_id, user_id, tag_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(tag, photo_id, uid,tag_id))
	else:
		if(tag != ""):
			cursor.execute("INSERT INTO tag_id_word (word, user_id) VALUES ('{0}', '{1}')".format(tag, uid))
			tag_id = cursor.execute("SELECT tag_id  FROM tag_id_word WHERE word = '{0}' and user_id = '{1}'".format(tag, uid))
			tag_id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO tags (word, photo_id, user_id, tag_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(tag, photo_id, uid,tag_id))
	conn.commit()
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Tag added", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo())


@app.route("/search", methods=['Get', 'POST'])
def search():
	input = request.form.get('search')
	tags = input.split(',')
	print tags
	if (tags == [u'']):
		if(flask_login.current_user.is_anonymous()):
			return render_template('home.html', photos=getPhotos(), comments=getComments(), logo=getLogo())
		else:
			return render_template('home.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), logo=getLogo())
	cursor = conn.cursor()
	res = []
	found = []
	# if myItem not in list:
	for tag in tags:
		if(cursor.execute("SELECT word FROM tags WHERE word = '{0}'".format(tag))):
			print("found")
		# 	cursor.execute("SELECT word, photo_id FROM tags WHERE word = '{0}'".format(tag))
		# 	found.append(cursor.fetchall())
		# for items in found[0]:
		# 	if
			cursor.execute("SELECT photos.imgdata, photos.photo_id, tags.photo_id, tags.word FROM photos, tags WHERE tags.word = '{0}' and tags.photo_id = photos.photo_id".format(tag))
			res.append(cursor.fetchall())
	if(flask_login.current_user.is_anonymous()):
		return render_template('home.html', searchresults=res[0], photos=getAllPhotos(), comments=getComments(), logo=getLogo())
	else:
		return render_template('home.html', message="searched!", searchresults=res[0], name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), logo=getLogo())


@app.route("/searchTags", methods=['Get', 'POST'])
def searchTags():
	input = request.form.get('tags')
	tags = input.split(',')
	print "searchTags" + str(tags)
	if (tags == [u'']):
		return render_template('home.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], photos=getAllPhotos(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getComments(), logo=getLogo())
	cursor = conn.cursor()
	res = []
	found = []
	# word = []
	for tag in tags:
		if(cursor.execute("SELECT word FROM tags WHERE word='{0}'".format(tag))):
			pid = cursor.execute("SELECT photo_id FROM tags WHERE word='{0}'".format(tag))
			result = cursor.fetchall()
			for r in result:
				print r
				found.append(r[0])
			print "found" + str(found)
			for f in found:
				cursor.execute("SELECT word FROM tags WHERE photo_id='{0}'".format(f))
				words = cursor.fetchall()
				for w in words:
					print w
					res.append(w)
				print "resulting words: " + str(res)
	# from collections import Counter
	# words=["i", "love", "you", "i", "you", "a", "are", "you", "you", "fine", "green"]
	ideas = [word for word, word_count in Counter(res).most_common(5)]
	print ideas
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=getUserNameFromEmail(flask_login.current_user.id)[0][0], message="Here are some tags", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)), likes=getUserLikes(), albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)), bio=getUserBio(flask_login.current_user.id)[0], tags=getUserTags(getUserIdFromEmail(flask_login.current_user.id)), prof_pic=getUserProfPic(flask_login.current_user.id), comments=getUserComments(), logo=getLogo(), tagIdeas=ideas)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

import datetime
from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
import s3_client
import db_client
import rds_client
import config
import os

application = Flask(__name__)
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800
application.config.update(SECRET_KEY=os.urandom(24))
application.config.from_object(__name__)
Session(application)

s3_client, db_client, rds_client = s3_client.s3_client(), db_client.db_client(), rds_client.rds_client()

def get_comments(posts):
    comments = []
    for post in posts:
        if (db_client.scan('comments', 'post_id', post['post_id'])):
            post_comments = db_client.scan('comments', 'post_id', post['post_id'])
            for post_comment in post_comments:
                if (post_comment['post_id'] == post['post_id']):
                    comments.append(post_comment)
    return comments

def get_liked(posts):
    liked = []
    for post in posts:
        likes = db_client.scan('likes', 'post_id', post['post_id'])
        if (db_client.scan('likes', 'post_id', post['post_id'])):
            for like in likes:
                if (like['email'] == session['user']['email']):
                    liked.append(like['post_id'])
    return liked

def start_db_session(ip_addr):
    db_client.create_tables()
    instance_state = rds_client.describe_instance()
    print("Printing instance state")
    print(instance_state)
    table = rds_client.define_tables()
    rds_client.execute_query(table)
    rds_client.describe_instance()
    query = """
        INSERT INTO session_data (session_id, start_datetime, ip_address
        ) VALUES (
        {}, {}, {},
        )""".format(application.config['SECRET_KEY'].hex(), str(datetime.datetime.now()), ip_addr)
    rds_client.execute_query(query)

def end_db_session():
    query = ("""
        UPDATE session_data SET end_datetime = {}
        WHERE session_id = {}""".format(str(datetime.datetime.now()), application.config['SECRET_KEY'].hex()))
    rds_client.execute_query(query)

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/login', methods=['GET', 'POST'])
def login():
    if (request.method == 'POST'):
        message = None
        email = request.form['email']
        password = request.form['password']
        if (db_client.get_item('users', { 'email': email })):
            if (db_client.get_item('users', { 'email': email })['password'] == password):
                    user = db_client.get_item('users', { 'email': email })
                    session['user'] = user
                    posts = db_client.scan("posts")
                    comments = get_comments(posts)
                    liked = get_liked(posts)
                    print("printing liked")
                    for like in liked:
                        print(like)
                    start_db_session("0.0.0.0")
                    return render_template('home.html', user=user, posts=posts, comments=comments, liked=liked, message=message)
            else:
                return render_template('index.html', message='Invalid Credentials. Please try again.')
        else:
            return render_template('index.html', message='Invalid Email. Please try again.')
    return render_template('index.html', message='Something went wrong. Please try again.')

@application.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('email', None)
    end_db_session()
    return render_template('index.html', message='You have been logged out successfully.')

@application.route('/register', methods=['GET', 'POST'])
def register():
    if (request.method == 'POST'):
        if (request.form['password'] == request.form['confirm_password']):
            if (db_client.get_item("users", { 'email': request.form['email'] } )):
                return render_template('register.html', message='Email already exists. Please try again.')
            else:
                item = { 
                        'email': request.form['email'], 
                        'first_name': request.form['first_name'],
                        'last_name': request.form['last_name'],
                        'user_name': request.form['first_name'] + " " + request.form['last_name'], 
                        'dob': request.form['dob'],
                        'password': request.form['password'],
                        'image_url': config.cloudfront_domain + "user_images/" + request.form['email'] + ".jpg"
                        }
                db_client.put_item("users", item)
                if "user_image" in request.files:
                    file = request.files['user_image']
                    file_name = "user_images/" + request.form['email'] + ".jpg"
                    s3_client.upload_fileobj(file, file_name)
                return render_template('index.html', message='Registration successful. Please login.')
        else:
            return render_template('register.html', message='Passwords do not match. Please try again.')
    return render_template('register.html')

@application.route('/home', methods=['GET', 'POST'])
def home():
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template("home.html", user=session['user'], posts=posts, comments=comments, liked=liked)

@application.route('/profile', methods=['GET', 'POST'])
def profile():
    if (request.method == 'POST'):
        print("Profile email: " + request.form['profile_email'])
        if (request.form['profile_email']):
            if (request.form['profile_email'] == session['user']['email']):
                email = session['user']['email']
                user = db_client.get_item("users", { 'email': email })
                logged_in = True
            else:
                email = request.form['profile_email']
                user = db_client.get_item("users", { 'email': email })
                logged_in = False
            posts = db_client.scan("posts", "email", session['user']['email'])
            friends = db_client.scan("friends", "email_1", session['user']['email'])
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('profile.html', user=user, posts=posts, friends=friends, comments=comments, liked=liked, logged_in=logged_in)
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('profile.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

@application.route('/friend', methods=['GET', 'POST'])
def friend():
    if (request.method == 'POST'):
        if (request.form['friend_email']):
            if (request.form['friend_email'] == session['user']['email']):
                return render_template('friend.html', message='You cannot add yourself as a friend.')
            else:
                if (db_client.get_item("users", { 'email': request.form['friend_email'] })):
                    if (db_client.get_item("friends", { 'email_1': session['user']['email'], 'email_2': request.form['friend_email'] })):
                        return render_template('friend.html', message='You are already friends with this user.')
                    else:
                        item = {
                                'email_1': session['user']['email'],
                                'email_2': request.form['friend_email']
                                }
                        db_client.put_item("friends", item)
                        posts = db_client.scan("posts", "email", session['user']['email'])
                        comments = get_comments(posts)
                        liked = get_liked(posts)
                        return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Friend added successfully.')
                else:
                    posts = db_client.scan("posts", "email", session['user']['email'])
                    comments = get_comments(posts)
                    liked = get_liked(posts)
                    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Friend added successfully.')
        else:
            posts = db_client.scan("posts", "email", session['user']['email'])
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Friend added successfully.')
    posts = db_client.scan("posts", "email", session['user']['email'])
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Friend added successfully.')

@application.route('/unfriend', methods=['GET', 'POST'])
def unfriend():
    if (request.method == 'POST'):
        if (request.form['unfriend_email']):
            if (request.form['unfriend_email'] == session['user']['email']):
                return render_template('unfriend.html', message='You cannot unfriend yourself.')
            else:
                if (db_client.get_item("friends", { 'email_1': session['user']['email'], 'email_2': request.form['unfriend_email'] })):
                    db_client.delete_item("friends", 'email_1', session['user']['email'], 'email_2', request.form['unfriend_email'])
                    posts = db_client.scan("posts", "email", session['user']['email'])
                    comments = get_comments(posts)
                    liked = get_liked(posts)
                    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Unfriended successfully.')
                else:
                    posts = db_client.scan("posts", "email", session['user']['email'])
                    comments = get_comments(posts)
                    liked = get_liked(posts)
                    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Unfriended successfully.')
        else:
            posts = db_client.scan("posts", "email", session['user']['email'])
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Unfriended successfully.')
    posts = db_client.scan("posts", "email", session['user']['email'])
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Unfriended successfully.')

@application.route('/friends', methods=['GET', 'POST'])
def friends():
    if (request.method == 'POST'):
        if (request.form['friends_email']):
            if (db_client.get_item("users", { 'email': request.form['friends_email'] })):
                matched_friends = db_client.scan("friends", "email_1", request.form['friends_email'])
                friends = []
                user = db_client.get_item("users", { 'email': request.form['friends_email'] })
                for matched_friend in matched_friends:
                    if (matched_friend['email_1'] == user['email']):
                        friends.append(db_client.get_item("users", { 'email': matched_friend['email_2'] }))
                print("Printing friends...")
                for friend in friends:
                    print(friend['email'] + " " + friend['user_name'])
                return render_template('friends.html', user=user, friends=friends)
            else:
                posts = db_client.scan("posts", "email", session['user']['email'])
                comments = get_comments(posts)
                liked = get_liked(posts)
                return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='User does not exist')
        else:
            posts = db_client.scan("posts", "email", session['user']['email'])
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Something went wrong. Please try again.')
    posts = db_client.scan("posts", "email", session['user']['email'])
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Something went wrong. Please try again.')

@application.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if (request.method == 'POST'):
        if (request.form['new_post_title'] and request.form['new_post_content']):
            item = {
                    'post_id': request.form['new_post_title'] + "-" + session['user']['email'],
                    'email': session['user']['email'],
                    'user_name': session['user']['user_name'],
                    'title': request.form['new_post_title'],
                    'content': request.form['new_post_content'],
                    'image_url': config.cloudfront_domain + "post_images/" + request.form['new_post_title'] + "-" + session['user']['email'] + ".jpg",
                    'datetime': str(datetime.datetime.now())
                    }
            db_client.put_item("posts", item)
            if "new_post_image" in request.files:
                file = request.files['new_post_image']
                file_name = "post_images/" + request.form['new_post_title'] + "-" + session['user']['email'] + ".jpg"
                s3_client.upload_fileobj(file, file_name)
            posts = db_client.scan("posts")
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Posted successfully")
    elif (request.method == 'GET'):
        posts = db_client.scan("posts")
        comments = get_comments(posts)
        liked = get_liked(posts)
        return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Method not POST. Please try agani.")
    else:
        posts = db_client.scan("posts")
        comments = get_comments(posts)
        liked = get_liked(posts)
        return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

@application.route('/like', methods=['GET', 'POST'])
def like():
    if (request.method == 'POST'):
        if (request.form['like_post_id']):
            if (db_client.get_item("likes", { 'email': session['user']['email'], 'post_id': request.form['like_post_id'] })):
                return render_template('home.html', message='You have already liked this post.')
            else:
                item = {
                        'email': session['user']['email'],
                        'post_id': request.form['like_post_id']
                        }
                db_client.put_item("likes", item)
                posts = db_client.scan("posts", "email", session['user']['email'])
                comments = get_comments(posts)
                liked = get_liked(posts)
                return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Liked successfully.')
        else:
            posts = db_client.scan("posts")
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

@application.route("/unlike", methods=['GET', 'POST'])
def unlike():
    if (request.method == 'POST'):
        if (request.form['unlike_post_id']):
            if (db_client.get_item("likes", { 'email': session['user']['email'], 'post_id': request.form['unlike_post_id'] })):
                db_client.delete_item("likes", 'post_id', request.form['unlike_post_id'], 'email', session['user']['email'])
                posts = db_client.scan("posts", "email", session['user']['email'])
                comments = get_comments(posts)
                liked = get_liked(posts)
                return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Unliked successfully.')
            else:
                posts = db_client.scan("posts")
                comments = get_comments(posts)
                liked = get_liked(posts)
                return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="You have not liked this post.")
        else:
            posts = db_client.scan("posts")
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

@application.route('/comment', methods=['GET', 'POST'])
def comment():
    if (request.method == 'POST'):
        if (request.form['comment_post_id'] and request.form['comment_content']):
            item = {
                    'comment_id': request.form['comment_post_id'] + "-" + session['user']['email'] + str(datetime.datetime.now()),
                    'post_id': request.form['comment_post_id'],
                    'email': session['user']['email'],
                    'name': session['user']['first_name'] + " " + session['user']['last_name'],
                    'content': request.form['comment_content'],
                    'datetime': str(datetime.datetime.now())
                    }
            db_client.put_item("comments", item)
            posts = db_client.scan("posts", "email", session['user']['email'])
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message='Commented successfully.')
        else:
            posts = db_client.scan("posts")
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

@application.route('/search', methods=['GET', 'POST'])
def search():
    if (request.method == 'POST'):
        print("Search content: " + request.form['search_content'])
        if (request.form['search_content']):
            post_results = db_client.scan("posts", "title", request.form['search_content'])
            print("Printing post results...")
            for post_result in post_results:
                print(post_result)
            user_results = db_client.scan("users", "user_name", request.form['search_content'])
            print("Printing user results...")
            for user_result in user_results:
                print(user_result)
            comments = get_comments(post_results)
            liked = get_liked(post_results)
            return render_template('search.html', user=session['user'], post_results=post_results, user_results=user_results, comments=comments, liked=liked, message='Search successful.')
        else:
            posts = db_client.scan("posts")
            comments = get_comments(posts)
            liked = get_liked(posts)
            return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")
    posts = db_client.scan("posts")
    comments = get_comments(posts)
    liked = get_liked(posts)
    return render_template('home.html', user=session['user'], posts=posts, comments=comments, liked=liked, message="Something went wrong. Please try again.")

if __name__ == '__main__':
    with application.test_request_context():
        session['key'] = 'value'
    application.run(host='0.0.0.0', port='80', debug=True)
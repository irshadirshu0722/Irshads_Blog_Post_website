from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy

from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from forms import CreatePostForm
from forms import Register,Login,CommandForm

from flask_gravatar import Gravatar
import smtplib
from Contact_details import my_password,my_email
import os

print(my_password,my_email)
'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

# import sqlite3
#
#
# db= sqlite3.connect("instance/new_post.dp")  # creating new database
#
# cursor = db.cursor()  # used to control



def admin_only(func):
    @wraps(func)
    def inner_func(*args, **kwargs):


        if current_user.is_authenticated:
            if current_user.id!=1:
                return abort(403)
            else :
                return func(*args, **kwargs)
        else:
            return abort(403)

    return inner_func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# TODO: Configure Flask-Login
login_manager=LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
db = SQLAlchemy()
db.init_app(app)



# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    img_url = db.Column(db.String(250), nullable=False)
    commends=relationship("Commands",backref="blog_posts")

# TODO: Create a User table for all your registered users.

class User(db.Model,UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(250),nullable=False)
    password = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(250), nullable=False)
    posts=relationship("BlogPost",backref="user")
    commands = relationship("Commands",backref="user")


class Commands(db.Model):
    __tablename__="Commands"
    id=db.Column(db.Integer,primary_key=True)
    commend = db.Column(db.String(250),nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    blog_id = db.Column(db.Integer,db.ForeignKey("blog_posts.id"))



with app.app_context():
    db.create_all()

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register' ,methods=["POST","GET"])
def register():
    form=Register()
    if request.method =="POST":
        email=request.form.get("email")
        password = request.form.get("password")
        check_user_in_db=db.session.execute(db.select(User).where(User.email==email)).scalars().all()
        if check_user_in_db:
            flash("User already exist")
            redirect("/register")
        hashed_and_salted_password=generate_password_hash(password=password,method="pbkdf2:sha256",salt_length=5)
        new_user = User(
            username=request.form.get("username"),
            email = email,
            password=hashed_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect('/')

    return render_template("register.html",form=form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods=["POST","GET"])
def login():
    form = Login()
    if request.method=="POST":
        email=request.form.get("email")
        email_in_db=db.session.execute(db.select(User).where(User.email==email)).scalar()
        if not email_in_db:
            flash("This email doesn't exist")
            return redirect('/login')
        elif not check_password_hash(email_in_db.password,request.form.get("password")):
            flash("Password is wrong")
            return redirect("/login")
        else:
            login_user(email_in_db)
            return redirect('/')




    return render_template("login.html",form=form)


@app.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('get_all_posts'))


@app.route('/')

def get_all_posts():

    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()



    return render_template("index.html", all_posts=posts ,is_loggined=current_user.is_authenticated)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=["POST","GET"])

def show_post(post_id):
    form=CommandForm()
    commands=db.get_or_404(BlogPost,post_id).commends

    if request.method=="POST":
        if not current_user.is_authenticated:
            flash("Please login or register to commend")
            return redirect("/login")
        new_command=Commands(
            commend=form.body.data,
            user=current_user,
            blog_posts=db.get_or_404(BlogPost,post_id)
        )
        db.session.add(new_command)
        db.session.commit()
        return redirect(f"/post/{post_id}")

    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post,current_user=current_user,form=form,commands=commands,is_loggined=current_user.is_authenticated)


# TODO: Use a decorator so only an admin user can create a new post

@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            user=current_user,
            date=date.today().strftime("%B %d, %Y"),

        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,is_loggined=current_user.is_authenticated)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True,is_loggined=current_user.is_authenticated)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html",is_loggined=current_user.is_authenticated)


@app.route("/contact" ,methods=["POST","GET"])
def contact():
    if request.method=="POST":
        user_email=request.form.get("email")
        user_name=request.form.get("name")
        user_message=request.form.get("message")
        user_mobile = request.form.get("phone")
        print(f" email going to send from email={my_email} , to email={my_email} , password={my_password}")
        with smtplib.SMTP("smtp.gmail.com") as connectiom:
            connectiom.starttls()
            connectiom.login(user=my_email,password=my_password)
            connectiom.sendmail(from_addr=my_email,to_addrs=my_email,
                                msg=f'''
Subject: Thank You for Contacting Irshad's Blog

Dear {user_name},

Thank you for reaching out to us through our website's contact form. We appreciate your interest and will get back to you as soon as possible.

Here are the details of your message:

Name: {user_name}
Email: {user_email}
Message: {user_message}
We will review your message and respond to your inquiry promptly. If you have any further questions or concerns, please feel free to contact us at [Your Contact Email Address].

Thank you once again for contacting us. We look forward to assisting you.

Best regards,
Muhammed irshad


'''

                                )
            return redirect("/")

    return render_template("contact.html",is_loggined=current_user.is_authenticated)


if __name__ == "__main__":
    app.run(debug=True, port=5002)

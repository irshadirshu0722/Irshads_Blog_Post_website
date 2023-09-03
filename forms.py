from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommandForm(FlaskForm):
    body=CKEditorField("comment",[DataRequired()])
    submit=SubmitField("Submit comment")

class Register(FlaskForm):
    username = StringField("username",[DataRequired()])
    email = StringField("email", [DataRequired()])
    password = PasswordField("password",[DataRequired()])
    submit = SubmitField("Register")


# TODO: Create a LoginForm to login existing users

class Login(FlaskForm):
    email = StringField("email",[DataRequired()])

    password = PasswordField("password",[DataRequired()])
    submit = SubmitField("Login")


# TODO: Create a CommentForm so users can leave comments below posts

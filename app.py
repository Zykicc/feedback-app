from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, BlankForm, FeedbackForm


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.app_context().push()
connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route("/")
def home():
  """redirect to register page"""

  return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register_form():
  """shows register page and form. handles register form submission"""
  form = RegisterForm()

  if form.validate_on_submit():
    username = form.username.data
    password = form.password.data
    email = form.email.data
    first_name = form.first_name.data
    last_name = form.last_name.data

    user = User.register(username, password, email, first_name, last_name)

    db.session.add(user)
    db.session.commit()

    session['username'] = user.username
    flash('Welcome! Successfully Created Your Account!', "success")
    return redirect(f"/users/{user.username}")

  return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login_form():
  
  """shows a form that will let users to log in. handles form submission and authentication"""

  if "username" in session:
        return redirect(f"/users/{session['username']}")

  form = LoginForm()

  if form.validate_on_submit():
    username = form.username.data
    password = form.password.data

    user = User.authenticate(username, password)  # <User> or False
    if user:
          flash(f"Welcome Back, {user.username}!", "primary")
          session['username'] = user.username
          return redirect(f"/users/{user.username}")
    else:
          form.username.errors = ["Invalid username/password."]

   
  
  return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')


@app.route("/users/<username>")
def show_user(username):
  """page for logged in users"""

  if "username" not in session or username != session['username']:
        raise Unauthorized()
  
  user = User.query.get(username)
  form = BlankForm()
  return render_template("user.html", user=user, form=form)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """remove user for database including all of the users feedback. clear information in the session"""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)

    db.session.delete(user)

    db.session.commit()

    session.pop("username")
    return redirect("/login")


@app.route("/users/<username>/feedback/add",methods=["GET", "POST"])
def add_feedback(username):
    """display form to add feedback and handle submission form"""

    if "username" not in session or username != session['username']:
        raise Unauthorized()
    
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")
    else:
        return render_template("add_feedback.html", form=form)\
        
@app.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("feedback_edit.html", form=form, feedback=feedback)

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = BlankForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")




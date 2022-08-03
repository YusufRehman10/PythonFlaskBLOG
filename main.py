from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime
from flask_mail import Mail
import math



with open('config.json','r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    SNO = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    Phone_num = db.Column(db.String(12), nullable=False)
    Msg = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    SNO = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    tagline = db.Column(db.String(12), nullable=False)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    #[0:params['no_of_posts']]

    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if (page==1):
        prev="#"
        next="/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/dashboard', methods=["GET","POST"])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_password']):
            session['user'] = username
            posts=Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            return render_template('login.html',params=params)
    else:
        return render_template('login.html', params=params)




@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/delete/<string:SNO>', methods = ["GET","POST"])
def delete(SNO):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(SNO=SNO).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/edit/<string:SNO>', methods = ["GET","POST"])
def edit(SNO):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            box_Title = request.form.get('Title')
            tline = request.form.get('tline')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if SNO=='0':
                post = Posts(Title=box_Title, slug=slug, Content=content, tagline=tline, img_file=img_file, Date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(SNO=SNO).first()
                post.Title=box_Title
                post.slug=slug
                post.Content=content
                post.tagline=tline
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+SNO)

        post=Posts.query.filter_by(SNO=SNO).first()
        return render_template('edit.html', params=params, post=post, SNO=SNO)

@app.route('/uploader', methods = ["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method=='POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/contact', methods = ["GET","POST"])
def contact():
    if (request.method=='POST'):
        '''Add entry to database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(Name=name, Phone_num=phone, Msg=message,Date=datetime.now(), Email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            'New Message from' + name,
            sender=email,
            recipients=[params['gmail-user']],
            body = message + '\n' + phone)



    return render_template('contact.html', params=params)

app.run(debug=True)
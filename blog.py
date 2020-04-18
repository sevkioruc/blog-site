from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Bu sayfayı görüntülemek için giriş yapın', 'danger')
            return redirect(url_for('login'))
    return decorated_function

app = Flask(__name__)
app.secret_key = 'blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///home/sevki/Desktop/blog/blog.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    author = db.Column(db.String(80), unique=True, nullable=False)
    content = db.Column(db.String(80), unique=True, nullable=False)
    createdDate = db.Column(db.DateTime, default=datetime.datetime.now)

class RegisterForm(Form):
    name = StringField('İsim Soyisim', validators=[validators.Length(min=5, max=15)])
    username =  StringField('Kullanıcı Adı', validators=[validators.Length(min=5, max=15)])
    email = StringField('Mail',validators=[validators.Email(message='Gecerli bir email adresi giriniz')])
    password = PasswordField('Password', validators = [
        validators.DataRequired(message='Lütfen bir parola belirleyiniz'),
        validators.EqualTo(fieldname='confirm', message='Parolanız uyuşmuyor')
    ])
    confirm = PasswordField('Parola Doğrula')

class LoginForm(Form):
    username =  StringField('Kullanıcı Adı')
    password = PasswordField('Password')


class ArticleForm(Form):
    title = StringField('Makale Başlığı', validators=[validators.Length(min=5, max=100)])
    content = TextAreaField('Makale İçeriği', validators=[validators.Length(min=10)])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        newUser = User(name= name, username= username, email= email, password= password)
        
        db.session.add(newUser)
        db.session.commit()
        flash('Başarı ile kayıt oldunuz', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        username = form.username.data
        passwordEntered = form.password.data

        user = User.query.filter_by(username=username).first()

        if user is not None:
            realPassword = user.password
            if sha256_crypt.verify(passwordEntered, realPassword):
                flash('Basarı ile giris yaptınız', 'success')
                
                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('index'))
            else:
                flash('Parola yanlış', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Kullanıcı bulunamadı', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/article/<string:id>')
def detail(id):
    article = Article.query.filter_by(id=id).first()
    return render_template('article.html', article = article)

@app.route('/dashboard')
@login_required
def dashboard():
    myArticles = Article.query.filter_by(author=session['username']).all()
    return render_template('dashboard.html', articles = myArticles)


@app.route('/addArticle', methods = ['GET', 'POST'])
@login_required
def addArticle():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data

        newArticle = Article(title= title, author=session['username'],content= content)

        db.session.add(newArticle)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('addArticle.html', form=form)


@app.route('/articles')
@login_required
def articles():
    articles = Article.query.all()

    if articles is not None:
        return render_template('articles.html', articles = articles)
    else:
        return render_template('articles.html')


@app.route('/delete/<string:id>')
@login_required
def delete(id):
    article = Article.query.filter_by(id = id).first()
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update/<string:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    if request.method == 'GET':
        article = Article.query.filter_by(id = id).first()
        
        if article is None:
            flash('Böyle bir makale bulunmamaktadır', 'danger')
            return redirect(url_for('index'))
        else:
            form = ArticleForm()
            form.title.data = article.title
            form.content.data = article.content
            return render_template('update.html', form = form)
        
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        db.session.query(Article).filter(Article.id == id).update({'title': newTitle, 'content': newContent})
        db.session.commit()

        return redirect(url_for('dashboard'))

if(__name__) == '__main__':
    db.create_all()
    app.run(debug=True)

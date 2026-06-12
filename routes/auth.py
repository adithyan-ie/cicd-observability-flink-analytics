from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from extensions import db
from models.user import User

auth_bp=Blueprint('auth',__name__)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        u=User(username=request.form['username'], email=request.form['email'])
        u.set_password(request.form['password'])
        db.session.add(u); db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(username=request.form['username']).first()
        if u and u.check_password(request.form['password']):
            login_user(u)
            return redirect('/')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

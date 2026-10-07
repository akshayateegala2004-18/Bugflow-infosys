from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            
            # Custom routing based on role
            if user.role == 'ADMIN':
                return redirect(url_for('user.dashboard'))  
            elif user.role == 'DEVELOPER':
                return redirect(url_for('developer.developer_dashboard'))
            elif user.role == 'TESTER':
                return redirect(url_for('tester.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
            
    return render_template('user/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
from flask import Flask, render_template, redirect, request, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whatsapp.db'
db = SQLAlchemy(app)

# 数据模型
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    numbers = db.Column(db.Text)
    short_code = db.Column(db.String(20), unique=True)
    expire_date = db.Column(db.DateTime)
    click_count = db.Column(db.Integer, default=0)

class IPLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(50))
    link_id = db.Column(db.Integer)
    access_time = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return 'WhatsApp Manager'

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    links = Link.query.all()
    return render_template('admin.html', links=links)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == '123' and request.form['password'] == '123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/<short_code>')
def redirect_whatsapp(short_code):
    link = Link.query.filter_by(short_code=short_code).first()
    if not link:
        return '链接不存在', 404
    
    # 检查链接是否过期
    if link.expire_date and link.expire_date < datetime.utcnow():
        return '链接已过期', 403
    
    # IP限制检查
    ip = request.remote_addr
    last_access = IPLog.query.filter_by(
        ip=ip, 
        link_id=link.id
    ).order_by(IPLog.access_time.desc()).first()
    
    if last_access and datetime.utcnow() - last_access.access_time < timedelta(hours=24):
        return '访问过于频繁，请24小时后再试', 403
    
    # 记录访问
    ip_log = IPLog(ip=ip, link_id=link.id)
    link.click_count += 1
    db.session.add(ip_log)
    db.session.commit()
    
    # 随机选择号码
    numbers = link.numbers.split(',')
    random_number = random.choice(numbers)
    return redirect(f'https://wa.me/{random_number}')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

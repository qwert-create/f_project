from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    mentor = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    def average_rating(self):
        reviews = Review.query.filter_by(course_id=self.id).all()
        if not reviews:
            return 0
        total = sum(review.rating for review in reviews)
        return total / len(reviews)

    def popularity(self):
        reviews_count = Review.query.filter_by(course_id=self.id).count()
        return reviews_count

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref='reviews')
    user = db.relationship('User', backref='reviews')

class user_courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

class CourseLesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_name = db.Column(db.String(200), nullable=False)
    lesson_desc = db.Column(db.Text, nullable=False)
    lesson_link = db.Column(db.String(200), nullable=False)
    lesson_num = db.Column(db.Integer, nullable=False)


app = Flask(__name__, template_folder='C:\\Users\\vlase\\Downloads\\course1\\templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

@app.context_processor
def utility_processor():
    def round_value(value):
        return round(value)
    return dict(round=round_value)

@app.route('/')
def index():
    courses = Course.query.all()
    courses_with_ratings = [(course, course.average_rating(), course.popularity()) for course in courses]
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        userid = session['user_id']
        conn = sqlite3.connect('instance/site.db')
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT course_id FROM user_courses WHERE user_id = ?", (userid,))
            result = cur.fetchall()
            result = [r[0] for r in result] if result else []
    else:
        userid = None
        result = []
    return render_template('index.html', courses_with_ratings=courses_with_ratings, result=result, userid=userid, user=user)

@app.route('/add_review/<int:course_id>', methods=['POST'])
def add_review(course_id):
    if 'user_id' in session:
        rating = request.form['rating']
        comment = request.form['comment']
        user_id = session['user_id']
        new_review = Review(rating=rating, comment=comment, user_id=user_id, course_id=course_id)
        db.session.add(new_review)
        db.session.commit()
        flash('Ваш відгук додано!', 'success')
        return redirect(url_for('index'))
    else:
        flash('Для додавання відгуку потрібно увійти в систему.', 'danger')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username 
            flash('Ви успішно увійшли до системи!', 'success')
            
            if username == 'Admin':
                user.is_admin = True
                db.session.commit()

                return redirect(url_for('admin_actions'))

            return redirect(url_for('index'))
        else:
            flash("Невдала спроба входу. Будь ласка, перевірте ваше ім'я користувача та пароль.", 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Ваш обліковий запис створено! Тепер ви можете увійти.', 'success')
            return redirect(url_for('login'))
        else:
            flash("Невдала реєстрація. Ім'я користувача вже існує. Виберіть інший.", 'danger')
    return render_template('register.html')

@app.route('/admin_actions', methods=['GET', 'POST'])
def admin_actions():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            if request.method == 'POST':
                action = request.form['action']
                if action == 'add':
                    return redirect(url_for('add_course'))
                elif action == 'delete':
                    return redirect(url_for('delete_course'))
                elif action == 'addlesson':
                    return redirect(url_for('add_lesson_sel'))
                elif action == 'deletelesson':
                    return redirect(url_for('delete_lesson_sel'))
            return render_template('admin_actions.html')
    return redirect(url_for('index'))

@app.route('/delete_course', methods=['GET', 'POST'])
def delete_course():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            if request.method == 'POST':
                title = request.form['title']
                course_to_delete = Course.query.filter_by(title=title).first()
                if course_to_delete:
                    Review.query.filter_by(course_id=course_to_delete.id).delete()
                    db.session.delete(course_to_delete)
                    db.session.commit()
                    flash('Курс було успішно видалено!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Курс не знайдено або не може бути видалений.', 'danger')
            return render_template('delete_course.html')
    return redirect(url_for('index'))


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            if request.method == 'POST':
                title = request.form['title']
                description = request.form['description']
                duration = request.form['duration']
                mentor = request.form['mentor']
                price = request.form['price']
                new_course = Course (
                    title=title,
                    description=description,
                    duration=duration,
                    mentor=mentor,
                    price=price
                )
                db.session.add(new_course)
                db.session.commit()
                flash('Курс було успішно додано!', 'success')
                return redirect(url_for('index'))
            return render_template('add_course.html')
    return redirect(url_for('index'))

@app.route('/add_lesson_sel', methods=['GET', 'POST'])
def add_lesson_sel():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            courses = Course.query.all()
            if request.method == 'POST':
                course_id = request.form['course_id']
                return redirect(url_for('add_lesson', course_id=course_id))
            return render_template('add_lesson_sel.html', courses=courses)
    return redirect(url_for('index'))

@app.route('/add_lesson/<int:course_id>', methods=['GET', 'POST'])
def add_lesson(course_id):
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            if request.method == 'POST':
                lesson_name = request.form['lesson_name']
                lesson_desc = request.form['lesson_desc']
                lesson_link_notready = request.form['lesson_link']
                lesson_link = lesson_link_notready.replace('watch?v=', 'embed/')
                max_lesson_num = db.session.query(db.func.max(CourseLesson.lesson_num)).filter_by(course_id=course_id).scalar()
                if max_lesson_num is None:
                    max_lesson_num = 0
                new_lesson = CourseLesson (
                    course_id=course_id,
                    lesson_name=lesson_name,
                    lesson_desc=lesson_desc,
                    lesson_link=lesson_link,
                    lesson_num=max_lesson_num + 1
                )
                db.session.add(new_lesson)
                db.session.commit()
                flash('Урок було успішно додано!', 'success')
                return redirect(url_for('course', course_id=course_id))
            return render_template('add_lesson.html', course_id=course_id)
    return redirect(url_for('index'))

@app.route('/course/<int:course_id>/lessons')
def course(course_id):
    user_id = session.get('user_id')
    if user_id:
        conn = sqlite3.connect('instance/site.db')
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM User_Courses WHERE user_id = ? AND course_id = ?", (user_id, course_id))
            is_buyed = cur.fetchone()[0] > 0
            if not is_buyed:
                return redirect(url_for('index'))
            cur.execute("SELECT lesson_name, lesson_num FROM Course_Lesson WHERE course_id = ? ORDER BY lesson_num", (course_id,))
            result = cur.fetchall()
        return render_template('course.html', result=result, course_id=course_id)
    else:
        return redirect(url_for('login'))   

@app.route('/course/<int:course_id>/lesson/<int:lesson_num>')
def lesson(course_id, lesson_num):
    user_id = session.get('user_id')
    if user_id:
        conn = sqlite3.connect('instance/site.db')
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM User_Courses WHERE user_id = ? AND course_id = ?", (user_id, course_id))
            is_buyed = cur.fetchone()[0] > 0
            if not is_buyed:
                return redirect(url_for('index'))
        conn = sqlite3.connect('instance/site.db')
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT lesson_name, lesson_desc, lesson_link FROM Course_Lesson WHERE course_id = ? and lesson_num = ?", (course_id, lesson_num,))
            result = cur.fetchall()
        return render_template('lesson.html', result=result, course_id=course_id)
    else:
        return redirect(url_for('login'))

@app.route('/delete_lesson_sel', methods=['GET', 'POST'])
def delete_lesson_sel():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            courses = Course.query.all()
            if request.method == 'POST':
                course_id = request.form['course_id']
                return redirect(url_for('delete_lesson', course_id=course_id))
            return render_template('delete_lesson_sel.html', courses=courses)
    return redirect(url_for('index'))

@app.route('/delete_lesson/<int:course_id>', methods=['GET', 'POST'])
def delete_lesson(course_id):
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user.is_admin:
            lessons = CourseLesson.query.filter_by(course_id=course_id).all()
            if request.method == 'POST':
                lesson_id = request.form['lesson_id']
                lesson_to_delete = CourseLesson.query.get(lesson_id)
                if lesson_to_delete:
                    db.session.delete(lesson_to_delete)
                    db.session.commit()
                    return redirect(url_for('index'))
                else:
                    flash('Урок не знайдено або не може бути видалений.', 'danger')
            return render_template('delete_lesson.html', lessons=lessons, course_id=course_id)
    return redirect(url_for('index'))

@app.route('/payment/<int:course_id>', methods=['GET', 'POST'])
def payment(course_id):
    if 'user_id' not in session:
        flash('Для оплати потрібно увійти в систему.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    course_price = None
    conn = sqlite3.connect('instance/site.db')
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT price FROM course WHERE id = ?", (course_id,))
        course_price = cur.fetchone()
        if course_price:
            course_price = course_price[0]
        else:
            flash('Курс не знайдено', 'danger')
            return redirect(url_for('index'))

    if request.method == 'POST':
        cardnumber = request.form['cardnumber']
        expmonth = request.form['expmonth']
        expyear = request.form['expyear']
        cvv = request.form['cvv']
        conn = sqlite3.connect('bankbase.db')
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM bank WHERE cardnumber = ? AND expmonth = ? AND expyear = ? AND cvv = ?", (cardnumber, expmonth, expyear, cvv))
            result = cur.fetchone()
            if result:
                balance = result[0]
                if balance >= course_price:
                    new_balance = balance - course_price
                    cur.execute("UPDATE bank SET balance = ? WHERE cardnumber = ? AND expmonth = ? AND expyear = ? AND cvv = ?",
                                (new_balance, cardnumber, expmonth, expyear, cvv))
                    conn = sqlite3.connect('instance/site.db')
                    with conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO user_courses (user_id, course_id) VALUES (?, ?)", 
                                    (user_id, course_id))
                        conn.commit()
                    flash('Платіж успішно завершено!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Недостатньо коштів на балансі', 'danger')
            else:
                flash('Неправильні дані картки', 'danger')
        return render_template('payment.html', course_id=course_id, course_price=course_price)

    return render_template('payment.html', course_id=course_id, course_price=course_price)


@app.errorhandler(403)
def access_forbidden(error):
    return render_template('403.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
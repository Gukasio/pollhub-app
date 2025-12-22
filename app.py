from flask import Flask, flash, render_template, request, url_for

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import timezone
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-12345'

# Настройка базы данных
db_path = os.path.join(os.path.dirname(__file__), 'polls.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель опроса
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_one = db.Column(db.String(200), nullable=False)
    option_two = db.Column(db.String(200), nullable=False)
    option_three = db.Column(db.String(200), nullable=False)
    option_four = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Poll {self.title}>'


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    ip_address = db.Column(db.String(100), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3 или 4
    voted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Связь с опросом
    poll = db.relationship('Poll', backref=db.backref('votes', lazy=True))

    def __repr__(self):
        return f'<Vote for Poll {self.poll_id}, option {self.selected_option}>'


@app.route('/')
def index():
    # Получаем все опросы из БД, отсортированные по дате (новые первыми)
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    return render_template('index.html', polls=polls)

# Временные маршруты для работы HTML
@app.route('/create', methods=['GET', 'POST'])
def create_poll():
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.form.get('title')
        question = request.form.get('question')
        option_one = request.form.get('option_one')
        option_two = request.form.get('option_two')
        option_three = request.form.get('option_three')
        option_four = request.form.get('option_four')
        
        # Валидация данных
        if not title or not question:
            flash('Название и вопрос опроса обязательны!', 'danger')
            return app.redirect(app.url_for('create_poll'))
        
        if not all([option_one, option_two, option_three, option_four]):
            flash('Все 4 варианта ответа должны быть заполнены!', 'danger')
            return app.redirect(app.url_for('create_poll'))
        
        # Создаем новый опрос
        new_poll = Poll(
            title=title.strip(),
            question=question.strip(),
            option_one=option_one.strip(),
            option_two=option_two.strip(),
            option_three=option_three.strip(),
            option_four=option_four.strip()
        )
        
        # Сохраняем в БД
        try:
            db.session.add(new_poll)
            db.session.commit()
            flash('Опрос успешно создан!', 'success')
            return app.redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании опроса: {str(e)}', 'danger')
            return app.redirect(app.url_for('create_poll'))
    
    # GET запрос - показываем форму (форму сделает напарник)
    return render_template('create_poll.html')

@app.route('/admin')
def admin():
    return 'Админ-панель (в разработке)'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()        
    app.run(debug=True)
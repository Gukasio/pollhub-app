from flask import Flask, flash, redirect, render_template, request, session, url_for

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
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
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
        option_1 = request.form.get('option_1')
        option_2 = request.form.get('option_2')
        option_3 = request.form.get('option_3')
        option_4 = request.form.get('option_4')
        
        # Валидация данных
        if not title or not question:
            flash('Название и вопрос опроса обязательны!', 'danger')
            return app.redirect(app.url_for('create_poll'))
        
        if not all([option_1, option_2, option_3, option_4]):
            flash('Все 4 варианта ответа должны быть заполнены!', 'danger')
            return app.redirect(app.url_for('create_poll'))
        
        # Создаем новый опрос
        new_poll = Poll(
            title=title.strip(),
            question=question.strip(),
            option_1=option_1.strip(),
            option_2=option_2.strip(),
            option_3=option_3.strip(),
            option_4=option_4.strip()
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

@app.route('/poll/<int:poll_id>')
def poll_detail(poll_id):
    # Находим опрос по ID или возвращаем 404
    poll = Poll.query.get_or_404(poll_id)
    
    # Получаем IP пользователя для проверки голосования
    user_ip = request.remote_addr
    
    # Проверяем голосовал ли уже этот IP
    has_voted = Vote.query.filter_by(poll_id=poll_id, ip_address=user_ip).first() is not None
    
    return render_template('poll_detail.html', 
                         poll=poll, 
                         has_voted=has_voted, 
                         user_ip=user_ip)

@app.route('/poll/<int:poll_id>/vote', methods=['POST'])
def vote(poll_id):
    """Обработка голосования"""
    
    # Находим опрос
    poll = Poll.query.get_or_404(poll_id)
    
    # Получаем выбранный вариант
    selected_option = request.form.get('selected_option')
    
    # Валидация: выбран ли вариант
    if not selected_option or selected_option not in ['1', '2', '3', '4']:
        flash('Пожалуйста, выберите вариант ответа', 'danger')
        return redirect(url_for('poll_detail', poll_id=poll_id))
    
    # Получаем IP пользователя
    user_ip = request.remote_addr
    
    # Проверяем не голосовал ли уже этот IP в этом опросе
    existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=user_ip).first()
    if existing_vote:
        flash(f'Вы уже голосовали в этом опросе (IP: {user_ip})', 'warning')
        return redirect(url_for('poll_results', poll_id=poll_id))
    
    # Создаем новый голос
    new_vote = Vote(
        poll_id=poll_id,
        ip_address=user_ip,
        selected_option=int(selected_option)
    )
    
    # Сохраняем в БД
    try:
        db.session.add(new_vote)
        db.session.commit()
        flash('Ваш голос успешно учтен!', 'success')
        return redirect(url_for('poll_results', poll_id=poll_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сохранении голоса: {str(e)}', 'danger')
        return redirect(url_for('poll_detail', poll_id=poll_id))

@app.route('/admin')
def admin():
    """Админ-панель без авторизации (для учебного проекта)"""
    # Получаем все опросы с количеством голосов
    polls = Poll.query.all()
    
    # Добавляем статистику к каждому опросу
    polls_with_stats = []
    for poll in polls:
        vote_count = Vote.query.filter_by(poll_id=poll.id).count()
        polls_with_stats.append({
            'poll': poll,
            'vote_count': vote_count,
            'created_date': poll.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    # Общая статистика
    total_polls = len(polls)
    total_votes = Vote.query.count()
    
    return render_template('admin.html',
                         polls_with_stats=polls_with_stats,
                         total_polls=total_polls,
                         total_votes=total_votes)


@app.route('/admin/poll/<int:poll_id>/delete', methods=['POST'])
def delete_poll(poll_id):
    """Удаление опроса и всех связанных голосов"""
    poll = Poll.query.get_or_404(poll_id)
    
    try:
        # Сначала удаляем все голоса для этого опроса
        Vote.query.filter_by(poll_id=poll_id).delete()
        
        # Затем удаляем сам опрос
        db.session.delete(poll)
        db.session.commit()
        
        flash(f'Опрос "{poll.title}" успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/poll/<int:poll_id>/results')
def poll_results(poll_id):
    """Страница результатов опроса"""
    
    poll = Poll.query.get_or_404(poll_id)
    user_ip = request.remote_addr
    
    # Получаем все голоса для этого опроса
    votes = Vote.query.filter_by(poll_id=poll_id).all()
    total_votes = len(votes)
    
    # Считаем голоса по вариантам
    vote_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for vote in votes:
        vote_counts[vote.selected_option] += 1
    
    # Находим голос текущего пользователя
    user_vote = None
    for vote in votes:
        if vote.ip_address == user_ip:
            user_vote = vote.selected_option
            break

    # Считаем проценты
    percentages = {}
    option_texts = {
        1: poll.option_1,
        2: poll.option_2, 
        3: poll.option_3,
        4: poll.option_4
    }
    
    if total_votes > 0:
        for option in range(1, 5):
            percentages[option] = (vote_counts[option] / total_votes) * 100
    
    avg_per_option = round(total_votes / 4) if total_votes > 0 else 0
    leading_option = 0
    leading_percentage = 0
    
    if total_votes > 0:
        max_votes = 0
        for option, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                leading_option = option
                leading_percentage = percentages[option]


    return render_template('poll_results.html',
                         poll=poll,
                         total_votes=total_votes,
                         vote_counts=vote_counts,
                         percentages=percentages,
                         option_texts=option_texts,
                         user_vote=user_vote,
                         user_ip=user_ip,
                         avg_per_option=avg_per_option,
                         leading_option=leading_option,
                         leading_percentage=leading_percentage)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()        
    app.run(debug=True)

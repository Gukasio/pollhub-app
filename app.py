import os
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy


# Инициализация приложения
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'polls.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модели базы данных
class Poll(db.Model):
    """Модель опроса"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Poll "{self.title}">'
    
    def get_option_text(self, option_number):
        """Получить текст варианта ответа по номеру"""
        options = {
            1: self.option_1,
            2: self.option_2,
            3: self.option_3,
            4: self.option_4
        }
        return options.get(option_number, "Неизвестный вариант")
    
    def get_vote_count(self):
        """Получить количество голосов для этого опроса"""
        return Vote.query.filter_by(poll_id=self.id).count()


class Vote(db.Model):
    """Модель голоса"""
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    ip_address = db.Column(db.String(100), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3 или 4
    voted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Связи
    poll = db.relationship('Poll', backref=db.backref('votes', lazy=True))

    def __repr__(self):
        return f'<Vote poll:{self.poll_id} option:{self.selected_option}>'


# Вспомогательные функции
def validate_poll_data(title, question, options):
    """Валидация данных опроса"""
    errors = []
    
    if not title or not title.strip():
        errors.append('Название опроса обязательно')
    
    if not question or not question.strip():
        errors.append('Вопрос опроса обязателен')
    
    for i, option in enumerate(options, 1):
        if not option or not option.strip():
            errors.append(f'Вариант ответа {i} обязателен')
    
    return errors


def calculate_vote_statistics(poll_id):
    """Расчет статистики голосования для опроса"""
    votes = Vote.query.filter_by(poll_id=poll_id).all()
    total_votes = len(votes)
    
    # Подсчет голосов по вариантам
    vote_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for vote in votes:
        vote_counts[vote.selected_option] += 1
    
    # Расчет процентов
    percentages = {}
    if total_votes > 0:
        for option in range(1, 5):
            percentages[option] = (vote_counts[option] / total_votes) * 100
    
    return {
        'votes': votes,
        'total_votes': total_votes,
        'vote_counts': vote_counts,
        'percentages': percentages
    }


def get_user_vote(poll_id, user_ip):
    """Получить голос пользователя для опроса"""
    return Vote.query.filter_by(poll_id=poll_id, ip_address=user_ip).first()


# Маршруты приложения
@app.route('/')
def index():
    """Главная страница - список всех опросов"""
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    return render_template('index.html', polls=polls)


@app.route('/create', methods=['GET', 'POST'])
def create_poll():
    """Создание нового опроса"""
    if request.method == 'POST':
        # Получение данных из формы
        form_data = {
            'title': request.form.get('title', '').strip(),
            'question': request.form.get('question', '').strip(),
            'options': [
                request.form.get('option_1', '').strip(),
                request.form.get('option_2', '').strip(),
                request.form.get('option_3', '').strip(),
                request.form.get('option_4', '').strip()
            ]
        }
        
        # Валидация
        errors = validate_poll_data(
            form_data['title'], 
            form_data['question'], 
            form_data['options']
        )
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('create_poll'))
        
        # Создание опроса
        try:
            new_poll = Poll(
                title=form_data['title'],
                question=form_data['question'],
                option_1=form_data['options'][0],
                option_2=form_data['options'][1],
                option_3=form_data['options'][2],
                option_4=form_data['options'][3]
            )
            
            db.session.add(new_poll)
            db.session.commit()
            
            flash('Опрос успешно создан!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании опроса: {str(e)}', 'danger')
            return redirect(url_for('create_poll'))
    
    # GET запрос - отображение формы
    return render_template('create_poll.html')


@app.route('/poll/<int:poll_id>')
def poll_detail(poll_id):
    """Страница опроса с формой голосования"""
    poll = Poll.query.get_or_404(poll_id)
    user_ip = request.remote_addr
    user_vote = get_user_vote(poll_id, user_ip)
    
    return render_template(
        'poll_detail.html',
        poll=poll,
        has_voted=user_vote is not None,
        user_ip=user_ip,
        user_vote=user_vote
    )


@app.route('/poll/<int:poll_id>/vote', methods=['POST'])
def vote(poll_id):
    """Обработка голосования"""
    poll = Poll.query.get_or_404(poll_id)
    user_ip = request.remote_addr
    selected_option = request.form.get('selected_option')
    
    # Валидация выбора
    if not selected_option or selected_option not in ['1', '2', '3', '4']:
        flash('Пожалуйста, выберите вариант ответа', 'danger')
        return redirect(url_for('poll_detail', poll_id=poll_id))
    
    # Проверка повторного голосования
    if get_user_vote(poll_id, user_ip):
        flash('Вы уже голосовали в этом опросе!', 'warning')
        return redirect(url_for('poll_results', poll_id=poll_id))
    
    # Сохранение голоса
    try:
        new_vote = Vote(
            poll_id=poll_id,
            ip_address=user_ip,
            selected_option=int(selected_option)
        )
        
        db.session.add(new_vote)
        db.session.commit()
        
        flash('Ваш голос успешно учтен!', 'success')
        return redirect(url_for('poll_results', poll_id=poll_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сохранении голоса: {str(e)}', 'danger')
        return redirect(url_for('poll_detail', poll_id=poll_id))


@app.route('/poll/<int:poll_id>/results')
def poll_results(poll_id):
    """Страница результатов опроса"""
    poll = Poll.query.get_or_404(poll_id)
    user_ip = request.remote_addr
    
    # Получение статистики
    stats = calculate_vote_statistics(poll_id)
    user_vote = get_user_vote(poll_id, user_ip)
    
    # Подготовка данных для шаблона
    option_texts = {
        1: poll.option_1,
        2: poll.option_2,
        3: poll.option_3,
        4: poll.option_4
    }
    
    # Определение лидирующего варианта
    leading_option = None
    leading_percentage = 0
    
    if stats['total_votes'] > 0:
        for option, percentage in stats['percentages'].items():
            if percentage > leading_percentage:
                leading_percentage = percentage
                leading_option = option
    
    return render_template(
        'poll_results.html',
        poll=poll,
        total_votes=stats['total_votes'],
        vote_counts=stats['vote_counts'],
        percentages=stats['percentages'],
        option_texts=option_texts,
        user_vote=user_vote.selected_option if user_vote else None,
        user_ip=user_ip,
        leading_option=leading_option,
        leading_percentage=leading_percentage
    )


@app.route('/admin')
def admin():
    """Админ-панель"""
    polls = Poll.query.all()
    
    # Подготовка данных для отображения
    polls_with_stats = []
    for poll in polls:
        polls_with_stats.append({
            'poll': poll,
            'vote_count': poll.get_vote_count(),
            'created_date': poll.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    total_votes = Vote.query.count()
    
    return render_template(
        'admin.html',
        polls_with_stats=polls_with_stats,
        total_polls=len(polls),
        total_votes=total_votes
    )


@app.route('/admin/poll/<int:poll_id>/delete', methods=['POST'])
def delete_poll(poll_id):
    """Удаление опроса"""
    poll = Poll.query.get_or_404(poll_id)
    poll_title = poll.title
    
    try:
        # Удаление связанных голосов
        Vote.query.filter_by(poll_id=poll_id).delete()
        
        # Удаление опроса
        db.session.delete(poll)
        db.session.commit()
        
        flash(f'Опрос "{poll_title}" успешно удален', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))


@app.errorhandler(404)
def page_not_found(error):
    """Обработка 404 ошибки"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка 500 ошибки"""
    db.session.rollback()
    return render_template('500.html'), 500

# Тествые маршруты для проверки
@app.route('/test/500')
def test_500_error():
    """Тестовый маршрут для проверки 500 ошибки"""
    # Искусственно вызываем исключение
    raise Exception("Тестовая 500 ошибка - страница ошибки работает!")


@app.route('/test/404')
def test_404_error():
    """Тестовый маршрут для проверки 404 ошибки"""
    from flask import abort  # Добавьте этот импорт вверху файла
    abort(404)  # Явно вызываем 404 ошибку


# Точка входа
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False) 
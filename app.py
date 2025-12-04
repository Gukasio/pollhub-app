from flask import Flask, render_template

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import timezone
import os

app = Flask(__name__)

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
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с опросом
    poll = db.relationship('Poll', backref=db.backref('votes', lazy=True))

    def __repr__(self):
        return f'<Vote for Poll {self.poll_id}, option {self.selected_option}>'


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
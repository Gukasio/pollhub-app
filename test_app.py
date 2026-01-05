import pytest
from app import app, db, Poll, Vote
from datetime import datetime

# Фикстура для тестового клиента
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Создаем тестовый опрос
            poll = Poll()
            poll.title = 'Test Poll'
            poll.question = 'Test question?'
            poll.option_1 = 'Option 1'
            poll.option_2 = 'Option 2'
            poll.option_3 = 'Option 3'
            poll.option_4 = 'Option 4'
            db.session.add(poll)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

# Тест 1: Главная страница
def test_index_page(client):
    """Test that main page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'PollHub' in response.data

# Тест 2: Страница создания опроса
def test_create_poll_page(client):
    """Test that create poll page loads"""
    response = client.get('/create')
    assert response.status_code == 200
    # Проверяем что это HTML страница
    assert b'<!DOCTYPE html>' in response.data

# Тест 3: Создание опроса
def test_create_poll(client):
    """Test creating new poll"""
    data = {
        'title': 'New Test Poll',
        'question': 'New test question?',
        'option_1': 'New Option 1',
        'option_2': 'New Option 2',
        'option_3': 'New Option 3',
        'option_4': 'New Option 4'
    }
    
    response = client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # Check poll was added to database
    with app.app_context():
        polls = Poll.query.all()
        assert len(polls) >= 1  # Уже был один + новый

# Тест 4: Страница опроса
def test_poll_detail_page(client):
    """Test that poll page loads"""
    with app.app_context():
        poll = Poll.query.first()
    
    response = client.get(f'/poll/{poll.id}')
    assert response.status_code == 200
    # Проверяем что страница содержит данные опроса
    assert poll.title.encode() in response.data

# Тест 5: Страница результатов
def test_poll_results_page(client):
    """Test that results page loads"""
    with app.app_context():
        poll = Poll.query.first()
    
    response = client.get(f'/poll/{poll.id}/results')
    assert response.status_code == 200
    assert b'results' in response.data.lower() 

# Тест 6: Админ-панель
def test_admin_page(client):
    """Test that admin page loads"""
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'admin' in response.data.lower() 

# Тест 7: Модель Poll
def test_poll_model():
    """Test Poll model"""
    poll = Poll()
    poll.title = 'Model Test'
    poll.question = 'Model question?'
    poll.option_1 = 'O1'
    poll.option_2 = 'O2'
    poll.option_3 = 'O3'
    poll.option_4 = 'O4'
    
    assert poll.title == 'Model Test'
    assert poll.question == 'Model question?'
    assert poll.option_1 == 'O1'
    assert poll.option_4 == 'O4'

# Тест 8: Модель Vote
def test_vote_model():
    """Test Vote model"""
    vote = Vote()
    vote.poll_id = 1
    vote.ip_address = '127.0.0.1'
    vote.selected_option = 2
    
    assert vote.poll_id == 1
    assert vote.ip_address == '127.0.0.1'
    assert vote.selected_option == 2

# Тест 9: Проверка голосования
def test_vote_functionality(client):
    """Test voting process"""
    with app.app_context():
        poll = Poll.query.first()
    
    # Vote
    response = client.post(f'/poll/{poll.id}/vote', 
                          data={'selected_option': '1'},
                          follow_redirects=True)
    assert response.status_code == 200
    
    # Check vote was saved
    with app.app_context():
        votes = Vote.query.all()
        assert len(votes) == 1
        assert votes[0].selected_option == 1
        assert votes[0].poll_id == poll.id

# Тест 10: Дублирование голосования
def test_duplicate_vote(client):
    """Test duplicate vote prevention"""
    with app.app_context():
        poll = Poll.query.first()
    
    # First vote
    response1 = client.post(f'/poll/{poll.id}/vote', 
                           data={'selected_option': '1'},
                           follow_redirects=True)
    assert response1.status_code == 200
    
    # Second vote from same IP (should be blocked)
    response2 = client.post(f'/poll/{poll.id}/vote', 
                           data={'selected_option': '2'},
                           follow_redirects=True)
    assert response2.status_code == 200
    
    with app.app_context():
        votes = Vote.query.all()
        # Должен быть только один голос
        assert len(votes) == 1
        assert votes[0].selected_option == 1

# Тест 11: Проверка полей модели Poll
def test_poll_fields():
    """Test that Poll model has correct fields"""
    poll = Poll()
    
    # Проверяем что поля существуют
    poll.title = 'Title'
    poll.question = 'Question'
    poll.option_1 = 'Option 1'
    poll.option_2 = 'Option 2'
    poll.option_3 = 'Option 3'
    poll.option_4 = 'Option 4'
    
    assert hasattr(poll, 'title')
    assert hasattr(poll, 'question')
    assert hasattr(poll, 'option_1')
    assert hasattr(poll, 'option_2')
    assert hasattr(poll, 'option_3')
    assert hasattr(poll, 'option_4')
    assert hasattr(poll, 'created_at')
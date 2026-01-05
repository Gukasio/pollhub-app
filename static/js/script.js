// Основной JavaScript для PollHub

document.addEventListener('DOMContentLoaded', function() {
    console.log('PollHub loaded successfully');
    
    // Анимация появления элементов
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(el => {
        el.style.opacity = '0';
        setTimeout(() => {
            el.style.opacity = '1';
        }, 100);
    });
    
    // Подтверждение удаления опроса
    const deleteButtons = document.querySelectorAll('.btn-delete-poll');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Удалить этот опрос и все голоса? Это действие нельзя отменить.')) {
                e.preventDefault();
            }
        });
    });
    
    // Плавная прокрутка
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
    
    // Обработка flash-сообщений
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
    
    // Валидация формы создания опроса
    const createForm = document.getElementById('create-poll-form');
    if (createForm) {
        createForm.addEventListener('submit', function(e) {
            const title = this.querySelector('[name="title"]').value.trim();
            const question = this.querySelector('[name="question"]').value.trim();
            
            if (!title || !question) {
                e.preventDefault();
                alert('Пожалуйста, заполните название и вопрос опроса');
                return false;
            }
            
            // Проверка всех вариантов ответа
            const options = [
                this.querySelector('[name="option_1"]').value.trim(),
                this.querySelector('[name="option_2"]').value.trim(),
                this.querySelector('[name="option_3"]').value.trim(),
                this.querySelector('[name="option_4"]').value.trim()
            ];
            
            const emptyOptions = options.filter(opt => !opt);
            if (emptyOptions.length > 0) {
                e.preventDefault();
                alert('Пожалуйста, заполните все 4 варианта ответа');
                return false;
            }
            
            return true;
        });
    }
});

// Утилиты
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('ru-RU', options);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
import os
import json
import datetime
from flask import Flask, render_template_string, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# КОНФИГУРАЦИЯ
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mars_mission_ultra_secret_key_99'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cognitive_test.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ДАННЫЕ ТЕСТА
BIASES = {
    'confirmation': 'Склонность к подтверждению',
    'dunning_kruger': 'Эффект Даннинга-Крюгера',
    'sunk_cost': 'Ловушка невозвратных затрат',
    'availability': 'Эвристика доступности',
    'hindsight': 'Ошибка хайндсайта',
    'base_rate_fallacy': 'Игнорирование базовой частоты',
    'anchoring': 'Эффект якоря',
    'hyperbolic_discounting': 'Гиперболическое дисконтирование',
    'disposition_effect': 'Эффект расположения',
    'overconfidence': 'Сверх уверенность',
    'conjunction_fallacy': 'Ошибка конъюнкции',
    'endowment_effect': 'Эффект владения',
    'prospect_theory': 'Теория перспектив',
    'false_consensus': 'Эффект ложного консенсуса',
    'ambiguity_aversion': 'Неприятие неопределенности',
    'denominator_neglect': 'Игнорирование знаменателя',
    'sample_size_neglect': 'Игнорирование размера выборки',
    'clustering_illusion': 'Иллюзия кластеризации'
}

QUESTIONS = [
    {
        'id': 1,
        'text': 'Вы вложили 1000$ в проект, который явно проваливается. Ваши действия?',
        'options': [
            {'text': 'Вложу еще 500$, чтобы спасти прошлые инвестиции', 'bias': 'sunk_cost'},
            {'text': 'Закрою проект и зафиксирую убытки', 'bias': None}
        ]
    },
    {
        'id': 2,
        'text': 'Ваш друг говорит, что курение не вредно, потому что его дед курил до 90 лет. Вы согласны?',
        'options': [
            {'text': 'Да, личный пример убедительнее статистики', 'bias': 'availability'},
            {'text': 'Нет, один пример не отменяет общую научную выборку', 'bias': None}
        ]
    },
    {
        'id': 3,
        'text': 'Насколько хорошо вы водите автомобиль по сравнению со средним водителем?',
        'options': [
            {'text': 'Я определенно вхожу в топ-10% лучших', 'bias': 'dunning_kruger'},
            {'text': 'Я обычный водитель, как и большинство', 'bias': None}
        ]
    },
    {
        'id': 4,
        'text': 'Вы ищете информацию о вреде кофе и открываете только те статьи, где написано, что он полезен. Это:',
        'options': [
            {'text': 'Объективный поиск информации', 'bias': None},
            {'text': 'Поиск подтверждения своего мнения', 'bias': 'confirmation'}
        ]
    },

    {
        'id': 1,
        'text': 'В городе живёт 1000 человек. 10 из них — террористы. Система распознавания имеет точность 99% (1% ложных срабатываний). Система сигнализирует на случайном человеке. Какова вероятность, что он действительно террорист?',
        'options': [
            {'text': 'Примерно 99% — система же точная', 'bias': 'base_rate_fallacy'},
            {'text': 'Примерно 50% — нужно учитывать, что террористов мало', 'bias': None},
            {'text': 'Примерно 9% — террористов очень мало, даже с точной системой', 'bias': 'base_rate_fallacy'}
        ]
    },
    {
        'id': 2,
        'text': 'Вы продаёте антикварную вазу. Покупатель говорит: «Такие обычно стоят 5000, но давай за 4000». Реальная рыночная цена — 4500. Ваши действия?',
        'options': [
            {'text': 'Соглашусь на 4000, это выше моей минималки 3500', 'bias': 'anchoring'},
            {'text': 'Назову 5000 и буду торговаться от этой цифры', 'bias': None},
            {'text': 'Покажу отчёт об оценке на 5500, чтобы сдвинуть якорь вверх', 'bias': None}
        ]
    },
    {
        'id': 3,
        'text': 'Выберите пару: (А1) 1000 руб. сегодня или (Б1) 1100 руб. через неделю. И отдельно: (А2) 1000 руб. через 52 недели или (Б2) 1100 руб. через 53 недели. Человек выбрал А1, но Б2. Это пример:',
        'options': [
            {'text': 'Рационального поведения — в каждом случае он выбрал больше', 'bias': None},
            {'text': 'Эффекта привязки к первому числу', 'bias': 'anchoring'},
            {'text': 'Гиперболического дисконтирования — сегодня терпеть не готов, а в далёком будущем — готов',
             'bias': 'hyperbolic_discounting'}
        ]
    },
    {
        'id': 4,
        'text': 'В городе 60% такси жёлтые, 40% белые. Свидетель аварии говорит: «Такси было жёлтым, я уверен на 80%». Какова реальная вероятность, что такси было жёлтым с учётом априорной вероятности?',
        'options': [
            {'text': '80% — доверяю свидетелю', 'bias': 'base_rate_fallacy'},
            {'text': 'Примерно 86% — по теореме Байеса', 'bias': None},
            {'text': 'Примерно 71% — где-то между 60% и 80%', 'bias': None}
        ]
    },
    {
        'id': 5,
        'text': 'Вы купили акции компании А по 100 руб. Сейчас они стоят 90 руб. Акции компании Б купили по 100 руб., сейчас 110 руб. Вам нужно срочно продать только одну из них (без налогов). Что вы сделаете?',
        'options': [
            {'text': 'Продам растущие акции (110 руб.), чтобы зафиксировать прибыль', 'bias': 'disposition_effect'},
            {'text': 'Продам падающие акции (90 руб.), чтобы не рисковать дальше', 'bias': None},
            {'text': 'Продам ту, у которой хуже перспективы, независимо от текущей цены', 'bias': None}
        ]
    },
    {
        'id': 6,
        'text': 'Спортсмен показал феноменальный результат на отборочных соревнованиях (в 3 раза лучше своего среднего). Тренер говорит: «На основных соревнованиях он выступит хуже». Это:',
        'options': [
            {'text': 'Пессимизм без оснований — нужно верить в спортсмена', 'bias': None},
            {'text': 'Понимание регрессии к среднему — экстремальные результаты случайны и сменяются обычными',
             'bias': None},
            {'text': 'Сверхосторожность, которая мешает победам', 'bias': 'overconfidence'}
        ]
    },
    {
        'id': 7,
        'text': 'Линда — 31 год, яркая, в юности участвовала в акциях протеста. Что вероятнее?',
        'options': [
            {'text': 'Линда — кассир в банке', 'bias': None},
            {'text': 'Линда — кассир в банке и феминистка', 'bias': 'conjunction_fallacy'},
            {'text': 'Оба варианта одинаково вероятны', 'bias': 'conjunction_fallacy'}
        ]
    },
    {
        'id': 8,
        'text': 'Вам дают кружку. Через минуту предлагают обменять её на шоколадку той же цены. Вы отказываетесь. Другому человеку дают шоколадку и предлагают обменять на кружку — он тоже отказывается. Это:',
        'options': [
            {'text': 'Рациональное предпочтение — каждый выбрал то, что ему нравится', 'bias': None},
            {'text': 'Эффект владения — люди переоценивают то, чем уже обладают', 'bias': 'endowment_effect'},
            {'text': 'Иллюзия контроля — каждый думает, что его предмет лучше', 'bias': 'illusion_of_control'}
        ]
    },
    {
        'id': 9,
        'text': 'Что вы выберете? Ситуация 1: А) гарантированные 5000 руб. или Б) 50% шанс получить 10000 руб. и 50% — 0 руб. Ситуация 2: В) гарантированная потеря 5000 руб. или Г) 50% шанс потерять 10000 руб. и 50% — 0 руб. Типичный человек выбирает А и Г. Это объясняется:',
        'options': [
            {'text': 'Противоречием в логике — так быть не должно', 'bias': None},
            {'text': 'Неприятием риска в области прибыли и стремлением к риску в области потерь (теория перспектив)',
             'bias': 'prospect_theory'},
            {'text': 'Просто случайностью, никакой закономерности нет', 'bias': None}
        ]
    },
    {
        'id': 10,
        'text': 'Вы купили билет в кино за 1000 руб. Через 10 минут фильм ужасно скучный. Что вы сделаете?',
        'options': [
            {'text': 'Уйду — деньги уже потрачены и не вернутся', 'bias': None},
            {'text': 'Останусь — не пропадать же деньгам', 'bias': 'sunk_cost_fallacy'},
            {'text': 'Подожду ещё 15 минут, может, станет лучше', 'bias': 'sunk_cost_fallacy'}
        ]
    },
    {
        'id': 11,
        'text': 'Вы считаете, что политика А — лучшая для страны. Как вы думаете, сколько процентов населения с вами согласны?',
        'options': [
            {'text': 'Около 50% — реалистичная оценка', 'bias': None},
            {'text': 'Около 75% — большинство же мыслит правильно', 'bias': 'false_consensus'},
            {'text': 'Около 30% — я в меньшинстве, и это нормально', 'bias': None}
        ]
    },
    {
        'id': 12,
        'text': 'В урне 30 красных шаров и 60 чёрных или жёлтых (пропорция неизвестна). Вы можете выбрать: А) выиграть 100 руб., если красный; Б) выиграть 100 руб., если чёрный. Большинство выбирает А. Это:',
        'options': [
            {'text': 'Рационально — красных ровно 30, а чёрных неизвестно сколько', 'bias': None},
            {'text': 'Неприятие неопределённости (ambiguity aversion) — люди предпочитают известный риск неизвестному',
             'bias': 'ambiguity_aversion'},
            {'text': 'Ошибка игрока — кажется, что красные выпадают чаще', 'bias': 'gamblers_fallacy'}
        ]
    },
    {
        'id': 13,
        'text': 'Какой риск кажется вам больше? А) 10 случаев на 1000 человек. Б) 100 случаев на 10000 человек. (Это одинаковые проценты — 1%)',
        'options': [
            {'text': 'А больше — 10 на 1000 звучит серьёзнее', 'bias': 'denominator_neglect'},
            {'text': 'Б больше — 100 случаев — это же целых 100!', 'bias': 'denominator_neglect'},
            {'text': 'Они одинаковы — 1% в обоих случаях', 'bias': None}
        ]
    },
    {
        'id': 14,
        'text': 'В больнице А рождается 10 детей в день, в больнице Б — 1000 детей в день. В какой больнице чаще доля мальчиков отличается от 50% более чем на 10%?',
        'options': [
            {'text': 'В больнице А — в маленькой выборке выше дисперсия', 'bias': None},
            {'text': 'В больнице Б — больше детей, больше отклонений', 'bias': 'sample_size_neglect'},
            {'text': 'Одинаково — законы вероятности везде одинаковы', 'bias': 'sample_size_neglect'}
        ]
    },
    {
        'id': 15,
        'text': 'На карте случайно отмечены 100 точек. Вы видите группу из 5 точек, расположенных близко друг к другу. Что вы думаете?',
        'options': [
            {'text': 'Это значимый кластер, не случайность — скорее всего, там что-то есть',
             'bias': 'clustering_illusion'},
            {'text': 'Это может быть случайностью — нужно проверить статистически', 'bias': None},
            {'text': 'Точно не случайно — 5 точек рядом не могут быть просто так', 'bias': 'clustering_illusion'}
        ]
    }

]


# МОДЕЛИ БАЗЫ ДАННЫХ
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(200), default='default_avatar.png')
    results = db.relationship('TestResult', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score_data = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# СОВРЕМЕННЫЙ ШАБЛОН С CSS И JS
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title or 'Когнитивный тест' }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary-color: #6366f1;
            --secondary-color: #8b5cf6;
            --accent-color: #ec4899;
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --card-shadow: 0 10px 40px rgba(0,0,0,0.1);
            --hover-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }

        body {
            font-family: 'Inter', sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }

        .navbar {
            background: rgba(255,255,255,0.95) !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 20px rgba(0,0,0,0.05);
            padding: 1rem 0;
        }

        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nav-link {
            color: #64748b !important;
            font-weight: 500;
            transition: all 0.3s;
            margin: 0 0.5rem;
        }

        .nav-link:hover {
            color: var(--primary-color) !important;
            transform: translateY(-2px);
        }

        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6rem 0;
            border-radius: 0 0 50px 50px;
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 600px;
            height: 600px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }

        .hero-section h1 {
            font-weight: 800;
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            animation: fadeInUp 0.8s ease;
        }

        .hero-section p {
            font-size: 1.25rem;
            opacity: 0.95;
            max-width: 600px;
            margin: 0 auto 2rem;
            animation: fadeInUp 0.8s ease 0.2s both;
        }

        .btn-modern {
            padding: 1rem 2.5rem;
            border-radius: 50px;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }

        .btn-primary-modern {
            background: white;
            color: var(--primary-color);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .btn-primary-modern:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            color: var(--primary-color);
        }

        .btn-outline-modern {
            background: transparent;
            color: white;
            border: 2px solid white;
        }

        .btn-outline-modern:hover {
            background: white;
            color: var(--primary-color);
            transform: translateY(-3px);
        }

        .card {
            border: none;
            border-radius: 20px;
            box-shadow: var(--card-shadow);
            transition: all 0.3s;
            overflow: hidden;
            background: white;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: var(--hover-shadow);
        }

        .card-header-modern {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1.5rem;
            font-weight: 600;
            border: none;
        }

        .form-control {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            padding: 0.75rem 1rem;
            transition: all 0.3s;
        }

        .form-control:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 4px rgba(99,102,241,0.1);
        }

        .btn {
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(99,102,241,0.4);
        }

        .question-card {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--card-shadow);
            transition: all 0.3s;
            border-left: 5px solid var(--primary-color);
        }

        .question-card:hover {
            transform: translateX(5px);
        }

        .question-number {
            display: inline-block;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 40px;
            font-weight: 700;
            margin-right: 1rem;
        }

        .option-radio {
            display: none;
        }

        .option-label {
            display: block;
            padding: 1rem 1.5rem;
            background: #f8fafc;
            border-radius: 12px;
            margin-bottom: 0.75rem;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }

        .option-label:hover {
            background: #e0e7ff;
            border-color: var(--primary-color);
        }

        .option-radio:checked + .option-label {
            background: linear-gradient(135deg, #e0e7ff, #ddd6fe);
            border-color: var(--primary-color);
            color: var(--primary-color);
            font-weight: 600;
        }

        .profile-avatar {
            width: 150px;
            height: 150px;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            font-size: 4rem;
            color: white;
            box-shadow: 0 10px 30px rgba(99,102,241,0.3);
        }

        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--card-shadow);
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin: 2rem 0;
        }

        .badge-modern {
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
        }

        .bg-gradient-primary {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        }

        .bg-gradient-success {
            background: linear-gradient(135deg, #10b981, #059669);
        }

        .bg-gradient-warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }

        .bg-gradient-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }

        .progress {
            height: 10px;
            border-radius: 10px;
            background: #e2e8f0;
            overflow: hidden;
        }

        .progress-bar {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            border-radius: 10px;
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .floating {
            animation: floating 3s ease-in-out infinite;
        }

        @keyframes floating {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        .table-modern {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: var(--card-shadow);
        }

        .table-modern thead {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
        }

        .table-modern th {
            font-weight: 600;
            border: none;
            padding: 1rem;
        }

        .table-modern td {
            padding: 1rem;
            vertical-align: middle;
        }

        .table-modern tbody tr {
            transition: all 0.3s;
        }

        .table-modern tbody tr:hover {
            background: #f8fafc;
            transform: scale(1.01);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-brain me-2"></i>CogniTest
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {% if current_user.is_authenticated %}
                        <li class="nav-item">
                            <a class="nav-link" href="/profile">
                                <i class="fas fa-user me-1"></i>{{ current_user.username }}
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/test">
                                <i class="fas fa-clipboard-list me-1"></i>Тест
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/logout">
                                <i class="fas fa-sign-out-alt me-1"></i>Выход
                            </a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="/login">
                                <i class="fas fa-sign-in-alt me-1"></i>Вход
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/register">
                                <i class="fas fa-user-plus me-1"></i>Регистрация
                            </a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div style="margin-top: 76px;">
        <!-- CONTENT_PLACEHOLDER -->
    </div>

    <footer class="bg-white py-4 mt-5" style="box-shadow: 0 -2px 20px rgba(0,0,0,0.05);">
        <div class="container text-center text-muted">
            <p class="mb-0"><i class="fas fa-brain me-2"></i>CogniTest © 2024. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def render_page(content_html, **kwargs):
    full_template = BASE_LAYOUT.replace('<!-- CONTENT_PLACEHOLDER -->', content_html)
    return render_template_string(full_template, **kwargs)


# МАРШРУТЫ
@app.route('/')
def index():
    content = """
    <div class="hero-section text-center">
        <div class="container position-relative" style="z-index: 1;">
            <div class="floating mb-4">
                <i class="fas fa-brain" style="font-size: 100px; opacity: 0.9;"></i>
            </div>
            <h1>Насколько вы рациональны?</h1>
            <p>Когнитивные искажения мешают нам принимать правильные решения. Пройдите наш тест, чтобы узнать, какие ловушки разума характерны для вас.</p>
            {% if not current_user.is_authenticated %}
                <a href="/register" class="btn btn-modern btn-primary-modern me-3">
                    <i class="fas fa-rocket me-2"></i>Начать бесплатно
                </a>
                <a href="/login" class="btn btn-modern btn-outline-modern">
                    <i class="fas fa-user me-2"></i>У меня есть аккаунт
                </a>
            {% else %}
                <a href="/test" class="btn btn-modern btn-primary-modern">
                    <i class="fas fa-play me-2"></i>Перейти к тесту
                </a>
            {% endif %}
        </div>
    </div>

    <div class="container mb-5">
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon mx-auto">
                        <i class="fas fa-brain"></i>
                    </div>
                    <h4>18 Типов искажений</h4>
                    <p class="text-muted">Тест охватывает основные когнитивные искажения, влияющие на принятие решений</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon mx-auto">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h4>Детальная статистика</h4>
                    <p class="text-muted">Получите подробный анализ ваших результатов с визуализацией данных</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon mx-auto">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h4>Научный подход</h4>
                    <p class="text-muted">Вопросы основаны на реальных исследованиях в области психологии</p>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(content, title="Главная")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Этот логин уже занят', 'danger')
            return redirect(url_for('register'))
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))

    content = """
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card p-5">
                    <div class="text-center mb-4">
                        <div class="profile-avatar" style="width: 100px; height: 100px; font-size: 2.5rem;">
                            <i class="fas fa-user-plus"></i>
                        </div>
                        <h3 class="fw-bold">Создать аккаунт</h3>
                        <p class="text-muted">Присоединяйтесь к CogniTest</p>
                    </div>
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Логин</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fas fa-user"></i></span>
                                <input type="text" name="username" class="form-control" placeholder="Придумайте логин" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Email</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fas fa-envelope"></i></span>
                                <input type="email" name="email" class="form-control" placeholder="your@email.com" required>
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Пароль</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fas fa-lock"></i></span>
                                <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                            </div>
                        </div>
                        <button class="btn btn-primary w-100 btn-lg">
                            <i class="fas fa-user-plus me-2"></i>Создать аккаунт
                        </button>
                    </form>
                    <p class="text-center mt-4 mb-0">
                        Уже есть аккаунт? <a href="/login" class="fw-semibold text-decoration-none">Войти</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(content, title="Регистрация")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль', 'danger')

    content = """
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card p-5">
                    <div class="text-center mb-4">
                        <div class="profile-avatar" style="width: 100px; height: 100px; font-size: 2.5rem;">
                            <i class="fas fa-sign-in-alt"></i>
                        </div>
                        <h3 class="fw-bold">С возвращением!</h3>
                        <p class="text-muted">Войдите в свой аккаунт</p>
                    </div>
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Логин</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fas fa-user"></i></span>
                                <input type="text" name="username" class="form-control" placeholder="Ваш логин" required>
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Пароль</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fas fa-lock"></i></span>
                                <input type="password" name="password" class="form-control" placeholder="Ваш пароль" required>
                            </div>
                        </div>
                        <button class="btn btn-primary w-100 btn-lg">
                            <i class="fas fa-sign-in-alt me-2"></i>Войти
                        </button>
                    </form>
                    <p class="text-center mt-4 mb-0">
                        Нет аккаунта? <a href="/register" class="fw-semibold text-decoration-none">Зарегистрироваться</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(content, title="Вход")


@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    if request.method == 'POST':
        results_counts = {k: 0 for k in BIASES.keys()}
        for q in QUESTIONS:
            answer = request.form.get(f'q_{q["id"]}')
            if answer and answer != 'none':
                results_counts[answer] = results_counts.get(answer, 0) + 1

        new_result = TestResult(user_id=current_user.id, score_data=json.dumps(results_counts))
        db.session.add(new_result)
        db.session.commit()
        flash('Тест завершен! Результаты сохранены.', 'success')
        return redirect(url_for('profile'))

    questions_html = ""
    for i, q in enumerate(QUESTIONS, 1):
        options_html = ""
        for j, opt in enumerate(q['options']):
            options_html += f"""
                <input type="radio" name="q_{q['id']}" id="q{q['id']}_{j}" 
                       class="option-radio" value="{opt['bias'] or 'none'}" required>
                <label for="q{q['id']}_{j}" class="option-label">
                    {opt['text']}
                </label>
            """

        questions_html += f"""
            <div class="question-card">
                <h5 class="mb-4">
                    <span class="question-number">{i}</span>
                    {q['text']}
                </h5>
                <div class="options-container">
                    {options_html}
                </div>
            </div>
        """

    content = f"""
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="text-center mb-5">
                    <h2 class="fw-bold mb-3">
                        <i class="fas fa-clipboard-list me-2 text-primary"></i>
                        Тест на рациональность
                    </h2>
                    <p class="text-muted">Ответьте на {len(QUESTIONS)} вопросов, чтобы узнать о своих когнитивных искажениях</p>
                    <div class="progress mt-3" style="max-width: 400px; margin: 1rem auto;">
                        <div class="progress-bar" role="progressbar" style="width: 0%" id="progressBar"></div>
                    </div>
                </div>

                <form method="post" id="testForm">
                    {questions_html}

                    <div class="text-center mb-5 mt-4">
                        <button type="submit" class="btn btn-primary btn-lg px-5">
                            <i class="fas fa-check-circle me-2"></i>Завершить тест
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        document.querySelectorAll('.option-radio').forEach(radio => {{
            radio.addEventListener('change', updateProgress);
        }});

        function updateProgress() {{
            const total = {len(QUESTIONS)};
            const answered = document.querySelectorAll('.option-radio:checked').length;
            const progress = (answered / total) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }}
    </script>
    """
    return render_page(content, title="Тест")


@app.route('/profile')
@login_required
def profile():
    results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.date.desc()).all()
    history = []
    latest_scores = None

    for r in results:
        scores = json.loads(r.score_data)
        if any(scores.values()):
            top_bias_key = max(scores, key=scores.get)
            top_bias_name = BIASES.get(top_bias_key, "Не определено")
            top_bias_value = scores[top_bias_key]
        else:
            top_bias_name = "Чистое мышление"
            top_bias_value = 0

        history.append({
            'date': r.date.strftime('%d.%m.%Y %H:%M'),
            'bias': top_bias_name,
            'value': top_bias_value
        })

        if latest_scores is None:
            latest_scores = scores

    # Подготовка данных для графика
    labels = []
    data = []
    colors = []
    color_palette = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#ef4444']

    if latest_scores:
        sorted_biases = sorted(latest_scores.items(), key=lambda x: x[1], reverse=True)[:7]
        for i, (bias_key, value) in enumerate(sorted_biases):
            if value > 0:
                labels.append(BIASES.get(bias_key, bias_key))
                data.append(value)
                colors.append(color_palette[i % len(color_palette)])

    charts_script = ""
    if labels:
        charts_script = f"""
        <script>
            const ctx = document.getElementById('biasChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Количество проявлений',
                        data: {json.dumps(data)},
                        backgroundColor: {json.dumps(colors)},
                        borderRadius: 10,
                        borderSkipped: false,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        title: {{
                            display: true,
                            text: 'Ваши когнитивные искажения',
                            font: {{ size: 16, weight: 'bold' }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{ stepSize: 1 }},
                            grid: {{ color: '#f1f5f9' }}
                        }},
                        x: {{
                            grid: {{ display: false }}
                        }}
                    }}
                }}
            }});
        </script>
        """

    history_rows = ""
    for item in history[:10]:
        badge_class = 'bg-gradient-primary' if item['value'] > 2 else 'bg-gradient-success'
        history_rows += f"""
            <tr>
                <td><i class="far fa-clock me-2 text-muted"></i>{item['date']}</td>
                <td><span class="badge {badge_class} badge-modern">{item['bias']}</span></td>
                <td><span class="text-muted">{item['value']} проявлений</span></td>
            </tr>
        """

    content = f"""
    <div class="container py-5">
        <div class="row mb-5">
            <div class="col-lg-4 mb-4">
                <div class="card text-center p-4 h-100">
                    <div class="profile-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <h3 class="fw-bold mb-1">{current_user.username}</h3>
                    <p class="text-muted mb-3">{current_user.email}</p>
                    <div class="stats-card rounded-3 p-3 mb-3" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="text-white-50 small">Пройдено тестов</div>
                                <div class="h4 mb-0 text-white fw-bold">{len(results)}</div>
                            </div>
                            <i class="fas fa-chart-bar text-white-50" style="font-size: 2rem;"></i>
                        </div>
                    </div>
                    <a href="/test" class="btn btn-primary w-100 mb-2">
                        <i class="fas fa-play me-2"></i>Пройти тест
                    </a>
                    <a href="/logout" class="btn btn-outline-danger w-100">
                        <i class="fas fa-sign-out-alt me-2"></i>Выйти
                    </a>
                </div>
            </div>

            <div class="col-lg-8">
                <div class="card p-4 mb-4">
                    <h4 class="fw-bold mb-4">
                        <i class="fas fa-chart-pie me-2 text-primary"></i>
                        Анализ результатов
                    </h4>
                    {f'<div class="chart-container"><canvas id="biasChart"></canvas></div>' if labels else '<div class="text-center py-5 text-muted"><i class="fas fa-chart-bar fa-3x mb-3 d-block"></i>Пройдите тест, чтобы увидеть статистику</div>'}
                </div>

                <div class="card p-4">
                    <h4 class="fw-bold mb-4">
                        <i class="fas fa-history me-2 text-primary"></i>
                        История тестов
                    </h4>
                    {f'''
                    <div class="table-responsive">
                        <table class="table table-modern">
                            <thead>
                                <tr>
                                    <th><i class="far fa-calendar me-2"></i>Дата</th>
                                    <th><i class="fas fa-brain me-2"></i>Доминирующее искажение</th>
                                    <th><i class="fas fa-chart-line me-2"></i>Активность</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history_rows}
                            </tbody>
                        </table>
                    </div>
                    ''' if history_rows else '<div class="text-center py-5 text-muted">История пуста</div>'}
                </div>
            </div>
        </div>
    </div>
    {charts_script}
    """
    return render_page(content, title="Профиль")


@app.route('/account/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Страница подтверждения удаления аккаунта"""

    if request.method == 'POST':
        password = request.form.get('confirm_password')
        confirm = request.form.get('confirm_checkbox')

        # Проверки
        if not confirm:
            flash('Подтвердите, что вы понимаете последствия', 'warning')
            return redirect(url_for('delete_account'))

        if not current_user.check_password(password):
            flash('Неверный пароль', 'danger')
            return redirect(url_for('delete_account'))

        # Логируем перед удалением
        app.logger.warning(f"Account deletion: user_id={current_user.id}, username={current_user.username}")

        # Cascade delete: сначала связанные записи
        TestResult.query.filter_by(user_id=current_user.id).delete()

        # Сохраняем данные для сообщения
        username = current_user.username

        # Удаляем пользователя и выходим
        db.session.delete(current_user)
        db.session.commit()
        logout_user()

        flash(f'Аккаунт "{username}" удалён. Все данные стёрты.', 'success')
        return redirect(url_for('index'))

    # GET-запрос: показываем страницу подтверждения
    content = """
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card border-danger">
                    <div class="card-header bg-danger text-white">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Удаление аккаунта
                    </div>
                    <div class="card-body">
                        <p class="lead">Вы уверены, что хотите удалить аккаунт <strong>{{ current_user.username }}</strong>?</p>
                        <ul class="text-muted small">
                            <li>❌ Все результаты тестов будут удалены</li>
                            <li>❌ История активности будет стёрта</li>
                            <li>❌ Восстановить данные будет невозможно</li>
                        </ul>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Введите пароль для подтверждения:</label>
                                <input type="password" name="confirm_password" class="form-control" required>
                            </div>
                            <div class="form-check mb-4">
                                <input class="form-check-input" type="checkbox" name="confirm_checkbox" id="confirmCheck" required>
                                <label class="form-check-label small" for="confirmCheck">
                                    Я понимаю, что это действие необратимо
                                </label>
                            </div>
                            <div class="d-grid gap-2">
                                <button type="submit" class="btn btn-danger">
                                    <i class="fas fa-trash-alt me-2"></i>Да, удалить аккаунт
                                </button>
                                <a href="/profile" class="btn btn-outline-secondary">Отмена</a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(content, title="Подтверждение удаления")

@app.route('/api/stats')
@login_required
def api_stats():
    last_res = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.date.desc()).first()
    if not last_res:
        return jsonify({"error": "No data"}), 404
    return jsonify({
        "user": current_user.username,
        "date": last_res.date.isoformat(),
        "scores": json.loads(last_res.score_data)
    })


@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)
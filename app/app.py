import os
import requests
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from extensions import db
from models import User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            existing_user_by_username = User.query.filter_by(username=username).first()
            if existing_user_by_username:
                flash('Пользователь с таким именем уже существует!')
                return redirect(url_for('register'))

            existing_user_by_email = User.query.filter_by(email=email).first()
            if existing_user_by_email:
                flash('Пользователь с таким email уже зарегистрирован!')
                return redirect(url_for('register'))

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)

            try:
                db.session.commit()
                flash('Регистрация прошла успешно!')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Произошла ошибка при регистрации. Попробуйте ещё раз.')
                return redirect(url_for('register'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Вы успешно вошли в систему!')
                return redirect(url_for('profile'))
            else:
                flash('Неверное имя пользователя или пароль!')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы!')
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    @app.route('/weather', methods=['GET', 'POST'])
    @login_required
    def weather():
        weather_data = None
        city = None

        if request.method == 'POST':
            city = request.form.get('city', 'Moscow')
            api_key = 'f362f942-8e2f-4a77-87bc-557b6c4773c4'
            city_coordinates = {
                'Moscow': '55.7558,37.6173',
                'Saint Petersburg': '59.9343,30.3351',
                'Novosibirsk': '55.0302,82.9204',
                'Ekaterinburg': '56.8519,60.6122',
                'Kazan': '55.7963,49.1089'
            }

            lat_lon = city_coordinates.get(city, '55.7558,37.6173')
            lat, lon = lat_lon.split(',')

            url = f'https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}'
            headers = {'X-Yandex-API-Key': api_key}

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                weather_data = {
                    'city': city,
                    'temperature': data['fact']['temp'],
                    'feels_like': data['fact']['feels_like'],
                    'condition': data['fact']['condition'],
            'wind_speed': data['fact']['wind_speed'],
            'humidity': data['fact']['humidity'],
            'pressure_mm': data['fact']['pressure_mm']
                }
            except requests.exceptions.RequestException as e:
                flash(f'Ошибка при получении данных: {str(e)}')
            except KeyError as e:
                flash(f'Неверный формат ответа API: отсутствует поле {str(e)}')

        return render_template('weather.html', weather_data=weather_data, city=city)


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

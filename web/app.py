from flask import Flask, render_template, request, jsonify
from bot.database import Session, User, MessageLog

app = Flask(__name__)

@app.route('/admin')
def admin_panel():
    # Проверка авторизации (пароль или проверка, что зашел админ)
    db = Session()
    users = db.query(User).all()
    return render_template('admin.html', users=users)

@app.route('/admin/api/user/<int:telegram_id>')
def user_details(telegram_id):
    db = Session()
    # Получаем последние 10 диалогов пользователя
    logs = db.query(MessageLog).filter_by(user_id=telegram_id).order_by(MessageLog.created_at.desc()).limit(10).all()
    return jsonify([{"role": l.role, "content": l.content[:200]} for l in logs])

if __name__ == '__main__':
    app.run(port=5000)
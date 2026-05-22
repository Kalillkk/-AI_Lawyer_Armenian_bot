from flask import Flask, render_template, jsonify
from bot.database import SessionLocal
from bot.models import User
from bot.config import ADMIN_ID
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/admin')
def admin_panel():
    # Простая проверка (можно улучшить)
    return render_template('admin.html')

@app.route('/api/users')
def api_users():
    db = SessionLocal()
    users = db.query(User).all()
    data = [{
        "id": u.telegram_id,
        "name": u.full_name,
        "requests": u.total_requests,
        "registered": u.registered_at.strftime("%Y-%m-%d")
    } for u in users]
    db.close()
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
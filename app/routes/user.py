from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import User, ReadingProgress, Book, Review
from app import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    reading_stats = ReadingProgress.query.filter_by(user_id=current_user.id).all()
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    return render_template('user/profile.html', 
                         user=current_user, 
                         reading_stats=reading_stats,
                         reviews=reviews)

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        data = request.get_json()
        current_user.dark_mode = data.get('dark_mode', current_user.dark_mode)
        db.session.commit()
        return jsonify({'status': 'success'})
    return render_template('user/settings.html', user=current_user)

@user_bp.route('/library')
@login_required
def library():
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('user/library.html', books=books)

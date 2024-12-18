from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class BookUploadForm(FlaskForm):
    title = StringField('Title', 
                       validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', 
                        validators=[Length(max=100)])
    description = TextAreaField('Description')
    book_file = FileField('Book File', 
                         validators=[
                             FileRequired(),
                             FileAllowed(['pdf', 'epub'], 'PDF and EPUB files only!')
                         ])
    submit = SubmitField('Upload Book')

class ReviewForm(FlaskForm):
    rating = StringField('Rating', 
                        validators=[DataRequired()])
    comment = TextAreaField('Comment')
    submit = SubmitField('Submit Review')

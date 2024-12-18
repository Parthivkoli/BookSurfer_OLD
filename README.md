# Digital Book Reader

A full-stack web application for reading and managing digital books, built with Flask.

## Features

- User authentication and profile management
- Book upload and management (PDF, EPUB)
- Reading progress tracking
- Personal library dashboard
- Book discovery with search and filters
- Reading statistics and bookmarks
- Dark/light mode toggle
- Responsive design

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///reader.db
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Project Structure

```
reader/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── migrations/
├── instance/
├── requirements.txt
├── .env
└── run.py
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

MIT License

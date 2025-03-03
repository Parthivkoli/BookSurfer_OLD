# BookSurfer📚🌊  
## ⚠️❗Switched to a new framework this has been discontinued.❗⚠️

Welcome to **BookSurfer**, a Flask-based web application to manage your reading journey and explore new books!  

## 🚀 Features  

- **📖 Explore Books**: Browse a vast collection of books across various genres.  
- **✨ Personalized Recommendations**: Get book suggestions tailored to your interests.  
- **📋 Reading Lists**: Create and manage your custom reading lists.  
- **📊 Progress Tracking**: Monitor your reading progress with ease.  

---

## 🛠️ Setup Instructions  

Follow these steps to set up the project on your local machine:  

### Prerequisites  

- Python 3.8+ 🐍  
- pip (Python package installer)  
- Virtual environment setup (optional but recommended)  

---

### 1. Clone the Repository  

```bash  
git clone https://github.com/Parthivkoli/BookSurfer.git  
cd BookSurfer  
```  

---

### 2. Create and Activate a Virtual Environment (Optional)  

```bash  
python -m venv venv  
source venv/bin/activate    # On macOS/Linux  
venv\Scripts\activate       # On Windows  
```  

---

### 3. Install Dependencies  

Install the required packages:  

```bash  
pip install -r requirements.txt  
```  

---

### 4. Set Up Environment Variables  

Create a `.env` file in the project root and configure the following:  

```plaintext  
FLASK_APP=app.py  
FLASK_ENV=development  
DATABASE_URI=your_database_uri  
SECRET_KEY=your_secret_key  
```  

Replace `your_database_uri` with your database connection string and `your_secret_key` with a secure key for session management.  

---

### 5. Initialize the Database  

```bash  
flask db init  
flask db migrate  
flask db upgrade  
```  

---

### 6. Run the Application  

Start the Flask development server:  

```bash  
flask run  
```  

The application will be accessible at `http://127.0.0.1:5000` or as indicated in the terminal.  

---

## 📦 File Structure  

```plaintext  
BookSurfer/  
│  
├── app/                  # Main application package  
│   ├── templates/        # HTML templates  
│   ├── static/           # Static files (CSS, JS, images)  
│   ├── routes.py         # Application routes  
│   ├── models.py         # Database models  
│   └── __init__.py       # App factory  
│  
├── migrations/           # Database migrations  
├── .env                  # Environment variables  
├── app.py                # Entry point for Flask  
├── requirements.txt      # Project dependencies  
└── README.md             # Project documentation  
```  

---

## 🤝 Contributing  

We welcome contributions! Fork the repository and create a pull request with your changes. Ensure your code follows the project's coding style.  

---

## 📄 License  

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.  

---

### ✨ Happy Surfing & Reading! 📖✨  
```

### Key Highlights:
1. **Flask-Specific Instructions**: Focused on Flask setup with environment variables and database migrations.
2. **File Structure**: Provides an overview of the project's organization.
3. **Emojis**: Added throughout to make the document engaging and visually appealing.

Let me know if you’d like to refine any section further! 🚀

from app import create_app

app = create_app()

# Vercel requires a 'handler' variable
handler = app 
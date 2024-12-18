from app import create_app

app = create_app()

# Vercel and Render require a 'handler' variable
handler = app 
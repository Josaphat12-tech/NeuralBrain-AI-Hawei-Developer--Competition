
from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    print(f"Connecting to: {app.config['SQLALCHEMY_DATABASE_URI']}")
    users = User.query.all()
    print(f"\nFound {len(users)} users in the database:")
    print("-" * 50)
    for user in users:
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Last Login: {user.last_login}")
        print("-" * 50)

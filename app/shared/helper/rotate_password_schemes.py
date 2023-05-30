import contextlib
from app.endpoints.urls import APIPrefix
from app.shared.auth.password_handler import get_password_hash, verify_password
from app.api.user.models import User
from app.api.agent.models import Agent
from app.api.admin.models import Admin

for route in APIPrefix.include:
    with contextlib.suppress(ImportError):
        exec(f"from app.api.{route}.models import ModelMixin as Base")

admins = Admin.read_all()
users = User.read_all()
agents = Agent.read_all()


def rotate_all():
    for admin in admins:
        try:
            admin.password = get_password_hash("123")
            admin.session.commit()
        except Exception as e:
            print(e)
            admin.session.rollback()

    for user in users:
        try:
            user.password = get_password_hash("123")
            user.session.commit()
        except Exception as e:
            print(e)
            user.session.rollback()

    for agent in agents:
        try:
            agent.password = get_password_hash("123")
            agent.session.commit()
        except Exception as e:
            print(e)
            agent.session.rollback()


def rotate_one(email=input("enter email"), password=input("enter password")):
    if user := User.read(email=email):
        user.password = get_password_hash(password)
        user.session.commit()
    else:
        print("user not found")


rotate_one()

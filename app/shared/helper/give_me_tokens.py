"""
@author: Kuro
"""
from app.shared.auth.auth_handler import sign_jwt

phone = input("Enter phone number: ")
print(sign_jwt(phone))

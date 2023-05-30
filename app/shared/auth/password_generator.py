"""
@author: Kuro
"""

import secrets
import string

"""
Never, under any circumstances should you use this code in production.
in addition, this code is not used in the project, ironically its actually being deprecated
for a worse version of itself. Were going to downgrade to 6 digit passwords. 
The reason for this is because the password is only used for the initial login, and then
the user is forced to change it. I hope.
"""


# def generate_password(length=16):
#     """
#     This Python function generates a random string of specified length using a
#     combination of letters, digits, and special characters.
#
#     :param length: The length parameter is an optional argument that specifies the
#     length of the generated string. If no value is provided for length, the default value of 12 will be
#     used, defaults to 12 (optional)
#     :return: a randomly generated string of characters with a default length of 12.
#     The string includes letters (both uppercase and lowercase), digits, and special characters. The
#     `secrets.choice()` function is used to randomly select characters from the `alphabet`
#     string, and the `join()` method is used to concatenate the selected characters into a single string.
#     """
#
#     letters = string.ascii_letters
#     digits = string.digits
#     special_chars = string.punctuation
#     alphabet = letters + digits + special_chars
#
#     def filter_chars():
#         random_char = secrets.choice(alphabet)
#         return random_char if random_char not in ['<', '>', '^'] else filter_chars()
#
#     return ''.join(''.join(filter_chars()) for _ in range(length))


def generate_password(length: int = 6) -> str:
    """
    This function generates a random string of numbers for a given length
    :param length:  The length parameter is an optional argument that specifies the length of the generated string.
    If no value is provided for length, the default value of 6 will be used, defaults to 6 (optional)
    :return: a randomly generated string of numbers with a default length of 6.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))

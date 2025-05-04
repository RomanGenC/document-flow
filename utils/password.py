import random
import re
import string


class Password:
    def __init__(self, password: str):
        self.password = password
        self.default_password_length = 16
        self.english_letters = string.ascii_letters
        self.digits = string.digits
        self.special_chars = "!@#$%^&*()-_=+[]{}|;:',.<>?/"
        self.russian_lowercase = ''.join(chr(code) for code in range(0x0430, 0x044F + 1)) + 'ё'
        self.russian_uppercase = ''.join(chr(code) for code in range(0x0410, 0x042F + 1)) + 'Ё'

    def contains_numbers(self, password) -> bool:
        return bool(re.search(r'[0-9]', password))

    def contains_uppercase(self, password) -> bool:
        return bool(re.search(r'[A-ZА-Я]', password))

    def contains_lowercase(self, password) -> bool:
        return bool(re.search(r'[a-zа-я]', password))

    def contains_specials(self, password):
        return bool(re.search(rf'[{self.special_chars}]', password))

    @staticmethod
    def get_score_by_strength(password_strength):
        score_by_strength = {
            1: 'Слабый',
            2: 'Слабый',
            3: 'Средний',
            4: 'Средний',
            5: 'Сильный',
            6: 'Сильный',
        }
        return score_by_strength.get(password_strength)

    def evaluate_strength(self, password):
        password_strength = 0
        if self.contains_numbers(password):
            password_strength += 1

        if self.contains_numbers(password):
            password_strength += 1

        if self.contains_uppercase(password):
            password_strength += 1

        if self.contains_specials(password):
            password_strength += 1

        if len(password) >= 12:
            password_strength += 1

        if len(password) >= 16:
            password_strength += 1

        return self.get_score_by_strength(password_strength)

    def generate_password(self, password_length=None) -> str:
        symbols_generate_password = ''.join(
            [
                self.english_letters,
                self.russian_uppercase,
                self.russian_lowercase,
                self.digits,
                self.special_chars,
            ]
        )
        if not password_length:
            password_length = self.default_password_length

        return ''.join(random.choices(symbols_generate_password, k=password_length))

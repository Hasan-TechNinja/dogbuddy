import re
from django.core.exceptions import ValidationError

class StrongPasswordValidator:
    def validate(self, password, user=None):
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must include at least one uppercase letter.")

        if not re.search(r"[a-z]", password):
            errors.append("Password must include at least one lowercase letter.")

        if not re.search(r"[0-9]", password):
            errors.append("Password must include at least one digit.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must include at least one special character.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Password must include uppercase, lowercase, number, special character and be 8+ chars."

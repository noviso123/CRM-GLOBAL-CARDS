import re
from typing import Optional


def normalize_digits(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", str(value))


def validate_cpf(cpf: str) -> bool:
    digits = normalize_digits(cpf)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    for i in range(9, 11):
        val = sum(int(digits[num]) * ((i + 1) - num) for num in range(0, i))
        check = ((val * 10) % 11) % 10
        if check != int(digits[i]):
            return False
    return True


def validate_cnpj(cnpj: str) -> bool:
    digits = normalize_digits(cnpj)
    if len(digits) != 14 or digits == digits[0] * 14:
        return False
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(d) * w for d, w in zip(digits[:12], weights_1))
    rem1 = sum1 % 11
    d1 = 0 if rem1 < 2 else 11 - rem1
    if int(digits[12]) != d1:
        return False
    sum2 = sum(int(d) * w for d, w in zip(digits[:13], weights_2))
    rem2 = sum2 % 11
    d2 = 0 if rem2 < 2 else 11 - rem2
    return int(digits[13]) == d2


def validate_cpf_cnpj(value: Optional[str]) -> bool:
    if not value or not str(value).strip():
        return True
    digits = normalize_digits(value)
    if len(digits) == 11:
        return validate_cpf(digits)
    if len(digits) == 14:
        return validate_cnpj(digits)
    return False


def validate_email(email: Optional[str]) -> bool:
    if not email or not email.strip():
        return True
    pattern = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email.strip()))


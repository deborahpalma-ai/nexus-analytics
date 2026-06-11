"""
NEXUS Analytics — auth.py
---------------------------
Autenticação: hash de senha com bcrypt,
registro e login de usuários.
"""

import bcrypt
from backend.database import create_user, get_user_by_email


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def register(name: str, email: str, password: str) -> dict:
    """
    Registra novo usuário.
    Retorna {'ok': True, 'user': {...}} ou {'ok': False, 'error': '...'}.
    """
    if not name or not email or not password:
        return {"ok": False, "error": "Preencha todos os campos."}
    if len(password) < 6:
        return {"ok": False, "error": "Senha deve ter ao menos 6 caracteres."}
    if get_user_by_email(email):
        return {"ok": False, "error": "E-mail já cadastrado."}

    hashed = hash_password(password)
    user   = create_user(name, email, hashed)
    if user:
        return {"ok": True, "user": user}
    return {"ok": False, "error": "Erro ao criar conta."}


def login(email: str, password: str) -> dict:
    """
    Autentica usuário.
    Retorna {'ok': True, 'user': {...}} ou {'ok': False, 'error': '...'}.
    """
    if not email or not password:
        return {"ok": False, "error": "Preencha todos os campos."}

    user = get_user_by_email(email)
    if not user:
        return {"ok": False, "error": "Conta não encontrada. Cadastre-se primeiro."}
    if not check_password(password, user["password"]):
        return {"ok": False, "error": "Senha incorreta."}

    return {"ok": True, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}

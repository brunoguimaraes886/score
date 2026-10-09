import hashlib
import hmac
import secrets


# 32 bytes aleatórios viram 43 caracteres de letras, números, - e _
# (docs/rotas.md, "Formatos").
ACCOUNT_TOKEN_BYTES = 32


def generate_account_token() -> str:
    """Um token novo para uma conta nova (API-16). Sai uma vez só, na resposta 201."""
    return secrets.token_urlsafe(ACCOUNT_TOKEN_BYTES)


def hash_account_token(account_token: str) -> str:
    """O SHA-256 do token, em 64 caracteres hexadecimais: é só isto que o banco guarda (API-16)."""
    return hashlib.sha256(account_token.encode("utf-8")).hexdigest()


def account_token_matches(account_token, token_hash) -> bool:
    """True quando o token recebido é o da conta.

    Token que falta (None) ou conta sem hash (cofrinho, contas do
    sistema) nunca bate. A comparação de tempo constante
    (hmac.compare_digest) não deixa o tempo da resposta contar quantos
    caracteres acertaram.
    """
    if account_token is None or token_hash is None:
        return False

    return hmac.compare_digest(hash_account_token(account_token), token_hash)

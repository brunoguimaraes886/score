import hashlib
import json


def hash_request_body(transaction_type: str, account_key: str, payload: dict) -> str:
    """O SHA-256 do pedido, em 64 caracteres hexadecimais (MOV-12, MOV-19).

    É o que a operação guarda em request_hash. O mesmo pedido é a mesma
    operação (DEPOSIT, WITHDRAWAL ou TRANSFER), na mesma conta da URL,
    com o mesmo corpo: os três entram no hash. A mesma
    request_control_key com outro hash é outro pedido (409 QIT001014).

    O texto que vira hash é o JSON com as chaves em ordem alfabética e sem
    espaços: o mesmo corpo com os campos em outra ordem dá o mesmo hash.
    """
    request = {
        "transaction_type": transaction_type,
        "account_key": account_key,
        "payload": payload,
    }
    canonical_text = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()

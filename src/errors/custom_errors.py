from errors import QIException


# ────────────────────────────────────────────────────────────────
# Cliente
# ────────────────────────────────────────────────────────────────


class InvalidDocumentNumber(QIException):
    """O CPF ou o CNPJ tem o formato certo e não existe.

    422, e não 400, de propósito: 400 quer dizer "não consegui ler o seu
    pedido". Aqui a API leu, entendeu, e o valor é que não pode existir —
    os dígitos verificadores não batem com a conta. Vale para o CPF do
    cliente e para o CPF ou CNPJ de quem deposita. O número não volta na
    mensagem (PRD-12).
    """

    code = "QIT001003"

    def __init__(self) -> None:
        title = "Invalid Document Number"
        http_status = 422
        description = "The document number is not a valid CPF or CNPJ."
        translation = "O CPF ou CNPJ informado não é válido."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedDocumentNumber(QIException):
    """Já existe um cliente com este CPF.

    409 Conflict: o pedido está correto em si, e o que impede é o que já
    está no banco.
    """

    code = "QIT001004"

    def __init__(self) -> None:
        title = "Document Number already registered"
        http_status = 409
        description = "There is already a customer with this document number."
        translation = "Já existe um cadastro com este CPF."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedEmail(QIException):
    code = "QIT001005"

    def __init__(self, email) -> None:
        title = "Email already registered"
        http_status = 409
        description = f"There is already a customer with the email {email}."
        translation = "Já existe um cadastro com este e-mail."
        super().__init__(title, self.code, http_status, description, translation)


class UnderageCustomer(QIException):
    code = "QIT001006"

    def __init__(self, age, minimum_age) -> None:
        title = "Customer is underage"
        http_status = 422
        description = f"The customer is {age} years old, and the minimum is {minimum_age}."
        translation = f"É preciso ter pelo menos {minimum_age} anos."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidBirthdate(QIException):
    """A data tem o formato certo e não existe no calendário.

    O `pattern` do schema sabe contar dígitos, não dias: "2025-02-30"
    passa pelo regex e morre no `date.fromisoformat`. Sem esta classe,
    esse ValueError virava 500.
    """

    code = "QIT001007"

    def __init__(self, birthdate) -> None:
        title = "Invalid Birthdate"
        http_status = 422
        description = f"The birthdate {birthdate} is not a real date."
        translation = "A data de nascimento informada não existe."
        super().__init__(title, self.code, http_status, description, translation)


class CustomerNotFound(QIException):
    """O cliente não existe, ou o token não é o da conta aberta dele.

    Os dois casos respondem igual (R8): quem não é o dono não descobre
    se o cliente existe.
    """

    code = "QIT001008"

    def __init__(self, customer_key) -> None:
        title = "Customer not Found"
        http_status = 404
        description = f"Customer with key {customer_key} was not found."
        translation = f"O cliente com chave {customer_key} não foi encontrado."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Conta
# ────────────────────────────────────────────────────────────────


class CustomerAlreadyHasAccount(QIException):
    code = "QIT001009"

    def __init__(self, customer_key) -> None:
        title = "Customer already has an account"
        http_status = 409
        description = f"Customer with key {customer_key} already has an account that is not closed."
        translation = "O cliente já tem uma conta que não foi encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotFound(QIException):
    """A conta não existe, não é de cliente, ou o token não é dela.

    Os três casos respondem igual (R8, API-09): recurso de outro dono é
    404, nunca 403.
    """

    code = "QIT001010"

    def __init__(self, account_key) -> None:
        title = "Account not Found"
        http_status = 404
        description = f"Account with key {account_key} was not found."
        translation = f"A conta com chave {account_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotActive(QIException):
    code = "QIT001011"

    def __init__(self, account_key, status) -> None:
        title = "Account is not active"
        http_status = 409
        description = f"Account with key {account_key} is {status} and cannot do this operation."
        translation = "A conta não está ativa: está bloqueada ou encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotEmpty(QIException):
    code = "QIT001012"

    def __init__(self, account_key) -> None:
        title = "Account is not empty"
        http_status = 409
        description = f"Account with key {account_key} has money in its balance or in its piggy bank."
        translation = "A conta só pode ser encerrada com o saldo e o cofrinho zerados."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotBlocked(QIException):
    code = "QIT001013"

    def __init__(self, account_key, status) -> None:
        title = "Account is not blocked"
        http_status = 409
        description = f"Account with key {account_key} is {status}, not BLOCKED."
        translation = "Só uma conta bloqueada pode ser desbloqueada."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Dinheiro
# ────────────────────────────────────────────────────────────────


class IdempotencyKeyConflict(QIException):
    """A mesma request_control_key chegou com outro pedido (MOV-12).

    Mesma chave e mesmo pedido não é erro: é a resposta da primeira vez.
    """

    code = "QIT001014"

    def __init__(self, request_control_key) -> None:
        title = "Idempotency key conflict"
        http_status = 409
        description = f"The request_control_key {request_control_key} was already used with a different request."
        translation = "Esta chave de idempotência já foi usada com outro pedido."
        super().__init__(title, self.code, http_status, description, translation)


class InsufficientBalance(QIException):
    code = "QIT001015"

    def __init__(self, account_key) -> None:
        title = "Insufficient balance"
        http_status = 422
        description = f"The balance of account {account_key} does not cover this operation."
        translation = "O saldo não cobre o valor da operação (e a tarifa, na transferência)."
        super().__init__(title, self.code, http_status, description, translation)


class SameAccountTransfer(QIException):
    code = "QIT001016"

    def __init__(self) -> None:
        title = "Same account transfer"
        http_status = 422
        description = "The destination account must be different from the origin account."
        translation = "A conta de destino precisa ser diferente da conta de origem."
        super().__init__(title, self.code, http_status, description, translation)


class DestinationAccountNotFound(QIException):
    code = "QIT001017"

    def __init__(self, account_key) -> None:
        title = "Destination account not Found"
        http_status = 404
        description = f"Destination account with key {account_key} was not found."
        translation = "A conta de destino não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class DestinationAccountNotActive(QIException):
    code = "QIT001018"

    def __init__(self, account_key) -> None:
        title = "Destination account is not active"
        http_status = 409
        description = f"Destination account with key {account_key} cannot receive money."
        translation = "A conta de destino não está ativa: está bloqueada ou encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class DailyTransferLimitReached(QIException):
    """A 11ª transferência enviada no dia contábil (CLI-08).

    É a única recusa que grava alguma coisa: a conta fica bloqueada na
    mesma requisição (DAD-13).
    """

    code = "QIT001019"

    def __init__(self, account_key) -> None:
        title = "Daily transfer limit reached"
        http_status = 422
        description = f"Account {account_key} reached the daily limit of transfers and was blocked."
        translation = "O limite diário de transferências foi atingido, e a conta foi bloqueada."
        super().__init__(title, self.code, http_status, description, translation)


class TransactionNotFound(QIException):
    code = "QIT001020"

    def __init__(self, transaction_key) -> None:
        title = "Transaction not Found"
        http_status = 404
        description = f"Transaction with key {transaction_key} was not found."
        translation = f"A operação com chave {transaction_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Cofrinho e categorias
# ────────────────────────────────────────────────────────────────


class CategoryNotFound(QIException):
    code = "QIT001021"

    def __init__(self, category_key) -> None:
        title = "Category not Found"
        http_status = 404
        description = f"Category with key {category_key} was not found in this piggy bank."
        translation = f"A categoria com chave {category_key} não foi encontrada neste cofrinho."
        super().__init__(title, self.code, http_status, description, translation)


class CategoryDeleted(QIException):
    code = "QIT001022"

    def __init__(self, category_key) -> None:
        title = "Category is deleted"
        http_status = 409
        description = f"Category with key {category_key} is deleted."
        translation = "A categoria foi excluída."
        super().__init__(title, self.code, http_status, description, translation)


class InsufficientCategoryBalance(QIException):
    code = "QIT001023"

    def __init__(self, category_key) -> None:
        title = "Insufficient category balance"
        http_status = 422
        description = f"The balance of category {category_key} does not cover this redemption."
        translation = "O saldo da categoria não cobre o resgate."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedCategoryName(QIException):
    code = "QIT001024"

    def __init__(self, name) -> None:
        title = "Category name already registered"
        http_status = 409
        description = f"There is already an active category named {name}."
        translation = "Já existe uma categoria ativa com este nome."
        super().__init__(title, self.code, http_status, description, translation)


class DefaultCategoryCannotBeDeleted(QIException):
    code = "QIT001025"

    def __init__(self, category_key) -> None:
        title = "Default category cannot be deleted"
        http_status = 409
        description = f"Category with key {category_key} is the default category."
        translation = "A categoria padrão (economias) não pode ser excluída."
        super().__init__(title, self.code, http_status, description, translation)


class CategoryNotEmpty(QIException):
    code = "QIT001026"

    def __init__(self, category_key) -> None:
        title = "Category is not empty"
        http_status = 409
        description = f"Category with key {category_key} has money."
        translation = "Só uma categoria zerada pode ser excluída."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Gamificação
# ────────────────────────────────────────────────────────────────


class NotEnoughFreePoints(QIException):
    code = "QIT001027"

    def __init__(self, requested, free) -> None:
        title = "Not enough free points"
        http_status = 422
        description = f"Requested {requested} points, but only {free} are free."
        translation = f"Pontos livres insuficientes: pedidos {requested}, livres {free}."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Virada do dia
# ────────────────────────────────────────────────────────────────


class DayAlreadyClosed(QIException):
    code = "QIT001028"

    def __init__(self, accounting_date) -> None:
        title = "Day already closed"
        http_status = 409
        description = f"The day {accounting_date} is already closed."
        translation = f"O dia {accounting_date} já foi fechado."
        super().__init__(title, self.code, http_status, description, translation)


class FutureAccountingDate(QIException):
    code = "QIT001029"

    def __init__(self, accounting_date, current_date) -> None:
        title = "Future accounting date"
        http_status = 422
        description = f"The day {accounting_date} is after the bank date {current_date}."
        translation = f"O dia {accounting_date} ainda não chegou: o banco está em {current_date}."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidAccountingDate(QIException):
    """A data tem o formato certo e não existe no calendário.

    Mesma ideia do InvalidBirthdate: o schema confere o formato, e
    "2026-02-30" só morre no `date.fromisoformat`.
    """

    code = "QIT001030"

    def __init__(self, accounting_date) -> None:
        title = "Invalid accounting date"
        http_status = 422
        description = f"The accounting date {accounting_date} is not a real date."
        translation = "A data informada não existe no calendário."
        super().__init__(title, self.code, http_status, description, translation)


class CdiUnavailable(QIException):
    """O Banco Central (o Mockserver) não respondeu a tempo (COF-20).

    503: a dependência está fora do ar ou lenta. A virada é desfeita
    inteira, e o dia não avança.
    """

    code = "QIT001031"

    def __init__(self, accounting_date) -> None:
        title = "CDI rate unavailable"
        http_status = 503
        description = f"The Central Bank did not answer the CDI rate for {accounting_date} in time."
        translation = "O Banco Central não respondeu a taxa do CDI a tempo."
        super().__init__(title, self.code, http_status, description, translation)


class NumericLimitExceeded(QIException):
    code = "QIT001032"

    def __init__(self) -> None:
        super().__init__("Numeric Limit Exceeded", self.code, 422,
                         "An accumulated value exceeds the BIGINT limit.",
                         "Um valor acumulado excede o limite numérico permitido.")

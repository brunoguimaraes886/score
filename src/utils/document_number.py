CPF_LENGTH = 11

CHECK_DIGIT_POSITIONS = [9, 10]

CNPJ_LENGTH = 14

# Pesos dos dois dígitos verificadores do CNPJ, da esquerda para a direita:
# o primeiro dígito usa os 12 primeiros dígitos; o segundo, os 13.
CNPJ_FIRST_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_SECOND_WEIGHTS = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

# Tamanho do documento formatado: CPF 000.000.000-00; CNPJ 00.000.000/0000-00.
FORMATTED_CPF_LENGTH = 14
FORMATTED_CNPJ_LENGTH = 18


def is_valid_cpf(document_number: str) -> bool:
    """Diz se um CPF existe de verdade — não se ele tem a cara certa.

    O schema em src/schemas/post_customers.json já cobrou o formato:
    três pontos, um hífen, onze dígitos. Isto aqui é outra pergunta, e a
    diferença entre as duas é a lição deste arquivo.

    Os dois últimos dígitos de um CPF não são escolhidos: eles são o
    RESULTADO de uma conta feita sobre os nove primeiros. Por isso um
    número pode ter o formato perfeito e não existir — "111.222.333-44"
    passa no schema e não passa aqui.

    É o mesmo motivo pelo qual a resposta dessa recusa é 422 e não 400:
    não é que a API não conseguiu ler o pedido; ela leu, entendeu, e o
    valor não pode existir.

    A conta, para cada um dos dois dígitos: multiplica cada dígito
    anterior por um peso que decresce, soma tudo, tira o resto da divisão
    por 11. Resto menor que 2 vira dígito 0; nos outros casos, o dígito é
    11 menos o resto.
    """
    digits = []
    for character in document_number:
        if character.isdigit():
            digits.append(int(character))

    if len(digits) != CPF_LENGTH:
        return False

    # Um CPF de dígitos todos iguais ("111.111.111-11") passa na conta
    # dos dígitos verificadores e mesmo assim não vale. São onze números
    # conhecidos, e a Receita não emite nenhum deles.
    all_digits_are_equal = True
    for digit in digits:
        if digit != digits[0]:
            all_digits_are_equal = False
            break

    if all_digits_are_equal:
        return False

    for position in CHECK_DIGIT_POSITIONS:
        total = 0
        first_weight = position + 1

        for index in range(position):
            total = total + digits[index] * (first_weight - index)

        remainder = total % 11

        if remainder < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - remainder

        if digits[position] != expected_digit:
            return False

    return True


def is_valid_cnpj(document_number: str) -> bool:
    """Diz se um CNPJ existe de verdade (MOV-16): a mesma pergunta do is_valid_cpf, com outros pesos.

    O schema post_deposits.json já cobrou o formato 00.000.000/0000-00.
    Aqui a conta: cada dígito verificador é o resto da soma dos dígitos
    anteriores multiplicados pelos pesos (CNPJ_FIRST_WEIGHTS e
    CNPJ_SECOND_WEIGHTS), dividida por 11. Resto menor que 2 vira 0; nos
    outros casos, o dígito é 11 menos o resto. CNPJ de dígitos todos
    iguais não vale.
    """
    digits = []
    for character in document_number:
        if character.isdigit():
            digits.append(int(character))

    if len(digits) != CNPJ_LENGTH:
        return False

    if len(set(digits)) == 1:
        return False

    for weights in [CNPJ_FIRST_WEIGHTS, CNPJ_SECOND_WEIGHTS]:
        position = len(weights)
        total = 0

        for index in range(position):
            total = total + digits[index] * weights[index]

        remainder = total % 11

        if remainder < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - remainder

        if digits[position] != expected_digit:
            return False

    return True


def mask_document_number(document_number: str) -> str:
    """O CPF ou o CNPJ de outra pessoa, mascarado (PRD-12, MOV-17).

    CPF 123.456.789-09 → ***.456.789-**: somem os 3 primeiros dígitos e
    os 2 verificadores. CNPJ 11.222.333/0001-81 → **.222.333/****-**:
    somem os 2 primeiros, a filial e os 2 verificadores. O documento
    chega formatado, como o banco o guarda; outro tamanho é erro de
    programa (ValueError), nunca dado de cliente.
    """
    if len(document_number) == FORMATTED_CPF_LENGTH:
        return "***" + document_number[3:12] + "**"

    if len(document_number) == FORMATTED_CNPJ_LENGTH:
        return "**" + document_number[2:11] + "****-**"

    raise ValueError(f"documento com {len(document_number)} caracteres não é CPF nem CNPJ formatado")

# Funções de uso geral no aplicativo

from datetime import date, datetime
import random
import string


def remove_prefixo(d):
    """
    Remove o prefixo das chaves de um dicionário.
    :param d: dicionário original com prefixo nas chaves
    :return: novo dicionário com as chaves sem o prefixo
    """
    # Obtém o prefixo a partir da primeira chave do dicionário
    first_key = next(iter(d))
    prefix = first_key.split('_')[0] + '_'

    # Cria um novo dicionário com as chaves sem o prefixo
    new_dict = {key[len(prefix):]: value for key, value in d.items()}
    return new_dict


def datetime_para_string(data):
    """
    Converte todos os objetos datetime em texto no dicionário fornecido.
    """
    for key, value in data.items():
        if isinstance(value, datetime):
            # Converte datetime para string ISO 8601
            data[key] = value.isoformat()
        elif isinstance(value, date):
            data[key] = value.isoformat()  # Converte date para string ISO 8601
    return data


def calcular_idade(data_nascimento_str):
    # Função que calcula a idade em anos de uma data no forma ISO (yyyy-mm-dd)

    # Converte a string da data para um objeto datetime no formato ISO
    data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d')
    hoje = datetime.today()
    # Calcula a diferença em anos
    idade = hoje.year - data_nascimento.year
    # Ajusta a idade se o aniversário ainda não aconteceu este ano
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade


def gerar_senha(tamanho=8):
    """
    Gera uma senha aleatória com:
     - letras maiúsculas
     - letras minúsculas
     - números
     - caracteres especiais
     - 8 ou mais caracteres
    :param tamanho: tamanho desejado da senha (padrão é 8)
    :return: string com a senha gerada
    """
    if tamanho < 8:
        raise ValueError("O tamanho da senha deve ser pelo menos 8 caracteres")

    letras_minusculas = string.ascii_lowercase
    letras_maiusculas = string.ascii_uppercase
    numeros = string.digits
    caracteres_especiais = '-_=+!#$&'

    todos_caracteres = letras_minusculas + \
        letras_maiusculas + numeros + caracteres_especiais

    # Garante que a senha tenha pelo menos um de cada tipo de caractere
    senha = [
        random.choice(letras_minusculas),
        random.choice(letras_maiusculas),
        random.choice(numeros),
        random.choice(caracteres_especiais)
    ]

    # Completa a senha com caracteres aleatórios até atingir o tamanho desejado
    senha += [random.choice(todos_caracteres)
              for _ in range(tamanho - len(senha))]

    # Embaralha os caracteres para evitar que a ordem dos tipos seja previsível
    random.shuffle(senha)

    return ''.join(senha)

# Teste de mesa
# print('\n\n\n', gerar_senha(), '\n\n\n')
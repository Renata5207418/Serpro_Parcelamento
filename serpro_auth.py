import base64
import time
import logging
from requests_pkcs12 import post  # Requisições HTTPS com certificado digital
from decouple import config  # Para carregar variáveis do .env
from dotenv import load_dotenv  # Para carregar o .env no ambiente

# ===========================================
# CARREGAR VARIÁVEIS DE AMBIENTE DO ARQUIVO .env
# ===========================================

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração básica de logging para exibir logs no console
logging.basicConfig(level=logging.INFO)

# ===========================================
# CACHE PARA TOKEN DE AUTENTICAÇÃO
# ===========================================
token_cache = {
    "access_token": None,  # Token de acesso
    "expires_in": None,    # Tempo de expiração (segundos)
    "timestamp": None      # Registro de tempo para validar expiração
}


# ===========================================
# FUNÇÃO PARA OBTER TOKEN DE AUTENTICAÇÃO
# ===========================================
def obter_token_autenticacao():
    """
    Obtém o token de autenticação do SERPRO.

    Retorna:
        tuple: (access_token, jwt_token) em caso de sucesso.
        Exception: Lança exceção em caso de erro.
    """

    # Verifica se o token armazenado ainda é válido
    if token_cache["access_token"] and token_cache["expires_in"] and token_cache["timestamp"]:
        # Calcula o tempo desde que o token foi gerado
        tempo_passado = time.time() - token_cache["timestamp"]
        # Se o token for válido (faltando pelo menos 30 segundos para expirar), reutiliza-o
        if tempo_passado < (token_cache["expires_in"] - 30):
            logging.info("Utilizando token em cache")
            return token_cache["access_token"], token_cache["jwt_token"]

    # ===========================================
    # CONFIGURAÇÃO DE CREDENCIAIS E CERTIFICADO
    # ===========================================

    # URL do endpoint de autenticação
    url = "https://autenticacao.sapi.serpro.gov.br/authenticate"

    # Caminho e informações do certificado digital
    caminho_certificado = config('CAMINHO_CERTIFICADO')  # Caminho para o certificado
    certificado = f"{caminho_certificado}/{config('NOME_CERTIFICADO')}"  # Nome do arquivo PFX
    senha_certificado = config('SENHA_CERTIFICADO')  # Senha do certificado

    # Credenciais do consumidor para autenticação na API
    consumer_key = config('CONSUMER_KEY')  # Chave do consumidor
    consumer_secret = config('CONSUMER_SECRET')  # Segredo do consumidor

    # ===========================================
    # CABEÇALHOS E CORPO DA REQUISIÇÃO
    # ===========================================
    headers = {
        # Autenticação básica com base64
        "Authorization": "Basic " + base64.b64encode(f"{consumer_key}:{consumer_secret}".encode("utf8")).decode("utf8"),
        "Role-Type": "TERCEIROS",  # Define o papel do usuário como terceiros
        "Content-Type": "application/x-www-form-urlencoded"  # Tipo de conteúdo
    }

    # Corpo da requisição para obter o token
    body = {'grant_type': 'client_credentials'}

    # ===========================================
    # ENVIO DA REQUISIÇÃO PARA O SERVIDOR
    # ===========================================
    try:
        # Envia a requisição POST usando o certificado digital
        response = post(
            url,
            data=body,
            headers=headers,
            verify=True,  # Habilita validação SSL
            pkcs12_filename=certificado,  # Caminho do certificado PFX
            pkcs12_password=senha_certificado  # Senha do certificado
        )

        # Levanta erro se a resposta não for bem-sucedida (status 200)
        response.raise_for_status()

        # ===========================================
        # TRATAMENTO DA RESPOSTA
        # ===========================================
        response_data = response.json()

        # Armazena os tokens no cache para reutilização
        token_cache["access_token"] = response_data.get("access_token")
        token_cache["jwt_token"] = response_data.get("jwt_token")
        token_cache["expires_in"] = response_data.get("expires_in")
        token_cache["timestamp"] = time.time()  # Marca o momento em que o token foi obtido

        logging.info("Token obtido com sucesso")

        # Retorna o token de acesso e o JWT token
        return token_cache["access_token"], token_cache["jwt_token"]

    except Exception as e:
        # Em caso de erro, registra no log e lança exceção
        logging.error(f"Erro ao obter token de autenticação: {e}")
        raise Exception(f"Erro ao autenticar: {e}")

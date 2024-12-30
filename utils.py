import json
import requests
from serpro_auth import obter_token_autenticacao
from dotenv import load_dotenv
import datetime
import re
from models import session, Requisicao

# Carrega as variáveis do ambiente
load_dotenv()


def fazer_requisicao_serpro(endpoint='/Emitir', method='POST', data=None):
    """
    Faz uma requisição para o endpoint da API do SERPRO.

    Parâmetros:
        endpoint (str): Caminho do endpoint da API (padrão: '/Emitir').
        method (str): Método HTTP usado na requisição (padrão: 'POST').
        data (dict): Dados a serem enviados no corpo da requisição.

    Retorna:
        tuple:
            - docArrecadacaoPdfB64 (str): Base64 do PDF gerado.
            - mensagem_texto (str): Mensagem retornada pela API.
    """
    # Obtém os tokens de autenticação
    try:
        access_token, jwt_token = obter_token_autenticacao()
    except Exception as e:
        print(f"Erro ao obter o token de autenticação: {e}")
        return None

    # Monta a URL da requisição
    url = f'https://gateway.apiserpro.serpro.gov.br/integra-contador/v1{endpoint}'

    # Define os cabeçalhos HTTP
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'jwt_token': jwt_token
    }

    # Log de depuração
    print(f"Fazendo requisição para {url}")
    print(f"Headers: {headers}")
    print(f"Payload de Dados: {json.dumps(data, indent=2)}")

    try:
        # Envia a requisição com base no método HTTP especificado
        if method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))
        elif method == 'GET':
            response = requests.get(url, headers=headers)
        else:
            print("Método HTTP não suportado.")
            return None

        # Log de resposta
        print(f"Status da resposta: {response.status_code}")
        print(f"Corpo da resposta: {response.text}")

        # Processa a resposta
        if response.status_code == 200:
            try:
                response_data = response.json()

                # Trata mensagens retornadas
                mensagens = response_data.get("mensagens", [])
                mensagem_texto = ", ".join(
                    [f"{mensagem.get('codigo', '')}: {mensagem.get('texto', '')}" for mensagem in mensagens]
                )

                # Verifica se há dados retornados
                if response_data.get("dados"):
                    try:
                        dados = json.loads(response_data["dados"])
                        if "docArrecadacaoPdfB64" in dados:
                            return dados["docArrecadacaoPdfB64"], mensagem_texto or None
                    except ValueError as ve:
                        return None, f"Erro ao processar 'dados': {ve}"

                return None, mensagem_texto or "Nenhum dado de arrecadação encontrado."

            except ValueError as ve:
                return None, f"Erro ao interpretar JSON da resposta: {ve}"
        else:
            try:
                response_data = response.json()
                mensagem_erro = response_data.get("mensagens", [{"texto": "Erro desconhecido do servidor"}])
                mensagem_texto = ", ".join(
                    [f"{mensagem.get('codigo', '')}: {mensagem.get('texto', '')}" for mensagem in mensagem_erro]
                )
                return None, mensagem_texto
            except ValueError:
                return None, f"Erro na requisição ao SERPRO: {response.status_code} - {response.text}"

    except requests.RequestException as e:
        return None, f"Erro na requisição: {str(e)}"


def formatar_numero_documento(numero):
    """
    Remove todos os caracteres não numéricos de um número de documento.

    Parâmetros:
        numero (str): Número do documento (CPF/CNPJ).

    Retorna:
        str: Número formatado apenas com dígitos.
    """
    return re.sub(r'\D', '', numero)


def montar_json_gerardas(numero_contribuinte, tipo_contribuinte, id_sistema, id_servico, parcela_para_emitir):
    """
    Monta o JSON necessário para solicitar o documento de arrecadação DAS.

    Parâmetros:
        numero_contribuinte (str): Número do contribuinte (CPF/CNPJ).
        tipo_contribuinte (int): Tipo do contribuinte (1 para CPF, 2 para CNPJ).
        id_sistema (str): ID do sistema solicitado.
        id_servico (str): ID do serviço solicitado.
        parcela_para_emitir (str): Data da parcela (AAAAMM).

    Retorna:
        dict: Estrutura JSON formatada para envio.
    """
    numero_contribuinte = formatar_numero_documento(numero_contribuinte)

    json_dados = {
        "contratante": {
            "numero": "00000000000000",  # Substituir pelo CNPJ do contratante
            "tipo": 2
        },
        "autorPedidoDados": {
            "numero": "00000000000000",  # Substituir pelo CNPJ do autor
            "tipo": 2
        },
        "contribuinte": {
            "numero": numero_contribuinte,
            "tipo": tipo_contribuinte
        },
        "pedidoDados": {
            "idSistema": id_sistema,
            "idServico": id_servico,
            "versaoSistema": "1.0",
            "dados": json.dumps({
                "parcelaParaEmitir": parcela_para_emitir
            })
        }
    }

    print(f"JSON montado para envio: {json.dumps(json_dados, indent=2)}")
    return json_dados


def salvar_resposta_recibo(requisicao_id, resposta_base64, status="Concluído", mensagem="Sucesso"):
    """
    Salva a resposta da API no banco de dados associada à requisição.

    Parâmetros:
        requisicao_id (int): ID da requisição no banco de dados.
        resposta_base64 (str): Documento em formato base64.
        status (str): Status do processamento (padrão: "Concluído").
        mensagem (str): Mensagem de status (padrão: "Sucesso").
    """
    requisicao = session.query(Requisicao).get(requisicao_id)
    if requisicao:
        requisicao.resposta_base64 = resposta_base64
        requisicao.status = status
        requisicao.response_message = mensagem
        requisicao.data_resposta = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
        print(f"Requisição {requisicao_id} atualizada com sucesso.")
    else:
        print(f"Requisição {requisicao_id} não encontrada.")

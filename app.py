from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db, session, Requisicao
from utils import montar_json_gerardas, fazer_requisicao_serpro
from empresa_codigos import CNPJ_CODIGO_EMPRESA
from sqlalchemy import extract
import secrets
import io
import pandas as pd
import zipfile
import base64
import datetime
import logging

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    """
    Classe para definir o usuário
    """
    # Banco de dados fictício para demonstração (substituir por base real)
    user_database = {
        "admin": {
            "username": "admin",
            "password": generate_password_hash("admin123", method='pbkdf2:sha256')
        },
        "usuario@exemplo.com": {
            "username": "usuario@exemplo.com",
            "password": generate_password_hash("senha123", method='pbkdf2:sha256')
        }
    }

    def __init__(self, username):
        self.id = username
        self.username = username

    @classmethod
    def get(cls, username):
        user_data = cls.user_database.get(username)
        if user_data:
            return User(username=user_data['username'])
        return None


@login_manager.user_loader
def load_user(user_id):
    """
     Carrega um usuário pelo ID para gerenciamento de login.
    """
    return User.get(user_id)


init_db()


@app.route('/')
@login_required
def index():
    """
    Renderiza a página inicial para usuários autenticados.
    """
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Gerencia o login de usuários.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.get(username)

        if user and check_password_hash(User.user_database[username]['password'], password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """
     Realiza o logout do usuário.
    """
    logout_user()
    return redirect(url_for('login'))


@app.route('/consulta', methods=['GET'])
def consulta():
    """
     Consulta requisições enviadas com base nos parâmetros fornecidos.
    """
    contribuinte = request.args.get('contribuinte', None)
    mes = request.args.get('mes', None)

    query = session.query(Requisicao)

    if contribuinte:
        query = query.filter(Requisicao.contribuinte == contribuinte)

    if mes:
        try:
            mes = int(mes)
            query = query.filter(extract('month', Requisicao.data_envio) == mes)
        except ValueError:
            pass

    requisicoes = query.all()

    requisicoes_lista = [
        {
            'contribuinte': req.contribuinte,
            'data_envio': req.data_envio.strftime('%d/%m/%Y') if req.data_envio else '',
            'status': req.status,
            'id': req.id,
            'resposta_base64': req.resposta_base64
        } for req in requisicoes
    ]

    total_guias = len(requisicoes_lista)

    return render_template('consulta.html', requisicoes=requisicoes_lista, total_guias=total_guias)


@app.route('/static/images/<path:filename>')
def serve_static(filename):
    """
    Serve arquivos estáticos da pasta `static/images`.
    """
    return send_from_directory('static/images', filename)


@app.route('/gerar_das', methods=['POST'])
@login_required
def gerar_das():
    """
    Gera um documento DAS baseado nos dados fornecidos no formulário.
    """
    numero_contribuinte = request.form.get('contribuinte')
    tipo_contribuinte = int(request.form.get('tipo_contribuinte'))
    id_sistema = request.form.get('id_sistema')
    id_servico = request.form.get('id_servico')
    parcela_para_emitir = request.form.get('parcela_para_emitir')

    json_data = montar_json_gerardas(
        numero_contribuinte,
        tipo_contribuinte,
        id_sistema,
        id_servico,
        parcela_para_emitir
    )

    try:
        resposta_pdf_b64, mensagem_erro = fazer_requisicao_serpro("/Emitir", method='POST', data=json_data)

        if resposta_pdf_b64:
            nova_requisicao = Requisicao(
                contribuinte=numero_contribuinte,
                tipo_contribuinte=tipo_contribuinte,
                id_sistema=id_sistema,
                id_servico=id_servico,
                data_envio=datetime.datetime.now(datetime.timezone.utc),
                status="Concluído",
                resposta_base64=resposta_pdf_b64
            )
            session.add(nova_requisicao)
            session.commit()

            return jsonify({
                "message": "Documento DAS gerado com sucesso!",
                "dados": {"id_requisicao": nova_requisicao.id}
            }), 200
        else:
            return jsonify({
                "error": "Erro ao gerar o documento DAS",
                "mensagem": mensagem_erro or "Ocorreu um erro desconhecido durante a geração do documento."
            }), 500

    except Exception as e:
        return jsonify({
            "error": "Erro ao processar o pedido",
            "mensagem": str(e)
        }), 500


@app.route('/enviar_em_lote', methods=['POST'])
def enviar_em_lote():
    """
        Gera o documento DAS baseado nos dados fornecidos do arquivo xlsx, extraindo linha por linha.
    """
    if 'fileUpload' not in request.files:
        logging.error("Nenhum arquivo enviado no campo 'fileUpload'.")
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['fileUpload']

    if file.filename == '':
        logging.error("Nenhum arquivo selecionado. O nome do arquivo está vazio.")
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        df = pd.read_excel(file)
        logging.info("Arquivo Excel lido com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo Excel: {str(e)}")
        return jsonify({'error': f'Erro ao ler o arquivo: {str(e)}'}), 400

    required_columns = {'CNPJ', 'ID_SISTEMA', 'ID_SERVICO', 'DATA_ENVIO'}
    if not required_columns.issubset(df.columns):
        logging.error(f"Colunas faltando no arquivo. Colunas encontradas: {list(df.columns)}")
        return jsonify({'error': 'Arquivo inválido. Verifique as colunas.'}), 400

    resultados = []
    for _, row in df.iterrows():
        numero_contribuinte = row['CNPJ']
        id_sistema = row['ID_SISTEMA']
        id_servico = row['ID_SERVICO']
        data_envio = row['DATA_ENVIO']

        logging.info(
            f"Processando linha - CNPJ: {numero_contribuinte}, ID_SISTEMA: {id_sistema}, ID_SERVICO: {id_servico}, "
            f"DATA_ENVIO: {data_envio}")

        try:
            if isinstance(data_envio, str) and '/' in data_envio:
                parcela_para_emitir = data_envio.replace('/', '')
            elif isinstance(data_envio, datetime.datetime):
                parcela_para_emitir = data_envio.strftime('%Y%m')
            else:
                raise ValueError(f"Erro ao processar a data: formato inválido ({data_envio})")

            tipo_contribuinte = 2

            json_data = montar_json_gerardas(
                numero_contribuinte,
                tipo_contribuinte,
                id_sistema,
                id_servico,
                parcela_para_emitir
            )

            resposta_pdf_b64, mensagem_erro = fazer_requisicao_serpro("/Emitir", method='POST', data=json_data)

            if resposta_pdf_b64:
                nova_requisicao = Requisicao(
                    contribuinte=numero_contribuinte,
                    tipo_contribuinte=tipo_contribuinte,
                    id_sistema=id_sistema,
                    id_servico=id_servico,
                    data_envio=datetime.datetime.now(datetime.timezone.utc),
                    status="Concluído",
                    resposta_base64=resposta_pdf_b64
                )
                session.add(nova_requisicao)
                session.commit()

                resultados.append({
                    "CNPJ": numero_contribuinte,
                    "status": "Sucesso",
                    "mensagem": "Documento DAS gerado com sucesso"
                })

                logging.info(f"Documento DAS gerado com sucesso para CNPJ: {numero_contribuinte}")

            else:
                resultados.append({
                    "CNPJ": numero_contribuinte,
                    "status": "Erro",
                    "mensagem": mensagem_erro or "Erro ao gerar o documento DAS"
                })

                logging.error(f"Erro ao gerar o documento DAS para CNPJ: {numero_contribuinte} - {mensagem_erro}")

        except Exception as e:
            resultados.append({
                "CNPJ": numero_contribuinte,
                "status": "Erro",
                "mensagem": f"Erro ao processar o CNPJ {numero_contribuinte}: {str(e)}"
            })
            logging.error(f"Erro ao processar o CNPJ {numero_contribuinte}: {str(e)}")

    return jsonify({
        "message": "Envio em lote concluído",
        "resultados": resultados
    }), 200


@app.route('/consultar_requisicoes', methods=['GET'])
@login_required
def consultar_requisicoes():
    """
    Consulta as requisições enviadas e salvas no banco, exibe em lista e filtra por data de envio.
    """
    contribuinte = request.args.get('contribuinte', None)

    if contribuinte:
        requisicoes = session.query(Requisicao).filter(Requisicao.contribuinte == contribuinte).all()
    else:
        requisicoes = session.query(Requisicao).all()

    requisicoes_lista = []
    for req in requisicoes:
        requisicoes_lista.append({
            'id': req.id,
            'contribuinte': req.contribuinte,
            'data_envio': req.data_envio.strftime('%d/%m/%Y %H:%M:%S') if req.data_envio else '',
            'status': req.status,
            'resposta_base64': True if req.resposta_base64 else False
        })

    return jsonify(requisicoes_lista)


@app.route('/baixar_recibo/<int:id>', methods=['GET'])
def baixar_recibo(id):
    """
    Faz o download da Guia.
    """
    requisicao = session.query(Requisicao).get(id)

    if requisicao and requisicao.resposta_base64:
        pdf_bytes = base64.b64decode(requisicao.resposta_base64)
        pdf_file = io.BytesIO(pdf_bytes)

        cnpj_contribuinte = requisicao.contribuinte

        codigo_empresa = CNPJ_CODIGO_EMPRESA.get(cnpj_contribuinte, "0000")

        data_envio = requisicao.data_envio
        mesano = data_envio.strftime('%m%Y')

        nome_arquivo = f"{codigo_empresa}-PARC SN-{mesano}.pdf"

        return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

    else:
        return jsonify({'message': 'Recibo não encontrado ou ainda não disponível.'}), 404


@app.route('/baixar_todos_recibos', methods=['GET'])
def baixar_todos_recibos():
    """
    Faz o Download em lote de todas as guias retornadas.
    """
    requisicoes = session.query(Requisicao).filter(Requisicao.resposta_base64.isnot(None)).all()

    if not requisicoes:
        return jsonify({'message': 'Nenhum recibo disponível para download.'}), 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for req in requisicoes:
            pdf_bytes = base64.b64decode(req.resposta_base64)

            cnpj_contribuinte = req.contribuinte
            codigo_empresa = CNPJ_CODIGO_EMPRESA.get(cnpj_contribuinte, "0000")
            data_envio = req.data_envio
            mesano = data_envio.strftime('%m%Y')
            nome_arquivo = f"{codigo_empresa}-PARC SN-{mesano}.pdf"
            zip_file.writestr(nome_arquivo, pdf_bytes)

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='recibos_em_lote.zip'
    )


if __name__ == "__main__":
    app.run(debug=True)

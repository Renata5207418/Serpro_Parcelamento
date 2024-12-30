from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# ===========================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ===========================================

"""
Define a base para os modelos do SQLAlchemy.
Todos os modelos devem herdar de Base.
"""
Base = declarative_base()


# ===========================================
# MODELO: REQUISICAO
# ===========================================

class Requisicao(Base):
    """
    Modelo para armazenar as requisições enviadas e suas respostas.

    Tabela: requisicoes
    """
    __tablename__ = 'requisicoes'

    # Identificador único da requisição
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Informações do Contribuinte
    contribuinte = Column(String, nullable=False)  # CPF ou CNPJ
    tipo_contribuinte = Column(Integer, nullable=False)  # Tipo: 1 - CPF, 2 - CNPJ

    # Informações do Sistema e do Serviço
    id_sistema = Column(String, nullable=False)  # Identificador do sistema
    id_servico = Column(String, nullable=False)  # Identificador do serviço

    # Resposta e Status
    resposta_base64 = Column(Text, nullable=True)  # Resposta em PDF codificada em Base64
    data_envio = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))  # Data de envio
    data_resposta = Column(DateTime, nullable=True)  # Data de resposta (opcional)
    status = Column(String, default="Pendente")  # Status inicial é "Pendente"
    response_message = Column(String, nullable=True)  # Mensagem de resposta (opcional)


# ===========================================
# CONFIGURAÇÃO DA CONEXÃO COM O BANCO DE DADOS
# ===========================================

"""
Cria a conexão com o banco de dados SQLite.
O parâmetro 'echo=True' exibe as operações SQL no console para depuração.
"""
engine = create_engine('sqlite:///serpro_app.db', echo=True)

"""
Cria uma fábrica de sessões para interagir com o banco de dados.
Cada instância de 'session' é usada para realizar operações no banco.
"""
Session = sessionmaker(bind=engine)
session = Session()


# ===========================================
# FUNÇÃO PARA INICIALIZAR O BANCO DE DADOS
# ===========================================

def init_db():
    """
    Inicializa o banco de dados criando as tabelas definidas no modelo.

    Observação:
        Esta função deve ser executada na primeira inicialização ou após alterações no modelo.
    """
    Base.metadata.create_all(engine)


# ===========================================
# EXECUÇÃO DIRETA DO ARQUIVO
# ===========================================

"""
Se este arquivo for executado diretamente (e não importado como módulo),
o banco de dados será inicializado automaticamente.
"""
if __name__ == "__main__":
    init_db()

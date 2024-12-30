"""
Módulo: empresa_codigos.py

Descrição:
    Mapeia os CNPJs das empresas para seus respectivos códigos.
    Esses códigos são usados para nomear documentos gerados pela aplicação.

Uso:
    Este dicionário é acessado diretamente pelo código para associar
    cada CNPJ ao código correspondente da empresa.

Exemplo:
    CNPJ_CODIGO_EMPRESA["00.000.000/0001-00"] -> "1234"

Observação:
    - Substitua os exemplos abaixo pelos valores reais em produção.
    - Caso o número de empresas cresça, recomenda-se armazenar esses
      dados em um banco de dados em vez de um dicionário fixo.
"""

# ===========================================
# MAPEAMENTO DE CNPJs PARA CÓDIGOS DE EMPRESA
# ===========================================

CNPJ_CODIGO_EMPRESA = {
    # Exemplos de CNPJs e seus códigos
    "00.000.000/0001-00": "1234",  # Empresa Exemplo 1
    "11.111.111/0001-11": "5678",  # Empresa Exemplo 2
    "22.222.222/0001-22": "9101",  # Empresa Exemplo 3
    "33.333.333/0001-33": "1121",  # Empresa Exemplo 4

}

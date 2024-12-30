# Sistema de Geração e Consulta de DAS

Este é um sistema web desenvolvido em **Python** com **Flask**, destinado à **geração e consulta de Documentos de Arrecadação do Simples Nacional (DAS)** utilizando a **API do SERPRO**.

---

## Recursos

- 🔒 **Login Seguro** – Autenticação com **Flask-Login** e senha criptografada.  
- 🧾 **Geração de DAS** – Integração com a **API do SERPRO** para emissão de documentos.  
- 📂 **Envio em Lote** – Suporte para upload de planilhas (**Excel**) com múltiplos contribuintes.  
- 📊 **Consulta de Requisições** – Histórico detalhado de envios com possibilidade de download dos recibos.  
- 📦 **Download em Lote** – Exportação dos recibos em formato **ZIP**.  
- 📱 **Interface Responsiva** – Utiliza **Bootstrap** para um design moderno e adaptável.  

---

## Tecnologias Utilizadas

**Backend:**  
- Python 3  
- Flask  
- SQLAlchemy  
- Flask-Login  
- Requests  

**Frontend:**  
- HTML5  
- CSS3  
- Bootstrap 5  
- JavaScript (IMask, FontAwesome)  

**Banco de Dados:**  
- SQLite  

**Autenticação:**  
- OAuth 1.0 com certificados digitais **PFX**.  

---

## Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

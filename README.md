# 💰 Somma - Dashboard Financeiro Pessoal

Sistema de controle financeiro pessoal desenvolvido com **Streamlit**, **Pandas** e **Plotly**. O Somma permite gerenciar suas despesas e receitas de forma simples e visual, com suporte a armazenamento híbrido (Google Sheets ou CSV local).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Funcionalidades

- ✅ **Dashboard interativo** com gráficos e métricas financeiras
- ✅ **Cadastro de transações** (despesas e receitas)
- ✅ **Categorização automática** de gastos
- ✅ **Visualização por período** com filtros
- ✅ **Edição e exclusão** de transações
- ✅ **Armazenamento híbrido**: Google Sheets (nuvem) ou CSV (local)
- ✅ **Interface responsiva** e profissional
- ✅ **Sincronização em tempo real** com Google Sheets

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 📦 Instalador Windows

Para uma instalação mais simples no Windows, utilize o instalador disponível:

🔗 [Download do Instalador Windows](https://drive.google.com/file/d/1KMy8YdF3fSQSAcapXkjzJciRBiyCvMs6/view?usp=drive_link)

### Instalação via Terminal

1. **Clone o repositório ou baixe os arquivos**

```bash
git clone <url-do-repositorio>
cd controlefinanceiroap
```

2. **Instale as dependências**

```bash
pip install -r requirements.txt
```

3. **Execute o dashboard**

```bash
streamlit run dashboard.py
```

O dashboard será aberto automaticamente no navegador em `http://localhost:8501`

---

## ☁️ Configuração do Google Sheets (Opcional)

Para sincronizar seus dados com o Google Sheets e acessá-los de qualquer lugar:

📖 [Manual de Configuração Google Sheets](https://drive.google.com/file/d/1cEqkNrLafyr-xZkhGlq0q1y9m6t0FnEu/view?usp=drive_link)

### Passos Resumidos:

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
2. Ative a API do Google Sheets e Google Drive
3. Crie uma conta de serviço e baixe o arquivo `credentials.json`
4. Coloque o arquivo `credentials.json` na pasta do projeto
5. Crie uma planilha chamada "Controle Financeiro" no Google Sheets
6. Compartilhe a planilha com o email da conta de serviço

---

## 📁 Estrutura do Projeto

```
controlefinanceiroap/
├── Dashboard.py              # Aplicação principal Streamlit
├── dados_financeiros.csv     # Dados locais (modo offline)
├── credentials.json          # Credenciais Google (opcional)
├── requirements.txt          # Dependências do projeto
├── README.md                 # Documentação
└── LICENSE                   # Licença do projeto
```

---

## 🏷️ Categorias Disponíveis

| Categoria      | Tipo            |
|----------------|-----------------|
| Moradia        | Despesa         |
| Alimentação    | Despesa         |
| Transporte     | Despesa         |
| Saúde          | Despesa         |
| Educação       | Despesa         |
| Lazer          | Despesa         |
| Salário        | Receita         |
| Freelance      | Receita         |
| Investimentos  | Receita/Despesa |
| Outros         | Ambos           |

---

## 🔄 Modos de Armazenamento

O Somma utiliza um sistema de armazenamento híbrido com fallback automático:

| Modo | Indicador | Descrição |
|------|-----------|-----------|
| **Google Sheets** | 🟢 | Dados sincronizados na nuvem |
| **CSV Local** | 🟠 | Dados salvos localmente |
| **Memória** | 🔴 | Dados temporários (sem persistência) |

---

## 📊 Dependências

```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.18.0
openpyxl>=3.1.0
gspread>=5.12.0
oauth2client>=4.1.3
```

---

## 🛠️ Tecnologias Utilizadas

- **[Streamlit](https://streamlit.io/)** - Framework para aplicações web em Python
- **[Pandas](https://pandas.pydata.org/)** - Manipulação e análise de dados
- **[Plotly](https://plotly.com/)** - Gráficos interativos
- **[gspread](https://gspread.readthedocs.io/)** - Integração com Google Sheets
- **[OpenPyXL](https://openpyxl.readthedocs.io/)** - Leitura de arquivos Excel

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abrir um Pull Request

---

## 📧 Suporte

Se você encontrar algum problema ou tiver sugestões, abra uma [issue](../../issues) no repositório.

---

<div align="center">
  <p>Desenvolvido com ❤️ para simplificar sua vida financeira</p>
</div>

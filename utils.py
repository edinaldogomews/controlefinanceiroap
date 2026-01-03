"""
Somma - Módulo de Utilitários Compartilhados
Contém todas as funções lógicas, classes e constantes do sistema.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import tempfile
import zipfile

# Imports para Auto-Update
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False

# Imports para Google Sheets (opcional)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from gspread.exceptions import SpreadsheetNotFound, APIError
    GSPREAD_DISPONIVEL = True
except ImportError:
    GSPREAD_DISPONIVEL = False


# ============================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================

# Caminhos do sistema
BASE_DIR = Path(__file__).parent
CAMINHO_CREDENCIAIS = BASE_DIR / "credentials.json"
CAMINHO_CSV = BASE_DIR / "dados_financeiros.csv"
CAMINHO_VERSION = BASE_DIR / "version.txt"
CAMINHO_PREFERENCIAS = BASE_DIR / "preferencias_update.csv"
CAMINHO_CONTAS = BASE_DIR / "contas.json"
CAMINHO_CARTOES = BASE_DIR / "cartoes.json"
NOME_PLANILHA = "Controle Financeiro"

# Estrutura de colunas do sistema
COLUNAS_SISTEMA = ['Data', 'Descricao', 'Categoria', 'Valor', 'Tipo', 'Conta']

# Tipos de Conta / Forma de Pagamento (legado - manter para compatibilidade)
TIPOS_CONTA = ['Conta Comum', 'Vale Refeição']

# Tipos de Grupo de Conta (novo sistema dinâmico)
TIPOS_GRUPO_CONTA = ['Disponível', 'Benefício']

# Mapeamento legado -> novo sistema
MAPEAMENTO_CONTA_LEGADO = {
    'Comum': 'Disponível',
    'Vale Refeição': 'Benefício',
    'VR': 'Benefício'
}

# Categorias específicas para Vale Refeição (Despesa)
CAT_VALE_REFEICAO = [
    'Alimentação',
    'Refeição',
    'Supermercado'
]

# Categorias de DESPESA
CAT_DESPESA = [
    'Moradia',
    'Alimentação',
    'Supermercado',
    'Transporte',
    'Saúde',
    'Educação',
    'Lazer',
    'Roupa',
    'Assinaturas/Serviços',
    'Impostos',
    'Seguros',
    'Internet',
    'Cartão de Crédito',
    'Empréstimos',
    'Outros (Despesa)'
]

# Categorias de RECEITA
CAT_RECEITA = [
    'Salário',
    'Freelance',
    'Investimentos',
    'Dividendos',
    'Aluguel Recebido',
    'Vendas',
    'Bônus',
    'Restituição IR',
    'Presente/Doação',
    'Outros (Receita)'
]

# Lista combinada para compatibilidade
CATEGORIAS_PADRAO = CAT_DESPESA + CAT_RECEITA

# Tipos de transação
TIPOS_TRANSACAO = ['Despesa', 'Receita']

# ============================================================
# CATÁLOGO DE BANCOS (Cores e Logos)
# ============================================================

# Função para gerar logo SVG em base64
def _gerar_logo_svg(inicial: str, cor_fundo: str, cor_texto: str = "#FFFFFF") -> str:
    """Gera um logo SVG circular com a inicial do banco em base64."""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="24" fill="{cor_fundo}"/>
        <text x="25" y="32" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="{cor_texto}" text-anchor="middle">{inicial}</text>
    </svg>'''
    import base64
    svg_bytes = svg.encode('utf-8')
    b64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

def _carregar_logo_local(nome_arquivo: str, fallback_inicial: str, cor_fundo: str, cor_texto: str = "#FFFFFF") -> str:
    """Carrega um logo SVG local da pasta assets e retorna como data URL base64.
    Se o arquivo não existir, gera um logo genérico com a inicial."""
    import base64
    import os

    # Caminho para a pasta assets
    pasta_assets = os.path.join(os.path.dirname(__file__), 'assets')
    caminho_arquivo = os.path.join(pasta_assets, nome_arquivo)

    if os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'rb') as f:
                conteudo = f.read()
            b64 = base64.b64encode(conteudo).decode('utf-8')
            # Detectar tipo de arquivo
            if nome_arquivo.endswith('.svg'):
                return f"data:image/svg+xml;base64,{b64}"
            elif nome_arquivo.endswith('.png'):
                return f"data:image/png;base64,{b64}"
            else:
                return f"data:image/svg+xml;base64,{b64}"
        except:
            pass

    # Fallback: gerar logo genérico
    return _gerar_logo_svg(fallback_inicial, cor_fundo, cor_texto)

CATALOGO_BANCOS = {
    "Nubank": {
        "nome": "Nubank",
        "cor_hex": "#820AD1",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("nubank.svg", "Nu", "#820AD1")
    },
    "Inter": {
        "nome": "Banco Inter",
        "cor_hex": "#FF7A00",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("inter.svg", "BI", "#FF7A00")
    },
    "Itau": {
        "nome": "Itaú",
        "cor_hex": "#EC7000",
        "cor_secundaria": "#003399",
        "logo_url": _carregar_logo_local("itau.svg", "Itaú", "#EC7000", "#003399")
    },
    "Bradesco": {
        "nome": "Bradesco",
        "cor_hex": "#CC092F",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("bradesco.svg", "B", "#CC092F")
    },
    "Santander": {
        "nome": "Santander",
        "cor_hex": "#EC0000",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("santander.svg", "S", "#EC0000")
    },
    "BancoDoBrasil": {
        "nome": "Banco do Brasil",
        "cor_hex": "#FFCC00",
        "cor_secundaria": "#003882",
        "logo_url": _carregar_logo_local("bb.svg", "BB", "#FFCC00", "#003882")
    },
    "Caixa": {
        "nome": "Caixa Econômica",
        "cor_hex": "#005CA9",
        "cor_secundaria": "#F37021",
        "logo_url": _carregar_logo_local("caixa.svg", "CEF", "#005CA9")
    },
    "C6Bank": {
        "nome": "C6 Bank",
        "cor_hex": "#1A1A1A",
        "cor_secundaria": "#FFCC00",
        "logo_url": _carregar_logo_local("c6.svg", "C6", "#1A1A1A", "#FFCC00")
    },
    "BTG": {
        "nome": "BTG Pactual",
        "cor_hex": "#001E50",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _gerar_logo_svg("BTG", "#001E50")
    },
    "XP": {
        "nome": "XP Investimentos",
        "cor_hex": "#1E1E1E",
        "cor_secundaria": "#D4AF37",
        "logo_url": _gerar_logo_svg("XP", "#1E1E1E", "#D4AF37")
    },
    "Neon": {
        "nome": "Neon",
        "cor_hex": "#00E5A0",
        "cor_secundaria": "#1A1A1A",
        "logo_url": _gerar_logo_svg("N", "#00E5A0", "#1A1A1A")
    },
    "PicPay": {
        "nome": "PicPay",
        "cor_hex": "#21C25E",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("picpay.svg", "PP", "#21C25E")
    },
    "iFood": {
        "nome": "iFood Benefícios",
        "cor_hex": "#EA1D2C",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _carregar_logo_local("ifood.svg", "iF", "#EA1D2C")
    },
    "Outro": {
        "nome": "Outro Banco",
        "cor_hex": "#607D8B",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _gerar_logo_svg("$", "#607D8B")
    },
    "Dinheiro": {
        "nome": "Dinheiro em Espécie",
        "cor_hex": "#4CAF50",
        "cor_secundaria": "#FFFFFF",
        "logo_url": _gerar_logo_svg("$", "#4CAF50")
    }
}

# Lista de bancos para selectbox
LISTA_BANCOS = list(CATALOGO_BANCOS.keys())

# Configurações de Auto-Update
GITHUB_OWNER = "edinaldogomews"
GITHUB_REPO = "controlefinanceiroap"
GITHUB_BRANCH = "main"

# Arquivos protegidos durante atualização
ARQUIVOS_PROTEGIDOS = [
    'credentials.json',
    'credenciais.json',
    'dados_financeiros.csv',
    'preferencias_update.csv',
    '.env',
    'venv',
    '.venv',
    '__pycache__',
]


# ============================================================
# CSS GLOBAL
# ============================================================
CSS_GLOBAL = """
    <style>
        /* ===== OCULTAR ELEMENTOS PADRÃO DO STREAMLIT ===== */
        .stDeployButton { display: none !important; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }

        /* ===== AJUSTES DE ESPAÇAMENTO ===== */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

        /* ===== ESTILIZAÇÃO DOS CARDS/MÉTRICAS ===== */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* ===== ESTILIZAÇÃO DA SIDEBAR ===== */
        hr { border: none; border-top: 1px solid #e9ecef; margin: 1rem 0; }

        /* ===== MELHORIAS NOS BOTÕES ===== */
        .stButton > button {
            transition: all 0.3s ease;
            border-radius: 8px;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* ===== TABELA DE DADOS ===== */
        .stDataFrame { border-radius: 10px; overflow: hidden; }

        /* ===== ESTILO DO AVISO DE ATUALIZAÇÃO ===== */
        .update-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            color: white;
        }

        /* ===== BOTÃO FLUTUANTE (FAB) ===== */
        .fab-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
        }

        .fab-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
            border: none;
            color: white;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(46, 134, 171, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .fab-button:hover {
            transform: scale(1.1) rotate(90deg);
            box-shadow: 0 6px 20px rgba(46, 134, 171, 0.6);
        }

        .fab-button:active {
            transform: scale(0.95);
        }
    </style>
"""

LOGO_SIDEBAR = """
    <div style="text-align: left; padding: 20px 5px;">
        <h1 style="
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: -1px;
        ">
            Somma<span style="color: #2E86AB;">.</span>
        </h1>
        <p style="
            color: #CCCCCC;
            font-size: 0.75rem;
            margin-top: -5px;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 2px;
        ">Financeiro</p>
    </div>
"""


# ============================================================
# FUNÇÕES AUXILIARES DE UI
# ============================================================
def aplicar_estilo_global():
    """Aplica o CSS global e o logo na sidebar."""
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
    st.sidebar.markdown(LOGO_SIDEBAR, unsafe_allow_html=True)
    st.sidebar.markdown("---")


# ============================================================
# MODAL DE GESTÃO GLOBAL (Novo Lançamento)
# ============================================================
@st.dialog("Gestão de Lançamentos", width="large")
def modal_gestao(armazenamento):
    """Modal global para adicionar, editar e excluir transações."""
    from datetime import date

    # Carregar dados
    df = armazenamento.carregar_dados()

    # Carregar contas e cartões do usuário
    contas_usuario = carregar_contas()
    cartoes_usuario = carregar_cartoes()

    # Montar lista de opções de conta/cartão
    opcoes_conta = []
    mapa_contas = {}  # Para mapear nome exibido -> valor a salvar

    # Adicionar contas bancárias
    for conta in contas_usuario:
        nome_exibir = f"🏦 {conta['nome']} ({conta['banco_nome']})"
        opcoes_conta.append(nome_exibir)
        mapa_contas[nome_exibir] = conta['nome']

    # Adicionar cartões de crédito
    for cartao in cartoes_usuario:
        nome_exibir = f"💳 {cartao['nome']} ({cartao['banco_nome']})"
        opcoes_conta.append(nome_exibir)
        mapa_contas[nome_exibir] = cartao['nome']

    # Se não houver contas/cartões cadastrados, usar opções padrão
    if not opcoes_conta:
        opcoes_conta = TIPOS_CONTA
        mapa_contas = {c: c for c in TIPOS_CONTA}

    # Criar abas
    aba_nova, aba_editar, aba_excluir = st.tabs(["➕ Nova", "✏️ Editar", "🗑️ Excluir"])

    # ========== ABA 1: NOVA TRANSAÇÃO ==========
    with aba_nova:
        st.subheader("Nova Transação")

        with st.form(key="form_modal_nova", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                nova_conta = st.selectbox(
                    "Conta/Cartão",
                    options=opcoes_conta,
                    key="modal_conta"
                )

            with col2:
                novo_tipo = st.selectbox(
                    "Tipo",
                    options=TIPOS_TRANSACAO,
                    key="modal_tipo"
                )

            col3, col4 = st.columns(2)

            with col3:
                nova_data = st.date_input(
                    "Data",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    key="modal_data"
                )

            with col4:
                novo_valor = st.number_input(
                    "Valor (R$)",
                    min_value=0.01,
                    value=None,
                    step=0.01,
                    format="%.2f",
                    placeholder="0.00",
                    key="modal_valor"
                )

            # Categorias baseadas no tipo
            if novo_tipo == "Receita":
                categorias = CAT_RECEITA
            else:
                categorias = CAT_DESPESA

            nova_categoria = st.selectbox(
                "Categoria",
                options=categorias,
                key="modal_categoria"
            )

            nova_descricao = st.text_input(
                "Descrição",
                placeholder="Ex: Salário, Conta de Luz, etc.",
                key="modal_descricao"
            )

            submit_nova = st.form_submit_button(
                "💾 Salvar",
                use_container_width=True,
                type="primary"
            )

            if submit_nova:
                if not nova_descricao.strip():
                    st.error("A descrição é obrigatória!")
                elif novo_valor is None or novo_valor <= 0:
                    st.error("O valor deve ser maior que zero!")
                else:
                    # Obter o nome real da conta/cartão para salvar
                    conta_salvar = mapa_contas.get(nova_conta, nova_conta)

                    sucesso, mensagem = armazenamento.salvar_transacao(
                        nova_data,
                        nova_descricao.strip(),
                        nova_categoria,
                        novo_valor,
                        novo_tipo,
                        conta_salvar
                    )

                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {mensagem}")

    # ========== ABA 2: EDITAR TRANSAÇÃO ==========
    with aba_editar:
        st.subheader("Editar Transação")

        if df.empty:
            st.info("Nenhuma transação para editar.")
        else:
            # Pegar últimas 10 transações (mais recentes)
            df_edit = df.copy()
            df_edit['Data'] = pd.to_datetime(df_edit['Data'], errors='coerce')
            df_edit = df_edit.sort_values('Data', ascending=False).head(10).reset_index(drop=True)

            # Selecionar transação
            opcoes_edit = []
            for idx, row in df_edit.iterrows():
                data_fmt = row['Data'].strftime('%d/%m') if pd.notna(row['Data']) else '—'
                valor_fmt = formatar_valor_br(row['Valor'])
                desc = str(row['Descricao'])[:25]
                emoji = "🟢" if row['Tipo'] == 'Receita' else "🔴"
                opcoes_edit.append(f"{emoji} {data_fmt} | {desc} | {valor_fmt}")

            idx_selecionado = st.selectbox(
                "Selecione a transação:",
                options=range(len(opcoes_edit)),
                format_func=lambda x: opcoes_edit[x],
                key="modal_edit_select"
            )

            if idx_selecionado is not None:
                row_edit = df_edit.iloc[idx_selecionado]

                # Encontrar índice original no DataFrame completo
                df_original = df.reset_index(drop=True)
                idx_original = df_original[
                    (df_original['Descricao'] == row_edit['Descricao']) &
                    (df_original['Valor'] == row_edit['Valor'])
                ].index
                idx_original = idx_original[0] if len(idx_original) > 0 else 0

                with st.form(key="form_modal_editar"):
                    col1, col2 = st.columns(2)

                    with col1:
                        data_valor = row_edit['Data'].date() if pd.notna(row_edit['Data']) else date.today()
                        edit_data = st.date_input("Data", value=data_valor, format="DD/MM/YYYY")

                    with col2:
                        edit_valor = st.number_input(
                            "Valor",
                            min_value=0.01,
                            value=float(row_edit['Valor']),
                            step=0.01,
                            format="%.2f"
                        )

                    edit_descricao = st.text_input("Descrição", value=str(row_edit['Descricao']))

                    col3, col4 = st.columns(2)

                    with col3:
                        tipo_atual = str(row_edit['Tipo'])
                        idx_tipo = TIPOS_TRANSACAO.index(tipo_atual) if tipo_atual in TIPOS_TRANSACAO else 0
                        edit_tipo = st.selectbox("Tipo", options=TIPOS_TRANSACAO, index=idx_tipo)

                    with col4:
                        # Encontrar a conta atual na lista de opções
                        conta_atual = str(row_edit['Conta'])
                        idx_conta = 0
                        for i, opt in enumerate(opcoes_conta):
                            if conta_atual in opt or mapa_contas.get(opt, '') == conta_atual:
                                idx_conta = i
                                break
                        edit_conta = st.selectbox("Conta/Cartão", options=opcoes_conta, index=idx_conta)

                    # Categoria
                    if edit_tipo == "Receita":
                        cats_edit = CAT_RECEITA
                    else:
                        cats_edit = CAT_DESPESA

                    cat_atual = str(row_edit['Categoria'])
                    if cat_atual not in cats_edit:
                        cats_edit = cats_edit + [cat_atual]
                    idx_cat = cats_edit.index(cat_atual) if cat_atual in cats_edit else 0
                    edit_categoria = st.selectbox("Categoria", options=cats_edit, index=idx_cat)

                    submit_edit = st.form_submit_button(
                        "💾 Salvar Alterações",
                        use_container_width=True,
                        type="primary"
                    )

                    if submit_edit:
                        if not edit_descricao.strip():
                            st.error("A descrição é obrigatória!")
                        elif edit_valor <= 0:
                            st.error("O valor deve ser maior que zero!")
                        else:
                            conta_salvar = mapa_contas.get(edit_conta, edit_conta)

                            sucesso, mensagem = armazenamento.editar_transacao(
                                idx_original,
                                edit_data,
                                edit_descricao.strip(),
                                edit_categoria,
                                edit_valor,
                                edit_tipo,
                                conta_salvar
                            )

                            if sucesso:
                                st.success(f"✅ {mensagem}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ {mensagem}")

    # ========== ABA 3: EXCLUIR TRANSAÇÃO ==========
    with aba_excluir:
        st.subheader("Excluir Transação")

        if df.empty:
            st.info("Nenhuma transação para excluir.")
        else:
            # Pegar últimas 10 transações
            df_del = df.copy()
            df_del['Data'] = pd.to_datetime(df_del['Data'], errors='coerce')
            df_del = df_del.sort_values('Data', ascending=False).head(10).reset_index(drop=True)

            st.caption("Clique no botão 🗑️ para excluir a transação.")

            for idx, row in df_del.iterrows():
                # Encontrar índice original
                df_original = df.reset_index(drop=True)
                idx_original = df_original[
                    (df_original['Descricao'] == row['Descricao']) &
                    (df_original['Valor'] == row['Valor'])
                ].index
                idx_original = idx_original[0] if len(idx_original) > 0 else 0

                data_fmt = row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else '—'
                valor_fmt = formatar_valor_br(row['Valor'])
                desc = str(row['Descricao'])[:20]
                emoji = "🟢" if row['Tipo'] == 'Receita' else "🔴"

                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(f"**{emoji} {data_fmt}** | {desc} | {valor_fmt}")

                with col2:
                    if st.button("🗑️", key=f"del_{idx}_{idx_original}", help="Excluir"):
                        sucesso, mensagem = armazenamento.excluir_transacao(idx_original)
                        if sucesso:
                            st.success("Excluído!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(mensagem)

                st.divider()


def exibir_botao_novo_lancamento(armazenamento):
    """Exibe o botão flutuante de Novo Lançamento no canto inferior direito."""

    # Inicializar estado do modal se não existir
    if 'show_novo_lancamento_modal' not in st.session_state:
        st.session_state['show_novo_lancamento_modal'] = False

    # Verificar query params (para o clique do botão flutuante)
    query_params = st.query_params
    if query_params.get("fab_click") == "1":
        st.query_params.clear()
        st.session_state['show_novo_lancamento_modal'] = True
        st.rerun()

    # Verificar se deve abrir o modal
    if st.session_state.get('show_novo_lancamento_modal', False):
        st.session_state['show_novo_lancamento_modal'] = False
        modal_gestao(armazenamento)

    # Injetar CSS e HTML para criar o botão flutuante
    st.markdown("""
        <style>
        /* ===== BOTÃO FLUTUANTE FAB - NOVO LANÇAMENTO ===== */

        /* Container do botão - posição fixa */
        #fab-novo-lancamento-container {
            position: fixed !important;
            bottom: 40px !important;
            right: 40px !important;
            z-index: 999999 !important;
            pointer-events: auto !important;
        }

        /* Estilo do botão circular */
        #fab-novo-lancamento {
            width: 70px !important;
            height: 70px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%) !important;
            border: none !important;
            color: white !important;
            font-size: 36px !important;
            font-weight: 300 !important;
            cursor: pointer !important;
            box-shadow: 0 6px 25px rgba(46, 134, 171, 0.7) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-decoration: none !important;
            line-height: 1 !important;
            padding: 0 !important;
            margin: 0 !important;
            outline: none !important;
        }

        #fab-novo-lancamento:hover {
            transform: scale(1.15) rotate(90deg) !important;
            box-shadow: 0 10px 35px rgba(46, 134, 171, 0.9) !important;
            background: linear-gradient(135deg, #3498db 0%, #2E86AB 100%) !important;
        }

        #fab-novo-lancamento:active {
            transform: scale(0.95) !important;
        }

        /* Tooltip customizado */
        #fab-novo-lancamento::after {
            content: 'Novo Lançamento';
            position: absolute;
            right: 85px;
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: normal;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
        }

        #fab-novo-lancamento:hover::after {
            opacity: 1;
        }
        </style>

        <div id="fab-novo-lancamento-container">
            <a href="?fab_click=1" id="fab-novo-lancamento" title="Novo Lançamento" target="_self">
                +
            </a>
        </div>
    """, unsafe_allow_html=True)


def exibir_menu_lateral(armazenamento):
    """Exibe o menu lateral completo com botão de ação global flutuante."""
    exibir_botao_novo_lancamento(armazenamento)


def exibir_rodape(versao_local: str = None):
    """Exibe o rodapé da sidebar com informações de versão."""
    if versao_local is None:
        versao_local = ler_versao_local()
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div style="font-size: 0.85rem; color: #888; line-height: 1.5;">
            <p style="margin: 3px 0;">Desenvolvido por Edinaldo Gomes</p>
            <p style="margin: 3px 0;">📧 edinaldosantos.contato@gmail.com</p>
            <p style="margin: 3px 0;">📦 Versão: {versao_local}</p>
            <p style="margin: 3px 0;">© 2025 Todos os direitos reservados</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def exibir_status_conexao(armazenamento):
    """Exibe o badge de status de conexão na sidebar, abaixo do logo."""
    modo_texto, modo_tipo, is_online = armazenamento.get_modo_info()

    if is_online:
        st.sidebar.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #d4edda, #c3e6cb);
                border: 1px solid #28a745;
                border-radius: 15px;
                padding: 5px 12px;
                display: inline-block;
                margin-bottom: 10px;
            ">
                <span style="color: #155724; font-weight: 600; font-size: 0.55rem;">
                    {modo_texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        cor_fundo = "#fff3cd" if modo_tipo == "warning" else "#f8d7da"
        cor_borda = "#ffc107" if modo_tipo == "warning" else "#dc3545"
        cor_texto = "#856404" if modo_tipo == "warning" else "#721c24"

        st.sidebar.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, {cor_fundo}, {cor_fundo});
                border: 1px solid {cor_borda};
                border-radius: 15px;
                padding: 5px 12px;
                display: inline-block;
                margin-bottom: 10px;
            ">
                <span style="color: {cor_texto}; font-weight: 600; font-size: 0.55rem;">
                    {modo_texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


def formatar_valor_br(valor: float) -> str:
    """Formata um valor numérico para o padrão brasileiro (R$ X.XXX,XX)."""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_mes_ano_completo(periodo: str) -> str:
    """Converte período YYYY-MM para formato 'Mês/Ano' (ex: Janeiro/2026)."""
    try:
        if pd.isna(periodo) or periodo == 'NaT':
            return 'Sem data'
        ano, mes = periodo.split('-')
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        return f"{meses[int(mes)-1]}/{ano}"
    except:
        return 'Sem data'


def formatar_mes_curto(periodo: str) -> str:
    """Converte período YYYY-MM para formato 'Mmm/AA' (ex: Jan/26)."""
    try:
        ano, mes = periodo.split('-')
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        return f"{meses[int(mes)-1]}/{ano[2:]}"
    except:
        return periodo


# ============================================================
# FUNÇÕES DE CÁLCULO DE SALDOS
# ============================================================
def calcular_saldos(df: pd.DataFrame) -> dict:
    """
    Calcula todos os saldos separados por conta.

    Returns:
        dict com: saldo_comum, saldo_vr, receitas_comum, despesas_comum,
                  receitas_vr, despesas_vr, tem_transacoes_vr, mostrar_card_vr
    """
    # Saldo Conta Comum
    df_conta_comum = df[df['Conta'] == 'Comum']
    receitas_comum = df_conta_comum[df_conta_comum['Tipo'] == 'Receita']['Valor'].sum()
    despesas_comum = df_conta_comum[df_conta_comum['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_comum = receitas_comum - despesas_comum

    # Saldo Vale Refeição
    df_conta_vr = df[df['Conta'] == 'Vale Refeição']
    receitas_vr = df_conta_vr[df_conta_vr['Tipo'] == 'Receita']['Valor'].sum()
    despesas_vr = df_conta_vr[df_conta_vr['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_vr = receitas_vr - despesas_vr

    # Verificar se deve mostrar card VR
    tem_transacoes_vr = len(df_conta_vr) > 0
    mostrar_card_vr = tem_transacoes_vr or saldo_vr != 0

    return {
        'saldo_comum': saldo_comum,
        'saldo_vr': saldo_vr,
        'receitas_comum': receitas_comum,
        'despesas_comum': despesas_comum,
        'receitas_vr': receitas_vr,
        'despesas_vr': despesas_vr,
        'tem_transacoes_vr': tem_transacoes_vr,
        'mostrar_card_vr': mostrar_card_vr
    }


def calcular_totais_periodo(df: pd.DataFrame) -> dict:
    """
    Calcula receitas e despesas totais de um DataFrame.

    Returns:
        dict com: total_receitas, total_despesas, saldo
    """
    total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()

    return {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': total_receitas - total_despesas
    }


# ============================================================
# FUNÇÕES DE VERSÃO E ATUALIZAÇÃO
# ============================================================
def ler_versao_local() -> str:
    """Lê a versão do arquivo local version.txt."""
    try:
        if CAMINHO_VERSION.exists():
            return CAMINHO_VERSION.read_text(encoding='utf-8').strip()
        return "0.0.0"
    except Exception:
        return "0.0.0"


# ============================================================
# SISTEMA DE AUTO-UPDATE
# ============================================================
class AutoUpdate:
    """Sistema de atualização automática via GitHub."""

    def __init__(self):
        self.versao_local = ler_versao_local()
        self.versao_remota = None
        self.url_zip = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
        self.url_version = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/version.txt"

    def verificar_atualizacao(self) -> tuple:
        """Verifica se há nova versão disponível."""
        if not REQUESTS_DISPONIVEL:
            return False, self.versao_local, "Biblioteca 'requests' não instalada."

        try:
            response = requests.get(self.url_version, timeout=10)
            response.raise_for_status()
            self.versao_remota = response.text.strip()

            if self.versao_remota != self.versao_local:
                return True, self.versao_remota, f"Nova versão disponível: {self.versao_remota}"
            else:
                return False, self.versao_remota, "Você está usando a versão mais recente."

        except requests.exceptions.Timeout:
            return False, self.versao_local, "Tempo limite excedido ao verificar atualizações."
        except requests.exceptions.ConnectionError:
            return False, self.versao_local, "Sem conexão com a internet."
        except Exception as e:
            return False, self.versao_local, f"Erro ao verificar: {str(e)}"

    def realizar_update(self, progress_callback=None) -> tuple:
        """Realiza o download e instalação da atualização."""
        if not REQUESTS_DISPONIVEL:
            return False, "Biblioteca 'requests' não instalada."

        pasta_app = BASE_DIR
        pasta_temp = None

        try:
            if progress_callback:
                progress_callback("📥 Baixando atualização...", 0.1)

            response = requests.get(self.url_zip, timeout=60, stream=True)
            response.raise_for_status()

            pasta_temp = Path(tempfile.mkdtemp())
            caminho_zip = pasta_temp / "update.zip"

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(caminho_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            progress = 0.1 + (downloaded / total_size) * 0.3
                            progress_callback(f"📥 Baixando... {downloaded // 1024} KB", progress)

            if progress_callback:
                progress_callback("📦 Extraindo arquivos...", 0.45)

            pasta_extracao = pasta_temp / "extracted"
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_extracao)

            pastas_extraidas = list(pasta_extracao.iterdir())
            if not pastas_extraidas:
                return False, "Arquivo ZIP vazio ou corrompido."

            pasta_repo = pastas_extraidas[0]

            if progress_callback:
                progress_callback("🔄 Atualizando arquivos...", 0.6)

            arquivos_atualizados = 0

            for item in pasta_repo.iterdir():
                nome_item = item.name

                if nome_item in ARQUIVOS_PROTEGIDOS:
                    continue

                destino = pasta_app / nome_item

                try:
                    if item.is_file():
                        shutil.copy2(item, destino)
                        arquivos_atualizados += 1
                    elif item.is_dir():
                        if destino.exists():
                            shutil.rmtree(destino)
                        shutil.copytree(item, destino)
                        arquivos_atualizados += 1
                except Exception as e:
                    print(f"Aviso: Não foi possível atualizar {nome_item}: {e}")

            if progress_callback:
                progress_callback("🧹 Limpando arquivos temporários...", 0.9)

            try:
                shutil.rmtree(pasta_temp)
            except Exception:
                pass

            if progress_callback:
                progress_callback("✅ Atualização concluída!", 1.0)

            return True, f"Atualização concluída! {arquivos_atualizados} arquivos atualizados."

        except requests.exceptions.Timeout:
            return False, "Tempo limite excedido durante o download."
        except requests.exceptions.ConnectionError:
            return False, "Falha na conexão durante o download."
        except zipfile.BadZipFile:
            return False, "Arquivo de atualização corrompido."
        except PermissionError:
            return False, "Sem permissão para atualizar arquivos. Execute como administrador."
        except Exception as e:
            return False, f"Erro durante atualização: {str(e)}"
        finally:
            if pasta_temp and pasta_temp.exists():
                try:
                    shutil.rmtree(pasta_temp)
                except Exception:
                    pass


# ============================================================
# FUNÇÕES DE PREFERÊNCIAS DE ATUALIZAÇÃO
# ============================================================
def carregar_preferencias_update() -> dict:
    """Carrega preferências de atualização do usuário."""
    try:
        if CAMINHO_PREFERENCIAS.exists():
            df = pd.read_csv(CAMINHO_PREFERENCIAS)
            if not df.empty:
                return df.iloc[0].to_dict()
    except Exception:
        pass

    return {
        'nao_perguntar': False,
        'lembrar_depois': False,
        'lembrar_data': '',
        'versao_ignorada': ''
    }


def salvar_preferencias_update(preferencias: dict):
    """Salva preferências de atualização do usuário."""
    try:
        df = pd.DataFrame([preferencias])
        df.to_csv(CAMINHO_PREFERENCIAS, index=False)
    except Exception:
        pass


def deve_mostrar_atualizacao(versao_remota: str) -> bool:
    """Verifica se deve mostrar o aviso de atualização."""
    prefs = carregar_preferencias_update()

    if prefs.get('nao_perguntar') and prefs.get('versao_ignorada') == versao_remota:
        return False

    if prefs.get('lembrar_depois') and prefs.get('lembrar_data'):
        try:
            data_lembrar = datetime.fromisoformat(prefs['lembrar_data'])
            if datetime.now() < data_lembrar:
                return False
        except Exception:
            pass

    return True


def resetar_preferencias_update():
    """Reseta as preferências de atualização."""
    try:
        if CAMINHO_PREFERENCIAS.exists():
            CAMINHO_PREFERENCIAS.unlink()
    except Exception:
        pass


# ============================================================
# SISTEMA DE ARMAZENAMENTO HÍBRIDO
# ============================================================
class ArmazenamentoHibrido:
    """
    Sistema de armazenamento com fallback:
    1. Google Sheets (se credentials.json existir)
    2. CSV Local (se não houver credenciais ou falhar conexão)
    3. DataFrame vazio (se não houver dados)
    """

    def __init__(self):
        self.modo = None
        self.worksheet = None
        self._detectar_modo()

    def _detectar_modo(self):
        """Detecta qual modo de armazenamento usar."""
        if CAMINHO_CREDENCIAIS.exists() and GSPREAD_DISPONIVEL:
            try:
                self.worksheet = self._conectar_gsheets()
                if self.worksheet is not None:
                    self.modo = 'gsheets'
                    return
            except Exception:
                pass

        if CAMINHO_CSV.exists():
            self.modo = 'csv'
            return

        self.modo = 'memoria'

    def _conectar_gsheets(self):
        """Conecta ao Google Sheets usando credenciais."""
        try:
            scopes = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credenciais = None

            try:
                credenciais_dict = st.secrets["gcp_service_account"]
                credenciais = ServiceAccountCredentials.from_json_keyfile_dict(
                    dict(credenciais_dict), scopes
                )
            except (KeyError, FileNotFoundError):
                if CAMINHO_CREDENCIAIS.exists():
                    credenciais = ServiceAccountCredentials.from_json_keyfile_name(
                        str(CAMINHO_CREDENCIAIS), scopes
                    )

            if credenciais is None:
                return None

            cliente = gspread.authorize(credenciais)
            planilha = cliente.open(NOME_PLANILHA)
            return planilha.get_worksheet(0)

        except Exception:
            return None

    def get_modo_info(self):
        """Retorna informações sobre o modo atual."""
        modos = {
            'gsheets': ('🟢 Conectado à Nuvem (Google Sheets)', 'success', True),
            'csv': ('🟠 Modo Offline (CSV Local)', 'warning', False),
            'memoria': ('🔴 Memória Temporária (sem persistência)', 'error', False)
        }
        return modos.get(self.modo, ('❓ Desconhecido', 'error', False))

    def carregar_dados(self):
        """Carrega dados de acordo com o modo atual."""
        if self.modo == 'gsheets':
            return self._carregar_gsheets()
        elif self.modo == 'csv':
            return self._carregar_csv()
        else:
            return self._criar_df_vazio()

    def _carregar_gsheets(self):
        """Carrega dados do Google Sheets."""
        try:
            if self.worksheet is None:
                self.worksheet = self._conectar_gsheets()

            if self.worksheet is None:
                self.modo = 'csv'
                return self._carregar_csv()

            registros = self.worksheet.get_all_records()

            if not registros:
                return self._criar_df_vazio()

            df = pd.DataFrame(registros)
            return self._normalizar_dados(df)

        except Exception:
            self.modo = 'csv'
            return self._carregar_csv()

    def _carregar_csv(self):
        """Carrega dados do arquivo CSV local."""
        try:
            if not CAMINHO_CSV.exists():
                return self._criar_df_vazio()

            df = pd.read_csv(CAMINHO_CSV)

            if df.empty:
                return self._criar_df_vazio()

            return self._normalizar_dados(df)

        except Exception:
            return self._criar_df_vazio()

    def _criar_df_vazio(self):
        """Cria um DataFrame vazio com a estrutura correta."""
        return pd.DataFrame(columns=COLUNAS_SISTEMA)

    def _normalizar_dados(self, df):
        """Normaliza o DataFrame para a estrutura padrão do sistema."""
        mapeamento = {
            'Vencimento': 'Data', 'data': 'Data', 'DATA': 'Data',
            'Descrição': 'Descricao', 'descricao': 'Descricao', 'DESCRICAO': 'Descricao',
            'categoria': 'Categoria', 'CATEGORIA': 'Categoria',
            'valor': 'Valor', 'VALOR': 'Valor',
            'tipo': 'Tipo', 'TIPO': 'Tipo', 'Status': 'Tipo',
            'conta': 'Conta', 'CONTA': 'Conta'
        }

        df = df.rename(columns=mapeamento)

        for col in COLUNAS_SISTEMA:
            if col not in df.columns:
                if col == 'Tipo':
                    df[col] = 'Despesa'
                elif col == 'Conta':
                    df[col] = 'Comum'
                else:
                    df[col] = ''

        df = df[[col for col in COLUNAS_SISTEMA if col in df.columns]]
        df = df.dropna(how='all')
        df['Valor'] = df['Valor'].apply(self._limpar_valor)

        # Converter data - primeiro tenta formato ISO (YYYY-MM-DD), depois outros formatos
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce', format='mixed', dayfirst=False)
        df['Descricao'] = df['Descricao'].fillna('').astype(str)
        df['Categoria'] = df['Categoria'].fillna('Outros').replace('', 'Outros')
        df['Tipo'] = df['Tipo'].fillna('Despesa').replace('', 'Despesa')
        df['Conta'] = df['Conta'].fillna('Comum').replace('', 'Comum')
        df['Tipo'] = df['Tipo'].apply(self._normalizar_tipo)
        df['Conta'] = df['Conta'].apply(self._normalizar_conta)
        df = df[df['Descricao'].str.strip() != '']

        return df.reset_index(drop=True)

    def _limpar_valor(self, valor):
        """Limpa e converte valor para float."""
        if pd.isna(valor) or valor == '':
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        valor_str = str(valor).replace('R$', '').strip().replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except ValueError:
            return 0.0

    def _normalizar_tipo(self, tipo):
        """Normaliza o tipo de transação."""
        tipo_str = str(tipo).strip().upper()
        if tipo_str in ['RECEITA', 'ENTRADA', 'CRÉDITO', 'CREDITO']:
            return 'Receita'
        elif tipo_str in ['DESPESA', 'SAÍDA', 'SAIDA', 'DÉBITO', 'DEBITO', 'PAGO', 'EM ABERTO']:
            return 'Despesa'
        return 'Despesa'

    def _normalizar_conta(self, conta):
        """Normaliza o valor da conta para o formato interno."""
        conta_str = str(conta).strip().upper()
        if conta_str in ['VALE REFEIÇÃO', 'VALE REFEICAO', 'VR', 'VALE-REFEIÇÃO', 'VALE-REFEICAO']:
            return 'Vale Refeição'
        elif conta_str in ['CONTA COMUM', 'COMUM', 'PRINCIPAL', '']:
            return 'Comum'
        return 'Comum'

    def salvar_dados(self, df):
        """Salva o DataFrame completo no armazenamento atual."""
        if self.modo == 'gsheets':
            return self._salvar_dados_gsheets(df)
        elif self.modo == 'csv':
            return self._salvar_dados_csv(df)
        else:
            return self._salvar_dados_memoria(df)

    def _salvar_dados_gsheets(self, df):
        """Salva DataFrame completo no Google Sheets."""
        try:
            if self.worksheet is None:
                self.worksheet = self._conectar_gsheets()

            if self.worksheet is None:
                self.modo = 'csv'
                return self._salvar_dados_csv(df)

            df_export = df.copy()
            df_export['Data'] = df_export['Data'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
            )
            df_export['Valor'] = df_export['Valor'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )

            self.worksheet.clear()
            self.worksheet.append_row(COLUNAS_SISTEMA)

            if not df_export.empty:
                dados = df_export.values.tolist()
                self.worksheet.append_rows(dados)

            return True, "Dados salvos com sucesso no Google Sheets!"

        except Exception as e:
            return False, f"Erro ao salvar no Google Sheets: {str(e)}"

    def _salvar_dados_csv(self, df):
        """Salva DataFrame completo no arquivo CSV."""
        try:
            df_export = df.copy()
            if 'Data' in df_export.columns:
                df_export['Data'] = df_export['Data'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
                )
            df_export.to_csv(CAMINHO_CSV, index=False)
            return True, "Dados salvos com sucesso no arquivo CSV!"
        except Exception as e:
            return False, f"Erro ao salvar no CSV: {str(e)}"

    def _salvar_dados_memoria(self, df):
        """Salva dados criando um novo arquivo CSV."""
        try:
            sucesso, mensagem = self._salvar_dados_csv(df)
            if sucesso:
                self.modo = 'csv'
                return True, "Arquivo CSV criado com sucesso! Dados salvos."
            return sucesso, mensagem
        except Exception as e:
            return False, f"Erro ao criar arquivo: {str(e)}"

    def salvar_transacao(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma nova transação."""
        if self.modo == 'gsheets':
            return self._salvar_transacao_gsheets(data, descricao, categoria, valor, tipo, conta)
        elif self.modo == 'csv':
            return self._salvar_transacao_csv(data, descricao, categoria, valor, tipo, conta)
        else:
            return self._salvar_transacao_memoria(data, descricao, categoria, valor, tipo, conta)

    def _salvar_transacao_gsheets(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma transação no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão com Google Sheets."

            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            nova_linha = [data_formatada, descricao, categoria, valor_formatado, tipo, conta]
            self.worksheet.append_row(nova_linha)

            return True, "Transação salva com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_csv(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma transação no arquivo CSV."""
        try:
            if CAMINHO_CSV.exists():
                df = pd.read_csv(CAMINHO_CSV)
                df = self._normalizar_dados(df)
            else:
                df = self._criar_df_vazio()

            # Formatar data explicitamente no formato ISO (YYYY-MM-DD) para evitar inversão dia/mês
            data_formatada = data.strftime('%Y-%m-%d') if hasattr(data, 'strftime') else str(data)

            nova_linha = pd.DataFrame([{
                'Data': pd.to_datetime(data_formatada),
                'Descricao': descricao,
                'Categoria': categoria,
                'Valor': valor,
                'Tipo': tipo,
                'Conta': conta
            }])

            df = pd.concat([df, nova_linha], ignore_index=True)
            return self._salvar_dados_csv(df)

        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_memoria(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva na memória e cria arquivo CSV."""
        try:
            sucesso, mensagem = self._salvar_transacao_csv(data, descricao, categoria, valor, tipo, conta)
            if sucesso:
                self.modo = 'csv'
                return True, "Arquivo CSV criado com sucesso! Dados salvos."
            return sucesso, mensagem
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def excluir_transacao(self, indice):
        """Exclui uma transação pelo índice."""
        if self.modo == 'gsheets':
            return self._excluir_gsheets(indice)
        elif self.modo == 'csv':
            return self._excluir_csv(indice)
        else:
            return False, "Não é possível excluir em modo memória."

    def _excluir_gsheets(self, indice):
        """Exclui do Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão."
            linha_sheet = indice + 2
            self.worksheet.delete_rows(linha_sheet)
            return True, "Transação excluída com sucesso!"
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    def _excluir_csv(self, indice):
        """Exclui do CSV."""
        try:
            df = pd.read_csv(CAMINHO_CSV)
            df = self._normalizar_dados(df)
            df = df.drop(indice).reset_index(drop=True)
            return self._salvar_dados_csv(df)
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    def editar_transacao(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita uma transação existente."""
        if self.modo == 'gsheets':
            return self._editar_gsheets(indice, data, descricao, categoria, valor, tipo, conta)
        elif self.modo == 'csv':
            return self._editar_csv(indice, data, descricao, categoria, valor, tipo, conta)
        else:
            return False, "Não é possível editar em modo memória."

    def _editar_gsheets(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão."

            linha_sheet = indice + 2
            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            novos_valores = [data_formatada, descricao, categoria, valor_formatado, tipo, conta]
            range_name = f"A{linha_sheet}:F{linha_sheet}"
            self.worksheet.update(range_name, [novos_valores])

            return True, "Transação atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"

    def _editar_csv(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita no CSV."""
        try:
            df = pd.read_csv(CAMINHO_CSV)
            df = self._normalizar_dados(df)

            df.at[indice, 'Data'] = data
            df.at[indice, 'Descricao'] = descricao
            df.at[indice, 'Categoria'] = categoria
            df.at[indice, 'Valor'] = valor
            df.at[indice, 'Tipo'] = tipo
            df.at[indice, 'Conta'] = conta

            return self._salvar_dados_csv(df)
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"


# ============================================================
# FUNÇÕES GLOBAIS COM CACHE
# ============================================================
@st.cache_resource
def get_armazenamento():
    """Retorna instância única do sistema de armazenamento."""
    return ArmazenamentoHibrido()


@st.cache_data(ttl=60)
def carregar_dados():
    """Carrega dados usando o sistema híbrido com cache."""
    armazenamento = get_armazenamento()
    return armazenamento.carregar_dados()


def limpar_cache_e_recarregar():
    """Limpa o cache de dados e força recarregamento."""
    st.cache_data.clear()
    st.rerun()


# ============================================================
# FUNÇÕES DE PERSISTÊNCIA - CONTAS E CARTÕES
# ============================================================
import json

def carregar_contas() -> list:
    """Carrega lista de contas bancárias do arquivo JSON."""
    try:
        if CAMINHO_CONTAS.exists():
            with open(CAMINHO_CONTAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception:
        return []


def salvar_conta(nome: str, banco_id: str, saldo_inicial: float = 0.0, tipo_grupo: str = 'Disponível') -> tuple:
    """
    Salva uma nova conta bancária.

    Args:
        nome: Nome personalizado da conta (ex: "Conta Principal")
        banco_id: ID do banco no CATALOGO_BANCOS (ex: "Nubank")
        saldo_inicial: Saldo inicial da conta
        tipo_grupo: Tipo de grupo da conta ('Disponível' ou 'Benefício')

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        contas = carregar_contas()

        # Verificar duplicata
        for conta in contas:
            if conta['nome'].lower() == nome.lower():
                return False, "Já existe uma conta com esse nome."

        # Validar tipo_grupo
        if tipo_grupo not in TIPOS_GRUPO_CONTA:
            tipo_grupo = 'Disponível'

        # Tratar saldo_inicial None como 0.0
        if saldo_inicial is None:
            saldo_inicial = 0.0

        # Obter dados do banco
        banco_info = CATALOGO_BANCOS.get(banco_id, CATALOGO_BANCOS['Outro'])

        nova_conta = {
            'id': len(contas) + 1,
            'nome': nome,
            'banco_id': banco_id,
            'banco_nome': banco_info['nome'],
            'cor_hex': banco_info['cor_hex'],
            'cor_secundaria': banco_info['cor_secundaria'],
            'logo_url': banco_info['logo_url'],
            'saldo_inicial': saldo_inicial,
            'tipo_grupo': tipo_grupo,
            'data_criacao': datetime.now().isoformat()
        }

        contas.append(nova_conta)

        with open(CAMINHO_CONTAS, 'w', encoding='utf-8') as f:
            json.dump(contas, f, ensure_ascii=False, indent=2)

        return True, f"Conta '{nome}' criada com sucesso!"

    except Exception as e:
        return False, f"Erro ao salvar conta: {str(e)}"


def excluir_conta(conta_id: int) -> tuple:
    """Exclui uma conta pelo ID."""
    try:
        contas = carregar_contas()
        contas = [c for c in contas if c['id'] != conta_id]

        with open(CAMINHO_CONTAS, 'w', encoding='utf-8') as f:
            json.dump(contas, f, ensure_ascii=False, indent=2)

        return True, "Conta excluída com sucesso!"
    except Exception as e:
        return False, f"Erro ao excluir conta: {str(e)}"


def carregar_cartoes() -> list:
    """Carrega lista de cartões de crédito do arquivo JSON."""
    try:
        if CAMINHO_CARTOES.exists():
            with open(CAMINHO_CARTOES, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception:
        return []


def salvar_cartao(nome: str, banco_id: str, limite: float, dia_fechamento: int, dia_vencimento: int) -> tuple:
    """
    Salva um novo cartão de crédito.

    Args:
        nome: Nome do cartão (ex: "Nubank Platinum")
        banco_id: ID do banco no CATALOGO_BANCOS
        limite: Limite total do cartão
        dia_fechamento: Dia do fechamento da fatura (1-31)
        dia_vencimento: Dia do vencimento da fatura (1-31)

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        cartoes = carregar_cartoes()

        # Verificar duplicata
        for cartao in cartoes:
            if cartao['nome'].lower() == nome.lower():
                return False, "Já existe um cartão com esse nome."

        # Validar dias
        if not (1 <= dia_fechamento <= 31):
            return False, "Dia de fechamento deve ser entre 1 e 31."
        if not (1 <= dia_vencimento <= 31):
            return False, "Dia de vencimento deve ser entre 1 e 31."

        # Obter dados do banco
        banco_info = CATALOGO_BANCOS.get(banco_id, CATALOGO_BANCOS['Outro'])

        novo_cartao = {
            'id': len(cartoes) + 1,
            'nome': nome,
            'banco_id': banco_id,
            'banco_nome': banco_info['nome'],
            'cor_hex': banco_info['cor_hex'],
            'cor_secundaria': banco_info['cor_secundaria'],
            'logo_url': banco_info['logo_url'],
            'limite': limite,
            'dia_fechamento': dia_fechamento,
            'dia_vencimento': dia_vencimento,
            'data_criacao': datetime.now().isoformat()
        }

        cartoes.append(novo_cartao)

        with open(CAMINHO_CARTOES, 'w', encoding='utf-8') as f:
            json.dump(cartoes, f, ensure_ascii=False, indent=2)

        return True, f"Cartão '{nome}' criado com sucesso!"

    except Exception as e:
        return False, f"Erro ao salvar cartão: {str(e)}"


def excluir_cartao(cartao_id: int) -> tuple:
    """Exclui um cartão pelo ID."""
    try:
        cartoes = carregar_cartoes()
        cartoes = [c for c in cartoes if c['id'] != cartao_id]

        with open(CAMINHO_CARTOES, 'w', encoding='utf-8') as f:
            json.dump(cartoes, f, ensure_ascii=False, indent=2)

        return True, "Cartão excluído com sucesso!"
    except Exception as e:
        return False, f"Erro ao excluir cartão: {str(e)}"


def obter_banco_info(banco_id: str) -> dict:
    """Retorna informações de um banco pelo ID."""
    return CATALOGO_BANCOS.get(banco_id, CATALOGO_BANCOS['Outro'])


# ============================================================
# FUNÇÕES AUXILIARES PARA CONTAS DINÂMICAS
# ============================================================

def obter_contas_por_tipo(tipo_grupo: str) -> list:
    """
    Retorna lista de nomes de contas filtradas por tipo_grupo.

    Args:
        tipo_grupo: 'Disponível' ou 'Benefício'

    Returns:
        Lista de nomes de contas do tipo especificado
    """
    contas = carregar_contas()
    return [c['nome'] for c in contas if c.get('tipo_grupo', 'Disponível') == tipo_grupo]


def obter_lista_contas_disponiveis() -> list:
    """
    Retorna lista de nomes de contas do tipo 'Disponível' (Dinheiro/Banco).
    Inclui mapeamento legado para 'Comum'.
    """
    contas = obter_contas_por_tipo('Disponível')
    # Adicionar conta legada 'Comum' se não houver contas cadastradas
    if not contas:
        contas = ['Comum']
    return contas


def obter_lista_contas_beneficio() -> list:
    """
    Retorna lista de nomes de contas do tipo 'Benefício' (VR/VA).
    Inclui mapeamento legado para 'Vale Refeição'.
    """
    contas = obter_contas_por_tipo('Benefício')
    # Adicionar conta legada 'Vale Refeição' se não houver contas cadastradas
    if not contas:
        contas = ['Vale Refeição']
    return contas


def obter_tipo_grupo_conta(nome_conta: str) -> str:
    """
    Retorna o tipo_grupo de uma conta pelo nome.
    Suporta mapeamento legado ('Comum' -> 'Disponível', 'Vale Refeição' -> 'Benefício').

    Args:
        nome_conta: Nome da conta

    Returns:
        'Disponível' ou 'Benefício'
    """
    # Verificar mapeamento legado primeiro
    if nome_conta in MAPEAMENTO_CONTA_LEGADO:
        return MAPEAMENTO_CONTA_LEGADO[nome_conta]

    # Buscar nas contas cadastradas
    contas = carregar_contas()
    for conta in contas:
        if conta['nome'] == nome_conta:
            return conta.get('tipo_grupo', 'Disponível')

    # Padrão: Disponível
    return 'Disponível'


def obter_todas_contas_para_filtro() -> dict:
    """
    Retorna um dicionário com listas de contas para uso em filtros.
    Combina contas cadastradas + legado para compatibilidade.

    Returns:
        dict com:
            - 'disponiveis': lista de nomes de contas disponíveis
            - 'beneficios': lista de nomes de contas benefício
            - 'todas': lista de todos os nomes de contas
    """
    contas = carregar_contas()

    disponiveis = []
    beneficios = []

    for conta in contas:
        tipo = conta.get('tipo_grupo', 'Disponível')
        if tipo == 'Disponível':
            disponiveis.append(conta['nome'])
        else:
            beneficios.append(conta['nome'])

    # Adicionar contas legadas para compatibilidade com dados antigos
    if 'Comum' not in disponiveis:
        disponiveis.append('Comum')
    if 'Vale Refeição' not in beneficios:
        beneficios.append('Vale Refeição')

    return {
        'disponiveis': disponiveis,
        'beneficios': beneficios,
        'todas': disponiveis + beneficios
    }


def calcular_saldos_dinamico(df: pd.DataFrame) -> dict:
    """
    Calcula saldos separados por tipo de grupo de conta (Disponível vs Benefício).
    Versão atualizada que suporta contas dinâmicas.

    Args:
        df: DataFrame com transações

    Returns:
        dict com: saldo_disponivel, saldo_beneficio, receitas_disponivel, despesas_disponivel,
                  receitas_beneficio, despesas_beneficio, tem_transacoes_beneficio, mostrar_card_beneficio
    """
    # Obter listas de contas por tipo
    info_contas = obter_todas_contas_para_filtro()
    contas_disponiveis = info_contas['disponiveis']
    contas_beneficio = info_contas['beneficios']

    # Saldo Contas Disponíveis (Banco/Dinheiro)
    df_disponivel = df[df['Conta'].isin(contas_disponiveis)]
    receitas_disponivel = df_disponivel[df_disponivel['Tipo'] == 'Receita']['Valor'].sum()
    despesas_disponivel = df_disponivel[df_disponivel['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_disponivel = receitas_disponivel - despesas_disponivel

    # Saldo Contas Benefício (VR/VA)
    df_beneficio = df[df['Conta'].isin(contas_beneficio)]
    receitas_beneficio = df_beneficio[df_beneficio['Tipo'] == 'Receita']['Valor'].sum()
    despesas_beneficio = df_beneficio[df_beneficio['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_beneficio = receitas_beneficio - despesas_beneficio

    # Verificar se deve mostrar card de benefício
    tem_transacoes_beneficio = len(df_beneficio) > 0
    mostrar_card_beneficio = tem_transacoes_beneficio or saldo_beneficio != 0

    return {
        'saldo_disponivel': saldo_disponivel,
        'saldo_beneficio': saldo_beneficio,
        'receitas_disponivel': receitas_disponivel,
        'despesas_disponivel': despesas_disponivel,
        'receitas_beneficio': receitas_beneficio,
        'despesas_beneficio': despesas_beneficio,
        'tem_transacoes_beneficio': tem_transacoes_beneficio,
        'mostrar_card_beneficio': mostrar_card_beneficio,
        # Aliases para compatibilidade com código legado
        'saldo_comum': saldo_disponivel,
        'saldo_vr': saldo_beneficio,
        'receitas_comum': receitas_disponivel,
        'despesas_comum': despesas_disponivel,
        'receitas_vr': receitas_beneficio,
        'despesas_vr': despesas_beneficio,
        'tem_transacoes_vr': tem_transacoes_beneficio,
        'mostrar_card_vr': mostrar_card_beneficio
    }


def calcular_saldo_anterior_dinamico(df: pd.DataFrame, tipo_grupo: str, data_inicio_mes) -> float:
    """
    Calcula o saldo acumulado de um grupo de contas (Disponível ou Benefício)
    considerando TODAS as transações anteriores a uma data.

    Args:
        df: DataFrame com transações
        tipo_grupo: 'Disponível' ou 'Benefício'
        data_inicio_mes: Data limite (transações anteriores a esta data)

    Returns:
        Saldo acumulado = Soma(Receitas) - Soma(Despesas)
    """
    if df.empty:
        return 0.0

    # Obter lista de contas do tipo
    info_contas = obter_todas_contas_para_filtro()
    if tipo_grupo == 'Disponível':
        lista_contas = info_contas['disponiveis']
    else:
        lista_contas = info_contas['beneficios']

    df_anterior = df[
        (df['Conta'].isin(lista_contas)) &
        (df['Data'].dt.date < data_inicio_mes)
    ].copy()

    if df_anterior.empty:
        return 0.0

    receitas = df_anterior[df_anterior['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df_anterior[df_anterior['Tipo'] == 'Despesa']['Valor'].sum()

    return receitas - despesas


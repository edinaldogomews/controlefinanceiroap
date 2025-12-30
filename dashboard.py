"""
Somma - Dashboard Financeiro Pessoal
Desenvolvido com Streamlit, Pandas e Plotly
Sistema de Armazenamento Híbrido: Google Sheets -> CSV Local -> DataFrame Vazio
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date
import os

# Imports para Google Sheets (opcional)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from gspread.exceptions import SpreadsheetNotFound, APIError
    GSPREAD_DISPONIVEL = True
except ImportError:
    GSPREAD_DISPONIVEL = False

# ============================================================
# CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA ST)
# ============================================================
st.set_page_config(
    page_title="Somma - Controle Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "### Somma\nDashboard para gerenciamento financeiro pessoal."
    }
)

# ============================================================
# CSS PERSONALIZADO - PROFISSIONALIZAÇÃO DA INTERFACE
# ============================================================
st.markdown("""
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
    </style>
""", unsafe_allow_html=True)

# ============================================================
# LOGO NA SIDEBAR
# ============================================================
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="
            background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 3px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        ">💰 Somma</h1>
        <p style="
            color: #555;
            font-size: 1rem;
            margin-top: 8px;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
        ">Controle Financeiro</p>
        <div style="
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #2E86AB, #1a5276);
            margin: 12px auto 0;
            border-radius: 2px;
        "></div>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# ============================================================
# CONFIGURAÇÕES DE ARMAZENAMENTO
# ============================================================
CAMINHO_CREDENCIAIS = Path(__file__).parent / "credentials.json"
CAMINHO_CSV = Path(__file__).parent / "dados_financeiros.csv"
NOME_PLANILHA = "Controle Financeiro"

# Estrutura de colunas do sistema
COLUNAS_SISTEMA = ['Data', 'Descricao', 'Categoria', 'Valor', 'Tipo']

# Categorias padrão disponíveis
CATEGORIAS_PADRAO = [
    'Moradia',
    'Alimentação',
    'Transporte',
    'Saúde',
    'Educação',
    'Lazer',
    'Salário',
    'Freelance',
    'Investimentos',
    'Outros'
]

# Tipos de transação
TIPOS_TRANSACAO = ['Despesa', 'Receita']


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
        self.modo = None  # 'gsheets', 'csv', 'memoria'
        self.worksheet = None
        self._detectar_modo()

    def _detectar_modo(self):
        """Detecta qual modo de armazenamento usar."""
        # Cenário A: Tentar Google Sheets
        if CAMINHO_CREDENCIAIS.exists() and GSPREAD_DISPONIVEL:
            try:
                self.worksheet = self._conectar_gsheets()
                if self.worksheet is not None:
                    self.modo = 'gsheets'
                    return
            except Exception:
                pass  # Fallback para CSV

        # Cenário B: Usar CSV local
        if CAMINHO_CSV.exists():
            self.modo = 'csv'
            return

        # Cenário C: Memória (DataFrame vazio)
        self.modo = 'memoria'

    def _conectar_gsheets(self):
        """Conecta ao Google Sheets usando credenciais."""
        try:
            scopes = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credenciais = None

            # Tentar st.secrets primeiro (Streamlit Cloud)
            try:
                credenciais_dict = st.secrets["gcp_service_account"]
                credenciais = ServiceAccountCredentials.from_json_keyfile_dict(
                    dict(credenciais_dict), scopes
                )
            except (KeyError, FileNotFoundError):
                # Usar arquivo local
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
                # Fallback para CSV
                self.modo = 'csv'
                return self._carregar_csv()

            registros = self.worksheet.get_all_records()

            if not registros:
                return self._criar_df_vazio()

            df = pd.DataFrame(registros)
            return self._normalizar_dados(df)

        except Exception:
            # Fallback para CSV
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
        # Mapeamento de possíveis nomes de colunas
        mapeamento = {
            'Vencimento': 'Data',
            'data': 'Data',
            'DATA': 'Data',
            'Descrição': 'Descricao',
            'descricao': 'Descricao',
            'DESCRICAO': 'Descricao',
            'categoria': 'Categoria',
            'CATEGORIA': 'Categoria',
            'valor': 'Valor',
            'VALOR': 'Valor',
            'tipo': 'Tipo',
            'TIPO': 'Tipo',
            'Status': 'Tipo'
        }

        # Renomear colunas
        df = df.rename(columns=mapeamento)

        # Garantir que todas as colunas existam
        for col in COLUNAS_SISTEMA:
            if col not in df.columns:
                if col == 'Tipo':
                    df[col] = 'Despesa'
                else:
                    df[col] = ''

        # Selecionar apenas as colunas do sistema
        df = df[[col for col in COLUNAS_SISTEMA if col in df.columns]]

        # Limpar dados
        df = df.dropna(how='all')

        # Limpar coluna Valor
        df['Valor'] = df['Valor'].apply(self._limpar_valor)

        # Converter Data para datetime
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)

        # Preencher valores NaN
        df['Descricao'] = df['Descricao'].fillna('').astype(str)
        df['Categoria'] = df['Categoria'].fillna('Outros').replace('', 'Outros')
        df['Tipo'] = df['Tipo'].fillna('Despesa').replace('', 'Despesa')

        # Normalizar valores de Tipo
        df['Tipo'] = df['Tipo'].apply(self._normalizar_tipo)

        # Remover linhas sem descrição
        df = df[df['Descricao'].str.strip() != '']

        return df.reset_index(drop=True)

    def _limpar_valor(self, valor):
        """Limpa e converte valor para float."""
        if pd.isna(valor) or valor == '':
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        valor_str = str(valor)
        valor_str = valor_str.replace('R$', '').strip()
        valor_str = valor_str.replace('.', '')
        valor_str = valor_str.replace(',', '.')
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

    # ============================================================
    # FUNÇÃO PRINCIPAL: salvar_dados(df)
    # ============================================================
    def salvar_dados(self, df):
        """
        Salva o DataFrame completo no armazenamento atual.
        - Google Sheets: Limpa a aba e escreve os dados novos
        - CSV Local: Sobrescreve o arquivo CSV

        Args:
            df: DataFrame com os dados a serem salvos

        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        if self.modo == 'gsheets':
            return self._salvar_dados_gsheets(df)
        elif self.modo == 'csv':
            return self._salvar_dados_csv(df)
        else:
            return self._salvar_dados_memoria(df)

    def _salvar_dados_gsheets(self, df):
        """Salva DataFrame completo no Google Sheets (limpa e reescreve)."""
        try:
            if self.worksheet is None:
                self.worksheet = self._conectar_gsheets()

            if self.worksheet is None:
                self.modo = 'csv'
                return self._salvar_dados_csv(df)

            df_export = df.copy()

            # Formatar Data como string
            df_export['Data'] = df_export['Data'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
            )

            # Formatar Valor como string monetária
            df_export['Valor'] = df_export['Valor'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )

            # Limpar a planilha
            self.worksheet.clear()

            # Escrever cabeçalho
            self.worksheet.append_row(COLUNAS_SISTEMA)

            # Escrever dados
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

    def salvar_transacao(self, data, descricao, categoria, valor, tipo):
        """Salva uma nova transação."""
        if self.modo == 'gsheets':
            return self._salvar_transacao_gsheets(data, descricao, categoria, valor, tipo)
        elif self.modo == 'csv':
            return self._salvar_transacao_csv(data, descricao, categoria, valor, tipo)
        else:
            return self._salvar_transacao_memoria(data, descricao, categoria, valor, tipo)

    def _salvar_transacao_gsheets(self, data, descricao, categoria, valor, tipo):
        """Salva uma transação no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão com Google Sheets."

            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            nova_linha = [data_formatada, descricao, categoria, valor_formatado, tipo]
            self.worksheet.append_row(nova_linha)

            return True, "Transação salva com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_csv(self, data, descricao, categoria, valor, tipo):
        """Salva uma transação no arquivo CSV."""
        try:
            if CAMINHO_CSV.exists():
                df = pd.read_csv(CAMINHO_CSV)
                df = self._normalizar_dados(df)
            else:
                df = self._criar_df_vazio()

            nova_linha = pd.DataFrame([{
                'Data': data,
                'Descricao': descricao,
                'Categoria': categoria,
                'Valor': valor,
                'Tipo': tipo
            }])

            df = pd.concat([df, nova_linha], ignore_index=True)

            return self._salvar_dados_csv(df)

        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_memoria(self, data, descricao, categoria, valor, tipo):
        """Salva na memória e cria arquivo CSV."""
        try:
            sucesso, mensagem = self._salvar_transacao_csv(data, descricao, categoria, valor, tipo)
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

    def editar_transacao(self, indice, data, descricao, categoria, valor, tipo):
        """Edita uma transação existente."""
        if self.modo == 'gsheets':
            return self._editar_gsheets(indice, data, descricao, categoria, valor, tipo)
        elif self.modo == 'csv':
            return self._editar_csv(indice, data, descricao, categoria, valor, tipo)
        else:
            return False, "Não é possível editar em modo memória."

    def _editar_gsheets(self, indice, data, descricao, categoria, valor, tipo):
        """Edita no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão."

            linha_sheet = indice + 2
            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            novos_valores = [data_formatada, descricao, categoria, valor_formatado, tipo]
            range_name = f"A{linha_sheet}:E{linha_sheet}"
            self.worksheet.update(range_name, [novos_valores])

            return True, "Transação atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"

    def _editar_csv(self, indice, data, descricao, categoria, valor, tipo):
        """Edita no CSV."""
        try:
            df = pd.read_csv(CAMINHO_CSV)
            df = self._normalizar_dados(df)

            df.at[indice, 'Data'] = data
            df.at[indice, 'Descricao'] = descricao
            df.at[indice, 'Categoria'] = categoria
            df.at[indice, 'Valor'] = valor
            df.at[indice, 'Tipo'] = tipo

            return self._salvar_dados_csv(df)
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"


# Inicializar sistema de armazenamento
@st.cache_resource
def get_armazenamento():
    return ArmazenamentoHibrido()


@st.cache_data(ttl=60)
def carregar_dados():
    """Carrega dados usando o sistema híbrido."""
    armazenamento = get_armazenamento()
    return armazenamento.carregar_dados()


# ============================================================
# FUNÇÃO AUXILIAR: salvar_dados (wrapper global)
# ============================================================
def salvar_dados(df):
    """
    Função global para salvar dados.
    Detecta automaticamente o modo de armazenamento e salva.
    Mostra mensagem de sucesso e recarrega a página se necessário.
    """
    armazenamento = get_armazenamento()
    sucesso, mensagem = armazenamento.salvar_dados(df)

    if sucesso:
        st.success(f"✅ {mensagem}")
        st.cache_data.clear()
        st.rerun()
    else:
        st.error(f"❌ {mensagem}")

    return sucesso, mensagem


# ============================================================
# FUNÇÃO PRINCIPAL: main()
# ============================================================
def main():
    # Obter sistema de armazenamento
    armazenamento = get_armazenamento()

    # ========== INDICADOR DE CONEXÃO NO TOPO ==========
    modo_texto, modo_tipo, is_online = armazenamento.get_modo_info()

    # Badge de status no topo do app
    if is_online:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #d4edda, #c3e6cb);
                border: 1px solid #28a745;
                border-radius: 25px;
                padding: 8px 20px;
                display: inline-block;
                margin-bottom: 15px;
            ">
                <span style="color: #155724; font-weight: 600; font-size: 0.9rem;">
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

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, {cor_fundo}, {cor_fundo});
                border: 1px solid {cor_borda};
                border-radius: 25px;
                padding: 8px 20px;
                display: inline-block;
                margin-bottom: 15px;
            ">
                <span style="color: {cor_texto}; font-weight: 600; font-size: 0.9rem;">
                    {modo_texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Título principal
    st.title("💰 Dashboard Financeiro")
    st.markdown("---")

    # Carregar dados
    df = carregar_dados()

    # Verificar se o DataFrame está vazio
    if df.empty:
        st.warning("📭 Nenhum registro encontrado.")
        st.info("Use o formulário na sidebar para adicionar sua primeira transação!")
        categorias_unicas = CATEGORIAS_PADRAO
        tipos_unicos = TIPOS_TRANSACAO
    else:
        tipos_unicos = df['Tipo'].unique().tolist()
        categorias_unicas = df['Categoria'].unique().tolist()

    # ========== SIDEBAR - FILTROS ==========
    st.sidebar.header("🔍 Filtros")

    if not df.empty:
        tipos_selecionados = st.sidebar.multiselect(
            "Tipo",
            options=tipos_unicos,
            default=tipos_unicos
        )

        categorias_selecionadas = st.sidebar.multiselect(
            "Categoria",
            options=categorias_unicas,
            default=categorias_unicas
        )
    else:
        tipos_selecionados = []
        categorias_selecionadas = []

    # ========== SIDEBAR - ADICIONAR NOVA TRANSAÇÃO ==========
    st.sidebar.markdown("---")

    if "limpar_formulario" not in st.session_state:
        st.session_state["limpar_formulario"] = False

    if st.session_state["limpar_formulario"]:
        st.session_state["form_descricao"] = ""
        st.session_state["form_valor"] = 0.0
        st.session_state["form_data"] = date.today()
        st.session_state["limpar_formulario"] = False

    with st.sidebar.expander("➕ Adicionar Nova Transação", expanded=df.empty):
        with st.container(border=True):
            st.subheader("📋 Nova Transação")

            # Linha 1: Data e Valor
            col1, col2 = st.columns(2)
            with col1:
                nova_data = st.date_input(
                    "📅 Data",
                    value=st.session_state.get("form_data", date.today()),
                    format="DD/MM/YYYY",
                    key="form_data"
                )
            with col2:
                novo_valor = st.number_input(
                    "💵 Valor (R$)",
                    min_value=0.00,
                    value=None,
                    step=0.01,
                    format="%.2f",
                    placeholder="0.00",
                    key="form_valor"
                )

            # Linha 2: Categoria e Tipo
            col3, col4 = st.columns(2)
            with col3:
                categorias_opcoes = sorted(set(CATEGORIAS_PADRAO + categorias_unicas))
                nova_categoria = st.selectbox(
                    "🏷️ Categoria",
                    options=categorias_opcoes,
                    key="form_categoria"
                )
            with col4:
                novo_tipo = st.selectbox(
                    "📊 Tipo",
                    options=TIPOS_TRANSACAO,
                    key="form_tipo"
                )

            # Linha 3: Descrição
            nova_descricao = st.text_input(
                "📝 Descrição",
                value=st.session_state.get("form_descricao", ""),
                placeholder="Ex: Conta de Luz",
                key="form_descricao"
            )

            # Botão Salvar
            if st.button("💾 Salvar Transação", use_container_width=True, type="primary"):
                valor_para_salvar = novo_valor if novo_valor is not None else 0.0

                if not nova_descricao.strip():
                    st.error("⚠️ A descrição é obrigatória!")
                elif valor_para_salvar <= 0:
                    st.error("⚠️ O valor deve ser maior que zero!")
                else:
                    with st.spinner("Salvando..."):
                        sucesso, mensagem = armazenamento.salvar_transacao(
                            nova_data,
                            nova_descricao.strip(),
                            nova_categoria,
                            valor_para_salvar,
                            novo_tipo
                        )

                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.session_state["limpar_formulario"] = True
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {mensagem}")

    # ========== SIDEBAR - GERENCIAR LANÇAMENTOS ==========
    st.sidebar.markdown("---")
    with st.sidebar.expander("📝 Gerenciar Lançamentos"):
        if df.empty:
            st.warning("📭 Nenhum lançamento para gerenciar.")
        else:
            df_reset = df.reset_index(drop=True)

            opcoes_gerenciar = []
            for idx, row in df_reset.iterrows():
                if pd.notna(row['Data']):
                    data_formatada = row['Data'].strftime('%d/%m/%Y')
                else:
                    data_formatada = 'Sem data'

                valor_formatado = f"R$ {row['Valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                descricao_str = str(row['Descricao'])[:20]
                opcao = f"{idx}: {data_formatada} - {descricao_str} - {valor_formatado}"
                opcoes_gerenciar.append(opcao)

            lancamento_selecionado = st.selectbox(
                "📋 Selecione o lançamento:",
                options=opcoes_gerenciar,
                key="select_gerenciar"
            )

            if lancamento_selecionado:
                indice_selecionado = int(lancamento_selecionado.split(":")[0])
                lancamento_detalhes = df_reset.iloc[indice_selecionado]

                tab_editar, tab_excluir = st.tabs(["✏️ Editar", "🗑️ Excluir"])

                with tab_editar:
                    with st.form(key=f"form_editar_{indice_selecionado}"):
                        st.markdown("**Editar Lançamento**")

                        data_atual = lancamento_detalhes['Data']
                        data_valor = data_atual.date() if pd.notna(data_atual) else date.today()

                        edit_data = st.date_input("📅 Data", value=data_valor, format="DD/MM/YYYY")
                        edit_descricao = st.text_input("📝 Descrição", value=str(lancamento_detalhes['Descricao']))
                        edit_valor = st.number_input("💵 Valor", min_value=0.0, value=float(lancamento_detalhes['Valor']), step=0.01)

                        categoria_atual = str(lancamento_detalhes['Categoria'])
                        categorias_edit = sorted(set(CATEGORIAS_PADRAO + categorias_unicas + [categoria_atual]))
                        idx_cat = categorias_edit.index(categoria_atual) if categoria_atual in categorias_edit else 0
                        edit_categoria = st.selectbox("🏷️ Categoria", options=categorias_edit, index=idx_cat)

                        tipo_atual = str(lancamento_detalhes['Tipo'])
                        idx_tipo = TIPOS_TRANSACAO.index(tipo_atual) if tipo_atual in TIPOS_TRANSACAO else 0
                        edit_tipo = st.selectbox("📊 Tipo", options=TIPOS_TRANSACAO, index=idx_tipo)

                        submit_editar = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")

                        if submit_editar:
                            if not edit_descricao.strip():
                                st.error("⚠️ A descrição é obrigatória!")
                            elif edit_valor <= 0:
                                st.error("⚠️ O valor deve ser maior que zero!")
                            else:
                                with st.spinner("Salvando..."):
                                    sucesso, mensagem = armazenamento.editar_transacao(
                                        indice_selecionado, edit_data, edit_descricao.strip(),
                                        edit_categoria, edit_valor, edit_tipo
                                    )
                                if sucesso:
                                    st.success(f"✅ {mensagem}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {mensagem}")

                with tab_excluir:
                    st.markdown("**Detalhes do Lançamento**")
                    st.caption(f"**Categoria:** {lancamento_detalhes['Categoria']}")
                    st.caption(f"**Tipo:** {lancamento_detalhes['Tipo']}")
                    st.caption(f"**Valor:** R$ {lancamento_detalhes['Valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                    st.warning("⚠️ Esta ação não pode ser desfeita!")

                    if st.button("🗑️ Excluir", use_container_width=True, type="primary"):
                        with st.spinner("Excluindo..."):
                            sucesso, mensagem = armazenamento.excluir_transacao(indice_selecionado)
                        if sucesso:
                            st.success(f"✅ {mensagem}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {mensagem}")

    # Se não há dados, parar aqui
    if df.empty:
        st.stop()

    # Aplicar filtros
    df_filtrado = df[
        (df['Tipo'].isin(tipos_selecionados)) &
        (df['Categoria'].isin(categorias_selecionadas))
    ]

    # ========== KPIs - MÉTRICAS PRINCIPAIS ==========
    st.subheader("📊 Resumo Financeiro")

    col1, col2, col3, col4 = st.columns(4)

    total_receitas = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = total_receitas - total_despesas

    with col1:
        st.metric(
            label="💵 Total de Receitas",
            value=f"R$ {total_receitas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    with col2:
        st.metric(
            label="💸 Total de Despesas",
            value=f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    with col3:
        st.metric(
            label="💰 Saldo",
            value=f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            delta=f"{'Positivo' if saldo >= 0 else 'Negativo'}"
        )

    with col4:
        st.metric(
            label="📋 Total de Transações",
            value=len(df_filtrado)
        )

    st.markdown("---")

    # ========== GRÁFICOS ==========
    st.subheader("📈 Visualizações")

    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.markdown("#### 🍩 Gastos por Categoria")

        if not df_filtrado.empty:
            gastos_categoria = df_filtrado.groupby('Categoria')['Valor'].sum().reset_index()
            gastos_categoria = gastos_categoria.sort_values('Valor', ascending=False)

            fig_rosca = px.pie(
                gastos_categoria,
                values='Valor',
                names='Categoria',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_rosca.update_traces(
                textposition='outside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
            )
            fig_rosca.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_rosca, use_container_width=True)
        else:
            st.info("Nenhum dado disponível.")

    with col_grafico2:
        st.markdown("#### 📅 Movimentação por Mês")

        if not df_filtrado.empty:
            df_mensal = df_filtrado.copy()
            df_mensal = df_mensal.dropna(subset=['Data'])

            if not df_mensal.empty:
                df_mensal['Mês'] = df_mensal['Data'].dt.to_period('M').astype(str)

                gastos_mensais = df_mensal.groupby(['Mês', 'Tipo'])['Valor'].sum().reset_index()

                def formatar_mes(periodo):
                    try:
                        ano, mes = periodo.split('-')
                        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                        return f"{meses[int(mes)-1]}/{ano[2:]}"
                    except:
                        return periodo

                gastos_mensais['Mês_Fmt'] = gastos_mensais['Mês'].apply(formatar_mes)

                fig_barras = px.bar(
                    gastos_mensais,
                    x='Mês_Fmt',
                    y='Valor',
                    color='Tipo',
                    barmode='group',
                    color_discrete_map={'Receita': '#2ecc71', 'Despesa': '#e74c3c'}
                )
                fig_barras.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Valor (R$)",
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("Nenhum dado com data válida.")
        else:
            st.info("Nenhum dado disponível.")

    st.markdown("#### 📊 Receitas vs Despesas")

    if not df_filtrado.empty:
        comparativo = pd.DataFrame({
            'Tipo': ['Receitas', 'Despesas'],
            'Valor': [total_receitas, total_despesas]
        })

        fig_comp = px.bar(
            comparativo,
            x='Tipo',
            y='Valor',
            color='Tipo',
            color_discrete_map={'Receitas': '#2ecc71', 'Despesas': '#e74c3c'},
            text_auto=True
        )
        fig_comp.update_traces(
            texttemplate='R$ %{y:,.2f}',
            textposition='outside'
        )
        fig_comp.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Valor (R$)",
            height=300,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    # ========== TABELA DE DADOS ==========
    st.subheader("📋 Dados Detalhados")

    if not df_filtrado.empty:
        df_exibicao = df_filtrado.copy()
        df_exibicao['Valor'] = df_exibicao['Valor'].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
        df_exibicao['Data'] = df_exibicao['Data'].fillna('Não informado')

        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        st.caption(f"Total de registros: {len(df_filtrado)}")
    else:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")

    # ========== RODAPÉ ==========
    st.sidebar.markdown("---")
    st.sidebar.caption("Dashboard Financeiro Gratuito")
    st.sidebar.caption("Desenvolvido por Edinaldo Gomes")
    st.sidebar.caption("📧 edinaldosantos.contato@gmail.com")
    st.sidebar.caption("v2025.1.4 | © 2025 Todos os direitos reservados")


if __name__ == "__main__":
    main()

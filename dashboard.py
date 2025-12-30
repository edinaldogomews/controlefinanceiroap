"""
Somma - Dashboard Financeiro Pessoal
Desenvolvido com Streamlit, Pandas e Plotly
Integração com Google Sheets via gspread
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import SpreadsheetNotFound, APIError

# ============================================================
# CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA ST)
# ============================================================
st.set_page_config(
    page_title="Somma - Controle Financeiro",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "### Somma\nDashboard para gerenciamento de despesas pessoais."
    }
)

# ============================================================
# CSS PERSONALIZADO - PROFISSIONALIZAÇÃO DA INTERFACE
# ============================================================
st.markdown("""
    <style>
        /* ===== OCULTAR ELEMENTOS PADRÃO DO STREAMLIT ===== */
        
        /* Ocultar botão "Deploy" do cabeçalho */
        .stDeployButton {
            display: none !important;
        }
        
        /* Ocultar menu hamburguer (3 pontos) do cabeçalho */
        #MainMenu {
            visibility: hidden;
        }
        
        /* Ocultar rodapé "Made with Streamlit" */
        footer {
            visibility: hidden;
        }
        
        /* Ocultar cabeçalho padrão */
        header[data-testid="stHeader"] {
            background: transparent;
        }
        
        /* ===== AJUSTES DE ESPAÇAMENTO ===== */
        
        /* Reduzir espaço superior do conteúdo principal */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* Ajustar padding da sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        
        /* ===== ESTILIZAÇÃO DOS CARDS/MÉTRICAS ===== */
        
        /* Estilo para os cartões de métricas */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* ===== ESTILIZAÇÃO DA SIDEBAR ===== */
        
        /* Linha divisória mais suave */
        hr {
            border: none;
            border-top: 1px solid #e9ecef;
            margin: 1rem 0;
        }
        
        /* ===== ESTILIZAÇÃO DOS EXPANDERS ===== */
        
        /* Expanders com bordas arredondadas */
        .streamlit-expanderHeader {
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* ===== MELHORIAS NOS BOTÕES ===== */
        
        /* Botões com transição suave */
        .stButton > button {
            transition: all 0.3s ease;
            border-radius: 8px;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* ===== TABELA DE DADOS ===== */
        
        /* Estilo para a tabela de dados */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
        }
        
    </style>
""", unsafe_allow_html=True)

# ============================================================
# LOGO NA SIDEBAR
# ============================================================
# Logo do aplicativo Somma
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
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
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
# CONFIGURAÇÕES DO GOOGLE SHEETS
# ============================================================
CAMINHO_CREDENCIAIS = Path(__file__).parent / "credentials.json"
NOME_PLANILHA = "Controle Financeiro - DB"

# Colunas que utilizamos no dashboard
COLUNAS_NECESSARIAS = ['Vencimento', 'Descrição', 'Valor', 'Categoria', 'Status']

# Categorias padrão disponíveis no formulário
CATEGORIAS_PADRAO = [
    'Moradia',
    'Saúde',
    'Pessoais e Educação',
    'Dívidas e Parcelamentos',
    'Assinaturas e Serviços',
    'Compromissos e Outros'
]


def conectar_gsheets():
    """
    Conecta ao Google Sheets usando credenciais de conta de serviço.

    Estratégia de autenticação:
    1. Tenta usar st.secrets["gcp_service_account"] (Streamlit Cloud)
    2. Fallback para arquivo credentials.json local (desenvolvimento)

    Retorna o objeto worksheet (primeira aba) ou None em caso de erro.
    """
    try:
        # Definir escopos de acesso
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        credenciais = None

        # Tentar autenticar via st.secrets (Streamlit Cloud)
        try:
            # st.secrets retorna um dicionário, usar from_json_keyfile_dict
            credenciais_dict = st.secrets["gcp_service_account"]
            credenciais = ServiceAccountCredentials.from_json_keyfile_dict(
                dict(credenciais_dict),
                scopes
            )
        except (KeyError, FileNotFoundError):
            # Fallback: usar arquivo credentials.json local (desenvolvimento)
            if CAMINHO_CREDENCIAIS.exists():
                credenciais = ServiceAccountCredentials.from_json_keyfile_name(
                    str(CAMINHO_CREDENCIAIS),
                    scopes
                )
            else:
                st.error("⚠️ Credenciais não encontradas!")
                st.warning(
                    """
                    **Como resolver:**

                    **Para Streamlit Cloud:**
                    1. Acesse o painel do seu app no Streamlit Cloud
                    2. Vá em **Settings** → **Secrets**
                    3. Adicione suas credenciais sob o cabeçalho `[gcp_service_account]`

                    **Para desenvolvimento local:**
                    1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
                    2. Crie um projeto e ative a API do Google Sheets
                    3. Crie uma Conta de Serviço e baixe o arquivo JSON
                    4. Renomeie para `credentials.json` e coloque na pasta do projeto
                    """
                )
                return None

        # Autorizar cliente gspread
        cliente = gspread.authorize(credenciais)

        # Abrir a planilha e retornar a primeira aba
        # Usa get_worksheet(0) para pegar a primeira aba, independente do nome ("Sheet1" ou "Página1")
        planilha = cliente.open(NOME_PLANILHA)
        worksheet = planilha.get_worksheet(0)

        return worksheet

    except SpreadsheetNotFound:
        st.error(f"⚠️ Planilha '{NOME_PLANILHA}' não encontrada!")
        st.warning(
            """
            **Como resolver:**

            1. Verifique se o nome da planilha está correto: **"Controle Financeiro - DB"**
            2. Copie o e-mail da conta de serviço (campo `client_email` nas credenciais)
            3. Compartilhe a planilha do Google com esse e-mail como **Editor**
            """
        )
        return None

    except APIError as e:
        st.error("⚠️ Erro de permissão na API do Google!")
        st.warning(
            """
            **Como resolver:**

            1. Copie o e-mail da conta de serviço (campo `client_email` nas credenciais)
            2. Vá até a planilha no Google Sheets
            3. Clique em **Compartilhar** e adicione o e-mail como **Editor**
            """
        )
        # Log interno sem expor ao usuário (opcional: usar logging)
        return None

    except Exception as e:
        st.error("⚠️ Erro ao conectar com Google Sheets. Verifique suas credenciais e conexão.")
        # Log interno sem expor ao usuário
        return None


@st.cache_data(ttl=60)
def carregar_dados():
    """
    Carrega e limpa os dados do Google Sheets.
    Retorna um DataFrame limpo ou None em caso de erro.
    """
    # Conectar ao Google Sheets
    worksheet = conectar_gsheets()

    if worksheet is None:
        return None

    # Obter todos os registros como lista de dicionários
    registros = worksheet.get_all_records()

    if not registros:
        # Retorna DataFrame vazio com as colunas necessárias
        return pd.DataFrame(columns=COLUNAS_NECESSARIAS)

    # Converter para DataFrame
    df = pd.DataFrame(registros)

    # Verificar se as colunas necessárias existem
    colunas_existentes = [col for col in COLUNAS_NECESSARIAS if col in df.columns]
    if not colunas_existentes:
        st.error("⚠️ A planilha não contém as colunas esperadas!")
        return None

    # Selecionar apenas as colunas necessárias
    df = df[[col for col in COLUNAS_NECESSARIAS if col in df.columns]]

    # Remover linhas completamente vazias
    df = df.dropna(how='all')

    # Limpeza da coluna Valor
    def limpar_valor(valor):
        if pd.isna(valor) or valor == '':
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        # Se for string, limpar formatação brasileira
        valor_str = str(valor)
        valor_str = valor_str.replace('R$', '').strip()
        valor_str = valor_str.replace('.', '')  # Remove ponto de milhar
        valor_str = valor_str.replace(',', '.')  # Troca vírgula por ponto
        try:
            return float(valor_str)
        except ValueError:
            return 0.0

    df['Valor'] = df['Valor'].apply(limpar_valor)
    df['Valor'] = df['Valor'].fillna(0.0)

    # Conversão da coluna Vencimento para datetime
    df['Vencimento'] = pd.to_datetime(df['Vencimento'], errors='coerce', dayfirst=True)

    # Remover linhas onde Descrição está vazia
    df = df.dropna(subset=['Descrição'])
    df = df[df['Descrição'].astype(str).str.strip() != '']

    # Preencher valores NaN em Status e Categoria
    df['Status'] = df['Status'].fillna('NÃO DEFINIDO')
    df['Categoria'] = df['Categoria'].fillna('SEM CATEGORIA')

    # Substituir strings vazias
    df['Status'] = df['Status'].replace('', 'NÃO DEFINIDO')
    df['Categoria'] = df['Categoria'].replace('', 'SEM CATEGORIA')

    return df


def salvar_nova_transacao(data_venc, descricao, valor, categoria, status):
    """
    Adiciona uma nova transação ao Google Sheets.
    """
    try:
        # Conectar ao Google Sheets
        worksheet = conectar_gsheets()

        if worksheet is None:
            return False, "Erro ao conectar com Google Sheets."

        # Formatar a data no padrão YYYY-MM-DD para o Google Sheets
        data_formatada = data_venc.strftime('%Y-%m-%d')

        # Formatar o valor no padrão brasileiro (R$ X.XXX,XX)
        valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Criar a nova linha com os dados
        nova_linha = [data_formatada, descricao, valor_formatado, categoria, status]

        # Adicionar a linha na planilha
        worksheet.append_row(nova_linha)

        return True, "Transação salva com sucesso!"

    except APIError as e:
        return False, f"Erro de API do Google: {str(e)}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def excluir_lancamento(indice_dataframe):
    """
    Exclui um lançamento do Google Sheets baseado no índice do DataFrame.

    Args:
        indice_dataframe: O índice da linha no DataFrame (começa em 0)

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        # Conectar ao Google Sheets
        worksheet = conectar_gsheets()

        if worksheet is None:
            return False, "Erro ao conectar com Google Sheets."

        # Calcular a linha no Google Sheets
        # Linha_Sheet = Índice_DataFrame + 2
        # (+1 porque o índice do Python começa em 0, +1 pelo cabeçalho na linha 1)
        linha_sheet = indice_dataframe + 2

        # Excluir a linha da planilha
        worksheet.delete_rows(linha_sheet)

        return True, "Lançamento excluído com sucesso!"

    except APIError as e:
        return False, f"Erro de API do Google: {str(e)}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def editar_lancamento(indice_dataframe, data_venc, descricao, valor, categoria, status):
    """
    Edita um lançamento existente no Google Sheets.

    Args:
        indice_dataframe: O índice da linha no DataFrame (começa em 0)
        data_venc: Nova data de vencimento
        descricao: Nova descrição
        valor: Novo valor
        categoria: Nova categoria
        status: Novo status

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        # Conectar ao Google Sheets
        worksheet = conectar_gsheets()

        if worksheet is None:
            return False, "Erro ao conectar com Google Sheets."

        # Calcular a linha no Google Sheets
        # Linha_Sheet = Índice_DataFrame + 2
        linha_sheet = indice_dataframe + 2

        # Formatar a data no padrão YYYY-MM-DD
        data_formatada = data_venc.strftime('%Y-%m-%d')

        # Formatar o valor no padrão brasileiro (R$ X.XXX,XX)
        valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Criar a lista com os novos valores
        novos_valores = [data_formatada, descricao, valor_formatado, categoria, status]

        # Atualizar a linha inteira (colunas A até E)
        # Formato: A{linha}:E{linha}
        range_name = f"A{linha_sheet}:E{linha_sheet}"
        worksheet.update(range_name, [novos_valores])

        return True, "Lançamento atualizado com sucesso!"

    except APIError as e:
        return False, f"Erro de API do Google: {str(e)}"
    except Exception as e:
        return False, f"Erro ao editar: {str(e)}"

    st.title("Somma - Dashboard Financeiro")
def main():
    # Título principal
    st.title("Dashboard Financeiro")
    st.markdown("---")

    # Carregar dados
    df = carregar_dados()

    # Verificar se os dados foram carregados
    if df is None:
        st.stop()

    # Verificar se o DataFrame está vazio
    if df.empty:
        st.warning("📭 Nenhum registro encontrado na planilha.")
        st.info("Use o formulário na sidebar para adicionar sua primeira despesa!")

        # Definir categorias padrão para o formulário
        categorias_unicas = ['Moradia', 'Alimentação', 'Transporte', 'Saúde', 'Educação', 'Lazer', 'Outros']
        status_unicos = ['EM ABERTO', 'PAGO']
    else:
        # Obter listas únicas para filtros
        status_unicos = df['Status'].unique().tolist()
        categorias_unicas = df['Categoria'].unique().tolist()

    # ========== SIDEBAR - FILTROS ==========
    st.sidebar.header("🔍 Filtros")

    if not df.empty:
        # Filtro de Status
        status_selecionados = st.sidebar.multiselect(
            "Status",
            options=status_unicos,
            default=status_unicos
        )

        # Filtro de Categoria
        categorias_selecionadas = st.sidebar.multiselect(
            "Categoria",
            options=categorias_unicas,
            default=categorias_unicas
        )
    else:
        status_selecionados = []
        categorias_selecionadas = []

    # ========== SIDEBAR - ADICIONAR NOVA DESPESA ==========
    st.sidebar.markdown("---")

    # Inicializar valores padrão do formulário se não existirem ou se flag de limpeza estiver ativo
    if "limpar_formulario" not in st.session_state:
        st.session_state["limpar_formulario"] = False

    if st.session_state["limpar_formulario"]:
        st.session_state["form_descricao"] = ""
        st.session_state["form_valor"] = 0.0
        st.session_state["form_data"] = date.today()
        st.session_state["limpar_formulario"] = False

    with st.sidebar.expander("➕ Adicionar Nova Despesa", expanded=df.empty):
        # Container com borda para distinção visual
        with st.container(border=True):
            st.subheader("📋 Adicionar Novo Registro")

            # Linha 1: Data e Valor lado a lado
            col1, col2 = st.columns(2)
            with col1:
                nova_data = st.date_input(
                    "📅 Data de Vencimento",
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

            # Linha 2: Categoria e Status lado a lado
            col3, col4 = st.columns(2)
            with col3:
                categorias_opcoes = sorted(set(CATEGORIAS_PADRAO + categorias_unicas))
                nova_categoria = st.selectbox(
                    "🏷️ Categoria",
                    options=categorias_opcoes,
                    key="form_categoria"
                )
            with col4:
                novo_status = st.selectbox(
                    "📊 Status",
                    options=["EM ABERTO", "PAGO"],
                    key="form_status"
                )

            # Linha 3: Descrição ocupando largura total
            nova_descricao = st.text_input(
                "📝 Descrição",
                value=st.session_state.get("form_descricao", ""),
                placeholder="Ex: Conta de Luz",
                key="form_descricao"
            )

            # Botão de Salvar
            if st.button("💾 Salvar Transação", use_container_width=True, type="primary"):
                # Tratar valor None (campo vazio)
                valor_para_salvar = novo_valor if novo_valor is not None else 0.0

                # Validações
                if not nova_descricao.strip():
                    st.error("⚠️ A descrição é obrigatória!")
                elif valor_para_salvar <= 0:
                    st.error("⚠️ O valor deve ser maior que zero!")
                else:
                    # Salvar a transação
                    with st.spinner("Salvando..."):
                        sucesso, mensagem = salvar_nova_transacao(
                            nova_data,
                            nova_descricao.strip(),
                            valor_para_salvar,
                            nova_categoria,
                            novo_status
                        )

                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        # Ativar flag para limpar formulário no próximo rerun
                        st.session_state["limpar_formulario"] = True
                        # Limpar cache e recarregar a página
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {mensagem}")

    # ========== SIDEBAR - GERENCIAR LANÇAMENTOS (EDITAR / EXCLUIR) ==========
    st.sidebar.markdown("---")
    with st.sidebar.expander("📝 Gerenciar Lançamentos (Editar / Excluir)"):
        if df.empty:
            st.warning("📭 Nenhum lançamento para gerenciar.")
        else:
            # Resetar o índice do DataFrame para garantir índices sequenciais
            df_reset = df.reset_index(drop=True)

            # Criar lista de opções para o selectbox
            # Formato: "{Index}: {Data} - {Descrição} - {Valor}"
            opcoes_gerenciar = []
            for idx, row in df_reset.iterrows():
                # Formatar a data
                if pd.notna(row['Vencimento']):
                    data_formatada = row['Vencimento'].strftime('%d/%m/%Y')
                else:
                    data_formatada = 'Sem data'

                # Formatar o valor
                valor_formatado = f"R$ {row['Valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                # Criar a string de opção (converter descrição para string)
                descricao_str = str(row['Descrição'])[:25]
                opcao = f"{idx}: {data_formatada} - {descricao_str} - {valor_formatado}"
                opcoes_gerenciar.append(opcao)

            # Selectbox para escolher o lançamento
            lancamento_selecionado = st.selectbox(
                "📋 Selecione o lançamento:",
                options=opcoes_gerenciar,
                key="select_gerenciar"
            )

            # Extrair o índice do lançamento selecionado
            if lancamento_selecionado:
                indice_selecionado = int(lancamento_selecionado.split(":")[0])
                lancamento_detalhes = df_reset.iloc[indice_selecionado]

                # Criar abas para Editar e Excluir
                tab_editar, tab_excluir = st.tabs(["✏️ Editar", "🗑️ Excluir"])

                # ===== ABA EDITAR =====
                with tab_editar:
                    with st.form(key=f"form_editar_{indice_selecionado}"):
                        st.markdown("**Editar Lançamento**")

                        # Campo Data - converter para date do Python
                        data_atual = lancamento_detalhes['Vencimento']
                        if pd.notna(data_atual):
                            data_valor = data_atual.date()
                        else:
                            data_valor = date.today()

                        edit_data = st.date_input(
                            "📅 Data de Vencimento",
                            value=data_valor,
                            format="DD/MM/YYYY"
                        )

                        # Campo Descrição
                        edit_descricao = st.text_input(
                            "📝 Descrição",
                            value=str(lancamento_detalhes['Descrição'])
                        )

                        # Campo Valor
                        edit_valor = st.number_input(
                            "💵 Valor (R$)",
                            min_value=0.0,
                            value=float(lancamento_detalhes['Valor']),
                            step=0.01,
                            format="%.2f"
                        )

                        # Campo Categoria - garantir que o valor atual esteja nas opções
                        categoria_atual = str(lancamento_detalhes['Categoria'])
                        categorias_edit = sorted(set(CATEGORIAS_PADRAO + categorias_unicas + [categoria_atual]))
                        idx_categoria = categorias_edit.index(categoria_atual) if categoria_atual in categorias_edit else 0

                        edit_categoria = st.selectbox(
                            "🏷️ Categoria",
                            options=categorias_edit,
                            index=idx_categoria
                        )

                        # Campo Status - garantir que o valor atual esteja nas opções
                        status_atual = str(lancamento_detalhes['Status'])
                        status_opcoes = ["EM ABERTO", "PAGO"]
                        if status_atual not in status_opcoes:
                            status_opcoes.append(status_atual)
                        idx_status = status_opcoes.index(status_atual) if status_atual in status_opcoes else 0

                        edit_status = st.selectbox(
                            "📊 Status",
                            options=status_opcoes,
                            index=idx_status
                        )

                        # Botão de salvar alterações
                        submit_editar = st.form_submit_button(
                            "💾 Salvar Alterações",
                            use_container_width=True,
                            type="primary"
                        )

                        if submit_editar:
                            # Validações
                            if not edit_descricao.strip():
                                st.error("⚠️ A descrição é obrigatória!")
                            elif edit_valor <= 0:
                                st.error("⚠️ O valor deve ser maior que zero!")
                            else:
                                with st.spinner("Salvando alterações..."):
                                    sucesso, mensagem = editar_lancamento(
                                        indice_selecionado,
                                        edit_data,
                                        edit_descricao.strip(),
                                        edit_valor,
                                        edit_categoria,
                                        edit_status
                                    )

                                if sucesso:
                                    st.success(f"✅ {mensagem}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {mensagem}")

                # ===== ABA EXCLUIR =====
                with tab_excluir:
                    st.markdown("**Detalhes do Lançamento**")

                    # Mostrar detalhes do lançamento selecionado
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.caption(f"**Categoria:** {lancamento_detalhes['Categoria']}")
                        st.caption(f"**Status:** {lancamento_detalhes['Status']}")
                    with col_det2:
                        st.caption(f"**Valor:** R$ {lancamento_detalhes['Valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                    st.markdown("---")
                    st.warning("⚠️ **Atenção:** Esta ação não pode ser desfeita!")

                    if st.button("🗑️ Excluir Lançamento", use_container_width=True, type="primary"):
                        with st.spinner("Excluindo..."):
                            sucesso, mensagem = excluir_lancamento(indice_selecionado)

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
        (df['Status'].isin(status_selecionados)) &
        (df['Categoria'].isin(categorias_selecionadas))
    ]

    # ========== KPIs - MÉTRICAS PRINCIPAIS ==========
    st.subheader("📊 Resumo Financeiro")

    col1, col2, col3 = st.columns(3)

    # Total de Despesas Fixas
    total_despesas = df_filtrado['Valor'].sum()

    # Total Já Pago
    total_pago = df_filtrado[df_filtrado['Status'].str.upper() == 'PAGO']['Valor'].sum()

    # Total Previsto em Aberto
    total_aberto = df_filtrado[df_filtrado['Status'].str.upper() == 'EM ABERTO']['Valor'].sum()

    with col1:
        st.metric(
            label="💵 Total de Despesas Fixas",
            value=f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    with col2:
        st.metric(
            label="✅ Total Já Pago",
            value=f"R$ {total_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    with col3:
        st.metric(
            label="⏳ Total Previsto em Aberto",
            value=f"R$ {total_aberto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    st.markdown("---")

    # ========== GRÁFICOS ==========
    st.subheader("📈 Visualizações")

    col_grafico1, col_grafico2 = st.columns(2)

    # Gráfico de Rosca - Distribuição por Categoria
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
            st.info("Nenhum dado disponível para exibir.")

    # Gráfico de Barras - Gastos por Mês
    with col_grafico2:
        st.markdown("#### 📅 Gastos por Mês")

        if not df_filtrado.empty:
            # Criar cópia para manipulação
            df_mensal = df_filtrado.copy()

            # Filtrar apenas registros com data válida
            df_mensal = df_mensal.dropna(subset=['Vencimento'])

            if not df_mensal.empty:
                # Extrair mês/ano do vencimento
                df_mensal['Mês'] = df_mensal['Vencimento'].dt.to_period('M').astype(str)

                # Agrupar por mês e somar valores
                gastos_mensais = df_mensal.groupby('Mês')['Valor'].sum().reset_index()
                gastos_mensais = gastos_mensais.sort_values('Mês')

                # Formatar nome do mês para exibição (ex: 2025-01 -> Jan/25)
                def formatar_mes(periodo):
                    try:
                        ano, mes = periodo.split('-')
                        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                        return f"{meses[int(mes)-1]}/{ano[2:]}"
                    except:
                        return periodo

                gastos_mensais['Mês_Formatado'] = gastos_mensais['Mês'].apply(formatar_mes)

                fig_barras_mes = px.bar(
                    gastos_mensais,
                    x='Mês_Formatado',
                    y='Valor',
                    color='Valor',
                    color_continuous_scale='Blues',
                    text_auto=True
                )
                fig_barras_mes.update_traces(
                    texttemplate='R$ %{y:,.0f}',
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.2f}<extra></extra>'
                )
                fig_barras_mes.update_layout(
                    showlegend=False,
                    xaxis_title="Mês",
                    yaxis_title="Valor (R$)",
                    coloraxis_showscale=False,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_barras_mes, use_container_width=True)
            else:
                st.info("Nenhum dado com data válida para exibir.")
        else:
            st.info("Nenhum dado disponível para exibir.")

    # Segunda linha de gráficos - Gastos por Status
    st.markdown("#### 📊 Gastos por Status")

    if not df_filtrado.empty:
        gastos_status = df_filtrado.groupby('Status')['Valor'].sum().reset_index()
        gastos_status = gastos_status.sort_values('Valor', ascending=True)

        fig_barras = px.bar(
            gastos_status,
            x='Valor',
            y='Status',
            orientation='h',
            color='Status',
            color_discrete_map={'PAGO': '#2ecc71', 'EM ABERTO': '#e74c3c'},
            text_auto=True
        )
        fig_barras.update_traces(
            texttemplate='R$ %{x:,.2f}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>'
        )
        fig_barras.update_layout(
            showlegend=False,
            xaxis_title="Valor (R$)",
            yaxis_title="",
            margin=dict(t=20, b=20, l=20, r=100),
            height=250
        )
        st.plotly_chart(fig_barras, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir.")

    st.markdown("---")

    # ========== TABELA DE DADOS ==========
    st.subheader("📋 Dados Detalhados")

    if not df_filtrado.empty:
        # Formatar DataFrame para exibição
        df_exibicao = df_filtrado.copy()
        df_exibicao['Valor'] = df_exibicao['Valor'].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        df_exibicao['Vencimento'] = df_exibicao['Vencimento'].dt.strftime('%d/%m/%Y')
        df_exibicao['Vencimento'] = df_exibicao['Vencimento'].fillna('Não informado')

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Total de registros exibidos: {len(df_filtrado)}")
    else:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")

    # ========== RODAPÉ NA SIDEBAR ==========
    st.sidebar.markdown("---")
    st.sidebar.caption("Dashboard Financeiro Gratuito")
    st.sidebar.caption("Desenvolvido por Edinaldo Gomes")
    st.sidebar.caption("📧 edinaldosantos.contato@gmail.com")
    st.sidebar.caption("v2025.1.2 | © 2025 Todos os direitos reservados")


if __name__ == "__main__":
    main()

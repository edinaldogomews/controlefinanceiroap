"""
Dashboard Financeiro Pessoal
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

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro Pessoal",
    page_icon="💰",
    layout="wide"
)

# Configurações do Google Sheets
CAMINHO_CREDENCIAIS = Path(__file__).parent / "credentials.json"
NOME_PLANILHA = "Controle Financeiro - DB"

# Colunas que utilizamos no dashboard
COLUNAS_NECESSARIAS = ['Vencimento', 'Descrição', 'Valor', 'Categoria', 'Status']


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
        planilha = cliente.open(NOME_PLANILHA)
        worksheet = planilha.sheet1

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
            f"""
            **Como resolver:**

            1. Copie o e-mail da conta de serviço (campo `client_email` nas credenciais)
            2. Vá até a planilha no Google Sheets
            3. Clique em **Compartilhar** e adicione o e-mail como **Editor**

            Erro técnico: {str(e)}
            """
        )
        return None

    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com Google Sheets: {str(e)}")
        return None


@st.cache_data(ttl=60)
def carregar_dados():
    """
    Carrega e limpa os dados do Google Sheets.
    Retorna um DataFrame limpo ou None em caso de erro.
    """
    try:
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

    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None


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


def main():
    # Título principal
    st.title("💰 Dashboard Financeiro Pessoal")
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
    with st.sidebar.expander("➕ Adicionar Nova Despesa", expanded=df.empty):
        # Campo de Data
        nova_data = st.date_input(
            "📅 Data de Vencimento",
            value=date.today(),
            format="DD/MM/YYYY"
        )

        # Campo de Descrição
        nova_descricao = st.text_input(
            "📝 Descrição",
            placeholder="Ex: Conta de Luz"
        )

        # Campo de Valor
        novo_valor = st.number_input(
            "💵 Valor (R$)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f"
        )

        # Campo de Categoria (puxando categorias existentes)
        categorias_opcoes = sorted(set(categorias_unicas))
        nova_categoria = st.selectbox(
            "🏷️ Categoria",
            options=categorias_opcoes
        )

        # Campo de Status
        novo_status = st.selectbox(
            "📊 Status",
            options=["EM ABERTO", "PAGO"]
        )

        # Botão de Salvar
        if st.button("💾 Salvar Transação", use_container_width=True):
            # Validações
            if not nova_descricao.strip():
                st.error("⚠️ A descrição é obrigatória!")
            elif novo_valor <= 0:
                st.error("⚠️ O valor deve ser maior que zero!")
            else:
                # Salvar a transação
                with st.spinner("Salvando..."):
                    sucesso, mensagem = salvar_nova_transacao(
                        nova_data,
                        nova_descricao.strip(),
                        novo_valor,
                        nova_categoria,
                        novo_status
                    )

                if sucesso:
                    st.success(f"✅ {mensagem}")
                    # Limpar cache e recarregar a página
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

    # Gráfico de Barras - Gastos por Status
    with col_grafico2:
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
                color_discrete_sequence=px.colors.qualitative.Pastel
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
                margin=dict(t=20, b=20, l=20, r=80)
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

        st.caption(f"📌 Total de registros exibidos: {len(df_filtrado)}")
    else:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")

    # Rodapé
    st.markdown("---")
    st.caption("💡 Dashboard Financeiro Pessoal | Desenvolvido por Edinaldo Gomes com Streamlit, Pandas e Plotly")


if __name__ == "__main__":
    main()

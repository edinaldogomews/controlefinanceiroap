"""
Dashboard Financeiro Pessoal
Desenvolvido com Streamlit, Pandas e Plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro Pessoal",
    page_icon="💰",
    layout="wide"
)

# Caminho do arquivo CSV
CAMINHO_CSV = Path(__file__).parent / "Controle de Despesas.xlsx - Fixos.csv"

# Colunas que utilizamos no dashboard
COLUNAS_NECESSARIAS = ['Vencimento', 'Descrição', 'Valor', 'Categoria', 'Status']


@st.cache_data
def carregar_dados():
    """
    Carrega e limpa os dados do arquivo CSV.
    Retorna um DataFrame limpo ou None em caso de erro.
    """
    try:
        # Carregar apenas as colunas necessárias
        df = pd.read_csv(
            CAMINHO_CSV,
            usecols=COLUNAS_NECESSARIAS,
            encoding='utf-8'
        )

        # Limpeza da coluna Valor
        def limpar_valor(valor):
            if pd.isna(valor):
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

        return df

    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None


def carregar_dados_brutos():
    """
    Carrega os dados brutos do CSV para salvar novas transações.
    Retorna o DataFrame completo ou None em caso de erro.
    """
    try:
        df = pd.read_csv(CAMINHO_CSV, encoding='utf-8')
        return df
    except Exception:
        return None


def salvar_nova_transacao(data_venc, descricao, valor, categoria, status):
    """
    Adiciona uma nova transação ao arquivo CSV.
    """
    try:
        # Carregar dados brutos (com todas as colunas originais)
        df_bruto = carregar_dados_brutos()

        if df_bruto is None:
            return False, "Erro ao carregar arquivo CSV."

        # Formatar a data no padrão dd/mm/yyyy
        data_formatada = data_venc.strftime('%d/%m/%Y')

        # Formatar o valor no padrão brasileiro (R$ X.XXX,XX)
        valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Criar nova linha com as colunas do CSV original
        # Preencher colunas extras com valores vazios
        nova_linha = {col: '' for col in df_bruto.columns}
        nova_linha['Vencimento'] = data_formatada
        nova_linha['Descrição'] = descricao
        nova_linha['Valor'] = valor_formatado
        nova_linha['Categoria'] = categoria
        nova_linha['Status'] = status

        # Criar DataFrame com a nova linha
        df_nova_linha = pd.DataFrame([nova_linha])

        # Concatenar com o DataFrame original
        df_atualizado = pd.concat([df_bruto, df_nova_linha], ignore_index=True)

        # Salvar de volta no CSV
        df_atualizado.to_csv(CAMINHO_CSV, index=False, encoding='utf-8')

        return True, "Transação salva com sucesso!"

    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def main():
    # Título principal
    st.title("💰 Dashboard Financeiro Pessoal")
    st.markdown("---")

    # Carregar dados
    df = carregar_dados()

    # Verificar se o arquivo foi encontrado
    if df is None:
        st.error("⚠️ Arquivo CSV não encontrado!")
        st.warning(
            f"""
            **Como resolver:**

            1. Verifique se o arquivo `Controle de Despesas.xlsx - Fixos.csv` existe na pasta do projeto.

            2. Se você tem apenas o arquivo Excel (.xlsx), exporte a aba "Fixos" como CSV:
               - Abra o arquivo `Controle de Despesas.xlsx` no Excel
               - Vá até a aba "Fixos"
               - Clique em **Arquivo > Salvar Como**
               - Escolha o formato **CSV UTF-8 (Delimitado por vírgulas)**
               - Salve como `Controle de Despesas.xlsx - Fixos.csv`

            3. Certifique-se de que o arquivo está no mesmo diretório do dashboard:
               `{CAMINHO_CSV.parent}`
            """
        )
        st.stop()

    # ========== SIDEBAR - FILTROS ==========
    st.sidebar.header("🔍 Filtros")

    # Filtro de Status
    status_unicos = df['Status'].unique().tolist()
    status_selecionados = st.sidebar.multiselect(
        "Status",
        options=status_unicos,
        default=status_unicos
    )

    # Filtro de Categoria
    categorias_unicas = df['Categoria'].unique().tolist()
    categorias_selecionadas = st.sidebar.multiselect(
        "Categoria",
        options=categorias_unicas,
        default=categorias_unicas
    )

    # ========== SIDEBAR - ADICIONAR NOVA DESPESA ==========
    st.sidebar.markdown("---")
    with st.sidebar.expander("➕ Adicionar Nova Despesa", expanded=False):
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
        categorias_opcoes = sorted(categorias_unicas)
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

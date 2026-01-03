"""
Somma - Página de Previsibilidade
Fluxo de Caixa com tabela de transações e saldos acumulados
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    exibir_menu_lateral,
    formatar_valor_br,
    get_armazenamento,
    carregar_dados,
    TIPOS_CONTA,
    TIPOS_TRANSACAO,
    CAT_DESPESA,
    CAT_RECEITA,
    CAT_VALE_REFEICAO
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Previsibilidade - Somma",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo global
aplicar_estilo_global()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_nome_dia_semana(data: date) -> str:
    """Retorna o nome do dia da semana em português."""
    dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    return dias[data.weekday()]


def obter_nome_mes(mes: int) -> str:
    """Retorna o nome do mês em português."""
    meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    return meses[mes]


def calcular_saldo_anterior(df: pd.DataFrame, conta: str, data_inicio_mes: date) -> float:
    """
    Calcula o saldo acumulado de uma conta específica
    considerando transações ANTERIORES ao primeiro dia do mês.
    """
    df_anterior = df[
        (df['Conta'] == conta) &
        (df['Data'].dt.date < data_inicio_mes)
    ].copy()

    if df_anterior.empty:
        return 0.0

    receitas = df_anterior[df_anterior['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df_anterior[df_anterior['Tipo'] == 'Despesa']['Valor'].sum()

    return receitas - despesas


def gerar_tabela_previsibilidade(df: pd.DataFrame, ano: int, mes: int) -> tuple:
    """
    Gera a tabela de previsibilidade com todas as transações do mês e saldos acumulados.
    Retorna um DataFrame com as transações e os saldos calculados linha a linha.
    """
    primeiro_dia = date(ano, mes, 1)

    # Preparar dados de transações
    df = df.copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

    # Calcular saldos anteriores ao mês (para cada conta)
    saldo_anterior_comum = calcular_saldo_anterior(df, 'Comum', primeiro_dia)
    saldo_anterior_vr = calcular_saldo_anterior(df, 'Vale Refeição', primeiro_dia)

    # Filtrar transações do mês
    df_mes = df[
        (df['Data'].dt.year == ano) &
        (df['Data'].dt.month == mes)
    ].copy()

    # Ordenar por data
    df_mes = df_mes.sort_values('Data').reset_index(drop=True)

    # Calcular saldo acumulado por transação
    saldo_comum = saldo_anterior_comum
    saldo_vr = saldo_anterior_vr
    saldos_comum = []
    saldos_vr = []

    for idx, row in df_mes.iterrows():
        valor = row['Valor']
        tipo = row['Tipo']
        conta = row['Conta']

        # Calcular movimento (positivo para receita, negativo para despesa)
        movimento = valor if tipo == 'Receita' else -valor

        if conta == 'Vale Refeição':
            saldo_vr += movimento
        else:
            saldo_comum += movimento

        saldos_comum.append(saldo_comum)
        saldos_vr.append(saldo_vr)

    df_mes['Saldo_Comum'] = saldos_comum
    df_mes['Saldo_VR'] = saldos_vr

    # Formatar data para exibição
    df_mes['Dia_Semana'] = df_mes['Data'].apply(lambda x: obter_nome_dia_semana(x.date()))
    df_mes['Data_Fmt'] = df_mes['Data'].dt.strftime('%d/%m')
    df_mes['Data_Display'] = df_mes['Dia_Semana'] + ' ' + df_mes['Data_Fmt']

    return df_mes, saldo_anterior_comum, saldo_anterior_vr


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():
    armazenamento = get_armazenamento()
    exibir_status_conexao(armazenamento)

    # Botão global de Novo Lançamento na sidebar
    exibir_menu_lateral(armazenamento)

    st.title("Previsibilidade")
    st.caption("Fluxo de Caixa - Visualize transações e saldos acumulados dia a dia")

    # Carregar dados
    df = carregar_dados()

    # Data de hoje
    data_hoje = date.today()

    # ========== SIDEBAR - SELEÇÃO DE MÊS/ANO ==========
    st.sidebar.header("Período")

    # Opções de mês
    meses_opcoes = {
        'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
        'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
        'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
    }

    col_mes, col_ano = st.sidebar.columns(2)

    with col_mes:
        mes_selecionado_nome = st.selectbox(
            "Mês",
            options=list(meses_opcoes.keys()),
            index=data_hoje.month - 1,
            key="prev_mes"
        )
        mes_selecionado = meses_opcoes[mes_selecionado_nome]

    with col_ano:
        ano_atual = data_hoje.year
        anos_opcoes = list(range(ano_atual - 1, ano_atual + 3))
        ano_selecionado = st.selectbox(
            "Ano",
            options=anos_opcoes,
            index=anos_opcoes.index(ano_atual),
            key="prev_ano"
        )

    # ========== VERIFICAR SE HÁ DADOS ==========
    if df.empty:
        st.warning("Nenhuma transação encontrada.")
        st.info("Acesse **Registrar** para adicionar transações!")
        exibir_rodape()
        st.stop()

    # ========== GERAR TABELA DE PREVISIBILIDADE ==========
    df_prev, saldo_ant_comum, saldo_ant_vr = gerar_tabela_previsibilidade(df, ano_selecionado, mes_selecionado)

    # ========== CARDS DE SALDO ==========
    st.subheader(f"Saldos em {obter_nome_mes(mes_selecionado)} {ano_selecionado}")

    # Calcular saldos finais
    if not df_prev.empty:
        saldo_final_comum = df_prev['Saldo_Comum'].iloc[-1]
        saldo_final_vr = df_prev['Saldo_VR'].iloc[-1]
    else:
        saldo_final_comum = saldo_ant_comum
        saldo_final_vr = saldo_ant_vr

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Saldo Anterior (Comum)",
            value=formatar_valor_br(saldo_ant_comum),
            help="Saldo acumulado antes do início do mês"
        )

    with col2:
        st.metric(
            label="Saldo Anterior (VR)",
            value=formatar_valor_br(saldo_ant_vr),
            help="Saldo acumulado antes do início do mês"
        )

    with col3:
        st.metric(
            label="Saldo Final Projetado",
            value=formatar_valor_br(saldo_final_comum + saldo_final_vr),
            delta=f"Comum: {formatar_valor_br(saldo_final_comum)}"
        )

    st.markdown("---")

    # ========== RESUMO DO MÊS ==========
    if not df_prev.empty:
        total_receitas = df_prev[df_prev['Tipo'] == 'Receita']['Valor'].sum()
        total_despesas = df_prev[df_prev['Tipo'] == 'Despesa']['Valor'].sum()
    else:
        total_receitas = 0
        total_despesas = 0

    saldo_mes = total_receitas - total_despesas

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        st.metric("Receitas do Mês", formatar_valor_br(total_receitas))
    with col_r2:
        st.metric("Despesas do Mês", formatar_valor_br(total_despesas))
    with col_r3:
        st.metric("Saldo do Mês", formatar_valor_br(saldo_mes),
                  delta="Positivo" if saldo_mes >= 0 else "Negativo")
    with col_r4:
        st.metric("Transações", len(df_prev))

    st.markdown("---")

    # ========== TABELA DE TRANSAÇÕES COM PREVISIBILIDADE ==========
    st.subheader(f"Transações de {obter_nome_mes(mes_selecionado)} {ano_selecionado}")

    if df_prev.empty:
        st.info("Nenhuma transação neste mês.")
    else:
        # Preparar DataFrame para exibição
        df_display = df_prev.copy()

        # Formatar valores
        df_display['Valor_Fmt'] = df_display['Valor'].apply(formatar_valor_br)
        df_display['Saldo_Comum_Fmt'] = df_display['Saldo_Comum'].apply(formatar_valor_br)
        df_display['Saldo_VR_Fmt'] = df_display['Saldo_VR'].apply(formatar_valor_br)

        # Selecionar e renomear colunas
        cols_exibir = ['Data_Display', 'Descricao', 'Categoria', 'Valor_Fmt', 'Tipo', 'Conta', 'Saldo_Comum_Fmt', 'Saldo_VR_Fmt']
        df_tabela = df_display[cols_exibir].copy()
        df_tabela.columns = ['Data', 'Descrição', 'Categoria', 'Valor', 'Tipo', 'Conta', 'Saldo Comum', 'Saldo VR']

        st.dataframe(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "Data": st.column_config.TextColumn("Data", width="medium"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="small"),
                "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                "Conta": st.column_config.TextColumn("Conta", width="small"),
                "Saldo Comum": st.column_config.TextColumn("Saldo Comum", width="medium"),
                "Saldo VR": st.column_config.TextColumn("Saldo VR", width="medium"),
            }
        )

    # ========== LEGENDA ==========
    st.markdown("""
    <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap; font-family: sans-serif;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 0.85rem; color: #555;">💡 A tabela exibe cada transação individualmente, atualizando o saldo acumulado linha a linha.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()

"""
Somma - Página de Extrato
Tabela de transações com filtros e gerenciamento (editar/excluir)
"""

import streamlit as st
import pandas as pd

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    exibir_menu_lateral,
    formatar_valor_br,
    formatar_mes_ano_completo,
    get_armazenamento,
    carregar_dados
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Extrato - Somma",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo global
aplicar_estilo_global()


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():
    # Obter sistema de armazenamento
    armazenamento = get_armazenamento()

    # Exibir status de conexão
    exibir_status_conexao(armazenamento)

    # Botão global de Novo Lançamento na sidebar
    exibir_menu_lateral(armazenamento)

    # Título da página (compacto)
    st.title("Extrato")
    st.caption("Visualize, filtre e gerencie todas as suas transações.")

    # Carregar dados
    df = carregar_dados()

    # Verificar se há dados
    if df.empty:
        st.warning("Nenhuma transação encontrada.")
        st.info("Acesse a página **Registrar** para adicionar sua primeira transação!")
        exibir_rodape()
        st.stop()

    # ========== PREPARAR DADOS ==========
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['Mes_Ano'] = df['Data'].dt.to_period('M').astype(str)

    # Obter listas únicas
    tipos_unicos = df['Tipo'].unique().tolist()
    categorias_unicas = df['Categoria'].unique().tolist()
    contas_unicas = df['Conta'].unique().tolist()

    # Obter meses únicos
    meses_unicos = df[df['Mes_Ano'] != 'NaT']['Mes_Ano'].dropna().unique().tolist()
    meses_unicos = sorted(meses_unicos, reverse=True)
    meses_formatados = [formatar_mes_ano_completo(m) for m in meses_unicos]

    # ========== FILTROS EM LINHA (4 colunas no topo) ==========
    opcoes_meses = ["Todos os meses"] + meses_formatados

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        mes_selecionado_fmt = st.selectbox(
            "Período",
            options=opcoes_meses,
            index=0,
            key="filtro_mes_extrato"
        )

    with col_f2:
        tipos_selecionados = st.multiselect(
            "Tipo",
            options=tipos_unicos,
            default=tipos_unicos,
            key="filtro_tipo_extrato"
        )

    with col_f3:
        categorias_selecionadas = st.multiselect(
            "Categoria",
            options=categorias_unicas,
            default=categorias_unicas,
            key="filtro_categoria_extrato"
        )

    with col_f4:
        contas_selecionadas = st.multiselect(
            "Conta",
            options=contas_unicas,
            default=contas_unicas,
            key="filtro_conta_extrato"
        )

    # Determinar mês selecionado
    if mes_selecionado_fmt == "Todos os meses":
        mes_selecionado = None
    else:
        idx = meses_formatados.index(mes_selecionado_fmt)
        mes_selecionado = meses_unicos[idx]

    # ========== APLICAR FILTROS ==========
    df_filtrado = df.copy()

    if mes_selecionado is not None:
        df_filtrado = df_filtrado[df_filtrado['Mes_Ano'] == mes_selecionado]

    if tipos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos_selecionados)]

    if categorias_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_selecionadas)]

    if contas_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['Conta'].isin(contas_selecionadas)]

    # ========== RESUMO DO PERÍODO (compacto) ==========
    total_receitas = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_periodo = total_receitas - total_despesas

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        st.metric("Receitas", formatar_valor_br(total_receitas))
    with col_r2:
        st.metric("Despesas", formatar_valor_br(total_despesas))
    with col_r3:
        st.metric("Saldo", formatar_valor_br(saldo_periodo),
                  delta="Positivo" if saldo_periodo >= 0 else "Negativo")
    with col_r4:
        st.metric("Transações", len(df_filtrado))

    st.markdown("---")

    # ========== TABELA DE TRANSAÇÕES ==========
    titulo_tabela = f"Transações de {mes_selecionado_fmt}" if mes_selecionado else "Todas as Transações"
    st.subheader(titulo_tabela)

    if df_filtrado.empty:
        st.warning("Nenhuma transação encontrada com os filtros selecionados.")
    else:
        df_exibicao = df_filtrado.copy()
        df_exibicao['Valor_Fmt'] = df_exibicao['Valor'].apply(formatar_valor_br)
        df_exibicao['Data_Fmt'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
        df_exibicao['Data_Fmt'] = df_exibicao['Data_Fmt'].fillna('—')

        df_tabela = df_exibicao[['Data_Fmt', 'Descricao', 'Categoria', 'Valor_Fmt', 'Tipo', 'Conta']].copy()
        df_tabela.columns = ['Data', 'Descrição', 'Categoria', 'Valor', 'Tipo', 'Conta']

        st.dataframe(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Data": st.column_config.TextColumn("Data", width="small"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="small"),
                "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                "Conta": st.column_config.TextColumn("Conta", width="small"),
            }
        )
        st.caption(f"Total: {len(df_filtrado)} registros")


    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()

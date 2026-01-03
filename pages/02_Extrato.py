"""
Somma - Página de Extrato
Tabela de transações com filtros e gerenciamento (editar/excluir)
"""

import streamlit as st
import pandas as pd
from datetime import date

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    exibir_menu_lateral,
    formatar_valor_br,
    formatar_mes_ano_completo,
    get_armazenamento,
    carregar_dados,
    limpar_cache_e_recarregar,
    TIPOS_CONTA,
    TIPOS_TRANSACAO,
    CATEGORIAS_PADRAO
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

    # ========== GERENCIAR LANÇAMENTOS (dentro de Expander) ==========
    with st.expander("Gerenciar Lançamentos", expanded=False):
        if df.empty:
            st.warning("Nenhum lançamento para gerenciar.")
        else:
            df_reset = df.reset_index(drop=True)

            # Lista de opções para seleção (ordenar por data decrescente para mostrar mais recentes primeiro)
            df_ordenado = df_reset.copy()
            df_ordenado['Data'] = pd.to_datetime(df_ordenado['Data'], errors='coerce')
            df_ordenado = df_ordenado.sort_values('Data', ascending=False).reset_index(drop=True)

            opcoes_gerenciar = []
            indices_originais = []
            for idx, row in df_ordenado.iterrows():
                # Guardar o índice original do DataFrame não ordenado
                idx_original = df_reset[(df_reset['Descricao'] == row['Descricao']) &
                                        (df_reset['Valor'] == row['Valor']) &
                                        (df_reset['Data'] == row['Data'])].index
                if len(idx_original) > 0:
                    idx_original = idx_original[0]
                else:
                    idx_original = idx

                indices_originais.append(idx_original)
                data_fmt = row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else '—'
                valor_fmt = formatar_valor_br(row['Valor'])
                desc = str(row['Descricao'])[:20]
                emoji = "+" if row['Tipo'] == 'Receita' else "-"
                opcoes_gerenciar.append(f"{idx_original}: {emoji} {data_fmt} | {desc} | {valor_fmt}")

            lancamento_selecionado = st.selectbox(
                "Selecione o lançamento:",
                options=opcoes_gerenciar,
                index=0,  # Seleciona o primeiro (mais recente)
                key="select_gerenciar",
                label_visibility="collapsed"
            )

            if lancamento_selecionado:
                indice_selecionado = int(lancamento_selecionado.split(":")[0])
                lancamento = df_reset.iloc[indice_selecionado]

                # ========== FORMULÁRIO DE EDIÇÃO EM GRID ==========
                with st.form(key=f"form_editar_{indice_selecionado}"):

                    # Linha 1: Data, Valor, Categoria
                    col_e1, col_e2, col_e3 = st.columns([1, 1, 2])

                    with col_e1:
                        data_valor = lancamento['Data'].date() if pd.notna(lancamento['Data']) else date.today()
                        edit_data = st.date_input("Data", value=data_valor, format="DD/MM/YYYY")

                    with col_e2:
                        edit_valor = st.number_input(
                            "Valor",
                            min_value=0.0,
                            value=float(lancamento['Valor']),
                            step=0.01,
                            format="%.2f"
                        )

                    with col_e3:
                        cat_atual = str(lancamento['Categoria'])
                        cats_edit = sorted(set(CATEGORIAS_PADRAO + categorias_unicas + [cat_atual]))
                        idx_cat = cats_edit.index(cat_atual) if cat_atual in cats_edit else 0
                        edit_categoria = st.selectbox("Categoria", options=cats_edit, index=idx_cat)

                    # Linha 2: Descrição
                    edit_descricao = st.text_input("Descrição", value=str(lancamento['Descricao']))

                    # Linha 3: Tipo e Conta
                    col_e4, col_e5 = st.columns(2)

                    with col_e4:
                        tipo_atual = str(lancamento['Tipo'])
                        idx_tipo = TIPOS_TRANSACAO.index(tipo_atual) if tipo_atual in TIPOS_TRANSACAO else 0
                        edit_tipo = st.selectbox("Tipo", options=TIPOS_TRANSACAO, index=idx_tipo)

                    with col_e5:
                        conta_atual = str(lancamento['Conta'])
                        conta_display = 'Conta Comum' if conta_atual == 'Comum' else conta_atual
                        idx_conta = TIPOS_CONTA.index(conta_display) if conta_display in TIPOS_CONTA else 0
                        edit_conta = st.selectbox("Conta", options=TIPOS_CONTA, index=idx_conta)

                    # Botões lado a lado
                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:
                        submit_editar = st.form_submit_button(
                            "Salvar Alterações",
                            use_container_width=True,
                            type="primary"
                        )

                    if submit_editar:
                        if not edit_descricao.strip():
                            st.error("A descrição é obrigatória!")
                        elif edit_valor <= 0:
                            st.error("O valor deve ser maior que zero!")
                        else:
                            conta_salvar = "Vale Refeição" if edit_conta == "Vale Refeição" else "Comum"

                            with st.spinner("Salvando..."):
                                sucesso, mensagem = armazenamento.editar_transacao(
                                    indice_selecionado,
                                    edit_data,
                                    edit_descricao.strip(),
                                    edit_categoria,
                                    edit_valor,
                                    edit_tipo,
                                    conta_salvar
                                )

                            if sucesso:
                                st.success(mensagem)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(mensagem)

                # Botão de exclusão (fora do form)
                st.markdown("---")
                col_excl1, col_excl2, col_excl3 = st.columns([1, 1, 2])

                with col_excl1:
                    if st.button("Excluir Lançamento", use_container_width=True, type="secondary"):
                        st.session_state['confirmar_exclusao'] = True

                with col_excl2:
                    if st.session_state.get('confirmar_exclusao', False):
                        if st.button("Confirmar Exclusão", use_container_width=True, type="primary"):
                            with st.spinner("Excluindo..."):
                                sucesso, mensagem = armazenamento.excluir_transacao(indice_selecionado)

                            if sucesso:
                                st.success(mensagem)
                                st.session_state['confirmar_exclusao'] = False
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(mensagem)

                with col_excl3:
                    if st.session_state.get('confirmar_exclusao', False):
                        st.warning("Esta ação não pode ser desfeita!")

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()

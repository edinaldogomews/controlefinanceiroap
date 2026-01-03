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
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
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

            # Lista de opções para seleção
            opcoes_gerenciar = []
            for idx, row in df_reset.iterrows():
                data_fmt = row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else '—'
                valor_fmt = formatar_valor_br(row['Valor'])
                desc = str(row['Descricao'])[:20]
                emoji = "+" if row['Tipo'] == 'Receita' else "-"
                opcoes_gerenciar.append(f"{idx}: {emoji} {data_fmt} | {desc} | {valor_fmt}")

            lancamento_selecionado = st.selectbox(
                "Selecione o lançamento:",
                options=opcoes_gerenciar,
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
"""
Somma - Página de Registro de Transações
Formulário para adicionar novas transações
"""

import streamlit as st
from datetime import date

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    get_armazenamento,
    carregar_dados,
    limpar_cache_e_recarregar,
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
    page_title="Registrar - Somma",
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

    # Título da página (compacto)
    st.title("Nova Transação")
    st.caption("Adicione uma nova receita ou despesa ao seu controle financeiro.")

    # Carregar dados existentes para categorias personalizadas
    df = carregar_dados()

    # ========== LINHA 1: CONTA E TIPO (lado a lado) ==========
    col_conta, col_tipo = st.columns(2)

    with col_conta:
        nova_conta = st.radio(
            "Conta",
            options=TIPOS_CONTA,
            horizontal=True,
            key="form_conta_radio",
            help="Conta Comum ou Vale Refeição"
        )

    with col_tipo:
        novo_tipo = st.radio(
            "Tipo",
            options=TIPOS_TRANSACAO,
            horizontal=True,
            key="form_tipo_radio",
            help="Receita ou Despesa"
        )

    # Lógica condicional de categorias baseada na Conta e Tipo
    if nova_conta == "Vale Refeição" and novo_tipo == "Despesa":
        categorias_do_tipo = CAT_VALE_REFEICAO.copy()
    elif novo_tipo == "Receita":
        categorias_do_tipo = CAT_RECEITA.copy()
    else:
        categorias_do_tipo = CAT_DESPESA.copy()

    # Adicionar categorias personalizadas do histórico
    if not df.empty:
        if nova_conta != "Vale Refeição" or novo_tipo != "Despesa":
            categorias_existentes = df[df['Tipo'] == novo_tipo]['Categoria'].unique().tolist()
            for cat in categorias_existentes:
                if cat not in categorias_do_tipo:
                    categorias_do_tipo.append(cat)

    categorias_do_tipo = sorted(categorias_do_tipo)

    # ========== FORMULÁRIO PRINCIPAL ==========
    with st.form(key="form_nova_transacao", clear_on_submit=True):

        # ========== LINHA 2: DATA, VALOR, CATEGORIA (proporção 1:1:2) ==========
        col_data, col_valor, col_categoria = st.columns([1, 1, 2])

        with col_data:
            nova_data = st.date_input(
                "Data",
                value=date.today(),
                format="DD/MM/YYYY",
                key="form_data"
            )

        with col_valor:
            novo_valor = st.number_input(
                "Valor (R$)",
                min_value=0.00,
                value=None,
                step=0.01,
                format="%.2f",
                placeholder="0.00",
                key="form_valor"
            )

        with col_categoria:
            nova_categoria = st.selectbox(
                "Categoria",
                options=categorias_do_tipo,
                key="form_categoria",
                help=f"Categorias para {nova_conta} - {novo_tipo}"
            )

        # ========== LINHA 3: DESCRIÇÃO (largura total) ==========
        nova_descricao = st.text_input(
            "Descrição",
            value="",
            placeholder="Ex: Conta de Luz" if novo_tipo == "Despesa" else "Ex: Salário Mensal",
            key="form_descricao"
        )

        # ========== BOTÃO SALVAR ==========
        submit_button = st.form_submit_button(
            "Salvar",
            use_container_width=True,
            type="primary"
        )

        if submit_button:
            valor_para_salvar = novo_valor if novo_valor is not None else 0.0

            if not nova_descricao.strip():
                st.error("A descrição é obrigatória!")
            elif valor_para_salvar <= 0:
                st.error("O valor deve ser maior que zero!")
            else:
                conta_para_salvar = "Vale Refeição" if nova_conta == "Vale Refeição" else "Comum"

                with st.spinner("Salvando..."):
                    sucesso, mensagem = armazenamento.salvar_transacao(
                        nova_data,
                        nova_descricao.strip(),
                        nova_categoria,
                        valor_para_salvar,
                        novo_tipo,
                        conta_para_salvar
                    )

                if sucesso:
                    st.success(mensagem)
                    st.balloons()
                    st.cache_data.clear()
                else:
                    st.error(mensagem)

    # ========== DICAS (Compacto) ==========
    with st.expander("Dicas para um bom controle financeiro", expanded=False):
        col_dica1, col_dica2 = st.columns(2)
        with col_dica1:
            st.markdown("""
            - **Registre todas as transações** - pequenas despesas fazem diferença
            - **Use categorias consistentes** - facilita a análise
            - **Atualize regularmente** - registre no mesmo dia
            """)
        with col_dica2:
            st.markdown("""
            - **Separe contas diferentes** - use Vale Refeição separadamente
            - **Revise mensalmente** - identifique oportunidades de economia
            """)

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()


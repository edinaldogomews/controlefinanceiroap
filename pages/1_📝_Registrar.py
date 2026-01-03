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
    page_icon="📝",
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
    st.title("📝 Registrar Transação")
    st.caption("Adicione uma nova receita ou despesa ao seu controle financeiro.")

    # Carregar dados existentes para categorias personalizadas
    df = carregar_dados()

    # ========== LINHA 1: CONTA E TIPO (lado a lado) ==========
    col_conta, col_tipo = st.columns(2)

    with col_conta:
        nova_conta = st.radio(
            "🏦 Conta",
            options=TIPOS_CONTA,
            horizontal=True,
            key="form_conta_radio",
            help="Conta Comum ou Vale Refeição"
        )

    with col_tipo:
        novo_tipo = st.radio(
            "📊 Tipo",
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
                "📅 Data",
                value=date.today(),
                format="DD/MM/YYYY",
                key="form_data"
            )

        with col_valor:
            novo_valor = st.number_input(
                "💵 Valor (R$)",
                min_value=0.00,
                value=None,
                step=0.01,
                format="%.2f",
                placeholder="0.00",
                key="form_valor"
            )

        with col_categoria:
            nova_categoria = st.selectbox(
                "🏷️ Categoria",
                options=categorias_do_tipo,
                key="form_categoria",
                help=f"Categorias para {nova_conta} - {novo_tipo}"
            )

        # ========== LINHA 3: DESCRIÇÃO (largura total) ==========
        nova_descricao = st.text_input(
            "📝 Descrição",
            value="",
            placeholder="Ex: Conta de Luz" if novo_tipo == "Despesa" else "Ex: Salário Mensal",
            key="form_descricao"
        )

        # ========== BOTÃO SALVAR ==========
        submit_button = st.form_submit_button(
            "💾 Salvar Transação",
            use_container_width=True,
            type="primary"
        )

        if submit_button:
            valor_para_salvar = novo_valor if novo_valor is not None else 0.0

            if not nova_descricao.strip():
                st.error("⚠️ A descrição é obrigatória!")
            elif valor_para_salvar <= 0:
                st.error("⚠️ O valor deve ser maior que zero!")
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
                    st.success(f"✅ {mensagem}")
                    st.balloons()
                    st.cache_data.clear()
                else:
                    st.error(f"❌ {mensagem}")

    # ========== DICAS (Compacto) ==========
    with st.expander("💡 Dicas para um bom controle financeiro", expanded=False):
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

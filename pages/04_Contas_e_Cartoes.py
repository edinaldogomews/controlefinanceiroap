"""
Somma - Página de Contas e Cartões
Gerenciamento de contas bancárias e cartões de crédito
"""

import streamlit as st
from datetime import datetime

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    exibir_menu_lateral,
    formatar_valor_br,
    get_armazenamento,
    CATALOGO_BANCOS,
    LISTA_BANCOS,
    carregar_contas,
    salvar_conta,
    excluir_conta,
    editar_conta,
    obter_conta_por_id,
    carregar_cartoes,
    salvar_cartao,
    excluir_cartao,
    obter_banco_info,
    TIPOS_GRUPO_CONTA
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Contas e Cartões - Somma",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo global
aplicar_estilo_global()

# CSS adicional para esta página
st.markdown("""
<style>
/* ===== CARDS DE CONTAS ===== */
.conta-card {
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}
.conta-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

/* ===== CARTÃO DE CRÉDITO VIRTUAL ===== */
.cartao-credito {
    width: 100%;
    max-width: 380px;
    height: 220px;
    border-radius: 16px;
    padding: 25px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    transition: transform 0.3s, box-shadow 0.3s;
}
.cartao-credito:hover {
    transform: scale(1.02);
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
}
.cartao-credito::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
}
.cartao-logo {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 60px;
    height: auto;
    opacity: 0.9;
}
.cartao-chip {
    width: 45px;
    height: 35px;
    background: linear-gradient(135deg, #f0c14b, #d4a437);
    border-radius: 6px;
    margin-bottom: 25px;
}
.cartao-numero {
    font-family: 'Courier New', monospace;
    font-size: 1.1rem;
    letter-spacing: 3px;
    margin-bottom: 20px;
}
.cartao-info {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.cartao-nome {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.cartao-validade {
    text-align: right;
    font-size: 0.8rem;
}
.cartao-validade span {
    display: block;
    font-size: 0.65rem;
    opacity: 0.7;
}

/* ===== PREVIEW DO BANCO ===== */
.banco-preview {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
.banco-preview img {
    width: 50px;
    height: 50px;
    object-fit: contain;
}
.banco-preview-nome {
    font-weight: 600;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DIALOGS (MODAIS)
# ============================================================

@st.dialog("✏️ Editar Conta", width="small")
def modal_editar_conta(conta_id: int):
    """Modal para editar uma conta bancária existente."""

    conta = obter_conta_por_id(conta_id)
    if not conta:
        st.error("Conta não encontrada!")
        return

    st.markdown("### Editar Conta")

    # Preview do banco
    cor = conta['cor_hex']
    logo = conta['logo_url']
    banco_nome = conta['banco_nome']

    if logo:
        st.markdown(f"""
        <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
            <img src="{logo}" alt="{banco_nome}">
            <span class="banco-preview-nome" style="color: {cor};">{banco_nome}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
            <div style="width: 50px; height: 50px; background: {cor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">
                {banco_nome[0]}
            </div>
            <span class="banco-preview-nome" style="color: {cor};">{banco_nome}</span>
        </div>
        """, unsafe_allow_html=True)

    # Inputs
    novo_nome = st.text_input(
        "Nome da Conta",
        value=conta['nome'],
        key="modal_edit_nome_conta"
    )

    # Tipo de Grupo da Conta
    tipo_atual = conta.get('tipo_grupo', 'Disponível')
    idx_tipo = TIPOS_GRUPO_CONTA.index(tipo_atual) if tipo_atual in TIPOS_GRUPO_CONTA else 0

    novo_tipo_grupo = st.selectbox(
        "Tipo de Conta",
        options=TIPOS_GRUPO_CONTA,
        index=idx_tipo,
        key="modal_edit_tipo_grupo_conta",
        help="**Disponível**: Conta bancária, dinheiro, investimentos. **Benefício**: Vale Refeição, Vale Alimentação, etc."
    )

    novo_saldo = st.number_input(
        "Saldo Inicial (R$)",
        min_value=0.0,
        value=float(conta['saldo_inicial']),
        step=0.01,
        format="%.2f",
        key="modal_edit_saldo_inicial"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_edit_conta"):
            st.rerun()

    with col2:
        if st.button("✅ Salvar", type="primary", use_container_width=True, key="btn_save_edit_conta"):
            sucesso, msg = editar_conta(conta_id, novo_nome, novo_saldo, novo_tipo_grupo)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


@st.dialog("➕ Nova Conta Bancária", width="small")
def modal_nova_conta():
    """Modal para adicionar nova conta bancária."""

    st.markdown("### Dados da Conta")

    # Selectbox de bancos
    banco_selecionado = st.selectbox(
        "Banco",
        options=LISTA_BANCOS,
        format_func=lambda x: CATALOGO_BANCOS[x]['nome'],
        key="modal_banco_conta"
    )

    # Preview do banco selecionado
    if banco_selecionado:
        banco_info = CATALOGO_BANCOS[banco_selecionado]
        cor = banco_info['cor_hex']
        logo = banco_info['logo_url']

        if logo:
            st.markdown(f"""
            <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
                <img src="{logo}" alt="{banco_info['nome']}">
                <span class="banco-preview-nome" style="color: {cor};">{banco_info['nome']}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
                <div style="width: 50px; height: 50px; background: {cor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">
                    {banco_info['nome'][0]}
                </div>
                <span class="banco-preview-nome" style="color: {cor};">{banco_info['nome']}</span>
            </div>
            """, unsafe_allow_html=True)

    # Inputs
    nome_conta = st.text_input(
        "Nome da Conta (opcional)",
        placeholder=f"Ex: Conta Principal (padrão: {CATALOGO_BANCOS[banco_selecionado]['nome']})",
        key="modal_nome_conta"
    )

    # Tipo de Grupo da Conta
    tipo_grupo = st.selectbox(
        "Tipo de Conta",
        options=TIPOS_GRUPO_CONTA,
        index=0,
        key="modal_tipo_grupo_conta",
        help="**Disponível**: Conta bancária, dinheiro, investimentos. **Benefício**: Vale Refeição, Vale Alimentação, etc."
    )

    # Informativo sobre o tipo selecionado
    if tipo_grupo == 'Disponível':
        st.info("**Conta Disponível**: Dinheiro de livre movimentação (bancos, carteiras, investimentos)")
    else:
        st.info("**Conta Benefício**: Vales e benefícios com uso restrito (VR, VA, VT, etc.)")

    saldo_inicial = st.number_input(
        "Saldo Inicial (R$)",
        min_value=0.0,
        value=None,
        step=0.01,
        format="%.2f",
        placeholder="0.00",
        key="modal_saldo_inicial"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("✅ Salvar", type="primary", use_container_width=True):
            # Se nome não preenchido, usar o nome do banco
            nome_final = nome_conta.strip() if nome_conta.strip() else CATALOGO_BANCOS[banco_selecionado]['nome']

            sucesso, msg = salvar_conta(nome_final, banco_selecionado, saldo_inicial, tipo_grupo)
            if sucesso:
                st.success(msg)
                st.balloons()
                st.rerun()
            else:
                st.error(msg)


@st.dialog("➕ Novo Cartão de Crédito", width="small")
def modal_novo_cartao():
    """Modal para adicionar novo cartão de crédito."""

    st.markdown("### Dados do Cartão")

    # Selectbox de bancos
    banco_selecionado = st.selectbox(
        "Banco/Emissor",
        options=LISTA_BANCOS,
        format_func=lambda x: CATALOGO_BANCOS[x]['nome'],
        key="modal_banco_cartao"
    )

    # Preview do banco selecionado
    if banco_selecionado:
        banco_info = CATALOGO_BANCOS[banco_selecionado]
        cor = banco_info['cor_hex']
        logo = banco_info['logo_url']

        if logo:
            st.markdown(f"""
            <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
                <img src="{logo}" alt="{banco_info['nome']}">
                <span class="banco-preview-nome" style="color: {cor};">{banco_info['nome']}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="banco-preview" style="background-color: {cor}20; border: 2px solid {cor};">
                <div style="width: 50px; height: 50px; background: {cor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">
                    {banco_info['nome'][0]}
                </div>
                <span class="banco-preview-nome" style="color: {cor};">{banco_info['nome']}</span>
            </div>
            """, unsafe_allow_html=True)

    # Inputs
    nome_cartao = st.text_input(
        "Nome do Cartão (opcional)",
        placeholder=f"Ex: Platinum (padrão: {CATALOGO_BANCOS[banco_selecionado]['nome']})",
        key="modal_nome_cartao"
    )

    limite = st.number_input(
        "Limite Total (R$)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        format="%.2f",
        key="modal_limite"
    )

    col_dias1, col_dias2 = st.columns(2)

    with col_dias1:
        dia_fechamento = st.number_input(
            "Dia de Fechamento",
            min_value=1,
            max_value=31,
            value=1,
            key="modal_dia_fechamento"
        )

    with col_dias2:
        dia_vencimento = st.number_input(
            "Dia de Vencimento",
            min_value=1,
            max_value=31,
            value=10,
            key="modal_dia_vencimento"
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_cartao"):
            st.rerun()

    with col2:
        if st.button("✅ Salvar", type="primary", use_container_width=True, key="btn_save_cartao"):
            # Se nome não preenchido, usar o nome do banco
            nome_final = nome_cartao.strip() if nome_cartao.strip() else CATALOGO_BANCOS[banco_selecionado]['nome']

            if limite <= 0:
                st.error("O limite deve ser maior que zero!")
            else:
                sucesso, msg = salvar_cartao(
                    nome_final,
                    banco_selecionado,
                    limite,
                    dia_fechamento,
                    dia_vencimento
                )
                if sucesso:
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)


# ============================================================
# FUNÇÕES DE RENDERIZAÇÃO
# ============================================================

def renderizar_card_conta(conta: dict):
    """Renderiza um card de conta bancária."""
    cor = conta['cor_hex']
    logo = conta['logo_url']
    nome = conta['nome']
    banco_nome = conta['banco_nome']
    saldo = conta['saldo_inicial']

    logo_html = f'<img src="{logo}" style="width: 40px; height: 40px; object-fit: contain;">' if logo else f'<div style="width: 40px; height: 40px; background: {cor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">{banco_nome[0]}</div>'

    st.markdown(f"""
    <div class="conta-card" style="background: linear-gradient(135deg, {cor}15, {cor}05); border-left: 4px solid {cor};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; align-items: center; gap: 12px;">
                {logo_html}
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #333;">{nome}</div>
                    <div style="font-size: 0.85rem; color: #666;">{banco_nome}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; color: #888; text-transform: uppercase;">Saldo Inicial</div>
                <div style="font-weight: 700, font-size: 1.2rem; color: {cor};">{formatar_valor_br(saldo)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return conta['id']


def renderizar_cartao_credito(cartao: dict):
    """Renderiza um cartão de crédito virtual estilizado."""
    cor = cartao['cor_hex']
    cor_sec = cartao['cor_secundaria']
    logo = cartao['logo_url']
    nome = cartao['nome']
    limite = cartao['limite']
    dia_fech = cartao['dia_fechamento']
    dia_venc = cartao['dia_vencimento']

    ultimos_digitos = str(cartao['id']).zfill(4)[-4:]
    logo_html = f'<img src="{logo}" class="cartao-logo">' if logo else ''

    st.markdown(f"""
    <div class="cartao-credito" style="background: linear-gradient(135deg, {cor}, {cor}CC);">
        {logo_html}
        <div class="cartao-chip"></div>
        <div class="cartao-numero" style="color: {cor_sec};">
            •••• •••• •••• {ultimos_digitos}
        </div>
        <div class="cartao-info">
            <div class="cartao-nome" style="color: {cor_sec};">{nome}</div>
            <div class="cartao-validade" style="color: {cor_sec};">
                <span>VENCIMENTO</span>
                Dia {dia_venc:02d}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top: 10px; padding: 10px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
            <span style="color: #666;">💳 Limite: <strong>{formatar_valor_br(limite)}</strong></span>
            <span style="color: #666;">📅 Fecha dia <strong>{dia_fech:02d}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return cartao['id']


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():
    armazenamento = get_armazenamento()
    exibir_status_conexao(armazenamento)
    exibir_menu_lateral(armazenamento)

    st.title("Contas e Cartões")
    st.caption("Gerencie suas contas bancárias e cartões de crédito")

    # Criar abas
    tab_contas, tab_cartoes = st.tabs(["🏦 Minhas Contas", "💳 Meus Cartões"])

    # ========== ABA: MINHAS CONTAS ==========
    with tab_contas:
        st.markdown("### Minhas Contas Bancárias")

        # Botão Nova Conta
        if st.button("Nova Conta", type="primary", key="btn_nova_conta"):
            modal_nova_conta()

        st.markdown("---")

        # Carregar e exibir contas
        contas = carregar_contas()

        if not contas:
            st.info("💡 Você ainda não cadastrou nenhuma conta bancária.")
            st.markdown("""
            <div style="text-align: center; padding: 30px; color: #888;">
                <div style="font-size: 3rem; margin-bottom: 10px;">🏦</div>
                <p>Clique em <strong>"➕ Nova Conta"</strong> para começar!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Exibir cards em grid
            cols = st.columns(2)

            for idx, conta in enumerate(contas):
                with cols[idx % 2]:
                    conta_id = renderizar_card_conta(conta)

                    # Botões de ação (Editar e Excluir) - lado a lado, compactos
                    col_spacer, col_edit, col_del, col_spacer2 = st.columns([2, 1, 1, 2])

                    with col_edit:
                        if st.button("Editar", key=f"edit_conta_{conta_id}", help="Editar esta conta"):
                            modal_editar_conta(conta_id)

                    with col_del:
                        if st.button("Excluir", key=f"del_conta_{conta_id}", help="Excluir esta conta"):
                            sucesso, msg = excluir_conta(conta_id)
                            if sucesso:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    st.markdown("<br>", unsafe_allow_html=True)

    # ========== ABA: MEUS CARTÕES ==========
    with tab_cartoes:
        st.markdown("### Meus Cartões de Crédito")

        # Botão Novo Cartão
        if st.button("➕ Novo Cartão", type="primary", key="btn_novo_cartao"):
            modal_novo_cartao()

        st.markdown("---")

        # Carregar e exibir cartões
        cartoes = carregar_cartoes()

        if not cartoes:
            st.info("💡 Você ainda não cadastrou nenhum cartão de crédito.")
            st.markdown("""
            <div style="text-align: center; padding: 30px; color: #888;">
                <div style="font-size: 3rem; margin-bottom: 10px;">💳</div>
                <p>Clique em <strong>"➕ Novo Cartão"</strong> para começar!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Exibir cartões em grid
            cols = st.columns(2)

            for idx, cartao in enumerate(cartoes):
                with cols[idx % 2]:
                    cartao_id = renderizar_cartao_credito(cartao)

                    # Botão de excluir
                    if st.button("🗑️ Excluir", key=f"del_cartao_{cartao_id}", help="Excluir este cartão"):
                        sucesso, msg = excluir_cartao(cartao_id)
                        if sucesso:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                    st.markdown("<br><br>", unsafe_allow_html=True)

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()

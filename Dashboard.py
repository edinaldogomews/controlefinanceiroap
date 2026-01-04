"""
Somma - Dashboard Financeiro Pessoal
Página Principal: Visão Geral com Cards e Gráficos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Importar do módulo compartilhado
from utils import (
    aplicar_estilo_global,
    exibir_rodape,
    exibir_status_conexao,
    exibir_menu_lateral,
    formatar_valor_br,
    formatar_mes_ano_completo,
    formatar_mes_curto,
    calcular_saldos,
    calcular_totais_periodo,
    get_armazenamento,
    carregar_dados,
    AutoUpdate,
    deve_mostrar_atualizacao,
    salvar_preferencias_update,
    resetar_preferencias_update,
    REQUESTS_DISPONIVEL,
    TIPOS_TRANSACAO,
    CATEGORIAS_PADRAO,
    # Novas importações para Contas e Cartões
    carregar_contas,
    carregar_cartoes,
    CATALOGO_BANCOS,
    editar_conta,
    obter_conta_por_id,
    TIPOS_GRUPO_CONTA,
    # NOVAS FUNÇÕES para Cold Start
    calcular_saldos_atuais,
    obter_saldo_total_disponivel,
    obter_saldo_total_beneficios
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA ST)
# ============================================================
st.set_page_config(
    page_title="Somma - Controle Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "### Somma\nDashboard para gerenciamento financeiro pessoal."
    }
)

# Aplicar estilo global
aplicar_estilo_global()


# ============================================================
# MODAL DE EDIÇÃO DE CONTA (DASHBOARD)
# ============================================================
@st.dialog("Editar Conta", width="small")
def modal_editar_conta_dashboard(conta_id: int):
    """Modal para editar saldo de uma conta diretamente do Dashboard."""

    conta = obter_conta_por_id(conta_id)
    if not conta:
        st.error("Conta não encontrada!")
        return

    st.markdown(f"### {conta['nome']}")
    st.caption(conta['banco_nome'])

    novo_saldo = st.number_input(
        "Saldo Atual (R$)",
        min_value=0.0,
        value=float(conta['saldo_inicial']),
        step=0.01,
        format="%.2f",
        key="dash_edit_saldo"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("Salvar", type="primary", use_container_width=True):
            sucesso, msg = editar_conta(conta_id, saldo_inicial=novo_saldo)
            if sucesso:
                st.success(msg)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(msg)


# ============================================================
# FUNÇÃO PRINCIPAL: main()
# ============================================================
def main():
    # Obter sistema de armazenamento
    armazenamento = get_armazenamento()

    # ========== SISTEMA DE AUTO-UPDATE ==========
    auto_update = AutoUpdate()

    # Inicializar estados do session_state para Auto-Update
    if 'update_verificado' not in st.session_state:
        st.session_state['update_verificado'] = False
        st.session_state['update_disponivel'] = False
        st.session_state['versao_remota'] = auto_update.versao_local
        st.session_state['update_msg'] = ''

    # Verificar atualização apenas uma vez por sessão
    if not st.session_state['update_verificado'] and REQUESTS_DISPONIVEL:
        tem_update, versao_remota, msg = auto_update.verificar_atualizacao()
        st.session_state['update_verificado'] = True
        st.session_state['update_disponivel'] = tem_update
        st.session_state['versao_remota'] = versao_remota
        st.session_state['update_msg'] = msg

    # ========== INDICADOR DE CONEXÃO NO TOPO ==========
    exibir_status_conexao(armazenamento)

    # ========== BOTÃO FLUTUANTE DE NOVO LANÇAMENTO ==========
    exibir_menu_lateral(armazenamento)

    # Título principal
    st.title("Visão Geral")
    st.markdown("---")

    # Carregar dados
    df = carregar_dados()

    # ========== SEÇÃO: MINHAS CONTAS E CARTÕES ==========
    contas = carregar_contas()
    cartoes = carregar_cartoes()

    # ========== CALCULAR SALDOS ATUAIS (COM SALDO INICIAL - COLD START) ==========
    saldos_info = calcular_saldos_atuais()

    # Mostrar seções de contas
    if contas:
        # ========== SEÇÃO: MINHAS CONTAS ==========
        st.subheader("Minhas Contas")

        # Usar o saldo calculado (inclui Saldo Inicial + Transações)
        saldo_total_contas = saldos_info['total_geral']

        # Criar mapa de saldos atuais para acesso rápido
        mapa_saldos = {c['nome']: c['saldo_atual'] for c in saldos_info['contas']}

        # Exibir cards horizontalmente
        num_contas = len(contas)
        cols_contas = st.columns(min(num_contas, 4))

        for idx, conta in enumerate(contas[:4]):  # Máximo 4 cards
            cor = conta['cor_hex']
            cor_sec = conta.get('cor_secundaria', '#FFFFFF')
            logo = conta.get('logo_url', '')
            nome = conta['nome']
            banco_nome = conta['banco_nome']
            conta_id = conta['id']

            # USAR SALDO CALCULADO (Saldo Inicial + Transações)
            saldo = mapa_saldos.get(nome, conta.get('saldo_inicial', 0.0))

            # Logo HTML
            if logo:
                logo_html = f'<img src="{logo}" style="width: 35px; height: 35px; object-fit: contain; filter: brightness(0) invert(1);">'
            else:
                logo_html = f'<div style="width: 35px; height: 35px; background: rgba(255,255,255,0.3); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;">{banco_nome[0]}</div>'

            with cols_contas[idx % len(cols_contas)]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {cor}, {cor}DD);
                    border-radius: 12px;
                    padding: 18px;
                    color: white;
                    box-shadow: 0 4px 15px {cor}40;
                    min-height: 120px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div>
                            <div style="font-weight: 700; font-size: 1rem;">{nome}</div>
                            <div style="font-size: 0.75rem; opacity: 0.85;">{banco_nome}</div>
                        </div>
                        {logo_html}
                    </div>
                    <div style="margin-top: 10px;">
                        <div style="font-size: 0.7rem; opacity: 0.8; text-transform: uppercase;">Saldo Atual</div>
                        <div style="font-weight: 700; font-size: 1.4rem;">{formatar_valor_br(saldo)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Botão de editar discreto abaixo do card
                if st.button("Editar saldo", key=f"dash_edit_{conta_id}", help="Editar saldo desta conta", type="secondary"):
                    modal_editar_conta_dashboard(conta_id)

        # Mostrar totalizador por tipo
        col_total1, col_total2 = st.columns(2)

        with col_total1:
            st.markdown(f"""
            <div style="text-align: left; margin-top: 10px; padding-left: 10px;">
                <span style="color: #666; font-size: 0.85rem;">Disponível: </span>
                <span style="font-weight: 700; font-size: 1rem; color: #2e7d32;">{formatar_valor_br(saldos_info['total_disponivel'])}</span>
            </div>
            """, unsafe_allow_html=True)

        with col_total2:
            if saldos_info['total_beneficio'] > 0:
                st.markdown(f"""
                <div style="text-align: left; margin-top: 10px;">
                    <span style="color: #666; font-size: 0.85rem;">Benefícios: </span>
                    <span style="font-weight: 700; font-size: 1rem; color: #1565c0;">{formatar_valor_br(saldos_info['total_beneficio'])}</span>
                </div>
                """, unsafe_allow_html=True)

        # Total geral
        st.markdown(f"""
        <div style="text-align: right; margin-top: 5px; padding-right: 10px;">
            <span style="color: #666; font-size: 0.9rem;">Saldo Total: </span>
            <span style="font-weight: 700; font-size: 1.1rem; color: #2e7d32;">{formatar_valor_br(saldo_total_contas)}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ========== SEÇÃO: MEUS CARTÕES ==========
    if cartoes:
        st.subheader("Meus Cartões")

        # Calcular fatura total (despesas do mês)
        fatura_total = 0.0
        if not df.empty:
            df_temp = df.copy()
            df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce')
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            df_mes_atual = df_temp[
                (df_temp['Data'].dt.month == mes_atual) &
                (df_temp['Data'].dt.year == ano_atual) &
                (df_temp['Tipo'] == 'Despesa')
            ]
            fatura_total = df_mes_atual['Valor'].sum() if not df_mes_atual.empty else 0.0

        # Distribuir fatura entre cartões (proporcional ao limite)
        limite_total = sum(c['limite'] for c in cartoes)

        # Exibir cards horizontalmente
        num_cartoes = len(cartoes)
        cols_cartoes = st.columns(min(num_cartoes, 4))

        for idx, cartao in enumerate(cartoes[:4]):  # Máximo 4 cards
            cor = cartao['cor_hex']
            cor_sec = cartao.get('cor_secundaria', '#FFFFFF')
            logo = cartao.get('logo_url', '')
            nome = cartao['nome']
            limite = cartao['limite']
            dia_venc = cartao['dia_vencimento']
            dia_fech = cartao['dia_fechamento']

            # Calcular fatura proporcional ao limite
            if limite_total > 0:
                fatura_cartao = (limite / limite_total) * fatura_total
            else:
                fatura_cartao = 0.0

            # Percentual usado
            percentual_usado = (fatura_cartao / limite * 100) if limite > 0 else 0

            # Logo HTML
            if logo:
                logo_html = f'<img src="{logo}" style="width: 30px; height: 30px; object-fit: contain; filter: brightness(0) invert(1); opacity: 0.9;">'
            else:
                logo_html = ''

            with cols_cartoes[idx % len(cols_cartoes)]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {cor}, {cor}CC);
                    border-radius: 14px;
                    padding: 18px;
                    color: white;
                    box-shadow: 0 6px 20px {cor}50;
                    min-height: 140px;
                    position: relative;
                    overflow: hidden;
                ">
                    <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="font-weight: 700; font-size: 0.95rem;">{nome}</div>
                        {logo_html}
                    </div>
                    <div style="margin-top: 12px;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase;">Fatura Atual</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">{formatar_valor_br(fatura_cartao)}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.75rem; opacity: 0.9;">
                        <span>📅 Venc: dia {dia_venc:02d}</span>
                        <span>Limite: {formatar_valor_br(limite)}</span>
                    </div>
                    <div style="margin-top: 8px; background: rgba(255,255,255,0.2); border-radius: 4px; height: 6px; overflow: hidden;">
                        <div style="width: {min(percentual_usado, 100):.0f}%; height: 100%; background: rgba(255,255,255,0.8); border-radius: 4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Mostrar totalizador
        st.markdown(f"""
        <div style="text-align: right; margin-top: 10px; padding-right: 10px;">
            <span style="color: #666; font-size: 0.9rem;">Fatura Total do Mês: </span>
            <span style="font-weight: 700; font-size: 1.1rem; color: #d32f2f;">{formatar_valor_br(fatura_total)}</span>
        </div>
        """, unsafe_allow_html=True)

    # Separador se houver contas ou cartões
    if contas or cartoes:
        st.markdown("---")
    else:
        # Nenhuma conta ou cartão cadastrado - mostrar botão para cadastrar
        st.info("Você ainda não cadastrou contas ou cartões. Configure-os para ter uma visão completa.")
        if st.button("Cadastrar Contas e Cartões", type="secondary"):
            st.switch_page("pages/04_Contas_e_Cartoes.py")
        st.markdown("---")

    # ========== VERIFICAR SE HÁ TRANSAÇÕES ==========
    # Mesmo sem transações, mostrar resumo se houver contas cadastradas
    if df.empty:
        if contas:
            # Mostrar resumo mesmo sem transações (Cold Start)
            st.subheader("Resumo Financeiro")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="Saldo Disponível",
                    value=formatar_valor_br(saldos_info['total_disponivel']),
                    help="Soma dos saldos de todas as suas contas bancárias"
                )

            with col2:
                st.metric(
                    label="Saldo Benefícios",
                    value=formatar_valor_br(saldos_info['total_beneficio']),
                    help="Soma dos saldos de VR, VA e outros benefícios"
                )

            with col3:
                st.metric(
                    label="Patrimônio Total",
                    value=formatar_valor_br(saldos_info['total_geral']),
                    help="Soma de todas as suas contas"
                )

            st.markdown("---")
            st.info("📝 Você ainda não possui transações registradas. Clique no botão **+** para adicionar sua primeira transação!")
        else:
            st.warning("Nenhum registro encontrado.")
            st.info("Acesse a página **Contas e Cartões** para cadastrar suas contas, ou clique no botão **+** para adicionar uma transação!")

        exibir_rodape(auto_update.versao_local)
        st.stop()

    # ========== SIDEBAR - AVISO DE ATUALIZAÇÃO ==========
    if st.session_state.get('update_disponivel', False):
        versao_remota = st.session_state.get('versao_remota', '')

        if deve_mostrar_atualizacao(versao_remota):
            st.sidebar.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    padding: 12px;
                    margin-bottom: 10px;
                    color: white;
                    text-align: center;
                ">
                    <p style="margin: 0; font-weight: bold; font-size: 1rem;">
                        🆕 Nova versão disponível!
                    </p>
                    <p style="margin: 3px 0; font-size: 0.85rem;">
                        {auto_update.versao_local} → {versao_remota}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.sidebar.button("🔄 Atualizar Agora", use_container_width=True, type="primary"):
                progress_container = st.sidebar.empty()
                status_container = st.sidebar.empty()

                def atualizar_progresso(texto, percentual):
                    progress_container.progress(percentual, text=texto)

                with st.spinner("Atualizando..."):
                    sucesso, mensagem = auto_update.realizar_update(atualizar_progresso)

                if sucesso:
                    progress_container.empty()
                    status_container.success(f"✅ {mensagem}")
                    st.balloons()
                    resetar_preferencias_update()
                    st.session_state['update_disponivel'] = False
                    st.session_state['update_verificado'] = False
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    progress_container.empty()
                    status_container.error(f"❌ {mensagem}")

            col_lembrar, col_ignorar = st.sidebar.columns(2)

            with col_lembrar:
                if st.button("⏰ Depois", use_container_width=True, help="Lembrar em 24h"):
                    prefs = {
                        'nao_perguntar': False,
                        'lembrar_depois': True,
                        'lembrar_data': (datetime.now() + timedelta(hours=24)).isoformat(),
                        'versao_ignorada': ''
                    }
                    salvar_preferencias_update(prefs)
                    st.rerun()

            with col_ignorar:
                if st.button("🚫 Ignorar", use_container_width=True, help="Ignorar versão"):
                    prefs = {
                        'nao_perguntar': True,
                        'lembrar_depois': False,
                        'lembrar_data': '',
                        'versao_ignorada': versao_remota
                    }
                    salvar_preferencias_update(prefs)
                    st.rerun()

            st.sidebar.markdown("---")

    # ========== CRIAR COLUNA MÊS/ANO PARA FILTRO ==========
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['Data'].dt.to_period('M').astype(str)
    df['Mes_Ano_Fmt'] = df['Mes_Ano'].apply(formatar_mes_ano_completo)

    # Obter tipos e categorias únicas para os filtros
    tipos_unicos = df['Tipo'].dropna().unique().tolist()
    categorias_unicas = df['Categoria'].dropna().unique().tolist()

    # Obter lista de meses únicos
    meses_unicos = df[df['Mes_Ano'] != 'NaT']['Mes_Ano'].dropna().unique().tolist()
    meses_unicos = sorted(meses_unicos, reverse=True)
    meses_formatados = [formatar_mes_ano_completo(m) for m in meses_unicos]

    # ========== SIDEBAR - FILTRO DE MÊS (VISÍVEL) ==========
    st.sidebar.header("Período")

    if meses_formatados:
        opcoes_meses = ["Todos os meses"] + meses_formatados
        mes_atual_sistema = datetime.now().strftime('%Y-%m')

        if mes_atual_sistema in meses_unicos:
            idx_mes_atual = meses_unicos.index(mes_atual_sistema)
            indice_padrao = idx_mes_atual + 1
        else:
            indice_padrao = 1 if len(opcoes_meses) > 1 else 0

        mes_selecionado_fmt = st.sidebar.selectbox(
            "Selecione o Mês",
            options=opcoes_meses,
            index=indice_padrao,
            key="filtro_mes"
        )

        if mes_selecionado_fmt == "Todos os meses":
            mes_selecionado = None
        else:
            idx = meses_formatados.index(mes_selecionado_fmt)
            mes_selecionado = meses_unicos[idx]
    else:
        mes_selecionado = None
        mes_selecionado_fmt = "Todos os meses"

    # ========== SIDEBAR - FILTROS AVANÇADOS (EXPANDER) ==========
    with st.sidebar.expander("Filtros Avançados", expanded=False):
        tipos_selecionados = st.multiselect(
            "Tipo de Transação",
            options=tipos_unicos,
            default=tipos_unicos,
            key="filtro_tipo"
        )

        categorias_selecionadas = st.multiselect(
            "Categorias",
            options=categorias_unicas,
            default=categorias_unicas,
            key="filtro_categoria"
        )

    # Aplicar filtros de tipo e categoria
    df_filtrado = df[
        (df['Tipo'].isin(tipos_selecionados)) &
        (df['Categoria'].isin(categorias_selecionadas))
    ]

    # Filtrar por mês
    if mes_selecionado is not None:
        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_selecionado].copy()
    else:
        df_mes = df_filtrado.copy()

    # ========== KPIs - MÉTRICAS PRINCIPAIS ==========
    st.subheader("Resumo Financeiro")

    # Calcular saldos usando função do utils
    saldos = calcular_saldos(df_filtrado)
    totais_mes = calcular_totais_periodo(df_mes)

    # Label dinâmico para os cards do mês
    label_periodo = f" ({mes_selecionado_fmt})" if mes_selecionado is not None else " (Geral)"

    # Definir número de colunas baseado na existência de VR
    if saldos['mostrar_card_vr']:
        col1, col2, col3, col4, col5 = st.columns(5)
    else:
        col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Saldo Principal",
            value=formatar_valor_br(saldos['saldo_comum']),
            delta=f"{'Positivo' if saldos['saldo_comum'] >= 0 else 'Negativo'}",
            help="Saldo acumulado da Conta Comum"
        )

    if saldos['mostrar_card_vr']:
        with col2:
            st.metric(
                label="Saldo VR",
                value=formatar_valor_br(saldos['saldo_vr']),
                delta=f"{'Positivo' if saldos['saldo_vr'] >= 0 else 'Negativo'}",
                help="Saldo acumulado do Vale Refeição"
            )

        with col3:
            st.metric(
                label=f"Receitas{label_periodo}",
                value=formatar_valor_br(totais_mes['total_receitas'])
            )

        with col4:
            st.metric(
                label=f"Transações{label_periodo}",
                value=len(df_mes)
            )

        with col5:
            st.metric(
                label=f"Despesas{label_periodo}",
                value=formatar_valor_br(totais_mes['total_despesas'])
            )
    else:
        with col2:
            st.metric(
                label=f"Receitas{label_periodo}",
                value=formatar_valor_br(totais_mes['total_receitas'])
            )

        with col3:
            st.metric(
                label=f"Transações{label_periodo}",
                value=len(df_mes)
            )

        with col4:
            st.metric(
                label=f"Despesas{label_periodo}",
                value=formatar_valor_br(totais_mes['total_despesas'])
            )

    st.markdown("---")

    # ========== GRÁFICOS ==========
    st.subheader("Visualizações")

    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.markdown(f"#### Gastos por Categoria{label_periodo}")

        if not df_mes.empty:
            gastos_categoria = df_mes.groupby('Categoria')['Valor'].sum().reset_index()
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
            st.info("Nenhum dado disponível para o período selecionado.")

    with col_grafico2:
        st.markdown("#### Movimentação por Mês")

        if not df_mes.empty:
            df_mensal = df_mes.copy()
            df_mensal = df_mensal.dropna(subset=['Data'])

            if not df_mensal.empty:
                df_mensal['Mês'] = df_mensal['Data'].dt.to_period('M').astype(str)
                gastos_mensais = df_mensal.groupby(['Mês', 'Tipo'])['Valor'].sum().reset_index()
                gastos_mensais['Mês_Fmt'] = gastos_mensais['Mês'].apply(formatar_mes_curto)

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
            st.info("Nenhum dado disponível para o período selecionado.")

    st.markdown(f"#### Receitas vs Despesas{label_periodo}")

    if not df_mes.empty:
        comparativo = pd.DataFrame({
            'Tipo': ['Receitas', 'Despesas'],
            'Valor': [totais_mes['total_receitas'], totais_mes['total_despesas']]
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
    else:
        st.info("Nenhum dado disponível para o período selecionado.")

    # ========== RODAPÉ ==========
    exibir_rodape(auto_update.versao_local)



if __name__ == "__main__":
    main()

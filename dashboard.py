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
    CATEGORIAS_PADRAO
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

    # Título principal
    st.title("Visão Geral")
    st.markdown("---")

    # Carregar dados
    df = carregar_dados()

    # Verificar se o DataFrame está vazio
    if df.empty:
        st.warning("Nenhum registro encontrado.")
        st.info("Acesse a página **Registrar** no menu lateral para adicionar sua primeira transação!")
        exibir_rodape(auto_update.versao_local)
        st.stop()

    # Obter tipos e categorias únicos
    tipos_unicos = df['Tipo'].unique().tolist()
    categorias_unicas = df['Categoria'].unique().tolist()

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
            label=f"Receitas{label_periodo}",
            value=formatar_valor_br(totais_mes['total_receitas'])
        )

    with col2:
        st.metric(
            label=f"Despesas{label_periodo}",
            value=formatar_valor_br(totais_mes['total_despesas'])
        )

    with col3:
        st.metric(
            label="Saldo Principal",
            value=formatar_valor_br(saldos['saldo_comum']),
            delta=f"{'Positivo' if saldos['saldo_comum'] >= 0 else 'Negativo'}",
            help="Saldo acumulado da Conta Comum"
        )

    with col4:
        st.metric(
            label=f"Transações{label_periodo}",
            value=len(df_mes)
        )

    if saldos['mostrar_card_vr']:
        with col5:
            st.metric(
                label="Saldo VR",
                value=formatar_valor_br(saldos['saldo_vr']),
                delta=f"{'Positivo' if saldos['saldo_vr'] >= 0 else 'Negativo'}",
                help="Saldo acumulado do Vale Refeição"
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

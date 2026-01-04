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
    calcular_saldo_anterior_com_inicial,
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



    # ========== VISÃO GERAL (NOVO LAYOUT) ==========
    contas = carregar_contas()
    cartoes = carregar_cartoes()
    
    # Cálculos para o Visão Geral
    # Se filtro de mês estiver ativo, usar mês selecionado, senão mês atual
    if mes_selecionado:
        data_ref = pd.to_datetime(mes_selecionado + '-01')
        mes_num = data_ref.month
        ano_num = data_ref.year
        data_inicio = datetime(ano_num, mes_num, 1)
        if mes_num == 12:
            data_fim = datetime(ano_num + 1, 1, 1)
        else:
            data_fim = datetime(ano_num, mes_num + 1, 1)
    else:
        # Se "Todos os meses", vamos usar o mês atual para o card de visão geral
        # ou talvez mostrar o acumulado total?
        # Pela imagem, parece focar num mês. Vamos assumir mês atual se "Todos"
        agora = datetime.now()
        mes_num = agora.month
        ano_num = agora.year
        data_inicio = datetime(ano_num, mes_num, 1)
        if mes_num == 12:
            data_fim = datetime(ano_num + 1, 1, 1)
        else:
            data_fim = datetime(ano_num, mes_num + 1, 1)

    # 1. Saldo Inicial (Até o início do mês)
    # Somar saldo de todas as contas (Disponível + Benefício)
    saldo_inicial_disp = calcular_saldo_anterior_com_inicial(df, 'Disponível', data_inicio)
    saldo_inicial_ben = calcular_saldo_anterior_com_inicial(df, 'Benefício', data_inicio)
    saldo_inicial_total = saldo_inicial_disp + saldo_inicial_ben

    # 2. Filtrar dados do mês para Receitas, Despesas e Transferências
    df_temp = df.copy()
    df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce')
    
    mask_mes = (df_temp['Data'] >= data_inicio) & (df_temp['Data'] < data_fim)
    df_periodo = df_temp[mask_mes]

    # Calcular totais
    # Receitas (excluindo transferências internas se a categoria for 'Transferência')
    receitas_periodo = df_periodo[
        (df_periodo['Tipo'] == 'Receita') & 
        (df_periodo['Categoria'] != 'Transferência')
    ]['Valor'].sum()

    # Despesas (excluindo transferências internas)
    despesas_periodo = df_periodo[
        (df_periodo['Tipo'] == 'Despesa') & 
        (df_periodo['Categoria'] != 'Transferência')
    ]['Valor'].sum()

    # Balanço de Transferências (Receita Transf - Despesa Transf)
    transf_entrada = df_periodo[
        (df_periodo['Tipo'] == 'Receita') & 
        (df_periodo['Categoria'] == 'Transferência')
    ]['Valor'].sum()
    
    transf_saida = df_periodo[
        (df_periodo['Tipo'] == 'Despesa') & 
        (df_periodo['Categoria'] == 'Transferência')
    ]['Valor'].sum()
    
    balanco_transferencias = transf_entrada - transf_saida

    # Saldo Atual (Final do Mês ou acumulado até agora dentro do mês)
    # Inicial + Receitas Totais (inc. transf) - Despesas Totais (inc. transf)
    # Ou simplesmente Inicial + Receitas Periodo - Despesas Periodo + Balanço Transferencias
    saldo_atual_total = saldo_inicial_total + receitas_periodo - despesas_periodo + balanco_transferencias
    
    # Previsto (Por enquanto igual ao atual, ou poderia somar contas fixas futuras)
    saldo_previsto = saldo_atual_total 

    # Renderizar Card Principal (Topo)
    # IMPORTANTE: Usar st.html para garantir renderização correta de HTML
    st.markdown(f"""
<div style="
    background-color: #1f2430;
    padding: 24px 30px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    margin-bottom: 25px;
    border: 1px solid rgba(255,255,255,0.08);
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
">
    <div style="display: flex; justify-content: space-between; align-items: flex-end; text-align: center; margin-bottom: 20px;">
        <div style="flex: 1;">
            <div style="font-size: 1.2rem; font-weight: 700; color: #b0bec5; margin-bottom: 4px;">{formatar_valor_br(saldo_inicial_total)}</div>
            <div style="font-size: 0.85rem; font-weight: 500; color: #78909c; letter-spacing: 0.5px;">Inicial</div>
        </div>
        <div style="flex: 1.2; padding-bottom: 5px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-bottom: 4px; text-shadow: 0 0 20px rgba(66, 165, 245, 0.4);">{formatar_valor_br(saldo_atual_total)}</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: #42a5f5; letter-spacing: 0.5px;">Saldo atual</div>
        </div>
        <div style="flex: 1;">
            <div style="font-size: 1.2rem; font-weight: 700; color: #b0bec5; margin-bottom: 4px;">{formatar_valor_br(saldo_previsto)}</div>
            <div style="font-size: 0.85rem; font-weight: 500; color: #78909c; letter-spacing: 0.5px;">Previsto</div>
        </div>
    </div>
    <div style="
        width: 100%;
        height: 12px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 6px;
        margin-top: 15px;
        overflow: visible;
        position: relative;
    ">
        <div style="
            width: 50%; 
            height: 100%; 
            background: linear-gradient(90deg, #42a5f5, #2196f3);
            border-radius: 6px;
            box-shadow: 0 0 12px rgba(33, 150, 243, 0.5);
        "></div>
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 20px;
            height: 20px;
            background-color: #2196f3;
            border: 3px solid #1f2430;
            border-radius: 50%;
            box-shadow: 0 0 0 2px #42a5f5;
        "></div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Renderizar Lista "Visão Geral"
    st.markdown(f"""
<div style="
  background-color: #1f2430;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  padding: 16px 18px;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
">
  <div style="display:flex; justify-content:space-between; align-items:center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
    <div style="display:flex; align-items:center; gap:14px;">
      <div style="width:40px; height:40px; background: rgba(25,118,210,0.18); color:#90caf9; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">🏛️</div>
      <span style="font-size:1rem; font-weight:600;">Contas</span>
    </div>
    <span style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(saldo_atual_total)}</span>
  </div>
  <div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
    <div style="display:flex; align-items:center; gap:14px;">
      <div style="width:40px; height:40px; background: rgba(46,125,50,0.18); color:#66bb6a; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">＋</div>
      <span style="font-size:1rem; font-weight:600;">Receitas</span>
    </div>
    <span style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(receitas_periodo)}</span>
  </div>
  <div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
    <div style="display:flex; align-items:center; gap:14px;">
      <div style="width:40px; height:40px; background: rgba(198,40,40,0.18); color:#ef5350; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">－</div>
      <span style="font-size:1rem; font-weight:600;">Despesas</span>
    </div>
    <span style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(despesas_periodo)}</span>
  </div>
  <div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0;">
    <div style="display:flex; align-items:center; gap:14px;">
      <div style="width:40px; height:40px; background: rgba(251,192,45,0.18); color:#fdd835; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">⇄</div>
      <span style="font-size:1rem; font-weight:600;">Balanço transferências</span>
    </div>
    <span style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(balanco_transferencias)}</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ========== SEÇÃO: CONTAS ==========
    # Carregar saldos atualizados de cada conta
    saldos_info_detalhado = calcular_saldos_atuais()
    lista_contas_detalhada = saldos_info_detalhado.get('contas', [])
    total_geral_contas = saldos_info_detalhado.get('total_geral', 0.0)

    if lista_contas_detalhada:
        st.subheader("Contas")
        
        # Início do Card
        html_contas = """
<div style="
  background-color: #1f2430;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  padding: 16px 18px;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  margin-bottom: 25px;
">
"""

        # Linhas das Contas
        for conta in lista_contas_detalhada:
            nome = conta['nome']
            saldo = conta['saldo_atual']
            info = conta.get('conta_info', {})
            banco_id = info.get('banco_id', 'Outro')
            
            # Tentar obter logo ou usar ícone padrão
            banco_data = CATALOGO_BANCOS.get(banco_id, CATALOGO_BANCOS.get('Outro'))
            logo_url = banco_data.get('logo', '') if banco_data else ''
            cor_primaria = banco_data.get('cor', '#78909c') if banco_data else '#78909c'
            
            # Ícone (Imagem ou Letra)
            if logo_url:
                icon_html = f'<div style="width:40px; height:40px; background: white; border-radius:50%; display:flex; align-items:center; justify-content:center; overflow:hidden;"><img src="{logo_url}" style="width:28px; height:28px; object-fit:contain;"></div>'
            else:
                icon_html = f'<div style="width:40px; height:40px; background: {cor_primaria}; color: white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.2rem;">{nome[0].upper()}</div>'

            html_contas += f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
    <div style="display:flex; align-items:center; gap:14px;">
        {icon_html}
        <div style="display:flex; flex-direction:column;">
            <span style="font-size:1rem; font-weight:600; color:#e0e0e0;">{nome}</span>
            <span style="font-size:0.75rem; color:#78909c;">Previsto</span>
        </div>
    </div>
    <div style="text-align:right;">
        <div style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(saldo)}</div>
        <div style="font-size:0.75rem; color:#78909c;">{formatar_valor_br(saldo)}</div>
    </div>
</div>
"""

        # Totalizador (Rodapé do Card)
        html_contas += f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding-top: 16px; margin-top: 4px;">
    <div style="display:flex; flex-direction:column;">
        <span style="font-size:1rem; font-weight:600; color:#e0e0e0;">Total</span>
        <span style="font-size:0.75rem; color:#78909c;">Previsto</span>
    </div>
    <div style="text-align:right;">
        <div style="font-weight:700; color:#e0e0e0;">{formatar_valor_br(total_geral_contas)}</div>
        <div style="font-size:0.75rem; color:#78909c;">{formatar_valor_br(total_geral_contas)}</div>
    </div>
</div>
</div>
"""
        
        st.markdown(html_contas, unsafe_allow_html=True)

    # ========== SEÇÃO: MEUS CARTÕES ==========
    if cartoes:
        st.subheader("Meus Cartões")

        # Calcular fatura total (despesas do mês)
        fatura_total = 0.0
        # Dicionário para armazenar faturas individuais por cartão
        faturas_por_cartao = {c['nome']: 0.0 for c in cartoes}
        
        if not df.empty:
            df_temp = df.copy()
            df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce')
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            # Filtrar despesas do mês atual
            df_mes_atual = df_temp[
                (df_temp['Data'].dt.month == mes_atual) &
                (df_temp['Data'].dt.year == ano_atual) &
                (df_temp['Tipo'] == 'Despesa')
            ]
            
            # Calcular fatura total
            fatura_total = df_mes_atual['Valor'].sum() if not df_mes_atual.empty else 0.0
            
            # Calcular fatura por cartão
            if not df_mes_atual.empty:
                gastos_por_conta = df_mes_atual.groupby('Conta')['Valor'].sum()
                for nome_cartao in faturas_por_cartao.keys():
                    if nome_cartao in gastos_por_conta:
                        faturas_por_cartao[nome_cartao] = gastos_por_conta[nome_cartao]

        # Distribuir fatura entre cartões (proporcional ao limite) - LEGADO
        # MANTIDO APENAS COMO FALLBACK se não houver dados específicos
        limite_total = sum(c['limite'] for c in cartoes)

        # Exibir cards horizontalmente
        num_cartoes = len(cartoes)
        # Ajustar para exibir até 4 colunas ou menos
        cols_cartoes = st.columns(min(num_cartoes, 4)) if num_cartoes > 0 else []

        for idx, cartao in enumerate(cartoes):
            # Se tiver mais que 4 cartões, continuar na linha de baixo (grid)
            
            cor = cartao['cor_hex']
            cor_sec = cartao.get('cor_secundaria', '#FFFFFF')
            logo = cartao.get('logo_url', '')
            nome = cartao['nome']
            limite = cartao['limite']
            dia_venc = cartao['dia_vencimento']
            dia_fech = cartao['dia_fechamento']

            # Calcular fatura real do cartão
            fatura_cartao = faturas_por_cartao.get(nome, 0.0)
            
            # Se a soma das faturas individuais for 0 mas houver fatura total (casos legados ou erro de nome),
            # usar rateio proporcional como fallback
            soma_faturas_individuais = sum(faturas_por_cartao.values())
            if soma_faturas_individuais == 0 and fatura_total > 0 and limite_total > 0:
                 fatura_cartao = (limite / limite_total) * fatura_total

            # Percentual usado
            percentual_usado = (fatura_cartao / limite * 100) if limite > 0 else 0

            # Logo HTML
            if logo:
                logo_html = f'<img src="{logo}" style="width: 30px; height: 30px; object-fit: contain; filter: brightness(0) invert(1); opacity: 0.9;">'
            else:
                logo_html = ''

            # Usar a coluna correspondente (ciclando se houver mais de 4)
            with cols_cartoes[idx % 4]:
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
    margin-bottom: 15px;
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
            height=490,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o período selecionado.")

    # ========== RODAPÉ ==========
    exibir_rodape(auto_update.versao_local)



if __name__ == "__main__":
    main()

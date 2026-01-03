"""
Somma - Página de Previsibilidade
Fluxo de Caixa Diário (Ledger) - Tabela estilo planilha Excel
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


def gerar_tabela_fluxo_caixa(df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
    """
    Gera a tabela de fluxo de caixa diário para o mês selecionado.
    Retorna um DataFrame com todos os dias do mês e os saldos calculados.
    """
    # Criar range de datas do mês
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    datas_mes = pd.date_range(start=primeiro_dia, end=ultimo_dia, freq='D')

    # Criar DataFrame base com todos os dias do mês
    df_fluxo = pd.DataFrame({'Data': datas_mes})
    df_fluxo['Data'] = pd.to_datetime(df_fluxo['Data'])

    # Preparar dados de transações
    df = df.copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

    # Filtrar transações do mês
    df_mes = df[
        (df['Data'].dt.year == ano) &
        (df['Data'].dt.month == mes)
    ].copy()

    # Calcular saldos anteriores ao mês (para cada conta)
    saldo_anterior_comum = calcular_saldo_anterior(df, 'Comum', primeiro_dia)
    saldo_anterior_vr = calcular_saldo_anterior(df, 'Vale Refeição', primeiro_dia)

    # Agrupar transações por dia e tipo
    # Entradas (Receitas) por dia - Conta Comum
    entradas_comum = df_mes[
        (df_mes['Tipo'] == 'Receita') & (df_mes['Conta'] == 'Comum')
    ].groupby(df_mes['Data'].dt.date)['Valor'].sum()

    # Saídas (Despesas) por dia - Conta Comum
    saidas_comum = df_mes[
        (df_mes['Tipo'] == 'Despesa') & (df_mes['Conta'] == 'Comum')
    ].groupby(df_mes['Data'].dt.date)['Valor'].sum()

    # Entradas (Receitas) por dia - VR
    entradas_vr = df_mes[
        (df_mes['Tipo'] == 'Receita') & (df_mes['Conta'] == 'Vale Refeição')
    ].groupby(df_mes['Data'].dt.date)['Valor'].sum()

    # Saídas (Despesas) por dia - VR
    saidas_vr = df_mes[
        (df_mes['Tipo'] == 'Despesa') & (df_mes['Conta'] == 'Vale Refeição')
    ].groupby(df_mes['Data'].dt.date)['Valor'].sum()

    # Preencher colunas no DataFrame de fluxo
    df_fluxo['Entradas_Comum'] = df_fluxo['Data'].dt.date.map(entradas_comum).fillna(0)
    df_fluxo['Saidas_Comum'] = df_fluxo['Data'].dt.date.map(saidas_comum).fillna(0)
    df_fluxo['Entradas_VR'] = df_fluxo['Data'].dt.date.map(entradas_vr).fillna(0)
    df_fluxo['Saidas_VR'] = df_fluxo['Data'].dt.date.map(saidas_vr).fillna(0)

    # Calcular totais do dia
    df_fluxo['Entradas'] = df_fluxo['Entradas_Comum'] + df_fluxo['Entradas_VR']
    df_fluxo['Saidas'] = df_fluxo['Saidas_Comum'] + df_fluxo['Saidas_VR']
    df_fluxo['Saldo_Dia'] = df_fluxo['Entradas'] - df_fluxo['Saidas']

    # Calcular movimento do dia por conta
    df_fluxo['Mov_Comum'] = df_fluxo['Entradas_Comum'] - df_fluxo['Saidas_Comum']
    df_fluxo['Mov_VR'] = df_fluxo['Entradas_VR'] - df_fluxo['Saidas_VR']

    # Calcular saldo acumulado (cascata) - Conta Comum
    df_fluxo['Saldo_Acum_Comum'] = saldo_anterior_comum + df_fluxo['Mov_Comum'].cumsum()

    # Calcular saldo acumulado (cascata) - Vale Refeição
    df_fluxo['Saldo_Acum_VR'] = saldo_anterior_vr + df_fluxo['Mov_VR'].cumsum()

    # Formatar coluna de data para exibição
    df_fluxo['Dia_Semana'] = df_fluxo['Data'].apply(lambda x: obter_nome_dia_semana(x.date()))
    df_fluxo['Data_Fmt'] = df_fluxo['Data'].dt.strftime('%d/%m')
    df_fluxo['Data_Display'] = df_fluxo['Dia_Semana'] + ' ' + df_fluxo['Data_Fmt']

    return df_fluxo, saldo_anterior_comum, saldo_anterior_vr


def estilizar_tabela(df: pd.DataFrame, data_hoje: date) -> pd.io.formats.style.Styler:
    """
    Aplica formatação condicional na tabela de fluxo de caixa.
    - Saldo negativo: vermelho
    - Saldo positivo: verde
    - Linha de hoje: destaque amarelo
    """
    def colorir_saldo(val):
        try:
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'color: #dc3545; background-color: #ffebee; font-weight: bold;'
                else:
                    return 'color: #155724; background-color: #e8f5e9;'
        except:
            pass
        return ''

    def destacar_hoje(row):
        """Destaca a linha do dia de hoje."""
        try:
            # Verificar se a data da linha é hoje
            data_row = row.name  # índice
            if hasattr(df, 'Data_Original'):
                data_linha = df.loc[data_row, 'Data_Original']
                if data_linha == data_hoje:
                    return ['background-color: #fff3cd; font-weight: bold;'] * len(row)
        except:
            pass
        return [''] * len(row)

    # Colunas de saldo para aplicar cor
    colunas_saldo = ['Saldo Dia', 'Saldo Comum', 'Saldo VR']
    colunas_existentes = [col for col in colunas_saldo if col in df.columns]

    # Aplicar estilos
    styled = df.style.applymap(colorir_saldo, subset=colunas_existentes)

    # Formatar valores como moeda
    formato_moeda = lambda x: formatar_valor_br(x) if isinstance(x, (int, float)) else x
    colunas_valor = ['Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR']
    colunas_formatar = [col for col in colunas_valor if col in df.columns]
    styled = styled.format(formato_moeda, subset=colunas_formatar)

    return styled


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():
    armazenamento = get_armazenamento()
    exibir_status_conexao(armazenamento)

    st.title("Previsibilidade")
    st.caption("Fluxo de Caixa Diário - Visualize entradas e saídas dia a dia")

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

    # ========== LANÇAMENTO RÁPIDO (EXPANDER) ==========
    with st.expander("⚡ Lançamento Rápido na Previsibilidade", expanded=False):
        st.caption("Adicione uma transação rapidamente e veja o impacto no fluxo de caixa")

        with st.form(key="form_lancamento_rapido", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                lr_data = st.date_input(
                    "Data",
                    value=data_hoje,
                    format="DD/MM/YYYY",
                    key="lr_data"
                )

            with col2:
                lr_tipo = st.selectbox(
                    "Tipo",
                    options=TIPOS_TRANSACAO,
                    key="lr_tipo"
                )

            with col3:
                lr_conta = st.selectbox(
                    "Conta",
                    options=TIPOS_CONTA,
                    key="lr_conta"
                )

            col4, col5 = st.columns([1, 2])

            with col4:
                lr_valor = st.number_input(
                    "Valor (R$)",
                    min_value=0.01,
                    value=None,
                    step=0.01,
                    format="%.2f",
                    placeholder="0.00",
                    key="lr_valor"
                )

            with col5:
                # Definir categorias baseado no tipo e conta
                if lr_conta == "Vale Refeição" and lr_tipo == "Despesa":
                    categorias = CAT_VALE_REFEICAO
                elif lr_tipo == "Receita":
                    categorias = CAT_RECEITA
                else:
                    categorias = CAT_DESPESA

                lr_categoria = st.selectbox(
                    "Categoria",
                    options=categorias,
                    key="lr_categoria"
                )

            lr_descricao = st.text_input(
                "Descrição",
                placeholder="Ex: Salário, Conta de Luz, etc.",
                key="lr_descricao"
            )

            submit_lr = st.form_submit_button(
                "Salvar Lançamento",
                use_container_width=True,
                type="primary"
            )

            if submit_lr:
                if not lr_descricao.strip():
                    st.error("A descrição é obrigatória!")
                elif lr_valor is None or lr_valor <= 0:
                    st.error("O valor deve ser maior que zero!")
                else:
                    conta_salvar = "Vale Refeição" if lr_conta == "Vale Refeição" else "Comum"

                    with st.spinner("Salvando..."):
                        sucesso, mensagem = armazenamento.salvar_transacao(
                            lr_data,
                            lr_descricao.strip(),
                            lr_categoria,
                            lr_valor,
                            lr_tipo,
                            conta_salvar
                        )

                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {mensagem}")

    # ========== VERIFICAR SE HÁ DADOS ==========
    if df.empty:
        st.warning("Nenhuma transação encontrada.")
        st.info("Use o formulário acima ou acesse **Registrar** para adicionar transações!")
        exibir_rodape()
        st.stop()

    # ========== GERAR TABELA DE FLUXO DE CAIXA ==========
    df_fluxo, saldo_ant_comum, saldo_ant_vr = gerar_tabela_fluxo_caixa(df, ano_selecionado, mes_selecionado)

    # ========== CARDS DE SALDO ANTERIOR ==========
    st.subheader(f"Saldos em {obter_nome_mes(mes_selecionado)} {ano_selecionado}")

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
        saldo_final_comum = df_fluxo['Saldo_Acum_Comum'].iloc[-1] if not df_fluxo.empty else saldo_ant_comum
        saldo_final_vr = df_fluxo['Saldo_Acum_VR'].iloc[-1] if not df_fluxo.empty else saldo_ant_vr
        st.metric(
            label="Saldo Final Projetado",
            value=formatar_valor_br(saldo_final_comum + saldo_final_vr),
            delta=f"Comum: {formatar_valor_br(saldo_final_comum)}"
        )

    st.markdown("---")

    # ========== TABELA DE FLUXO DE CAIXA ==========
    st.subheader("Fluxo de Caixa Diário")

    # Preparar DataFrame para exibição
    df_display = df_fluxo[[
        'Data_Display', 'Entradas', 'Saidas', 'Saldo_Dia',
        'Saldo_Acum_Comum', 'Saldo_Acum_VR'
    ]].copy()

    # Guardar data original para destacar hoje
    df_display['Data_Original'] = df_fluxo['Data'].dt.date

    # Renomear colunas
    df_display.columns = ['Data', 'Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR', 'Data_Original']

    # Identificar linha de hoje
    linha_hoje = None
    primeiro_dia_mes = date(ano_selecionado, mes_selecionado, 1)
    ultimo_dia_mes = date(ano_selecionado, mes_selecionado, calendar.monthrange(ano_selecionado, mes_selecionado)[1])

    if primeiro_dia_mes <= data_hoje <= ultimo_dia_mes:
        linha_hoje = (data_hoje - primeiro_dia_mes).days

    # Função para estilizar
    def aplicar_estilos(row):
        styles = [''] * len(row)
        idx = row.name

        # Destacar linha de hoje
        if linha_hoje is not None and idx == linha_hoje:
            styles = ['background-color: #fff3cd; font-weight: bold;'] * len(row)

        return styles

    def colorir_saldos(val, coluna):
        if coluna in ['Saldo Dia', 'Saldo Comum', 'Saldo VR']:
            try:
                if isinstance(val, (int, float)):
                    if val < 0:
                        return 'color: #dc3545; background-color: #ffebee; font-weight: bold;'
                    elif val > 0:
                        return 'color: #155724; background-color: #e8f5e9;'
            except:
                pass
        return ''

    # Preparar DataFrame final (sem coluna auxiliar)
    df_final = df_display[['Data', 'Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR']].copy()

    # Aplicar estilos
    styled_df = df_final.style.apply(aplicar_estilos, axis=1)

    # Aplicar cores nas colunas de saldo
    for col in ['Saldo Dia', 'Saldo Comum', 'Saldo VR']:
        styled_df = styled_df.applymap(
            lambda x: colorir_saldos(x, col),
            subset=[col]
        )

    # Formatar valores como moeda
    formato_moeda = lambda x: formatar_valor_br(x) if isinstance(x, (int, float)) else x
    styled_df = styled_df.format(formato_moeda, subset=['Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR'])

    # Exibir tabela
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )

    # ========== LEGENDA ==========
    st.markdown("""
    <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 20px; height: 20px; background-color: #e8f5e9; border: 1px solid #155724; border-radius: 3px;"></div>
            <span style="font-size: 0.85rem;">Saldo Positivo</span>
        </div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 20px; height: 20px; background-color: #ffebee; border: 1px solid #dc3545; border-radius: 3px;"></div>
            <span style="font-size: 0.85rem;">Saldo Negativo</span>
        </div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 20px; height: 20px; background-color: #fff3cd; border: 1px solid #856404; border-radius: 3px;"></div>
            <span style="font-size: 0.85rem;">Dia de Hoje</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== RESUMO DO MÊS ==========
    st.markdown("---")
    st.subheader("Resumo do Mês")

    total_entradas = df_fluxo['Entradas'].sum()
    total_saidas = df_fluxo['Saidas'].sum()
    saldo_mes = total_entradas - total_saidas

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Entradas", formatar_valor_br(total_entradas))

    with col2:
        st.metric("Total Saídas", formatar_valor_br(total_saidas))

    with col3:
        st.metric(
            "Saldo do Mês",
            formatar_valor_br(saldo_mes),
            delta="Positivo" if saldo_mes >= 0 else "Negativo"
        )

    with col4:
        # Contar dias com saldo negativo
        dias_negativos_comum = (df_fluxo['Saldo_Acum_Comum'] < 0).sum()
        dias_negativos_vr = (df_fluxo['Saldo_Acum_VR'] < 0).sum()
        total_dias_negativos = dias_negativos_comum + dias_negativos_vr

        if total_dias_negativos > 0:
            st.metric(
                "Dias em Alerta",
                f"{dias_negativos_comum} (Comum) / {dias_negativos_vr} (VR)",
                delta="Atenção!",
                delta_color="inverse"
            )
        else:
            st.metric("Dias em Alerta", "0", delta="OK!")

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()

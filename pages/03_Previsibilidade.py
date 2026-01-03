"""
Somma - Página de Previsibilidade
Fluxo de Caixa Diário (Ledger) - Visualização do saldo futuro projetado dia a dia
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
    carregar_dados
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Previsibilidade - Somma",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo global
aplicar_estilo_global()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_nome_dia_semana(data: date) -> str:
    """Retorna o nome abreviado do dia da semana em português."""
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
    considerando TODAS as transações anteriores ao primeiro dia do mês.
    Saldo = Soma(Receitas) - Soma(Despesas)
    """
    if df.empty:
        return 0.0

    df_anterior = df[
        (df['Conta'] == conta) &
        (df['Data'].dt.date < data_inicio_mes)
    ].copy()

    if df_anterior.empty:
        return 0.0

    receitas = df_anterior[df_anterior['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df_anterior[df_anterior['Tipo'] == 'Despesa']['Valor'].sum()

    return receitas - despesas


def gerar_fluxo_caixa_diario(df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
    """
    Gera o fluxo de caixa diário (ledger) com todos os dias do mês.
    Retorna um DataFrame com: Data, Entradas, Saídas, Saldo Dia, Saldo Acum Comum, Saldo Acum VR
    """
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    # Preparar dados
    df = df.copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

    # Calcular saldos anteriores ao mês (para cada conta)
    saldo_ant_comum = calcular_saldo_anterior(df, 'Comum', primeiro_dia)
    saldo_ant_vr = calcular_saldo_anterior(df, 'Vale Refeição', primeiro_dia)

    # Filtrar transações do mês
    df_mes = df[
        (df['Data'].dt.year == ano) &
        (df['Data'].dt.month == mes)
    ].copy()

    # Criar DataFrame com todos os dias do mês
    dias_do_mes = pd.date_range(start=primeiro_dia, end=ultimo_dia, freq='D')
    df_calendario = pd.DataFrame({'Data': dias_do_mes})

    # Agrupar transações por dia e conta
    # Entradas (Receitas)
    entradas_comum = df_mes[(df_mes['Tipo'] == 'Receita') & (df_mes['Conta'] == 'Comum')].groupby(
        df_mes['Data'].dt.date)['Valor'].sum().reset_index()
    entradas_comum.columns = ['Data', 'Entradas_Comum']

    entradas_vr = df_mes[(df_mes['Tipo'] == 'Receita') & (df_mes['Conta'] == 'Vale Refeição')].groupby(
        df_mes['Data'].dt.date)['Valor'].sum().reset_index()
    entradas_vr.columns = ['Data', 'Entradas_VR']

    # Saídas (Despesas)
    saidas_comum = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Conta'] == 'Comum')].groupby(
        df_mes['Data'].dt.date)['Valor'].sum().reset_index()
    saidas_comum.columns = ['Data', 'Saidas_Comum']

    saidas_vr = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Conta'] == 'Vale Refeição')].groupby(
        df_mes['Data'].dt.date)['Valor'].sum().reset_index()
    saidas_vr.columns = ['Data', 'Saidas_VR']

    # Converter Data do calendário para date (para merge)
    df_calendario['Data_date'] = df_calendario['Data'].dt.date

    # Fazer merge com o calendário
    df_resultado = df_calendario.copy()

    for df_temp, col in [(entradas_comum, 'Entradas_Comum'), (entradas_vr, 'Entradas_VR'),
                          (saidas_comum, 'Saidas_Comum'), (saidas_vr, 'Saidas_VR')]:
        if not df_temp.empty:
            df_resultado = df_resultado.merge(df_temp, left_on='Data_date', right_on='Data',
                                               how='left', suffixes=('', '_drop'))
            # Remover coluna duplicada do merge
            cols_drop = [c for c in df_resultado.columns if c.endswith('_drop') or c == 'Data_drop']
            df_resultado = df_resultado.drop(columns=[c for c in cols_drop if c in df_resultado.columns], errors='ignore')
            # Remover a coluna 'Data' que veio do merge (não a original)
            if 'Data_y' in df_resultado.columns:
                df_resultado = df_resultado.drop(columns=['Data_y'])
                df_resultado = df_resultado.rename(columns={'Data_x': 'Data'})
        else:
            df_resultado[col] = 0.0

    # Garantir que as colunas existem
    for col in ['Entradas_Comum', 'Entradas_VR', 'Saidas_Comum', 'Saidas_VR']:
        if col not in df_resultado.columns:
            df_resultado[col] = 0.0

    # Preencher NaN com 0
    df_resultado = df_resultado.fillna(0)

    # Calcular totais do dia
    df_resultado['Entradas'] = df_resultado['Entradas_Comum'] + df_resultado['Entradas_VR']
    df_resultado['Saidas'] = df_resultado['Saidas_Comum'] + df_resultado['Saidas_VR']
    df_resultado['Saldo_Dia'] = df_resultado['Entradas'] - df_resultado['Saidas']

    # Calcular saldo do dia por conta
    df_resultado['Saldo_Dia_Comum'] = df_resultado['Entradas_Comum'] - df_resultado['Saidas_Comum']
    df_resultado['Saldo_Dia_VR'] = df_resultado['Entradas_VR'] - df_resultado['Saidas_VR']

    # Calcular saldo acumulado (running total) por conta
    df_resultado['Saldo_Acum_Comum'] = saldo_ant_comum + df_resultado['Saldo_Dia_Comum'].cumsum()
    df_resultado['Saldo_Acum_VR'] = saldo_ant_vr + df_resultado['Saldo_Dia_VR'].cumsum()

    # Formatar data para exibição (Dia da semana + Dia/Mês)
    df_resultado['Dia_Semana'] = df_resultado['Data'].apply(lambda x: obter_nome_dia_semana(x.date()))
    df_resultado['Data_Fmt'] = df_resultado['Data'].dt.strftime('%d/%m')
    df_resultado['Data_Display'] = df_resultado['Dia_Semana'] + ' ' + df_resultado['Data_Fmt']

    # Limpar colunas auxiliares
    df_resultado = df_resultado.drop(columns=['Data_date'], errors='ignore')

    return df_resultado, saldo_ant_comum, saldo_ant_vr


def aplicar_estilos(df: pd.DataFrame, data_hoje: date) -> pd.io.formats.style.Styler:
    """
    Aplica estilos condicionais ao DataFrame:
    - Linha de hoje: fundo azul claro
    - Valores negativos: texto vermelho, fundo vermelho suave
    - Valores positivos: texto verde
    - Zeros: texto cinza
    """
    def estilizar_linha(row):
        """Retorna estilos para cada célula da linha."""
        estilos = [''] * len(row)

        # Verificar se é a linha de hoje
        if 'Data' in row.index and pd.notna(row['Data']):
            try:
                data_row = row['Data'].date() if hasattr(row['Data'], 'date') else row['Data']
                if data_row == data_hoje:
                    estilos = ['background-color: #e3f2fd; color: #1565c0; font-weight: bold'] * len(row)
                    return estilos
            except:
                pass

        return estilos

    def estilizar_valor(val, coluna):
        """Retorna estilo para valores numéricos."""
        if pd.isna(val):
            return ''

        try:
            valor = float(str(val).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except:
            return ''

        if valor < 0:
            return 'color: #d32f2f; background-color: #ffebee'
        elif valor > 0:
            return 'color: #2e7d32'
        else:
            return 'color: #9e9e9e'

    def aplicar_estilo_celula(val):
        """Aplica estilo baseado no valor."""
        if pd.isna(val):
            return ''
        try:
            valor = float(str(val).replace('R$', '').replace('.', '').replace(',', '.').strip())
            if valor < 0:
                return 'color: #d32f2f; background-color: #ffebee'
            elif valor > 0:
                return 'color: #2e7d32'
            else:
                return 'color: #9e9e9e'
        except:
            return ''

    # Colunas de valores para aplicar estilo
    colunas_valor = ['Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR']

    # Criar styler
    styler = df.style

    # Aplicar estilo para linha de hoje
    def highlight_hoje(row):
        if 'Data_Original' in df.columns:
            idx = row.name
            try:
                data_row = df.loc[idx, 'Data_Original']
                if pd.notna(data_row):
                    data_row = data_row.date() if hasattr(data_row, 'date') else data_row
                    if data_row == data_hoje:
                        return ['background-color: #e3f2fd; color: #1565c0; font-weight: bold'] * len(row)
            except:
                pass
        return [''] * len(row)

    styler = styler.apply(highlight_hoje, axis=1)

    # Aplicar estilo para valores
    for col in colunas_valor:
        if col in df.columns:
            styler = styler.applymap(aplicar_estilo_celula, subset=[col])

    return styler


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():
    armazenamento = get_armazenamento()
    exibir_status_conexao(armazenamento)
    exibir_menu_lateral(armazenamento)

    st.title("📊 Previsibilidade")
    st.caption("Fluxo de Caixa Diário - Visualize seu saldo futuro projetado dia a dia")

    # Carregar dados
    df = carregar_dados()

    # Data de hoje
    data_hoje = date.today()

    # ========== SIDEBAR - SELEÇÃO DE MÊS/ANO ==========
    st.sidebar.header("📅 Período")

    meses_opcoes = {
        'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
        'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
        'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
    }

    col_mes, col_ano = st.sidebar.columns(2)

    with col_mes:
        mes_nome = st.selectbox(
            "Mês",
            options=list(meses_opcoes.keys()),
            index=data_hoje.month - 1,
            key="prev_mes"
        )
        mes_selecionado = meses_opcoes[mes_nome]

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
        st.warning("⚠️ Nenhuma transação encontrada.")
        st.info("💡 Acesse **Registrar** para adicionar suas primeiras transações!")
        exibir_rodape()
        st.stop()

    # ========== GERAR FLUXO DE CAIXA ==========
    df_fluxo, saldo_ant_comum, saldo_ant_vr = gerar_fluxo_caixa_diario(df, ano_selecionado, mes_selecionado)

    # Calcular métricas do resumo
    saldo_inicial_total = saldo_ant_comum + saldo_ant_vr

    if not df_fluxo.empty:
        saldo_final_comum = df_fluxo['Saldo_Acum_Comum'].iloc[-1]
        saldo_final_vr = df_fluxo['Saldo_Acum_VR'].iloc[-1]
        total_entradas = df_fluxo['Entradas'].sum()
        total_saidas = df_fluxo['Saidas'].sum()
    else:
        saldo_final_comum = saldo_ant_comum
        saldo_final_vr = saldo_ant_vr
        total_entradas = 0
        total_saidas = 0

    saldo_final_total = saldo_final_comum + saldo_final_vr
    resultado_mes = total_entradas - total_saidas

    # ========== CARDS DE RESUMO ==========
    st.subheader(f"Resumo de {obter_nome_mes(mes_selecionado)} {ano_selecionado}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="💰 Saldo Inicial",
            value=formatar_valor_br(saldo_inicial_total),
            help="Saldo acumulado até o último dia do mês anterior"
        )

    with col2:
        st.metric(
            label="📈 Previsão Saldo Final",
            value=formatar_valor_br(saldo_final_total),
            delta=f"Comum: {formatar_valor_br(saldo_final_comum)}",
            help="Saldo projetado para o último dia do mês"
        )

    with col3:
        delta_resultado = "Superávit" if resultado_mes >= 0 else "Déficit"
        st.metric(
            label="📊 Resultado do Mês",
            value=formatar_valor_br(resultado_mes),
            delta=delta_resultado,
            delta_color="normal" if resultado_mes >= 0 else "inverse",
            help="Entradas - Saídas do mês"
        )

    st.markdown("---")

    # ========== TABELA DE FLUXO DE CAIXA ==========
    st.subheader(f"📅 Fluxo de Caixa Diário")

    # Preparar DataFrame para exibição
    df_display = df_fluxo.copy()

    # Guardar data original para estilização
    df_display['Data_Original'] = df_display['Data']

    # Formatar valores para exibição
    df_display['Entradas_Fmt'] = df_display['Entradas'].apply(formatar_valor_br)
    df_display['Saidas_Fmt'] = df_display['Saidas'].apply(formatar_valor_br)
    df_display['Saldo_Dia_Fmt'] = df_display['Saldo_Dia'].apply(formatar_valor_br)
    df_display['Saldo_Acum_Comum_Fmt'] = df_display['Saldo_Acum_Comum'].apply(formatar_valor_br)
    df_display['Saldo_Acum_VR_Fmt'] = df_display['Saldo_Acum_VR'].apply(formatar_valor_br)

    # Selecionar colunas para exibição
    df_tabela = df_display[['Data_Display', 'Entradas_Fmt', 'Saidas_Fmt', 'Saldo_Dia_Fmt',
                            'Saldo_Acum_Comum_Fmt', 'Saldo_Acum_VR_Fmt', 'Data_Original']].copy()
    df_tabela.columns = ['Data', 'Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR', 'Data_Original']

    # Aplicar estilos
    styled_df = aplicar_estilos(df_tabela, data_hoje)

    # Ocultar coluna auxiliar e exibir
    df_tabela_final = df_tabela.drop(columns=['Data_Original'])

    # Aplicar estilos novamente no df final
    def highlight_hoje_final(row):
        idx = row.name
        try:
            data_row = df_tabela.loc[idx, 'Data_Original']
            if pd.notna(data_row):
                data_row = data_row.date() if hasattr(data_row, 'date') else data_row
                if data_row == data_hoje:
                    return ['background-color: #e3f2fd; color: #1565c0; font-weight: bold'] * len(row)
        except:
            pass
        return [''] * len(row)

    def estilizar_valores(val):
        if pd.isna(val) or not isinstance(val, str) or 'R$' not in val:
            return ''
        try:
            valor = float(val.replace('R$', '').replace('.', '').replace(',', '.').strip())
            if valor < 0:
                return 'color: #d32f2f; background-color: #ffebee'
            elif valor > 0:
                return 'color: #2e7d32'
            else:
                return 'color: #9e9e9e'
        except:
            return ''

    colunas_valor = ['Entradas', 'Saídas', 'Saldo Dia', 'Saldo Comum', 'Saldo VR']

    styled_final = df_tabela_final.style.apply(highlight_hoje_final, axis=1)
    for col in colunas_valor:
        if col in df_tabela_final.columns:
            styled_final = styled_final.applymap(estilizar_valores, subset=[col])

    # Exibir tabela
    st.dataframe(
        styled_final,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Data": st.column_config.TextColumn("📅 Data", width="medium"),
            "Entradas": st.column_config.TextColumn("💚 Entradas", width="small"),
            "Saídas": st.column_config.TextColumn("❤️ Saídas", width="small"),
            "Saldo Dia": st.column_config.TextColumn("📊 Saldo Dia", width="small"),
            "Saldo Comum": st.column_config.TextColumn("🏦 Saldo Comum", width="medium"),
            "Saldo VR": st.column_config.TextColumn("🍽️ Saldo VR", width="medium"),
        }
    )

    # ========== LEGENDA ==========
    st.markdown("""
    <div style="display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap; font-family: sans-serif; font-size: 0.85rem;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="background-color: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-weight: bold;">Hoje</span>
            <span style="color: #555;">Dia atual destacado</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="color: #2e7d32; font-weight: bold;">Verde</span>
            <span style="color: #555;">Valores positivos</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="color: #d32f2f; font-weight: bold;">Vermelho</span>
            <span style="color: #555;">Valores negativos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== RODAPÉ ==========
    exibir_rodape()


if __name__ == "__main__":
    main()


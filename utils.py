"""
Somma - Módulo de Utilitários Compartilhados
Contém todas as funções lógicas, classes e constantes do sistema.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import tempfile
import zipfile

# Imports para Auto-Update
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False

# Imports para Google Sheets (opcional)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from gspread.exceptions import SpreadsheetNotFound, APIError
    GSPREAD_DISPONIVEL = True
except ImportError:
    GSPREAD_DISPONIVEL = False


# ============================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================

# Caminhos do sistema
BASE_DIR = Path(__file__).parent
CAMINHO_CREDENCIAIS = BASE_DIR / "credentials.json"
CAMINHO_CSV = BASE_DIR / "dados_financeiros.csv"
CAMINHO_VERSION = BASE_DIR / "version.txt"
CAMINHO_PREFERENCIAS = BASE_DIR / "preferencias_update.csv"
NOME_PLANILHA = "Controle Financeiro"

# Estrutura de colunas do sistema
COLUNAS_SISTEMA = ['Data', 'Descricao', 'Categoria', 'Valor', 'Tipo', 'Conta']

# Tipos de Conta / Forma de Pagamento
TIPOS_CONTA = ['Conta Comum', 'Vale Refeição']

# Categorias específicas para Vale Refeição (Despesa)
CAT_VALE_REFEICAO = [
    'Alimentação',
    'Refeição',
    'Supermercado'
]

# Categorias de DESPESA
CAT_DESPESA = [
    'Moradia',
    'Vale Alimentação/Refeição',
    'Transporte',
    'Saúde',
    'Educação',
    'Lazer',
    'Vestuário',
    'Assinaturas',
    'Impostos',
    'Seguros',
    'Telefone/Internet',
    'Cartão de Crédito',
    'Empréstimos',
    'Outros (Despesa)'
]

# Categorias de RECEITA
CAT_RECEITA = [
    'Salário',
    'Freelance',
    'Investimentos',
    'Dividendos',
    'Aluguel Recebido',
    'Vendas',
    'Bônus',
    'Restituição IR',
    'Presente/Doação',
    'Outros (Receita)'
]

# Lista combinada para compatibilidade
CATEGORIAS_PADRAO = CAT_DESPESA + CAT_RECEITA

# Tipos de transação
TIPOS_TRANSACAO = ['Despesa', 'Receita']

# Configurações de Auto-Update
GITHUB_OWNER = "edinaldogomews"
GITHUB_REPO = "controlefinanceiroap"
GITHUB_BRANCH = "main"

# Arquivos protegidos durante atualização
ARQUIVOS_PROTEGIDOS = [
    'credentials.json',
    'credenciais.json',
    'dados_financeiros.csv',
    'preferencias_update.csv',
    '.env',
    'venv',
    '.venv',
    '__pycache__',
]


# ============================================================
# CSS GLOBAL
# ============================================================
CSS_GLOBAL = """
    <style>
        /* ===== OCULTAR ELEMENTOS PADRÃO DO STREAMLIT ===== */
        .stDeployButton { display: none !important; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }

        /* ===== AJUSTES DE ESPAÇAMENTO ===== */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

        /* ===== ESTILIZAÇÃO DOS CARDS/MÉTRICAS ===== */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* ===== ESTILIZAÇÃO DA SIDEBAR ===== */
        hr { border: none; border-top: 1px solid #e9ecef; margin: 1rem 0; }

        /* ===== MELHORIAS NOS BOTÕES ===== */
        .stButton > button {
            transition: all 0.3s ease;
            border-radius: 8px;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* ===== TABELA DE DADOS ===== */
        .stDataFrame { border-radius: 10px; overflow: hidden; }

        /* ===== ESTILO DO AVISO DE ATUALIZAÇÃO ===== */
        .update-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            color: white;
        }
    </style>
"""

LOGO_SIDEBAR = """
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="
            background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 3px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        ">💰 Somma</h1>
        <p style="
            color: #555;
            font-size: 1rem;
            margin-top: 8px;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
        ">Controle Financeiro</p>
        <div style="
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #2E86AB, #1a5276);
            margin: 12px auto 0;
            border-radius: 2px;
        "></div>
    </div>
"""


# ============================================================
# FUNÇÕES AUXILIARES DE UI
# ============================================================
def aplicar_estilo_global():
    """Aplica o CSS global e o logo na sidebar."""
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
    st.sidebar.markdown(LOGO_SIDEBAR, unsafe_allow_html=True)
    st.sidebar.markdown("---")


def exibir_rodape(versao_local: str = None):
    """Exibe o rodapé da sidebar com informações de versão."""
    if versao_local is None:
        versao_local = ler_versao_local()
    st.sidebar.markdown("---")
    st.sidebar.caption("Dashboard Financeiro Gratuito")
    st.sidebar.caption("Desenvolvido por Edinaldo Gomes")
    st.sidebar.caption("📧 edinaldosantos.contato@gmail.com")
    st.sidebar.caption(f"📦 Versão: {versao_local}")
    st.sidebar.caption("© 2025 Todos os direitos reservados")


def exibir_status_conexao(armazenamento):
    """Exibe o badge de status de conexão no topo do app."""
    modo_texto, modo_tipo, is_online = armazenamento.get_modo_info()

    if is_online:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #d4edda, #c3e6cb);
                border: 1px solid #28a745;
                border-radius: 25px;
                padding: 8px 20px;
                display: inline-block;
                margin-bottom: 15px;
            ">
                <span style="color: #155724; font-weight: 600; font-size: 0.9rem;">
                    {modo_texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        cor_fundo = "#fff3cd" if modo_tipo == "warning" else "#f8d7da"
        cor_borda = "#ffc107" if modo_tipo == "warning" else "#dc3545"
        cor_texto = "#856404" if modo_tipo == "warning" else "#721c24"

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, {cor_fundo}, {cor_fundo});
                border: 1px solid {cor_borda};
                border-radius: 25px;
                padding: 8px 20px;
                display: inline-block;
                margin-bottom: 15px;
            ">
                <span style="color: {cor_texto}; font-weight: 600; font-size: 0.9rem;">
                    {modo_texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


def formatar_valor_br(valor: float) -> str:
    """Formata um valor numérico para o padrão brasileiro (R$ X.XXX,XX)."""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_mes_ano_completo(periodo: str) -> str:
    """Converte período YYYY-MM para formato 'Mês/Ano' (ex: Janeiro/2026)."""
    try:
        if pd.isna(periodo) or periodo == 'NaT':
            return 'Sem data'
        ano, mes = periodo.split('-')
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        return f"{meses[int(mes)-1]}/{ano}"
    except:
        return 'Sem data'


def formatar_mes_curto(periodo: str) -> str:
    """Converte período YYYY-MM para formato 'Mmm/AA' (ex: Jan/26)."""
    try:
        ano, mes = periodo.split('-')
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        return f"{meses[int(mes)-1]}/{ano[2:]}"
    except:
        return periodo


# ============================================================
# FUNÇÕES DE CÁLCULO DE SALDOS
# ============================================================
def calcular_saldos(df: pd.DataFrame) -> dict:
    """
    Calcula todos os saldos separados por conta.

    Returns:
        dict com: saldo_comum, saldo_vr, receitas_comum, despesas_comum,
                  receitas_vr, despesas_vr, tem_transacoes_vr, mostrar_card_vr
    """
    # Saldo Conta Comum
    df_conta_comum = df[df['Conta'] == 'Comum']
    receitas_comum = df_conta_comum[df_conta_comum['Tipo'] == 'Receita']['Valor'].sum()
    despesas_comum = df_conta_comum[df_conta_comum['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_comum = receitas_comum - despesas_comum

    # Saldo Vale Refeição
    df_conta_vr = df[df['Conta'] == 'Vale Refeição']
    receitas_vr = df_conta_vr[df_conta_vr['Tipo'] == 'Receita']['Valor'].sum()
    despesas_vr = df_conta_vr[df_conta_vr['Tipo'] == 'Despesa']['Valor'].sum()
    saldo_vr = receitas_vr - despesas_vr

    # Verificar se deve mostrar card VR
    tem_transacoes_vr = len(df_conta_vr) > 0
    mostrar_card_vr = tem_transacoes_vr or saldo_vr != 0

    return {
        'saldo_comum': saldo_comum,
        'saldo_vr': saldo_vr,
        'receitas_comum': receitas_comum,
        'despesas_comum': despesas_comum,
        'receitas_vr': receitas_vr,
        'despesas_vr': despesas_vr,
        'tem_transacoes_vr': tem_transacoes_vr,
        'mostrar_card_vr': mostrar_card_vr
    }


def calcular_totais_periodo(df: pd.DataFrame) -> dict:
    """
    Calcula receitas e despesas totais de um DataFrame.

    Returns:
        dict com: total_receitas, total_despesas, saldo
    """
    total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()

    return {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': total_receitas - total_despesas
    }


# ============================================================
# FUNÇÕES DE VERSÃO E ATUALIZAÇÃO
# ============================================================
def ler_versao_local() -> str:
    """Lê a versão do arquivo local version.txt."""
    try:
        if CAMINHO_VERSION.exists():
            return CAMINHO_VERSION.read_text(encoding='utf-8').strip()
        return "0.0.0"
    except Exception:
        return "0.0.0"


# ============================================================
# SISTEMA DE AUTO-UPDATE
# ============================================================
class AutoUpdate:
    """Sistema de atualização automática via GitHub."""

    def __init__(self):
        self.versao_local = ler_versao_local()
        self.versao_remota = None
        self.url_zip = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
        self.url_version = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/version.txt"

    def verificar_atualizacao(self) -> tuple:
        """Verifica se há nova versão disponível."""
        if not REQUESTS_DISPONIVEL:
            return False, self.versao_local, "Biblioteca 'requests' não instalada."

        try:
            response = requests.get(self.url_version, timeout=10)
            response.raise_for_status()
            self.versao_remota = response.text.strip()

            if self.versao_remota != self.versao_local:
                return True, self.versao_remota, f"Nova versão disponível: {self.versao_remota}"
            else:
                return False, self.versao_remota, "Você está usando a versão mais recente."

        except requests.exceptions.Timeout:
            return False, self.versao_local, "Tempo limite excedido ao verificar atualizações."
        except requests.exceptions.ConnectionError:
            return False, self.versao_local, "Sem conexão com a internet."
        except Exception as e:
            return False, self.versao_local, f"Erro ao verificar: {str(e)}"

    def realizar_update(self, progress_callback=None) -> tuple:
        """Realiza o download e instalação da atualização."""
        if not REQUESTS_DISPONIVEL:
            return False, "Biblioteca 'requests' não instalada."

        pasta_app = BASE_DIR
        pasta_temp = None

        try:
            if progress_callback:
                progress_callback("📥 Baixando atualização...", 0.1)

            response = requests.get(self.url_zip, timeout=60, stream=True)
            response.raise_for_status()

            pasta_temp = Path(tempfile.mkdtemp())
            caminho_zip = pasta_temp / "update.zip"

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(caminho_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            progress = 0.1 + (downloaded / total_size) * 0.3
                            progress_callback(f"📥 Baixando... {downloaded // 1024} KB", progress)

            if progress_callback:
                progress_callback("📦 Extraindo arquivos...", 0.45)

            pasta_extracao = pasta_temp / "extracted"
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_extracao)

            pastas_extraidas = list(pasta_extracao.iterdir())
            if not pastas_extraidas:
                return False, "Arquivo ZIP vazio ou corrompido."

            pasta_repo = pastas_extraidas[0]

            if progress_callback:
                progress_callback("🔄 Atualizando arquivos...", 0.6)

            arquivos_atualizados = 0

            for item in pasta_repo.iterdir():
                nome_item = item.name

                if nome_item in ARQUIVOS_PROTEGIDOS:
                    continue

                destino = pasta_app / nome_item

                try:
                    if item.is_file():
                        shutil.copy2(item, destino)
                        arquivos_atualizados += 1
                    elif item.is_dir():
                        if destino.exists():
                            shutil.rmtree(destino)
                        shutil.copytree(item, destino)
                        arquivos_atualizados += 1
                except Exception as e:
                    print(f"Aviso: Não foi possível atualizar {nome_item}: {e}")

            if progress_callback:
                progress_callback("🧹 Limpando arquivos temporários...", 0.9)

            try:
                shutil.rmtree(pasta_temp)
            except Exception:
                pass

            if progress_callback:
                progress_callback("✅ Atualização concluída!", 1.0)

            return True, f"Atualização concluída! {arquivos_atualizados} arquivos atualizados."

        except requests.exceptions.Timeout:
            return False, "Tempo limite excedido durante o download."
        except requests.exceptions.ConnectionError:
            return False, "Falha na conexão durante o download."
        except zipfile.BadZipFile:
            return False, "Arquivo de atualização corrompido."
        except PermissionError:
            return False, "Sem permissão para atualizar arquivos. Execute como administrador."
        except Exception as e:
            return False, f"Erro durante atualização: {str(e)}"
        finally:
            if pasta_temp and pasta_temp.exists():
                try:
                    shutil.rmtree(pasta_temp)
                except Exception:
                    pass


# ============================================================
# FUNÇÕES DE PREFERÊNCIAS DE ATUALIZAÇÃO
# ============================================================
def carregar_preferencias_update() -> dict:
    """Carrega preferências de atualização do usuário."""
    try:
        if CAMINHO_PREFERENCIAS.exists():
            df = pd.read_csv(CAMINHO_PREFERENCIAS)
            if not df.empty:
                return df.iloc[0].to_dict()
    except Exception:
        pass

    return {
        'nao_perguntar': False,
        'lembrar_depois': False,
        'lembrar_data': '',
        'versao_ignorada': ''
    }


def salvar_preferencias_update(preferencias: dict):
    """Salva preferências de atualização do usuário."""
    try:
        df = pd.DataFrame([preferencias])
        df.to_csv(CAMINHO_PREFERENCIAS, index=False)
    except Exception:
        pass


def deve_mostrar_atualizacao(versao_remota: str) -> bool:
    """Verifica se deve mostrar o aviso de atualização."""
    prefs = carregar_preferencias_update()

    if prefs.get('nao_perguntar') and prefs.get('versao_ignorada') == versao_remota:
        return False

    if prefs.get('lembrar_depois') and prefs.get('lembrar_data'):
        try:
            data_lembrar = datetime.fromisoformat(prefs['lembrar_data'])
            if datetime.now() < data_lembrar:
                return False
        except Exception:
            pass

    return True


def resetar_preferencias_update():
    """Reseta as preferências de atualização."""
    try:
        if CAMINHO_PREFERENCIAS.exists():
            CAMINHO_PREFERENCIAS.unlink()
    except Exception:
        pass


# ============================================================
# SISTEMA DE ARMAZENAMENTO HÍBRIDO
# ============================================================
class ArmazenamentoHibrido:
    """
    Sistema de armazenamento com fallback:
    1. Google Sheets (se credentials.json existir)
    2. CSV Local (se não houver credenciais ou falhar conexão)
    3. DataFrame vazio (se não houver dados)
    """

    def __init__(self):
        self.modo = None
        self.worksheet = None
        self._detectar_modo()

    def _detectar_modo(self):
        """Detecta qual modo de armazenamento usar."""
        if CAMINHO_CREDENCIAIS.exists() and GSPREAD_DISPONIVEL:
            try:
                self.worksheet = self._conectar_gsheets()
                if self.worksheet is not None:
                    self.modo = 'gsheets'
                    return
            except Exception:
                pass

        if CAMINHO_CSV.exists():
            self.modo = 'csv'
            return

        self.modo = 'memoria'

    def _conectar_gsheets(self):
        """Conecta ao Google Sheets usando credenciais."""
        try:
            scopes = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credenciais = None

            try:
                credenciais_dict = st.secrets["gcp_service_account"]
                credenciais = ServiceAccountCredentials.from_json_keyfile_dict(
                    dict(credenciais_dict), scopes
                )
            except (KeyError, FileNotFoundError):
                if CAMINHO_CREDENCIAIS.exists():
                    credenciais = ServiceAccountCredentials.from_json_keyfile_name(
                        str(CAMINHO_CREDENCIAIS), scopes
                    )

            if credenciais is None:
                return None

            cliente = gspread.authorize(credenciais)
            planilha = cliente.open(NOME_PLANILHA)
            return planilha.get_worksheet(0)

        except Exception:
            return None

    def get_modo_info(self):
        """Retorna informações sobre o modo atual."""
        modos = {
            'gsheets': ('🟢 Conectado à Nuvem (Google Sheets)', 'success', True),
            'csv': ('🟠 Modo Offline (CSV Local)', 'warning', False),
            'memoria': ('🔴 Memória Temporária (sem persistência)', 'error', False)
        }
        return modos.get(self.modo, ('❓ Desconhecido', 'error', False))

    def carregar_dados(self):
        """Carrega dados de acordo com o modo atual."""
        if self.modo == 'gsheets':
            return self._carregar_gsheets()
        elif self.modo == 'csv':
            return self._carregar_csv()
        else:
            return self._criar_df_vazio()

    def _carregar_gsheets(self):
        """Carrega dados do Google Sheets."""
        try:
            if self.worksheet is None:
                self.worksheet = self._conectar_gsheets()

            if self.worksheet is None:
                self.modo = 'csv'
                return self._carregar_csv()

            registros = self.worksheet.get_all_records()

            if not registros:
                return self._criar_df_vazio()

            df = pd.DataFrame(registros)
            return self._normalizar_dados(df)

        except Exception:
            self.modo = 'csv'
            return self._carregar_csv()

    def _carregar_csv(self):
        """Carrega dados do arquivo CSV local."""
        try:
            if not CAMINHO_CSV.exists():
                return self._criar_df_vazio()

            df = pd.read_csv(CAMINHO_CSV)

            if df.empty:
                return self._criar_df_vazio()

            return self._normalizar_dados(df)

        except Exception:
            return self._criar_df_vazio()

    def _criar_df_vazio(self):
        """Cria um DataFrame vazio com a estrutura correta."""
        return pd.DataFrame(columns=COLUNAS_SISTEMA)

    def _normalizar_dados(self, df):
        """Normaliza o DataFrame para a estrutura padrão do sistema."""
        mapeamento = {
            'Vencimento': 'Data', 'data': 'Data', 'DATA': 'Data',
            'Descrição': 'Descricao', 'descricao': 'Descricao', 'DESCRICAO': 'Descricao',
            'categoria': 'Categoria', 'CATEGORIA': 'Categoria',
            'valor': 'Valor', 'VALOR': 'Valor',
            'tipo': 'Tipo', 'TIPO': 'Tipo', 'Status': 'Tipo',
            'conta': 'Conta', 'CONTA': 'Conta'
        }

        df = df.rename(columns=mapeamento)

        for col in COLUNAS_SISTEMA:
            if col not in df.columns:
                if col == 'Tipo':
                    df[col] = 'Despesa'
                elif col == 'Conta':
                    df[col] = 'Comum'
                else:
                    df[col] = ''

        df = df[[col for col in COLUNAS_SISTEMA if col in df.columns]]
        df = df.dropna(how='all')
        df['Valor'] = df['Valor'].apply(self._limpar_valor)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)
        df['Descricao'] = df['Descricao'].fillna('').astype(str)
        df['Categoria'] = df['Categoria'].fillna('Outros').replace('', 'Outros')
        df['Tipo'] = df['Tipo'].fillna('Despesa').replace('', 'Despesa')
        df['Conta'] = df['Conta'].fillna('Comum').replace('', 'Comum')
        df['Tipo'] = df['Tipo'].apply(self._normalizar_tipo)
        df['Conta'] = df['Conta'].apply(self._normalizar_conta)
        df = df[df['Descricao'].str.strip() != '']

        return df.reset_index(drop=True)

    def _limpar_valor(self, valor):
        """Limpa e converte valor para float."""
        if pd.isna(valor) or valor == '':
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        valor_str = str(valor).replace('R$', '').strip().replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except ValueError:
            return 0.0

    def _normalizar_tipo(self, tipo):
        """Normaliza o tipo de transação."""
        tipo_str = str(tipo).strip().upper()
        if tipo_str in ['RECEITA', 'ENTRADA', 'CRÉDITO', 'CREDITO']:
            return 'Receita'
        elif tipo_str in ['DESPESA', 'SAÍDA', 'SAIDA', 'DÉBITO', 'DEBITO', 'PAGO', 'EM ABERTO']:
            return 'Despesa'
        return 'Despesa'

    def _normalizar_conta(self, conta):
        """Normaliza o valor da conta para o formato interno."""
        conta_str = str(conta).strip().upper()
        if conta_str in ['VALE REFEIÇÃO', 'VALE REFEICAO', 'VR', 'VALE-REFEIÇÃO', 'VALE-REFEICAO']:
            return 'Vale Refeição'
        elif conta_str in ['CONTA COMUM', 'COMUM', 'PRINCIPAL', '']:
            return 'Comum'
        return 'Comum'

    def salvar_dados(self, df):
        """Salva o DataFrame completo no armazenamento atual."""
        if self.modo == 'gsheets':
            return self._salvar_dados_gsheets(df)
        elif self.modo == 'csv':
            return self._salvar_dados_csv(df)
        else:
            return self._salvar_dados_memoria(df)

    def _salvar_dados_gsheets(self, df):
        """Salva DataFrame completo no Google Sheets."""
        try:
            if self.worksheet is None:
                self.worksheet = self._conectar_gsheets()

            if self.worksheet is None:
                self.modo = 'csv'
                return self._salvar_dados_csv(df)

            df_export = df.copy()
            df_export['Data'] = df_export['Data'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
            )
            df_export['Valor'] = df_export['Valor'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )

            self.worksheet.clear()
            self.worksheet.append_row(COLUNAS_SISTEMA)

            if not df_export.empty:
                dados = df_export.values.tolist()
                self.worksheet.append_rows(dados)

            return True, "Dados salvos com sucesso no Google Sheets!"

        except Exception as e:
            return False, f"Erro ao salvar no Google Sheets: {str(e)}"

    def _salvar_dados_csv(self, df):
        """Salva DataFrame completo no arquivo CSV."""
        try:
            df_export = df.copy()
            if 'Data' in df_export.columns:
                df_export['Data'] = df_export['Data'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
                )
            df_export.to_csv(CAMINHO_CSV, index=False)
            return True, "Dados salvos com sucesso no arquivo CSV!"
        except Exception as e:
            return False, f"Erro ao salvar no CSV: {str(e)}"

    def _salvar_dados_memoria(self, df):
        """Salva dados criando um novo arquivo CSV."""
        try:
            sucesso, mensagem = self._salvar_dados_csv(df)
            if sucesso:
                self.modo = 'csv'
                return True, "Arquivo CSV criado com sucesso! Dados salvos."
            return sucesso, mensagem
        except Exception as e:
            return False, f"Erro ao criar arquivo: {str(e)}"

    def salvar_transacao(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma nova transação."""
        if self.modo == 'gsheets':
            return self._salvar_transacao_gsheets(data, descricao, categoria, valor, tipo, conta)
        elif self.modo == 'csv':
            return self._salvar_transacao_csv(data, descricao, categoria, valor, tipo, conta)
        else:
            return self._salvar_transacao_memoria(data, descricao, categoria, valor, tipo, conta)

    def _salvar_transacao_gsheets(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma transação no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão com Google Sheets."

            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            nova_linha = [data_formatada, descricao, categoria, valor_formatado, tipo, conta]
            self.worksheet.append_row(nova_linha)

            return True, "Transação salva com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_csv(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva uma transação no arquivo CSV."""
        try:
            if CAMINHO_CSV.exists():
                df = pd.read_csv(CAMINHO_CSV)
                df = self._normalizar_dados(df)
            else:
                df = self._criar_df_vazio()

            nova_linha = pd.DataFrame([{
                'Data': data,
                'Descricao': descricao,
                'Categoria': categoria,
                'Valor': valor,
                'Tipo': tipo,
                'Conta': conta
            }])

            df = pd.concat([df, nova_linha], ignore_index=True)
            return self._salvar_dados_csv(df)

        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def _salvar_transacao_memoria(self, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Salva na memória e cria arquivo CSV."""
        try:
            sucesso, mensagem = self._salvar_transacao_csv(data, descricao, categoria, valor, tipo, conta)
            if sucesso:
                self.modo = 'csv'
                return True, "Arquivo CSV criado com sucesso! Dados salvos."
            return sucesso, mensagem
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def excluir_transacao(self, indice):
        """Exclui uma transação pelo índice."""
        if self.modo == 'gsheets':
            return self._excluir_gsheets(indice)
        elif self.modo == 'csv':
            return self._excluir_csv(indice)
        else:
            return False, "Não é possível excluir em modo memória."

    def _excluir_gsheets(self, indice):
        """Exclui do Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão."
            linha_sheet = indice + 2
            self.worksheet.delete_rows(linha_sheet)
            return True, "Transação excluída com sucesso!"
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    def _excluir_csv(self, indice):
        """Exclui do CSV."""
        try:
            df = pd.read_csv(CAMINHO_CSV)
            df = self._normalizar_dados(df)
            df = df.drop(indice).reset_index(drop=True)
            return self._salvar_dados_csv(df)
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    def editar_transacao(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita uma transação existente."""
        if self.modo == 'gsheets':
            return self._editar_gsheets(indice, data, descricao, categoria, valor, tipo, conta)
        elif self.modo == 'csv':
            return self._editar_csv(indice, data, descricao, categoria, valor, tipo, conta)
        else:
            return False, "Não é possível editar em modo memória."

    def _editar_gsheets(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita no Google Sheets."""
        try:
            if self.worksheet is None:
                return False, "Erro de conexão."

            linha_sheet = indice + 2
            data_formatada = data.strftime('%Y-%m-%d')
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            novos_valores = [data_formatada, descricao, categoria, valor_formatado, tipo, conta]
            range_name = f"A{linha_sheet}:F{linha_sheet}"
            self.worksheet.update(range_name, [novos_valores])

            return True, "Transação atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"

    def _editar_csv(self, indice, data, descricao, categoria, valor, tipo, conta='Comum'):
        """Edita no CSV."""
        try:
            df = pd.read_csv(CAMINHO_CSV)
            df = self._normalizar_dados(df)

            df.at[indice, 'Data'] = data
            df.at[indice, 'Descricao'] = descricao
            df.at[indice, 'Categoria'] = categoria
            df.at[indice, 'Valor'] = valor
            df.at[indice, 'Tipo'] = tipo
            df.at[indice, 'Conta'] = conta

            return self._salvar_dados_csv(df)
        except Exception as e:
            return False, f"Erro ao editar: {str(e)}"


# ============================================================
# FUNÇÕES GLOBAIS COM CACHE
# ============================================================
@st.cache_resource
def get_armazenamento():
    """Retorna instância única do sistema de armazenamento."""
    return ArmazenamentoHibrido()


@st.cache_data(ttl=60)
def carregar_dados():
    """Carrega dados usando o sistema híbrido com cache."""
    armazenamento = get_armazenamento()
    return armazenamento.carregar_dados()


def limpar_cache_e_recarregar():
    """Limpa o cache de dados e força recarregamento."""
    st.cache_data.clear()
    st.rerun()

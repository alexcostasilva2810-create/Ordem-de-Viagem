import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. DESIGN E CONFIGURAÇÃO (TRAVA DE GRID)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 1rem; margin: auto; }
    
    /* Força todas as colunas a terem o mesmo tamanho e não quebrarem */
    [data-testid="column"] {
        width: calc(33.3333% - 1rem) !important;
        flex: 1 1 calc(33.3333% - 1rem) !important;
        min-width: 300px !important;
    }
    
    /* Ajuste de espaçamento vertical */
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    
    /* Balsa flexível sem quebrar o vizinho */
    div[data-baseweb="select"] > div:first-child { max-height: none !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. FUNÇÕES DE APOIO (PDF E DADOS)
# =========================================================
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=2)
def carregar_dados_zion():
    client = conectar()
    sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
    ativos = sh.worksheet("Ativos").col_values(1)[1:]
    balsas = sh.worksheet("Balsas").col_values(1)[1:]
    rotas = sh.worksheet("Rotas").get_all_values()[1:]
    hist = sh.worksheet("Historico").get_all_values()
    df_h = pd.DataFrame(hist[1:], columns=hist[0]).loc[:, ~pd.Series(hist[0]).duplicated()]
    return ativos, balsas, rotas, df_h

class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        self.cell(0, 10, f'Gerado em: {datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")}', align='C')

# =========================================================
# 3. INTERFACE (4 LINHAS X 3 COLUNAS)
# =========================================================
with st.sidebar:
    pagina = st.radio("NAVEGAÇÃO", ["📊 Simulações", "📜 Histórico"])

ativos, lista_balsas, lista_rotas, df_h = carregar_dados_zion()
d = st.session_state.dados_edit

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    with st.expander("🔍 BUSCAR REGISTRO"):
        id_sel = st.selectbox("ID:", ["---"] + df_h.iloc[:, 0].tolist())
        if st.button("CARREGAR"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
            st.rerun()

    # --- LINHA 1 ---
    l1c1, l1c2, l1c3 = st.columns(3)
    v_emp = l1c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    v_bal = l1c2.multiselect("Balsas", lista_balsas, default=ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else [])
    v_com = l1c3.text_input("Comandante", value=d.get('Comandante', ""))

    # --- LINHA 2 ---
    l2c1, l2c2, l2c3 = st.columns(3)
    oris = sorted(list(set([r[0] for r in lista_rotas if r[0]])))
    dess = sorted(list(set([r[1] for r in lista_rotas if r[1]])))
    v_ori = l2c1.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
    v_des = l2c2.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
    v_chf = l2c3.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    # --- LINHA 3 ---
    l3c1, l3c2, l3c3 = st.columns(3)
    v_vol = l3c1.number_input("Volume (M³)", value=float(str(d.get('Volume',0)).replace('.','').replace(',','.')) if d.get('Volume') else 0.0)
    v_fat = l3c2.number_input("Faturamento (R$)", value=float(str(d.get('Faturamento',0)).replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0)
    v_hor = l3c3.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    # --- LINHA 4 ---
    l4c1, l4c2, l4c3 = st.columns(3)
    v_tmp = l4c1.number_input("Tempo (H)", value=int(d.get('Tempo Previsto (H)', 0)))
    v_cbm = l4c2.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
    v_dsl = l4c3.number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel',0)).replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0)

    v_obs = st.text_area("Observações", value=d.get('Observações', ""))
    
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E GERAR PDF"):
        pdf = PDF_ZION()
        pdf.add_page()
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"ID: {d.get('ID', 'NOVO')}", ln=True)
        pdf.cell(0, 10, f"Empurrador: {v_emp}", ln=True)
        pdf.cell(0, 10, f"Faturamento: R$ {v_fat:,.2f}", ln=True)
        st.download_button("📥 BAIXAR ORDEM", pdf.output(dest="S").encode("latin-1"), "ordem.pdf")

elif pagina == "📜 Histórico":
    st.dataframe(df_h, use_container_width=True, hide_index=True)

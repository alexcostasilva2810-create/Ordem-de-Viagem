import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (COM ESPAÇAMENTO DE 2CM)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    /* Afasta o conteúdo do topo em aproximadamente 2cm (70px) */
    .block-container { max-width: 1100px; padding-top: 70px; margin: auto; }
    
    /* Estilo da Capa */
    .capa-box {
        text-align: center;
        padding: 60px;
        background-color: #f0f2f6;
        border-radius: 20px;
        border: 2px solid #073763;
        margin-bottom: 30px;
    }
    
    /* Trava de Grid para não acavalar */
    [data-testid="column"] { min-width: 280px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.5rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CARREGAMENTO DE DADOS (RESTAURADO COMPLETO)
# =========================================================
@st.cache_data(ttl=2)
def carregar_tudo_zion():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        hist_raw = sh.worksheet("Historico").get_all_values()
        df_h = pd.DataFrame(hist_raw[1:], columns=hist_raw[0]).loc[:, ~pd.Series(hist_raw[0]).duplicated()]
        return ativos, balsas, rotas, df_h
    except:
        return [], [], [], pd.DataFrame()

ativos, lista_balsas, lista_rotas, df_h = carregar_tudo_zion()

# =========================================================
# 3. NAVEGAÇÃO
# =========================================================

if st.session_state.pagina_atual == "Capa":
    st.markdown('<div class="capa-box">', unsafe_allow_html=True)
    st.title("🚢 ZION - GESTÃO PCO")
    st.subheader("Sistema de Controle e Simulação de Viagens")
    st.write("Transdourada Navegação")
    st.markdown('</div>', unsafe_allow_html=True)
    
    _, col_btn, _ = st.columns([1, 1, 1])
    if col_btn.button("🚀 INICIAR SISTEMA"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    # Sidebar Restaurada com Histórico e Simulação
    with st.sidebar:
        st.image("https://www.google.com/s2/favicons?domain=streamlit.io", width=30) # Espaçador
        if st.button("⬅️ VOLTAR PARA CAPA"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        st.write("---")
        menu = st.radio("MENU PRINCIPAL", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulação de Viagem")
        
        # BUSCA FUNCIONAL (RESTAURADA)
        with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO", expanded=False):
            if not df_h.empty:
                id_sel = st.selectbox("Escolha um ID para carregar:", ["---"] + df_h.iloc[:, 0].tolist())
                if st.button("CARREGAR DADOS"):
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                    st.rerun()

        d = st.session_state.dados_edit
        v_id = d.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))

        # --- LINHA 1 ---
        c1, c2, c3 = st.columns(3)
        v_emp = c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
        try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
        except: b_def = []
        v_bal = c2.multiselect("Balsas", lista_balsas, default=b_def)
        v_com = c3.text_input("Comandante", value=d.get('Comandante', ""))

        # --- LINHA 2 ---
        c4, c5, c6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = c4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
        v_des = c5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
        v_chf = c6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

        # --- LINHA 3 ---
        c7, c8, c9 = st.columns(3)
        v_vol = c7.number_input("Volume (M³)", value=float(str(d.get('Volume',0)).replace('.','').replace(',','.')) if d.get('Volume') else 0.0)
        v_fat = c8.number_input("Faturamento (R$)", value=float(str(d.get('Faturamento',0)).replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0)
        v_hor = c9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

        # --- LINHA 4 ---
        c10, c11, c12 = st.columns(3)
        v_tmp = c10.number_input("Tempo (H)", value=int(d.get('Tempo Previsto (H)', 0)))
        v_cbm = c11.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
        v_dsl = c12.number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel',0)).replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0)

        v_obs = st.text_area("Observações", value=d.get('Observações', ""))
        
        st.write(f"### STATUS: {'✅ APROVADO' if v_fat >= 50000 else '⚠️ ANÁLISE'}")
        
        if st.button("💾 FINALIZAR E SALVAR"):
            st.success("Simulação concluída!")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        st.dataframe(df_h, use_container_width=True, hide_index=True)

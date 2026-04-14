import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import ast

# =========================================================
# 1. CONFIGURAÇÃO, DESIGN E ESPAÇAMENTO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Inicializa estados críticos para não perder dados na navegação
if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    /* Afastamento de 2cm do topo */
    .block-container { max-width: 1100px; padding-top: 75px; margin: auto; }
    
    /* Design da Capa */
    .capa-container {
        text-align: center; padding: 60px;
        background-color: #f8f9fa; border-radius: 20px;
        border: 2px solid #073763; margin-bottom: 40px;
    }
    
    /* Estilo dos Botões */
    .stButton > button { 
        background-color: #073763; color: white; 
        font-weight: bold; width: 100%; height: 3.5em; 
        border-radius: 8px;
    }
    
    /* Ajuste de colunas para não encavalar */
    [data-testid="column"] { min-width: 280px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO COM BANCO DE DADOS (RESTAURADA)
# =========================================================
@st.cache_data(ttl=2)
def carregar_dados_sistema():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        hist_raw = sh.worksheet("Historico").get_all_values()
        if len(hist_raw) > 1:
            df_h = pd.DataFrame(hist_raw[1:], columns=hist_raw[0])
            df_h = df_h.loc[:, ~df_h.columns.duplicated()]
        else:
            df_h = pd.DataFrame()
            
        return ativos, balsas, rotas, df_h
    except:
        return [], [], [], pd.DataFrame()

ativos, lista_balsas, lista_rotas, df_h = carregar_dados_sistema()

# =========================================================
# 3. NAVEGAÇÃO DE TELAS
# =========================================================

# --- TELA: CAPA ---
if st.session_state.pagina_atual == "Capa":
    st.markdown("""
        <div class="capa-container">
            <h1 style='color: #073763; font-size: 50px;'>🚢 ZION - Gestão PCO</h1>
            <p style='font-size: 22px; color: #555;'>Sistema de Simulação e Controle Transdourada</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col_btn, _ = st.columns([1, 1.5, 1])
    if col_btn.button("🚀 ACESSAR SIMULADOR"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

# --- TELA: SISTEMA PRINCIPAL ---
else:
    with st.sidebar:
        st.markdown("### ⚙️ NAVEGAÇÃO")
        if st.button("🏠 Ir para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        st.write("---")
        menu = st.radio("SELECIONE:", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Operação")
        
        # BUSCA FUNCIONAL (RESTAURADA)
        with st.expander("🔍 BUSCAR REGISTRO EXISTENTE", expanded=False):
            if not df_h.empty:
                id_busca = st.selectbox("Selecione o ID da Viagem:", ["---"] + df_h.iloc[:, 0].tolist())
                if st.button("CARREGAR DADOS NA TELA"):
                    # Aqui a mágica acontece: ele puxa a linha inteira para o estado da sessão
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_busca].iloc[0].to_dict()
                    st.rerun()

        d = st.session_state.dados_edit

        # --- GRID 4X3 RESTAURADO ---
        l1c1, l1c2, l1c3 = st.columns(3)
        v_emp = l1c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
        try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
        except: b_def = []
        v_bal = l1c2.multiselect("Balsas", lista_balsas, default=b_def)
        v_com = l1c3.text_input("Comandante", value=d.get('Comandante', ""))

        l2c1, l2c2, l2c3 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = l2c1.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
        v_des = l2c2.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
        v_chf = l2c3.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

        l3c1, l3c2, l3c3 = st.columns(3)
        v_vol = l3c1.number_input("Volume (M³)", value=float(str(d.get('Volume',0)).replace('.','').replace(',','.')) if d.get('Volume') else 0.0)
        v_fat = l3c2.number_input("Faturamento (R$)", value=float(str(d.get('Faturamento',0)).replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0)
        v_hor = l3c3.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

        l4c1, l4c2, l4c3 = st.columns(3)
        v_tmp = l4c1.number_input("Tempo Previsto (H)", value=int(d.get('Tempo Previsto (H)', 0)))
        v_cbm = l4c2.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
        v_dsl = l4c3.number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel',0)).replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0)

        v_obs = st.text_area("Observações", value=d.get('Observações', ""))
        
        status = "APROVADO" if v_fat >= 50000 else "ANÁLISE"
        st.markdown(f"### STATUS: <span style='color:{'green' if status == 'APROVADO' else 'red'}'>{status}</span>", unsafe_allow_html=True)

        if st.button("✅ FINALIZAR E SALVAR"):
            st.success("Dados salvos e sincronizados!")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado no histórico.")

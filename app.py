import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# ==========================================
# # 01 - CONFIGURAÇÃO DE TELA E CSS (VISUAL)
# ==========================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

st.markdown("""
    <style>
    /* Ajusta o respiro da tela */
    .block-container {padding-top: 1rem; padding-left: 2rem;}
    
    /* Força os campos a terem 190px (~5cm) */
    div[data-testid="stSelectbox"], 
    div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], 
    div[data-testid="stMultiSelect"] {
        width: 190px !important;
    }

    /* Aproxima os campos horizontalmente (GAP de 1.5cm) */
    [data-testid="column"] {
        width: 230px !important; 
        flex: none !important;
    }
    
    /* Compacta o espaçamento vertical entre linhas */
    .element-container { margin-bottom: -0.6rem !important; }
    label { font-size: 13px !important; font-weight: bold; margin-bottom: -0.5rem !important; }
    
    /* Estilo do botão principal */
    .stButton > button {
        width: 190px !important;
        background-color: #073763;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# # 02 - CONEXÃO COM GOOGLE SHEETS
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na conexão com Google: {e}")
        return None

# ==========================================
# # 03 - FUNÇÕES OPERACIONAIS (SALVAR E PDF)
# ==========================================
def salvar_dados(client, linha):
    try:
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        aba_hist = sh.worksheet("Historico")
        aba_hist.append_row(linha)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na aba 'Historico': {e}")
        return False

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ZION - ORDEM DE VIAGEM", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for k, v in dados.items():
        pdf.cell(200, 8, f"{k}: {v}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# # 04 - INTERFACE PRINCIPAL
# ==========================================
st.title("🚢 ZION - Gestão PCO")
client = conectar_google()

if client:
    # Busca dados para alimentar os selects
    def carregar_dados(nome_aba):
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet(nome_aba).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()

    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    t_sim, t_atv, t_bal, t_rot = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

    with t_sim:
        v_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.subheader(f"Nova Viagem: {v_id}")
        
        # LINHA 1
        c1, c2, c3 = st.columns(3)
        v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0].tolist() if not df_atv.empty else ["-"])
        v_balsas = c2.multiselect("Balsas", df_bal.iloc[:,0].tolist() if not df_bal.empty else ["-"])
        v_com = c3.text_input("Comandante")

        # LINHA 2
        c4, c5, c6 = st.columns(3)
        v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique().tolist() if not df_rot.empty else ["-"])
        v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique().tolist() if not df_rot.empty else ["-"])
        v_chf = c6.text_input("Chefe de Máquinas")

        # LINHA 3
        c7, c8, c9 = st.columns(3)
        v_vol = c7.number_input("Volume", min_value=0.0)
        v_fat = c8.number_input("Faturamento", min_value=0.0)
        v_hor = c9.number_input("Horímetro", min_value=0.0)

        # LINHA 4
        c10, c11 = st.columns(2)
        v_tmp = c10.number_input("Tempo (Horas)", min_value=0)
        v_cbm = c11.number_input("Combustível (L)", min_value=0)

        st.markdown("---")
        if st.button("VALIDAR E SALVAR"):
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            dados_sheets = [v_id, v_emp, ", ".join(v_balsas), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
            
            if salvar_dados(client, dados_sheets):
                st.success(f"Viagem {v_id} salva com sucesso!")
                
                # Prepara o PDF para download
                dados_pdf = {"Viagem": v_id, "Empurrador": v_emp, "Rota": f"{v_ori} x {v_des}", "Data": agora}
                pdf_res = gerar_pdf(dados_pdf)
                st.download_button("📥 Baixar Ordem de Viagem (PDF)", data=pdf_res, file_name=f"{v_id}.pdf")

    # Visualização rápida das outras abas
    with t_atv: st.dataframe(df_atv, use_container_width=True)
    with t_bal: st.dataframe(df_bal, use_container_width=True)
    with t_rot: st.dataframe(df_rot, use_container_width=True)

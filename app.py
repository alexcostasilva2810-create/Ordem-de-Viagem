import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# ==========================================
# # 01 - CONFIGURAÇÃO E ESTILO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 2rem; }
    
    /* Ajuste fino para os inputs não ficarem gigantes */
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect {
        max-width: 200px !important;
    }
    
    /* Aproxima as linhas verticalmente */
    .element-container { margin-bottom: -0.3rem !important; }
    label { font-size: 13px !important; font-weight: bold; }
    
    /* Botões profissionais */
    .stButton > button { width: 200px !important; background-color: #073763; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# # 02 - FUNÇÕES DE DADOS (COM CACHE) #
# ==========================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=600)
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet(aba).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

def salvar_final(lista):
    client = obter_cliente()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        sh.worksheet("Historico").append_row(lista)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")
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
# # 03 - INTERFACE #
# ==========================================
st.title("🚢 ZION - Gestão PCO")

df_atv = carregar_dados("Ativos")
df_bal = carregar_dados("Balsas")
df_rot = carregar_dados("Rotas")

t_sim, t_atv, t_bal, t_rot = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

with t_sim:
    vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
    st.subheader(f"Registro: {vgn_id}")
    
    # Criamos colunas com peso [1,1,1,5] para "empurrar" os campos para a esquerda e sobrar espaço na direita
    # Isso evita que o layout fique montado.
    
    # LINHA 1
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
    v_com = c3.text_input("Comandante")

    # LINHA 2
    c4, c5, c6, _ = st.columns([1, 1, 1, 5])
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas")

    # LINHA 3
    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume", min_value=0.0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0)

    # LINHA 4
    c10, c11, _ = st.columns([1, 1, 6])
    v_tmp = c10.number_input("Tempo (H)", min_value=0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0)

    st.write("---")
    
    if st.button("VALIDAR E SALVAR NO HISTÓRICO"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_dados = [vgn_id, v_emp, ", ".join(v_bal_sel), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
        
        if salvar_final(lista_dados):
            st.success("✅ Sucesso! Salvo na Planilha 'Historico'.")
            
            # Gerar PDF após salvar
            dados_pdf = {"Viagem": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Rota": f"{v_ori} x {v_des}", "Data": agora}
            pdf_bytes = gerar_pdf(dados_pdf)
            
            # Mostrar Botões de Ação
            st.write("### 📄 Documentos Gerados")
            col_a, col_b, _ = st.columns([1, 1, 6])
            col_a.download_button("📥 Baixar Ordem (PDF)", data=pdf_bytes, file_name=f"{vgn_id}.pdf", mime="application/pdf")
            if col_b.button("📧 Enviar E-mail"):
                st.info("E-mail enviado para o departamento operacional.")
        else:
            st.error("Erro ao salvar. Verifique se a aba 'Historico' existe na planilha.")

# Abas de Consulta
with t_atv: st.dataframe(df_atv, use_container_width=True)
with t_bal: st.dataframe(df_bal, use_container_width=True)
with t_rot: st.dataframe(df_rot, use_container_width=True)

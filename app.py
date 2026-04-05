import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# ==========================================
# # 01 - CONFIGURAÇÃO E ESTILO (VISUAL) #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 1.5rem; }
    
    /* Campos com 5cm (190px) */
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], div[data-testid="stMultiSelect"] {
        width: 190px !important;
    }
    
    /* Aproximação horizontal dos campos */
    [data-testid="column"] {
        width: 210px !important; 
        flex: none !important;
        margin-right: 15px !important;
    }
    
    /* Compactação vertical */
    .element-container { margin-bottom: -0.5rem !important; }
    label { font-size: 12px !important; font-weight: bold; margin-bottom: -0.8rem !important; }
    
    /* Botões */
    .stButton > button { width: 190px !important; background-color: #003366; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# # 02 - CONEXÃO E CACHE (ANTI-ERRO 429) #
# ==========================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except:
        return None

@st.cache_data(ttl=600) # Guarda os dados por 10 min para não estourar a cota do Google
def carregar_dados_planilha(aba):
    client = obter_cliente()
    if client:
        ID = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID)
        data = sh.worksheet(aba).get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

def salvar_no_historico(lista_dados):
    client = obter_cliente()
    if client:
        try:
            ID = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
            sh = client.open_by_key(ID)
            wks = sh.worksheet("Historico")
            wks.append_row(lista_dados)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
            return False
    return False

# ==========================================
# # 03 - FUNÇÕES DE SAÍDA (PDF) #
# ==========================================
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
# # 04 - INTERFACE PRINCIPAL #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")

# Carrega os dados usando o Cache (evita erro 429)
df_atv = carregar_dados_planilha("Ativos")
df_bal = carregar_dados_planilha("Balsas")
df_rot = carregar_dados_planilha("Rotas")

tabs = st.tabs(["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas"])

with tabs[0]:
    vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
    st.subheader(f"Nº Registro: {vgn_id}")
    
    # LINHA 1
    c1, c2, c3 = st.columns(3)
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_bal = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
    v_com = c3.text_input("Comandante")

    # LINHA 2
    c4, c5, c6 = st.columns(3)
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas")

    # LINHA 3
    c7, c8, c9 = st.columns(3)
    v_vol = c7.number_input("Volume", min_value=0.0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
    v_hor = c9.number_input("Horímetro Inicial", min_value=0.0)

    # LINHA 4
    c10, c11 = st.columns(2)
    v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0)

    st.markdown("---")
    
    # Botão de Validação
    if st.button("VALIDAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [vgn_id, v_emp, ", ".join(v_bal), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
        
        if salvar_no_historico(lista_final):
            st.success(f"✅ Viagem {vgn_id} salva com sucesso no Google Sheets!")
        else:
            st.warning("⚠️ Não salvou na planilha (limite do Google), mas pode gerar o PDF abaixo.")

        # PDF Gerado em memória
        dados_p = {"ID": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Rota": f"{v_ori} x {v_des}", "Data": agora}
        pdf_out = gerar_pdf(dados_p)
        
        st.write("### Ações:")
        b1, b2 = st.columns(2)
        b1.download_button("📥 Baixar PDF", data=pdf_out, file_name=f"{vgn_id}.pdf", mime="application/pdf")
        
        if b2.button("📧 Enviar E-mail"):
            st.info("E-mail enviado para o setor de Operações (Simulado).")

# Abas de consulta
with tabs[1]: st.dataframe(df_atv, use_container_width=True, hide_index=True)
with tabs[2]: st.dataframe(df_bal, use_container_width=True, hide_index=True)
with tabs[3]: st.dataframe(df_rot, use_container_width=True, hide_index=True)

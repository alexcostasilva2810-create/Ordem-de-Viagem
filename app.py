import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF # Biblioteca para o PDF

# =========================================================
# BLOCO 1: CONFIGURAÇÕES E LOGO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 250px !important; }
    .stButton > button { 
        width: 100% !important; max-width: 250px;
        background-color: #073763; color: white; font-weight: bold; height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

try:
    st.sidebar.image("icone ZION.png", use_container_width=True)
except:
    pass

st.sidebar.title("MENU ZION")
pagina = st.sidebar.radio("Navegação", ["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas", "📜 Histórico"])

# =========================================================
# FUNÇÃO PARA GERAR PDF
# =========================================================
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "ZION TECNOLOGIA - RESUMO DE VIAGEM", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    
    for chave, valor in dados.items():
        pdf.cell(0, 10, f"{chave}: {valor}", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# BLOCO 2: CONEXÃO
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# BLOCO 3: SIMULAÇÕES
# =========================================================
if pagina == "📊 Simulações":
    st.title("🚢 ZION - Gestão PCO")

    if 'dados_edit' not in st.session_state:
        st.session_state.dados_edit = None

    # BUSCA
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_hist_busca = carregar_dados("Historico")
        if not df_hist_busca.empty:
            lista_vgm = ["---"] + df_hist_busca.iloc[:, 0].tolist()
            selecionado = st.selectbox("Selecione:", lista_vgm)
            if st.button("CARREGAR"):
                st.session_state.dados_edit = df_hist_busca[df_hist_busca.iloc[:, 0] == selecionado].iloc[0].to_dict()
                st.rerun()

    vgn_id = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {vgn_id}")

    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # CAMPOS
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume (m³)", min_value=0, step=1, format="%d", value=int(float(st.session_state.dados_edit.get('Volume (m³)', 0))) if st.session_state.dados_edit else 0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0.0)) if st.session_state.dados_edit else 0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0, value=float(st.session_state.dados_edit.get('Horímetro', 0.0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    st.markdown(f"### STATUS: {status_viagem}")

    # SALVAMENTO
    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [vgn_id, v_emp, v_com, v_vol, v_fat, v_hor, status_viagem, v_obs, agora]
        
        client = obter_cliente()
        if client:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            sh.worksheet("Historico").append_row(lista_final)
            
            # Prepara dados para o PDF
            dados_pdf = {"ID": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Volume": v_vol, "Faturamento": v_fat, "Status": status_viagem}
            pdf_bytes = gerar_pdf(dados_pdf)
            
            st.success("✅ Salvo!")
            st.download_button(label="📥 BAIXAR PDF DA VIAGEM", data=pdf_bytes, file_name=f"{vgn_id}.pdf", mime="application/pdf")

# =========================================================
# BLOCO 4: HISTÓRICO
# =========================================================
elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(carregar_dados("Historico"), use_container_width=True)

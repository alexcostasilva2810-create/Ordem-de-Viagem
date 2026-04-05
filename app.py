import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# BLOCO 1: CONFIGURAÇÕES E ESTILO
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
# FUNÇÕES DE APOIO (PDF PERSONALIZADO)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287) # Borda do PDF
        try: self.image('fundo_offshore.jpg', x=10, y=50, w=190, h=150) # Marca d'água
        except: pass
        self.set_font('Arial', 'B', 16)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ZION TECNOLOGIA - RESUMO DE VIAGEM', border=0, ln=True, align='C')
        self.ln(5)

def gerar_pdf_pco(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    
    for chave, valor in dados.items():
        if chave == "Observações":
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "OBSERVAÇÕES:", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, str(valor), border=1)
        else:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(50, 10, f"{chave}:", border='B')
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 10, f" {valor}", border='B', ln=True)
            
    return pdf.output(dest="S").encode("latin-1")

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
# BLOCO 9: PÁGINA DE SIMULAÇÕES (RESTADO COMPLETO)
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
            selecionado = st.selectbox("Selecione o registro:", lista_vgm)
            if st.button("CARREGAR DADOS"):
                if selecionado != "---":
                    st.session_state.dados_edit = df_hist_busca[df_hist_busca.iloc[:, 0] == selecionado].iloc[0].to_dict()
                    st.rerun()

    vgn_id = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    proxima_edicao = int(st.session_state.dados_edit.get('Edicoes', 0)) + 1 if st.session_state.dados_edit else 0

    st.subheader(f"Registro: {vgn_id}")

    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # --- LINHA 1 ---
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    bal_def = []
    if st.session_state.dados_edit:
        try: bal_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: pass
    v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [], default=bal_def)
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    # --- LINHA 2 ---
    c4, c5, c6, _ = st.columns([1, 1, 1, 5])
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', '') if st.session_state.dados_edit else "")

    # --- LINHA 3 ---
    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume (m³)", min_value=0, step=1, format="%d", value=int(float(st.session_state.dados_edit.get('Volume (m³)', 0))) if st.session_state.dados_edit else 0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0.0)) if st.session_state.dados_edit else 0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0, value=float(st.session_state.dados_edit.get('Horímetro', 0.0)) if st.session_state.dados_edit else 0.0)

    # --- LINHA 4 ---
    c10, c11, c12, _ = st.columns([1, 1, 1, 5])
    v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0, value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0, value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)
    v_diesel = c12.number_input("Custo Diesel (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0.0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [vgn_id, v_emp, str(v_bal_sel), v_com, v_ori, v_des, v_vol, v_fat, v_hor, v_tmp, v_cbm, v_diesel, status_viagem, v_obs, agora, proxima_edicao]
        
        client = obter_cliente()
        if client:
            try:
                sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
                aba = sh.worksheet("Historico")
                if st.session_state.dados_edit:
                    try: aba.delete_rows(aba.find(vgn_id).row)
                    except: pass
                aba.append_row(lista_final)
                
                # Dados para o PDF
                d_pdf = {
                    "ID": vgn_id, "Empurrador": v_emp, "Balsas": str(v_bal_sel), 
                    "Comandante": v_com, "Origem": v_ori, "Destino": v_des,
                    "Volume": f"{v_vol:,} m3", "Faturamento": f"R$ {v_fat:,.2f}", 
                    "Status": status_viagem, "Observações": v_obs
                }
                pdf_output = gerar_pdf_pco(d_pdf)
                
                st.success("✅ Salvo com sucesso!")
                st.download_button("📥 BAIXAR PDF DA VIAGEM", pdf_output, f"{vgn_id}.pdf", "application/pdf")
                st.session_state.dados_edit = None
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# =========================================================
# DEMAIS ABAS (SEM ALTERAÇÃO)
# =========================================================
elif pagina == "📋 Ativos":
    st.dataframe(carregar_dados("Ativos"), use_container_width=True)
elif pagina == "⛴️ Balsas":
    st.dataframe(carregar_dados("Balsas"), use_container_width=True)
elif pagina == "📍 Rotas":
    st.dataframe(carregar_dados("Rotas"), use_container_width=True)
elif pagina == "📜 Histórico":
    st.dataframe(carregar_dados("Historico"), use_container_width=True)

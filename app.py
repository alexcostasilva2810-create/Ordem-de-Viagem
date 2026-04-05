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
# FUNÇÃO PDF PERSONALIZADO (COM BORDA, FUNDO E OBS)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        # Borda externa em todas as páginas
        self.rect(5, 5, 200, 287)
        # Imagem de fundo suave (Marca d'água)
        try:
            # Tenta colocar a imagem ocupando quase a página toda
            self.image('fundo_offshore.jpg', x=10, y=50, w=190, h=150)
        except:
            pass # Se não achar a imagem, segue sem ela
        
        self.set_font('Arial', 'B', 20)
        self.set_text_color(7, 55, 99) # Azul ZION
        self.cell(0, 20, 'ZION TECNOLOGIA - RESUMO DE VIAGEM', border=0, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} - Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C')

def gerar_pdf_bonito(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)

    # Tabela de informações
    def linha(label, valor):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, f"{label}:", border='B')
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f" {valor}", border='B', ln=True)

    linha("ID da Viagem", dados['ID'])
    linha("Empurrador", dados['Empurrador'])
    linha("Comandante", dados['Comandante'])
    linha("Volume", dados['Volume'])
    linha("Faturamento", dados['Faturamento'])
    linha("Status", dados['Status'])
    
    # Campo de Observações (Multilinha)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "OBSERVAÇÕES DA VIAGEM:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, dados['Observações'], border=1)
    
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# BLOCO 2: CONEXÃO E DEMAIS FUNÇÕES (GSPREAD)
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

    # Busca (Igual ao código anterior)
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

    # Carregar listas
    df_atv, df_bal, df_rot = carregar_dados("Ativos"), carregar_dados("Balsas"), carregar_dados("Rotas")

    # Layout do Form
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume (m³)", min_value=0, step=1, format="%d", value=int(float(st.session_state.dados_edit.get('Volume (m³)', 0))) if st.session_state.dados_edit else 0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0.0)) if st.session_state.dados_edit else 0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0, value=float(st.session_state.dados_edit.get('Horímetro', 0.0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    
    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [vgn_id, v_emp, "[]", v_com, "", "", v_vol, v_fat, v_hor, 0, 0, 0, status_viagem, v_obs, agora, proxima_edicao]
        
        client = obter_cliente()
        if client:
            try:
                sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
                aba = sh.worksheet("Historico")
                if st.session_state.dados_edit:
                    try: aba.delete_rows(aba.find(vgn_id).row)
                    except: pass
                aba.append_row(lista_final)
                
                # Prepara PDF com TODOS os campos solicitados
                dados_pdf = {
                    "ID": vgn_id, 
                    "Empurrador": v_emp, 
                    "Comandante": v_com, 
                    "Volume": f"{v_vol:,} m3", 
                    "Faturamento": f"R$ {v_fat:,.2f}", 
                    "Status": status_viagem,
                    "Observações": v_obs if v_obs else "Sem observações."
                }
                pdf_bytes = gerar_pdf_bonito(dados_pdf)
                
                st.success("✅ Salvo no Sistema!")
                st.download_button("📥 BAIXAR PDF PERSONALIZADO", pdf_bytes, f"Resumo_{vgn_id}.pdf", "application/pdf")
                st.session_state.dados_edit = None
            except Exception as e:
                st.error(f"Erro: {e}")

# (Restante do código das outras abas igual...)

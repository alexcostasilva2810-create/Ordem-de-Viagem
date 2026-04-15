import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast
import uuid

# --- 1. CONFIGURAÇÕES E BANCO DE USUÁRIOS ---
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Espaço para você cadastrar Usuário | Senha | Perfil
USUARIOS = {
    "admin": {"senha": "123", "perfil": "Administrador"},
    "operador": {"senha": "456", "perfil": "Operador"}
}

if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1150px; padding-top: 40px; margin: auto; }
    .stMultiSelect div[data-baseweb="select"] > div:first-child { max-height: 180px; overflow-y: auto; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3.5em; }
    .login-container { max-width: 400px; margin: auto; padding: 30px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE SUPORTE ---
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        sh = conectar()
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(hist[1:], columns=hist[0]) if len(hist) > 1 else pd.DataFrame()
        return ativos, balsas, rotas, df
    except:
        return [], [], [], pd.DataFrame()

class PDF_PCO(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE SERVICO - TRANSDOURADA', align='C', ln=True)
        self.ln(5)
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f'Registro gerado em: {agora} - Local: Belem/PA', align='C')

# --- 3. TELA DE LOGIN (CAPA) ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; color: #073763;'>Zion - Abertura de O.S para Viagem</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("🚀 ENTRAR NO SISTEMA"):
            if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                st.session_state.autenticado = True
                st.session_state.user_perfil = USUARIOS[usuario]["perfil"]
                st.session_state.user_nome = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. SISTEMA PRINCIPAL ---
else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados()

    with st.sidebar:
        st.write(f"👤 **Usuário:** {st.session_state.user_nome}")
        st.write(f"🛡️ **Perfil:** {st.session_state.user_perfil}")
        st.write("---")
        menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])
        if st.button("🚪 Sair"):
            st.session_state.autenticado = False
            st.rerun()

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Operação")
        
        with st.expander("🔍 Pesquisar Registro"):
            id_sel = st.selectbox("ID Viagem:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []))
            if st.button("Carregar Dados"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.rerun()

        d = st.session_state.dados_edit

        # LAYOUT DE CAMPOS (MANTIDO)
        col1, col2, col3 = st.columns([1, 2, 1])
        v_emp = col1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
        try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
        except: b_def = []
        v_bal = col2.multiselect("Balsas (Comboio)", lista_balsas, default=[b for b in b_def if b in lista_balsas])
        v_com = col3.text_input("Comandante", value=d.get('Comandante', ""))

        col4, col5, col6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = col4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
        v_des = col5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
        v_chf = col6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

        col7, col8, col9 = st.columns(3)
        v_vol = col7.number_input("Volume M³", value=int(str(d.get('Volume', 0)).replace('.','')) if d.get('Volume') else 0)
        v_fat = col8.number_input("Faturamento (R$)", value=float(d.get('Faturamento', 0.0)))
        v_hor = col9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

        col10, col11, col12 = st.columns(3)
        v_tem = col10.number_input("Tempo Previsto (H)", value=int(d.get('Tempo (H)', 0)))
        v_combus = col11.number_input("Combustivel (L)", value=int(d.get('Combustivel (L)', 0)))
        v_custo = col12.number_input("Custo Diesel (R$)", value=float(d.get('Custo Diesel', 0.0)))

        v_obs = st.text_area("Observações", value=d.get('Observações', ""))

        if st.button("🚀 FINALIZAR, GUARDAR E GERAR O.S."):
            if not v_bal:
                st.error("Selecione o comboio!")
            else:
                vol_format = f"{v_vol:,.0f}".replace(",", ".")
                id_v = str(uuid.uuid4())[:8].upper()
                data_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                try:
                    sh = conectar()
                    ws = sh.worksheet("Historico")
                    ws.append_row([id_v, data_v, v_emp, str(v_bal), v_com, v_ori, v_des, vol_format, v_fat, v_hor, v_tem, v_combus, v_custo, v_obs])
                    st.cache_data.clear()
                    
                    pdf = PDF_PCO()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 10)
                    dados_os = {
                        "ID Viagem": id_v, "Data": data_v, "Empurrador": v_emp, "Comboio": ", ".join(v_bal),
                        "Comandante": v_com, "Origem": v_ori, "Destino": v_des, "Volume M³": vol_format,
                        "Faturamento": f"R$ {v_fat:,.2f}", "Combustivel (L)": v_combus, "Operador": st.session_state.user_nome
                    }
                    for k, v in dados_os.items():
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(60, 10, f" {k}:", border=1, fill=True)
                        pdf.cell(0, 10, f" {v}", border=1, ln=True)
                    
                    pdf.ln(20)
                    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                    pdf.cell(0, 5, f"Assinatura do Responsavel ({st.session_state.user_perfil})", align='C')
                    
                    pdf_bytes = pdf.output(dest="S").encode("latin-1")
                    st.success(f"✅ Viagem {id_v} Guardada!")
                    st.download_button("📥 BAIXAR O.S. PROFISSIONAL", pdf_bytes, f"OS_{id_v}.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        st.dataframe(df_h, use_container_width=True, hide_index=True)

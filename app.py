import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (2CM DE ESPAÇO NO TOPO)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 75px; margin: auto; }
    .capa-container {
        text-align: center; padding: 50px;
        background-color: #f8f9fa; border-radius: 20px;
        border: 2px solid #073763; margin-bottom: 40px;
    }
    .stButton > button { 
        background-color: #073763; color: white; 
        font-weight: bold; width: 100%; height: 3.5em; 
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. GERADOR DE PDF (LAYOUT O.S.)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")
        self.cell(0, 10, f'Gerado em: {agora} - ZION Gestão PCO', align='C')

def gerar_pdf_os(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 10, f" {k}", border=1, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f" {v}", border=1, ln=True)
        pdf.set_font("Arial", "B", 10)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO BLINDADA (EVITA DUPLICATAS E ERROS)
# =========================================================
def carregar_dados_seguro():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        # Carrega e limpa Ativos/Balsas
        ativos = [x for x in sh.worksheet("Ativos").col_values(1)[1:] if x]
        balsas = [x for x in sh.worksheet("Balsas").col_values(1)[1:] if x]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        # Carrega Histórico e remove colunas duplicadas (Cura o erro do print)
        hist_raw = sh.worksheet("Historico").get_all_values()
        if len(hist_raw) > 1:
            df = pd.DataFrame(hist_raw[1:], columns=hist_raw[0])
            df = df.loc[:, ~df.columns.duplicated()].copy() # REMOVE DUPLICADAS
        else:
            df = pd.DataFrame()
            
        return ativos, balsas, rotas, df
    except Exception as e:
        st.error(f"Erro na Planilha: {e}")
        return ["Erro"], ["Erro"], [], pd.DataFrame()

# =========================================================
# 4. LÓGICA DE NAVEGAÇÃO E TELAS
# =========================================================

if st.session_state.pagina_atual == "Capa":
    st.markdown('<div class="capa-container">', unsafe_allow_html=True)
    st.title("🚢 ZION - GESTÃO PCO")
    st.subheader("Sistema de Controle de Viagens | Transdourada")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col_btn, col2 = st.columns([1, 1.5, 1])
    if col_btn.button("🚀 ENTRAR NO SIMULADOR"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    # Carregamento imediato ao entrar no sistema
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_seguro()

    with st.sidebar:
        st.title("MENU")
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        st.write("---")
        menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulação de Viagem")
        
        # BUSCA FUNCIONAL
        with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO", expanded=False):
            if not df_h.empty:
                id_sel = st.selectbox("Escolha o ID:", ["---"] + df_h.iloc[:, 0].tolist())
                if st.button("CARREGAR DADOS"):
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                    st.rerun()

        d = st.session_state.dados_edit
        v_id = d.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))

        # --- GRID DE DADOS ---
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

        if st.button("✅ FINALIZAR E GERAR O.S."):
            dados_final = {
                "ID Viagem": v_id, "Empurrador": v_emp, "Balsas": ", ".join(v_bal),
                "Comandante": v_com, "Chefe de Máquinas": v_chf,
                "Rota": f"{v_ori} x {v_des}", "Volume": f"{v_vol:,.3f} M³",
                "Faturamento": f"R$ {v_fat:,.2f}", "Status": status, "Observações": v_obs
            }
            pdf_out = gerar_pdf_os(dados_final)
            st.success("O.S. Pronta para baixar!")
            st.download_button("📥 BAIXAR PDF DA O.S.", data=pdf_out, file_name=f"OS_{v_id}.pdf", mime="application/pdf")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado para exibir no momento.")

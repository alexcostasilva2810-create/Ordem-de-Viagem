import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# =========================================================
# BLOCO 1: CONFIGURAÇÕES E LOGO NO MENU LATERAL
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 210px !important; }
    .stButton > button { 
        width: 100% !important; max-width: 250px;
        background-color: #073763; color: white; font-weight: bold; height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

try:
    st.sidebar.image("icone ZION.png", use_container_width=True)
except:
    st.sidebar.warning("Logo não encontrada.")

st.sidebar.title("MENU ZION")
pagina = st.sidebar.radio("Navegação", ["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas", "📜 Histórico"])

# =========================================================
# BLOCO 2: CONEXÃO COM A PLANILHA
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

def carregar_dados(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# BLOCO 3: PÁGINA DE SIMULAÇÕES (COM BUSCA E EDIÇÃO)
# =========================================================
st.title("🚢 ZION - Gestão PCO")

if pagina == "📊 Simulações":
    # --- SISTEMA DE BUSCA PARA EDIÇÃO ---
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        busca_id = st.text_input("Digite o ID da Viagem (ex: VGM 0504-1816)")
        btn_buscar = st.button("BUSCAR NA BASE")

    # Inicialização de variáveis de estado
    if 'dados_edit' not in st.session_state:
        st.session_state.dados_edit = None

    if btn_buscar and busca_id:
        df_hist = carregar_dados("Historico")
        if not df_hist.empty and busca_id in df_hist.iloc[:,0].values:
            st.session_state.dados_edit = df_hist[df_hist.iloc[:,0] == busca_id].iloc[0].to_dict()
            st.success(f"Registro {busca_id} carregado para edição!")
        else:
            st.error("Registro não encontrado.")

    # Define o ID (Novo ou Existente)
    if st.session_state.dados_edit:
        vgn_id = st.session_state.dados_edit.get('ID', busca_id)
        # Lógica de Contador de Edição
        edicoes = st.session_state.dados_edit.get('Edicoes', '0')
        proxima_edicao = int(edicoes) + 1
    else:
        vgn_id = datetime.now().strftime("VGM %d%m-%H%M")
        proxima_edicao = 0

    st.subheader(f"Registro: {vgn_id}")

    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # --- CAMPOS DO FORMULÁRIO (Preenchem se for edição) ---
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    c4, c5, c6, _ = st.columns([1, 1, 1, 5])
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe Maquinas', '') if st.session_state.dados_edit else "")

    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume (m³)", min_value=0, max_value=5000000, step=1, format="%d", value=int(float(st.session_state.dados_edit.get('Volume', 0))) if st.session_state.dados_edit else 0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Faturamento', 0.0)) if st.session_state.dados_edit else 0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0, value=float(st.session_state.dados_edit.get('Horimetro', 0.0)) if st.session_state.dados_edit else 0.0)

    c10, c11, c12, _ = st.columns([1, 1, 1, 5])
    v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0, value=int(st.session_state.dados_edit.get('Tempo', 0)) if st.session_state.dados_edit else 0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0, value=int(st.session_state.dados_edit.get('Combustivel', 0)) if st.session_state.dados_edit else 0)
    v_custo_diesel = c12.number_input("Custo Diesel (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Custo Diesel', 0.0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações", value=st.session_state.dados_edit.get('Obs', '') if st.session_state.dados_edit else "")

    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

    # --- BOTÃO SALVAR ---
    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [
            vgn_id, v_emp, str(v_bal_sel), v_com, v_ori, v_des, 
            v_vol, v_fat, v_hor, v_tmp, v_cbm, v_custo_diesel, status_viagem, v_obs, agora, proxima_edicao
        ]
        
        client = obter_cliente()
        if client:
            try:
                sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
                aba_hist = sh.worksheet("Historico")
                
                # Se for edição, remove a linha antiga antes de salvar a nova
                if st.session_state.dados_edit:
                    cell = aba_hist.find(vgn_id)
                    aba_hist.delete_rows(cell.row)
                
                aba_hist.append_row(lista_final)
                st.success(f"✅ Salvo com sucesso! Edições: {proxima_edicao}")
                
                # LIMPAR CAMPOS (Reset de sessão)
                st.session_state.dados_edit = None
                st.rerun() 
            except Exception as e:
                st.error(f"Erro: {e}")

# =========================================================
# BLOCO 4: DEMAIS PÁGINAS
# =========================================================
elif pagina == "📋 Ativos":
    st.dataframe(carregar_dados("Ativos"), use_container_width=True)
elif pagina == "⛴️ Balsas":
    st.dataframe(carregar_dados("Balsas"), use_container_width=True)
elif pagina == "📍 Rotas":
    st.dataframe(carregar_dados("Rotas"), use_container_width=True)
elif pagina == "📜 Histórico":
    st.dataframe(carregar_dados("Historico"), use_container_width=True)

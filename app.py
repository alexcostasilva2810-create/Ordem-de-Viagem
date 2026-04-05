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
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 250px !important; }
    .stButton > button { 
        width: 100% !important; max-width: 250px;
        background-color: #073763; color: white; font-weight: bold; height: 3em;
    }
    /* Estilo para o Status */
    .status-box { font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# Exibição da Logo no Topo da Sidebar
try:
    st.sidebar.image("icone ZION.png", use_container_width=True)
except:
    st.sidebar.warning("Arquivo 'icone ZION.png' não encontrado.")

st.sidebar.title("MENU ZION")
pagina = st.sidebar.radio(
    "Navegação",
    ["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas", "📜 Histórico"]
)

# =========================================================
# BLOCO 2: CONEXÃO COM A PLANILHA (COM CACHE)
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60) # Cache de 1 minuto para não estourar a cota do Google
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            if len(data) > 1:
                return pd.DataFrame(data[1:], columns=data[0])
        except: pass
    return pd.DataFrame()

# =========================================================
# BLOCO 3: PÁGINA DE SIMULAÇÕES (EDIÇÃO E BUSCA)
# =========================================================
if pagina == "📊 Simulações":
    st.title("🚢 ZION - Gestão PCO")

    # Inicializa estado de edição se não existir
    if 'dados_edit' not in st.session_state:
        st.session_state.dados_edit = None

    # --- NOVO SISTEMA DE BUSCA POR DROPDOWN ---
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO", expanded=False):
        df_hist_busca = carregar_dados("Historico")
        if not df_hist_busca.empty:
            lista_vgm = ["--- Selecione um Registro ---"] + df_hist_busca.iloc[:, 0].tolist()
            selecionado = st.selectbox("Escolha o registro para editar:", lista_vgm)
            
            if st.button("CARREGAR DADOS"):
                if selecionado != "--- Selecione um Registro ---":
                    st.session_state.dados_edit = df_hist_busca[df_hist_busca.iloc[:, 0] == selecionado].iloc[0].to_dict()
                    st.success(f"Dados de {selecionado} carregados!")
                    st.rerun()
        else:
            st.info("Nenhum registro encontrado no histórico.")

    # Define o ID (Novo ou Existente) e Contador de Edição
    if st.session_state.dados_edit:
        vgn_id = st.session_state.dados_edit.get('ID')
        edicao_atual = int(st.session_state.dados_edit.get('Edicoes', 0))
        proxima_edicao = edicao_atual + 1
    else:
        vgn_id = datetime.now().strftime("VGM %d%m-%H%M")
        proxima_edicao = 0

    st.subheader(f"Registro: {vgn_id}")

    # Carregamento das listas de apoio
    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # --- FORMULÁRIO ---
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    
    # Lógica para multiselect na edição
    bal_default = []
    if st.session_state.dados_edit:
        import ast
        try: bal_default = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: bal_default = []

    v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [], default=bal_default)
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    c4, c5, c6, _ = st.columns([1, 1, 1, 5])
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', '') if st.session_state.dados_edit else "")

    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    # Volume como Inteiro (Sem ,00)
    v_vol_val = int(float(st.session_state.dados_edit.get('Volume (m³)', 0))) if st.session_state.dados_edit else 0
    v_vol = c7.number_input("Volume (m³)", min_value=0, max_value=5000000, step=1, format="%d", value=v_vol_val)
    
    v_fat_val = float(st.session_state.dados_edit.get('Faturamento (R$)', 0.0)) if st.session_state.dados_edit else 0.0
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0, value=v_fat_val)
    
    v_hor_val = float(st.session_state.dados_edit.get('Horímetro', 0.0)) if st.session_state.dados_edit else 0.0
    v_hor = c9.number_input("Horímetro", min_value=0.0, value=v_hor_val)

    c10, c11, c12, _ = st.columns([1, 1, 1, 5])
    v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0, value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0, value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)
    v_diesel = c12.number_input("Custo Diesel (R$)", min_value=0.0, value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0.0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    # STATUS
    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor_status = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor_status}'>{status_viagem}</span>", unsafe_allow_html=True)

    # BOTÃO SALVAR
    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [
            vgn_id, v_emp, str(v_bal_sel), v_com, v_ori, v_des, 
            v_vol, v_fat, v_hor, v_tmp, v_cbm, v_diesel, status_viagem, v_obs, agora, proxima_edicao
        ]
        
        client = obter_cliente()
        if client:
            try:
                sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
                aba_hist = sh.worksheet("Historico")
                
                # Se for edição, remove a versão anterior
                if st.session_state.dados_edit:
                    try:
                        celula = aba_hist.find(vgn_id)
                        aba_hist.delete_rows(celula.row)
                    except: pass
                
                aba_hist.append_row(lista_final)
                st.success(f"✅ Registro {vgn_id} salvo com sucesso!")
                
                # Reseta e Limpa a tela
                st.session_state.dados_edit = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# =========================================================
# BLOCO 4: OUTRAS PÁGINAS
# =========================================================
elif pagina == "📋 Ativos":
    st.title("📋 Ativos")
    st.dataframe(carregar_dados("Ativos"), use_container_width=True)

elif pagina == "⛴️ Balsas":
    st.title("⛴️ Balsas")
    st.dataframe(carregar_dados("Balsas"), use_container_width=True)

elif pagina == "📍 Rotas":
    st.title("📍 Rotas")
    st.dataframe(carregar_dados("Rotas"), use_container_width=True)

elif pagina == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    st.dataframe(carregar_dados("Historico"), use_container_width=True)

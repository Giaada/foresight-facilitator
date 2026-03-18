import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.database import init_db, lista_sessioni, crea_sessione

st.set_page_config(
    page_title="Foresight Facilitator",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Sidebar navigazione ───────────────────────────────────
with st.sidebar:
    st.markdown("## 🧭 Foresight Facilitator")
    st.divider()

    if "sessione_id" in st.session_state:
        st.success(f"Sessione attiva: **#{st.session_state.sessione_id}**")
        if st.button("← Cambia sessione", use_container_width=True):
            del st.session_state["sessione_id"]
            st.rerun()
        st.divider()
        st.page_link("pages/1_Setup.py", label="⚙️ Setup", use_container_width=True)
        st.page_link("pages/2_Horizon_Scanning.py", label="🔭 Horizon Scanning", use_container_width=True)
        st.page_link("pages/3_Transizione.py", label="🔀 Transizione", use_container_width=True)
        st.page_link("pages/4_Scenario_Planning.py", label="🗺️ Scenario Planning", use_container_width=True)
        st.page_link("pages/5_Report.py", label="📄 Report", use_container_width=True)
    else:
        st.info("Nessuna sessione selezionata")

# ── Home ──────────────────────────────────────────────────
st.title("🧭 Foresight Facilitator")
st.markdown("Strumento di facilitazione per sessioni di **Strategic Foresight** guidate dall'AI.")
st.divider()

col1, col2 = st.columns(2)

# Nuova sessione
with col1:
    st.subheader("➕ Nuova sessione")
    with st.form("nuova_sessione"):
        domanda = st.text_area(
            "Domanda di ricerca *",
            placeholder="Es. Come evolverà il sistema sanitario nei prossimi 10 anni?",
            height=100,
        )
        frame = st.text_input(
            "Orizzonte temporale *",
            placeholder="Es. 2035, prossimi 10 anni, 2030–2040",
        )

        st.markdown("**Key Points** per lo Scenario Planning")
        st.caption("Dimensioni che ogni scenario dovrà esplorare")
        kp_raw = st.text_area(
            "Un key point per riga",
            placeholder="Tecnologia\nLavoro\nGovernance\nAmbiente",
            height=100,
            label_visibility="collapsed",
        )

        st.markdown("**Fenomeni / Trend iniziali**")
        st.caption("Un fenomeno per riga. Potrai aggiungerne altri nella fase successiva.")
        fenomeni_raw = st.text_area(
            "Un fenomeno per riga",
            placeholder="Intelligenza Artificiale generativa\nInvecchiamento della popolazione\nTransizione energetica",
            height=120,
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button("Crea sessione", use_container_width=True, type="primary")

    if submitted:
        if not domanda.strip() or not frame.strip():
            st.error("Domanda di ricerca e orizzonte temporale sono obbligatori.")
        else:
            key_points = [k.strip() for k in kp_raw.strip().splitlines() if k.strip()]
            fenomeni = [{"testo": f.strip()} for f in fenomeni_raw.strip().splitlines() if f.strip()]
            sid = crea_sessione(domanda.strip(), frame.strip(), key_points, fenomeni)
            st.session_state["sessione_id"] = sid
            st.success(f"Sessione #{sid} creata!")
            st.switch_page("pages/1_Setup.py")

# Sessioni esistenti
with col2:
    st.subheader("📂 Sessioni esistenti")
    sessioni = lista_sessioni()

    if not sessioni:
        st.info("Nessuna sessione ancora creata.")
    else:
        STATO_EMOJI = {
            "setup": "⚙️",
            "horizon_scanning": "🔭",
            "transizione": "🔀",
            "scenario_planning": "🗺️",
            "concluso": "✅",
        }
        for s in sessioni:
            emoji = STATO_EMOJI.get(s["stato"], "•")
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**#{s['id']}** {emoji} `{s['stato']}`")
                    st.caption(f"*{s['domanda_ricerca'][:80]}{'...' if len(s['domanda_ricerca']) > 80 else ''}*")
                    st.caption(f"🕐 {s['frame_temporale']} · {s['created_at'][:10]}")
                with col_b:
                    if st.button("Apri", key=f"apri_{s['id']}", use_container_width=True):
                        st.session_state["sessione_id"] = s["id"]
                        st.switch_page("pages/1_Setup.py")

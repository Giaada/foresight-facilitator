import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.database import init_db, get_sessione_by_id, get_sessione_by_codice, registra_partecipante

st.set_page_config(page_title="Foresight Facilitator", page_icon="🧭", layout="wide")
init_db()

ruolo = st.session_state.get("ruolo")  # None | "facilitatore" | "partecipante"

# ── CSS globale per nascondere sidebar nella home ─────────
HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
</style>
"""

if ruolo == "facilitatore":
    pages = {
        "Sessione": [
            st.Page("pages/fac_setup.py", title="⚙️ Setup", default=True),
        ],
        "Facilitazione": [
            st.Page("pages/fac_hs.py", title="🔭 Horizon Scanning"),
            st.Page("pages/fac_transizione.py", title="🔀 Transizione"),
            st.Page("pages/fac_scenario.py", title="🗺️ Scenario Planning"),
            st.Page("pages/fac_report.py", title="📄 Report"),
        ],
    }

    with st.sidebar:
        if st.session_state.get("sessione_id"):
            sessione = get_sessione_by_id(st.session_state.sessione_id)
            if sessione:
                st.success("Sessione attiva")
                st.metric("Codice partecipanti", sessione["codice"])
                if st.button("Cambia sessione"):
                    del st.session_state["sessione_id"]
                    st.rerun()
        st.divider()
        if st.button("🔒 Esci"):
            st.session_state.clear()
            st.rerun()

    pg = st.navigation(pages)
    pg.run()

elif ruolo == "partecipante":
    pages = {
        "": [
            st.Page("pages/par_hs.py", title="🔭 Horizon Scanning", default=True),
            st.Page("pages/par_scenario.py", title="🗺️ Scenario Planning"),
        ]
    }

    with st.sidebar:
        p = st.session_state.get("partecipante", {})
        st.markdown(f"👤 **{p.get('nome', '')}**")
        sessione = get_sessione_by_id(p.get("sessione_id")) if p.get("sessione_id") else None
        if sessione:
            domanda = sessione["domanda_ricerca"]
            st.caption(f"📌 {domanda[:60]}{'...' if len(domanda) > 60 else ''}")
            st.caption(f"⏱️ {sessione['frame_temporale']}")
        if st.button("Esci"):
            st.session_state.clear()
            st.rerun()

    pg = st.navigation(pages)
    pg.run()

else:
    # HOME: scelta ruolo — niente sidebar, niente navigation reale
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    def _home():
        st.markdown(
            "<h1 style='text-align:center'>🧭 Foresight Facilitator</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center;color:#6B7280'>Strumento di facilitazione per sessioni di <strong>Strategic Foresight</strong> guidate dall'AI</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_fac, col_gap, col_par, col_right = st.columns([1, 3, 0.5, 3, 1])

        # ── Card Facilitatore ─────────────────────────────
        with col_fac:
            with st.container(border=True):
                st.markdown("### 🎙️ Sono il facilitatore")
                st.caption("Accedi con la password per gestire la sessione")
                st.markdown("<br>", unsafe_allow_html=True)

                with st.form("login_fac_home"):
                    pwd = st.text_input("Password", type="password", placeholder="Inserisci la password")
                    ok = st.form_submit_button("Accedi come facilitatore", use_container_width=True, type="primary")

                if ok:
                    from lib.auth import get_password
                    if pwd == get_password():
                        st.session_state["ruolo"] = "facilitatore"
                        st.rerun()
                    else:
                        st.error("Password non corretta.")

        # ── Card Partecipante ─────────────────────────────
        with col_par:
            with st.container(border=True):
                st.markdown("### 🙋 Sono un partecipante")
                st.caption("Inserisci il codice della sessione e il tuo nome")
                st.markdown("<br>", unsafe_allow_html=True)

                with st.form("login_par_home"):
                    codice = st.text_input(
                        "Codice sessione",
                        placeholder="Es. ABCDEF",
                        max_chars=6,
                    )
                    nome = st.text_input("Il tuo nome", placeholder="Es. Mario Rossi")
                    ok_par = st.form_submit_button("Partecipa", use_container_width=True, type="primary")

                if ok_par:
                    if not codice.strip() or not nome.strip():
                        st.error("Inserisci codice sessione e nome.")
                    else:
                        sessione = get_sessione_by_codice(codice.strip())
                        if not sessione:
                            st.error("Codice sessione non trovato. Verifica con il facilitatore.")
                        else:
                            partecipante = registra_partecipante(sessione["id"], nome.strip())
                            st.session_state["ruolo"] = "partecipante"
                            st.session_state["partecipante"] = partecipante
                            st.rerun()

    pg = st.navigation({"": [st.Page(_home, title="Home", default=True)]})
    pg.run()

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
            
            stato = sessione.get("stato", "setup")
            
            if stato in ("scenario_planning", "scenario_planning_gruppo", "concluso"):
                from lib.database import get_partecipanti, get_scenari
                plist = get_partecipanti(sessione["id"])
                par_corrente = next((x for x in plist if x["id"] == p.get("id")), None)
                if par_corrente and par_corrente.get("gruppo_numero"):
                    slist = get_scenari(sessione["id"])
                    scen = next((s for s in slist if s["numero"] == par_corrente["gruppo_numero"]), None)
                    if scen and scen.get("quadrante"):
                        st.caption(f"🧭 Quadrante: **{scen['quadrante']}**")
            
            st.divider()
            
            if stato == "horizon_scanning": idx = 0
            elif stato in ("transizione", "elaborazione_orizzonte", "definizione_driver"): idx = 1
            elif stato == "scenario_planning": idx = 2
            elif stato == "scenario_planning_gruppo": idx = 3
            elif stato == "concluso": idx = 4
            else: idx = -1
            
            fasi = [
                "🔭 Horizon Scanning",
                "⚙️ Elaborazione Assi",
                "👤 Scenario Individuale",
                "⚠️ Minacce e Opportunità",
                "🤝 Discussione di Gruppo",
                "📄 Report Finale"
            ]
            
            stepper_html = """
            <style>
            .stepper { list-style: none; padding: 0; margin: 10px 0 20px 5px; }
            .stepper li { position: relative; padding-left: 28px; margin-bottom: 24px; color: #6B7280; font-size: 14px; font-weight: 500;}
            .stepper li.active { color: #4F46E5; font-weight: 700; }
            .stepper li.done { color: #10B981; }
            .stepper li::before {
              content: ''; position: absolute; left: 0; top: 4px; width: 12px; height: 12px;
              border-radius: 50%; background: white; border: 2px solid #D1D5DB; z-index: 2;
            }
            .stepper li.active::before { border-color: #4F46E5; background: #4F46E5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2); }
            .stepper li.done::before { border-color: #10B981; background: #10B981; }
            .stepper li:not(:last-child)::after {
              content: ''; position: absolute; left: 5px; top: 16px; bottom: -24px;
              width: 2px; background: #E5E7EB; z-index: 1;
            }
            .stepper li.done:not(:last-child)::after { background: #10B981; }
            </style>
            <ul class="stepper">
            """
            
            for i, f in enumerate(fasi):
                css_class = ""
                if i < idx: css_class = "done"
                elif i == idx: css_class = "active"
                stepper_html += f'<li class="{css_class}">{f}</li>'
            stepper_html += "</ul>"
            
            st.markdown(stepper_html, unsafe_allow_html=True)
            st.divider()

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

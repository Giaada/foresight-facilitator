import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_sessione, get_scenari, get_scenario, aggiorna_scenario, get_messaggi
from lib.agent import invia_messaggio, avvia_scenario

st.set_page_config(page_title="Scenario Planning · Foresight Facilitator", page_icon="🗺️", layout="wide")

if "sessione_id" not in st.session_state:
    st.warning("Nessuna sessione selezionata.")
    st.page_link("app.py", label="← Torna alla home")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione(sid)
scenari = get_scenari(sid)

if not scenari:
    st.error("Scenari non trovati. Torna alla Transizione e avvia lo Scenario Planning.")
    st.page_link("pages/3_Transizione.py", label="← Torna alla Transizione")
    st.stop()

# ── Header ────────────────────────────────────────────────
st.markdown(f"### 🗺️ Scenario Planning — Sessione #{sid}")
st.caption(f"Orizzonte: **{sessione['frame_temporale']}** · Driver: **{sessione.get('driver1_nome','?')} × {sessione.get('driver2_nome','?')}**")
with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

# ── Panoramica scenari ────────────────────────────────────
st.subheader("📊 Stato scenari")
STEP_LABEL = {
    "intro": "Introduzione", "key_points": "Key Points",
    "narrativa": "Narrativa", "titolo": "Titolo",
    "minacce": "Minacce", "opportunita": "Opportunità", "concluso": "✅ Completato"
}
STEP_NUM = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"]

ov_cols = st.columns(4)
for i, sc in enumerate(scenari):
    with ov_cols[i]:
        step_idx = STEP_NUM.index(sc["step_corrente"]) if sc["step_corrente"] in STEP_NUM else 0
        progresso = step_idx / (len(STEP_NUM) - 1)
        completato = sc["step_corrente"] == "concluso"
        with st.container(border=True):
            st.markdown(f"**Scenario {sc['numero']}** `{sc['quadrante']}`")
            titolo = sc.get("titolo") or "—"
            st.caption(f"*{titolo}*")
            st.progress(progresso, text=STEP_LABEL.get(sc["step_corrente"], sc["step_corrente"]))

st.divider()

# ── Tabs per ogni scenario ────────────────────────────────
tab_labels = [f"Scenario {s['numero']} {'✅' if s['step_corrente']=='concluso' else ''}" for s in scenari]
tabs = st.tabs(tab_labels)

for tab, scenario in zip(tabs, scenari):
    with tab:
        sc = get_scenario(scenario["id"])
        if not sc:
            continue

        # Descrizione quadrante
        d1 = sessione.get("driver1_nome", "Driver 1")
        d2 = sessione.get("driver2_nome", "Driver 2")
        asse_x = (sessione.get("driver1_pos") if sc["quadrante"][0] == "+" else sessione.get("driver1_neg")) or d1
        asse_y = (sessione.get("driver2_pos") if sc["quadrante"][1] == "+" else sessione.get("driver2_neg")) or d2
        st.markdown(f"**Quadrante:** {asse_x} × {asse_y}")

        col_chat, col_output = st.columns([3, 2])

        # ── Chat con l'agente ─────────────────────────────
        with col_chat:
            st.markdown("#### 💬 Conversazione con l'Agente")

            messaggi = get_messaggi(sc["id"])

            # Avvia agente se nessun messaggio
            if not messaggi and sc["step_corrente"] == "intro":
                with st.spinner("L'agente si sta preparando..."):
                    avvia_scenario(sc, sessione)
                    st.rerun()

            # Mostra chat
            chat_container = st.container(height=400)
            with chat_container:
                for msg in messaggi:
                    if msg["ruolo"] == "assistant":
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(msg["contenuto"])
                    elif msg["ruolo"] == "user" and msg["contenuto"] not in ("__avvia__",):
                        with st.chat_message("user", avatar="🧑‍💼"):
                            st.markdown(msg["contenuto"])

            # Input facilitatore
            if sc["step_corrente"] != "concluso":
                input_key = f"input_sc_{sc['id']}"
                testo = st.chat_input(
                    "Scrivi la risposta del gruppo...",
                    key=f"chat_{sc['id']}"
                )
                if testo:
                    with st.spinner("L'agente sta elaborando..."):
                        _, nuovo_step = invia_messaggio(sc, sessione, testo)
                    st.rerun()
            else:
                st.success("Scenario completato!")

        # ── Output scenario ───────────────────────────────
        with col_output:
            st.markdown("#### 📝 Scenario in costruzione")
            sc = get_scenario(scenario["id"])  # ricarica

            if sc.get("titolo"):
                st.markdown(f"### {sc['titolo']}")

            if sc.get("narrativa"):
                with st.container(border=True):
                    st.markdown("**Narrativa**")
                    st.markdown(sc["narrativa"])

            if sc.get("minacce"):
                with st.container(border=True):
                    st.markdown("**⚠️ Minacce**")
                    for m in sc["minacce"]:
                        st.markdown(f"- {m}")

            if sc.get("opportunita"):
                with st.container(border=True):
                    st.markdown("**✨ Opportunità**")
                    for o in sc["opportunita"]:
                        st.markdown(f"- {o}")

            if sc.get("key_points_data"):
                with st.expander("🔍 Key Points esplorati"):
                    for kp, risposta in sc["key_points_data"].items():
                        st.markdown(f"**{kp}:** {risposta}")

            # Modifica manuale titolo
            st.divider()
            st.markdown("**Modifica manuale**")
            titolo_edit = st.text_input(
                "Titolo scenario",
                value=sc.get("titolo") or "",
                key=f"titolo_{sc['id']}",
                placeholder="Es. Il Mondo Interconnesso"
            )
            if st.button("Salva titolo", key=f"salva_titolo_{sc['id']}"):
                aggiorna_scenario(sc["id"], titolo=titolo_edit)
                st.rerun()

st.divider()

# ── Chiudi sessione ───────────────────────────────────────
tutti_conclusi = all(s["step_corrente"] == "concluso" for s in get_scenari(sid))
if tutti_conclusi or st.checkbox("Forza chiusura sessione"):
    if st.button("✅ Chiudi sessione e vai al Report", type="primary", use_container_width=True):
        from lib.database import aggiorna_sessione
        aggiorna_sessione(sid, stato="concluso")
        st.switch_page("pages/5_Report.py")

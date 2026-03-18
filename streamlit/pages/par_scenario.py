import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import (
    get_sessione_by_id, get_scenari, get_scenario,
    get_messaggi, get_partecipanti
)
from lib.agent import invia_messaggio, avvia_scenario

# ── Leggi partecipante dalla session ─────────────────────
partecipante = st.session_state.get("partecipante")
if not partecipante:
    st.error("Sessione non trovata. Torna alla home e accedi come partecipante.")
    st.stop()

sessione_id = partecipante.get("sessione_id")
partecipante_id = partecipante.get("id")
nome = partecipante.get("nome", "")

sessione = get_sessione_by_id(sessione_id) if sessione_id else None
if not sessione:
    st.error("Sessione non trovata.")
    st.stop()

# ── Header ────────────────────────────────────────────────
st.markdown("## 🗺️ Scenario Planning")
st.markdown(f"👤 **{nome}**")

with st.container(border=True):
    st.markdown(f"**Domanda di ricerca:** {sessione['domanda_ricerca']}")
    st.markdown(f"**Orizzonte temporale:** {sessione['frame_temporale']}")

st.divider()

# ── Controlla stato sessione ──────────────────────────────
stato = sessione.get("stato")

if stato not in ("scenario_planning", "concluso"):
    st.info("⏳ La sessione non è ancora nella fase di Scenario Planning. Attendi istruzioni dal facilitatore.")

    @st.fragment(run_every=10)
    def _attendi_scenario():
        s = get_sessione_by_id(sessione_id)
        if s and s.get("stato") in ("scenario_planning", "concluso"):
            st.rerun()
    _attendi_scenario()

    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

# ── Recupera gruppo del partecipante ─────────────────────
partecipanti_db = get_partecipanti(sessione_id)
par_db = next((p for p in partecipanti_db if p["id"] == partecipante_id), None)
gruppo_numero = par_db.get("gruppo_numero") if par_db else None

if not gruppo_numero:
    st.info("⏳ Non sei ancora stato/a assegnato/a a un gruppo. Attendi che il facilitatore assegni i gruppi.")

    @st.fragment(run_every=10)
    def _attendi_gruppo():
        plist = get_partecipanti(sessione_id)
        p = next((x for x in plist if x["id"] == partecipante_id), None)
        if p and p.get("gruppo_numero"):
            st.rerun()
    _attendi_gruppo()

    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

# ── Recupera scenario corrispondente al gruppo ────────────
# gruppo_numero corrisponde a scenario.numero
scenari = get_scenari(sessione_id)
scenario_corrente = next((s for s in scenari if s["numero"] == gruppo_numero), None)

if not scenario_corrente:
    st.info("⏳ Lo scenario per il tuo gruppo non è ancora disponibile. Attendi il facilitatore.")
    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

sc = get_scenario(scenario_corrente["id"])
if not sc:
    st.error("Scenario non trovato.")
    st.stop()

# ── Layout: chat + pannello scenario ─────────────────────
# Descrizione quadrante
d1 = sessione.get("driver1_nome", "Driver 1")
d2 = sessione.get("driver2_nome", "Driver 2")
asse_x = (
    sessione.get("driver1_pos") if sc["quadrante"][0] == "+" else sessione.get("driver1_neg")
) or d1
asse_y = (
    sessione.get("driver2_pos") if sc["quadrante"][1] == "+" else sessione.get("driver2_neg")
) or d2

st.markdown(
    f"**Gruppo {gruppo_numero}** — Scenario `{sc['quadrante']}`: {asse_x} × {asse_y}"
)

col_chat, col_panel = st.columns([3, 2])

# ── Chat ──────────────────────────────────────────────────
with col_chat:
    st.markdown("### 💬 Conversazione con l'Agente")

    messaggi = get_messaggi(sc["id"])

    # Avvia agente se nessun messaggio
    if not messaggi and sc["step_corrente"] == "intro":
        with st.spinner("L'agente si sta preparando..."):
            avvia_scenario(sc, sessione)
            st.rerun()

    # Mostra chat
    chat_container = st.container(height=450)
    with chat_container:
        for msg in messaggi:
            if msg["ruolo"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["contenuto"])
            elif msg["ruolo"] == "user":
                with st.chat_message("user", avatar="🙋"):
                    st.markdown(msg["contenuto"])

    # Input risposta gruppo
    if sc["step_corrente"] != "concluso":
        testo = st.chat_input(
            "Scrivi la risposta del gruppo...",
            key=f"chat_par_{sc['id']}",
        )
        if testo:
            with st.spinner("L'agente sta elaborando..."):
                _, nuovo_step = invia_messaggio(sc, sessione, testo)
            st.rerun()
    else:
        st.success("🎉 Scenario completato! Ottimo lavoro.")

# ── Pannello scenario in costruzione ─────────────────────
with col_panel:
    with st.expander("📝 Scenario in costruzione", expanded=True):
        sc_aggiornato = get_scenario(sc["id"])

        if sc_aggiornato.get("titolo"):
            st.markdown(f"### {sc_aggiornato['titolo']}")
        else:
            st.caption("*Titolo non ancora definito*")

        if sc_aggiornato.get("narrativa"):
            with st.container(border=True):
                st.markdown("**Narrativa**")
                st.markdown(sc_aggiornato["narrativa"])

        if sc_aggiornato.get("minacce"):
            with st.container(border=True):
                st.markdown("**⚠️ Minacce**")
                for m in sc_aggiornato["minacce"]:
                    st.markdown(f"- {m}")

        if sc_aggiornato.get("opportunita"):
            with st.container(border=True):
                st.markdown("**✨ Opportunità**")
                for o in sc_aggiornato["opportunita"]:
                    st.markdown(f"- {o}")

        if sc_aggiornato.get("key_points_data"):
            st.markdown("**Key Points esplorati:**")
            for kp, risposta in sc_aggiornato["key_points_data"].items():
                st.markdown(f"- **{kp}:** {risposta}")

        if not any([
            sc_aggiornato.get("titolo"),
            sc_aggiornato.get("narrativa"),
            sc_aggiornato.get("minacce"),
            sc_aggiornato.get("opportunita"),
        ]):
            st.info("Lo scenario si costruirà durante la conversazione con l'agente.")

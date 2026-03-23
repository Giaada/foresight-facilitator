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
            st.rerun(scope="app")
    _attendi_scenario()

    if st.button("🔄 Aggiorna", key="btn_aggiorna_stato"):
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
            st.rerun(scope="app")
    _attendi_gruppo()

    if st.button("🔄 Aggiorna", key="btn_aggiorna_gruppo"):
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
asse_x_pos = sessione.get("driver1_pos", "Alto")
asse_x_neg = sessione.get("driver1_neg", "Basso")
asse_y_pos = sessione.get("driver2_pos", "Alto")
asse_y_neg = sessione.get("driver2_neg", "Basso")

q_x = asse_x_pos if sc["quadrante"][0] == "+" else asse_x_neg
q_y = asse_y_pos if sc["quadrante"][1] == "+" else asse_y_neg

css_matrix = f"""
<div style="background-color: white; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.25rem; display: flex; flex-direction: row; gap: 2rem; align-items: center; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
  <div style="flex: 1; font-size: 0.875rem; color: #374151;">
    <h3 style="font-size: 1rem; font-weight: bold; color: #312e81; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
      Bussola Scenario: Quadrante <span style="color: #4f46e5; background-color: #eef2ff; border: 1px solid #e0e7ff; padding: 0.125rem 0.5rem; border-radius: 0.25rem;">{sc['quadrante']}</span>
    </h3>
    <p style="line-height: 1.6; margin:0;">Il vostro gruppo sta attivamente esplorando l'incrocio tra <strong>{q_x}</strong> (sull'asse <em>{d1}</em>) e <strong>{q_y}</strong> (sull'asse <em>{d2}</em>).</p>
  </div>
  <div style="display: flex; flex-direction: column; align-items: center; flex-shrink: 0;">
    <div style="font-size: 11px; font-weight: bold; color: #9ca3af; margin-bottom: 4px; text-transform: capitalize;">{asse_y_pos}</div>
    <div style="display: flex; align-items: center;">
      <div style="font-size: 11px; font-weight: bold; color: #9ca3af; margin-right: 8px; writing-mode: vertical-rl; transform: rotate(180deg); text-transform: capitalize;">{asse_x_neg}</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; width: 100px; height: 100px; border: 3px solid #334155; background-color: #f8fafc; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
        <div style="border-right: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; display: flex; align-items: center; justify-content: center; background-color: {'#4f46e5' if sc['quadrante'] == '-+' else 'transparent'}; color: {'white' if sc['quadrante'] == '-+' else 'transparent'}; font-size: 10px; font-weight: bold; opacity: 0.8;">- +</div>
        <div style="border-bottom: 1px solid #cbd5e1; display: flex; align-items: center; justify-content: center; background-color: {'#4f46e5' if sc['quadrante'] == '++' else 'transparent'}; color: {'white' if sc['quadrante'] == '++' else 'transparent'}; font-size: 10px; font-weight: bold; opacity: 0.8;">+ +</div>
        <div style="border-right: 1px solid #cbd5e1; display: flex; align-items: center; justify-content: center; background-color: {'#4f46e5' if sc['quadrante'] == '--' else 'transparent'}; color: {'white' if sc['quadrante'] == '--' else 'transparent'}; font-size: 10px; font-weight: bold; opacity: 0.8;">- -</div>
        <div style="display: flex; align-items: center; justify-content: center; background-color: {'#4f46e5' if sc['quadrante'] == '+-' else 'transparent'}; color: {'white' if sc['quadrante'] == '+-' else 'transparent'}; font-size: 10px; font-weight: bold; opacity: 0.8;">+ -</div>
      </div>
      <div style="font-size: 11px; font-weight: bold; color: #9ca3af; margin-left: 8px; writing-mode: vertical-rl; text-transform: capitalize;">{asse_x_pos}</div>
    </div>
    <div style="font-size: 11px; font-weight: bold; color: #9ca3af; margin-top: 4px; text-transform: capitalize;">{asse_y_neg}</div>
  </div>
</div>
"""
st.markdown(css_matrix, unsafe_allow_html=True)

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
        st.info("Attendi che il facilitatore pubblichi il report PDF consolidato contenente le riflessioni di tutti i gruppi.")
        if st.button("Torna alla vista principale", type="primary"):
            st.rerun()

# ── Pannello scenario in costruzione ─────────────────────
with col_panel:
    @st.fragment(run_every=5)
    def _pannello_scenario():
        sc_live = get_scenario(sc["id"])
        if not sc_live:
            return

        STEP_LABEL = {
            "intro": "🟡 Introduzione",
            "key_points": "🔵 Key Points",
            "narrativa": "🟣 Narrativa",
            "titolo": "🟠 Titolo",
            "minacce": "🔴 Minacce",
            "opportunita": "🟢 Opportunità",
            "concluso": "✅ Concluso",
        }
        step_label = STEP_LABEL.get(sc_live["step_corrente"], sc_live["step_corrente"])
        st.caption(f"Step: {step_label}")

        with st.expander("📝 Scenario in costruzione", expanded=True):
            if sc_live.get("titolo"):
                st.markdown(f"### {sc_live['titolo']}")
            else:
                st.caption("*Titolo non ancora definito*")

            if sc_live.get("narrativa"):
                with st.container(border=True):
                    st.markdown("**Narrativa**")
                    st.markdown(sc_live["narrativa"])

            if sc_live.get("minacce"):
                with st.container(border=True):
                    st.markdown("**⚠️ Minacce**")
                    for m in sc_live["minacce"]:
                        st.markdown(f"- {m}")

            if sc_live.get("opportunita"):
                with st.container(border=True):
                    st.markdown("**✨ Opportunità**")
                    for o in sc_live["opportunita"]:
                        st.markdown(f"- {o}")

            if sc_live.get("key_points_data"):
                st.markdown("**Key Points esplorati:**")
                for kp, risposta in sc_live["key_points_data"].items():
                    st.markdown(f"- **{kp}:** {risposta}")

            if not any([
                sc_live.get("titolo"),
                sc_live.get("narrativa"),
                sc_live.get("minacce"),
                sc_live.get("opportunita"),
            ]):
                st.info("Lo scenario si costruirà durante la conversazione con l'agente.")

    _pannello_scenario()

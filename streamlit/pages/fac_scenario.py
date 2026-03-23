import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import (
    get_sessione_by_id, aggiorna_sessione,
    get_scenari, get_scenario, aggiorna_scenario,
    get_scenari_individuali, get_partecipanti
)
from lib.agent import unisci_scenari_gruppo

check_facilitatore()

if not st.session_state.get("sessione_id"):
    st.warning("Nessuna sessione attiva. Vai su Setup per aprire o creare una sessione.")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione_by_id(sid)

if not sessione:
    st.error("Sessione non trovata.")
    st.stop()

st.markdown(f"### 🗺️ Scenario Planning — Sessione #{sid}")
st.caption(
    f"Orizzonte: **{sessione['frame_temporale']}** · "
    f"Driver: **{sessione.get('driver1_nome', '?')} × {sessione.get('driver2_nome', '?')}**"
)

with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

STEP_LABEL = {
    "intro": "Introduzione",
    "key_points": "Key Points",
    "narrativa": "Narrativa",
    "titolo": "Titolo",
    "minacce": "Minacce",
    "opportunita": "Opportunità",
    "concluso": "✅ Completato",
}
STEP_NUM = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"]

stato = sessione.get("stato")

@st.fragment(run_every=15)
def _overview_scenari():
    scenari_gruppo = get_scenari(sid)
    scenari_indiv = get_scenari_individuali(sid)
    
    if not scenari_gruppo:
        st.info("Scenari non ancora creati. Torna alla Transizione e avvia lo Scenario Planning.")
        return

    st.subheader("📊 Stato scenari")
    ov_cols = st.columns(4)
    for i, sc in enumerate(scenari_gruppo):
        with ov_cols[i]:
            with st.container(border=True):
                st.markdown(f"**Scenario {sc['numero']}** `{sc['quadrante']}`")
                if stato == "scenario_planning":
                    indivs = [s for s in scenari_indiv if s["numero"] == sc["numero"]]
                    conclusi = sum(1 for s in indivs if s["step_corrente"] == "concluso")
                    tot = len(indivs)
                    st.progress(conclusi / max(1, tot) if tot > 0 else 0.0, text=f"Individuali fini: {conclusi}/{tot}")
                else:
                    st.progress(1.0 if sc["step_corrente"] == "concluso" else 0.0, text="Sintesi di Gruppo")


_overview_scenari()

scenari_gruppo = get_scenari(sid)
scenari_individuali = get_scenari_individuali(sid)
partecipanti = get_partecipanti(sid)
par_map = {p["id"]: p["nome"] for p in partecipanti}

if not scenari_gruppo:
    st.stop()

st.divider()

if stato == "scenario_planning":
    st.info("Fase 1: **Drafting Individuale**. I partecipanti stanno lavorando in autonomia.")
    
    tab_labels = [f"Gruppo {s['numero']}" for s in scenari_gruppo]
    tabs = st.tabs(tab_labels)
    
    for tab, sc_g in zip(tabs, scenari_gruppo):
        with tab:
            indivs = [s for s in scenari_individuali if s["numero"] == sc_g["numero"]]
            st.markdown(f"**Membri di questo quadrante ({len(indivs)})**")
            
            for s_ind in indivs:
                nome_par = par_map.get(s_ind["partecipante_id"], "Sconosciuto")
                step_val = s_ind.get("step_corrente", "intro")
                is_done = (step_val == "concluso")
                
                with st.expander(f"👤 {nome_par} - Step: {STEP_LABEL.get(step_val, step_val)} {'✅' if is_done else '⏳'}"):
                    if s_ind.get("narrativa"):
                        st.markdown(f"**Bozza:** {s_ind['narrativa']}")
                    if s_ind.get("minacce"):
                        st.markdown("**Minacce:** " + ", ".join(s_ind["minacce"]))
                    if s_ind.get("opportunita"):
                        st.markdown("**Opportunità:** " + ", ".join(s_ind["opportunita"]))

    st.divider()
    
    # Check if all individuals are done
    tutti_conclusi = all(s["step_corrente"] == "concluso" for s in scenari_individuali) if scenari_individuali else False
    
    with st.container(border=True):
        if tutti_conclusi:
            st.success("Tutti i partecipanti hanno completato la loro stesura individuale!")
        else:
            completati = sum(1 for s in scenari_individuali if s["step_corrente"] == "concluso")
            st.warning(f"In attesa del completamento individuale ({completati}/{len(scenari_individuali)} conclusi).")
            
        st.markdown("Crea la bozza consolidata per spostare la sessione alla **Fase 2 (Discussione di Gruppo)**.")
        if st.button("🚀 Genera Bozze Integrate di Gruppo e Unisci Partecipanti", type="primary", use_container_width=True):
            with st.spinner("L'Intelligenza Artificiale sta leggendo e unificando tutti i contributi..."):
                for sc_g in scenari_gruppo:
                    indivs = [s for s in scenari_individuali if s["numero"] == sc_g["numero"]]
                    unisci_scenari_gruppo(sc_g, sessione, indivs)
                aggiorna_sessione(sid, stato="scenario_planning_gruppo")
            st.success("Bozze consolidate con successo!")
            st.rerun()

elif stato in ("scenario_planning_gruppo", "concluso"):
    if stato == "scenario_planning_gruppo":
        st.success("Fase 2: **Sintesi di Gruppo**. I partecipanti stanno visualizzando le bozze consolidate.")
    else:
        st.success("Sessione Conclusa. Questi i risultati finali:")
    
    tab_labels = [f"Gruppo {s['numero']}" for s in scenari_gruppo]
    tabs = st.tabs(tab_labels)
    
    for tab, sc_g in zip(tabs, scenari_gruppo):
        with tab:
            d1 = sessione.get("driver1_nome", "Driver 1")
            d2 = sessione.get("driver2_nome", "Driver 2")
            asse_x = (sessione.get("driver1_pos") if sc_g["quadrante"][0] == "+" else sessione.get("driver1_neg")) or d1
            asse_y = (sessione.get("driver2_pos") if sc_g["quadrante"][1] == "+" else sessione.get("driver2_neg")) or d2
            st.markdown(f"**Quadrante:** `{sc_g['quadrante']}` — {asse_x} × {asse_y}")

            col_info, col_edit = st.columns([3, 2])
            with col_info:
                if sc_g.get("narrativa"):
                    with st.container(border=True):
                        st.markdown("**Bozza Integrata**")
                        st.markdown(sc_g["narrativa"])
                if sc_g.get("minacce"):
                    with st.container(border=True):
                        st.markdown("**⚠️ Minacce Emerse**")
                        for m in sc_g["minacce"]:
                            st.markdown(f"- {m}")
                if sc_g.get("opportunita"):
                    with st.container(border=True):
                        st.markdown("**✨ Opportunità Emerse**")
                        for o in sc_g["opportunita"]:
                            st.markdown(f"- {o}")
            with col_edit:
                st.markdown("**Modifica manuale Titolo**")
                titolo_edit = st.text_input("Titolo scenario", value=sc_g.get("titolo") or "", key=f"t_{sc_g['id']}")
                if st.button("Salva titolo", key=f"btn_t_{sc_g['id']}"):
                    aggiorna_scenario(sc_g["id"], titolo=titolo_edit)
                    st.rerun()

    st.divider()
    if stato != "concluso":
        if st.button("✅ Chiudi definitivamente sessione e vai al Report", type="primary", use_container_width=True):
            aggiorna_sessione(sid, stato="concluso")
            st.switch_page("pages/fac_report.py")
    else:
        if st.button("Vai al Report", type="primary", use_container_width=True):
            st.switch_page("pages/fac_report.py")

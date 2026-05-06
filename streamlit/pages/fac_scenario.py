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
from lib.quadrant_ui import draw_quadrant_matrix

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

                with st.expander(f"👤 {nome_par} — {STEP_LABEL.get(step_val, step_val)} {'✅' if is_done else '⏳'}"):
                    if s_ind.get("narrativa"):
                        st.markdown(f"**Bozza:** {s_ind['narrativa']}")
                    if s_ind.get("minacce"):
                        st.markdown("**Minacce:** " + ", ".join(s_ind["minacce"]))
                    if s_ind.get("opportunita"):
                        st.markdown("**Opportunità:** " + ", ".join(s_ind["opportunita"]))
                    if is_done:
                        if st.button(f"↩️ Riapri lavoro di {nome_par}", key=f"reset_{s_ind['id']}", use_container_width=True):
                            aggiorna_scenario(s_ind["id"], step_corrente="opportunita")
                            st.rerun()

            st.divider()

            n_conclusi = sum(1 for s in indivs if s["step_corrente"] == "concluso")
            n_tot = len(indivs)
            bozza_generata = bool(sc_g.get("narrativa"))

            if bozza_generata:
                st.success(f"✅ Bozza integrata generata per il Gruppo {sc_g['numero']}.")
                if st.button(f"🔄 Rigenera Bozza", key=f"rigenera_{sc_g['id']}", use_container_width=True):
                    with st.spinner("Rigenerazione in corso..."):
                        unisci_scenari_gruppo(sc_g, sessione, indivs)
                    st.success("Bozza rigenerata!")
                    st.rerun()
            else:
                if n_conclusi < n_tot:
                    st.warning(f"⏳ {n_conclusi}/{n_tot} partecipanti hanno completato il lavoro individuale.")
                else:
                    st.success(f"✅ Tutti i {n_tot} partecipanti hanno completato il lavoro individuale.")
                if st.button(
                    f"🚀 Genera Bozza Integrata — Gruppo {sc_g['numero']}",
                    key=f"genera_{sc_g['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner(f"L'AI sta integrando i contributi del Gruppo {sc_g['numero']}..."):
                        unisci_scenari_gruppo(sc_g, sessione, indivs)
                    st.success(f"Bozza del Gruppo {sc_g['numero']} generata!")
                    st.rerun()

    st.divider()

    # ── Avanzamento fase globale ──────────────────────────────
    n_bozze = sum(1 for sc_g in scenari_gruppo if sc_g.get("narrativa"))
    n_gruppi = len(scenari_gruppo)
    completati_tot = sum(1 for s in scenari_individuali if s["step_corrente"] == "concluso")
    tot_indiv = len(scenari_individuali)

    with st.container(border=True):
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Lavori individuali conclusi", f"{completati_tot}/{tot_indiv}")
        with col_stat2:
            st.metric("Bozze di gruppo generate", f"{n_bozze}/{n_gruppi}")

        if n_bozze == 0:
            st.info("Genera almeno una bozza integrata per poter avanzare alla Fase di Gruppo.")
        elif n_bozze < n_gruppi:
            st.warning(f"Solo {n_bozze}/{n_gruppi} bozze generate. I gruppi mancanti non potranno accedere alla fase di discussione finché non avranno una bozza.")
        else:
            st.success("Tutte le bozze sono pronte!")

        rimasti = tot_indiv - completati_tot
        if not st.session_state.get("confirm_avanza_gruppo"):
            if rimasti > 0 and n_bozze > 0:
                st.warning(f"⚠️ {rimasti} partecipante/i non ha ancora concluso il lavoro individuale.")
            if st.button(
                "▶️ Avanza alla Fase di Gruppo",
                type="primary",
                use_container_width=True,
                disabled=(n_bozze == 0),
            ):
                if rimasti > 0:
                    st.session_state["confirm_avanza_gruppo"] = True
                    st.rerun()
                else:
                    aggiorna_sessione(sid, stato="scenario_planning_gruppo")
                    st.success("Sessione avanzata alla Fase di Gruppo!")
                    st.rerun()
        else:
            st.error(f"⚠️ CONFERMA: {rimasti} partecipante/i non ha completato il proprio scenario. Avanzando ora non potranno più modificarlo.")
            col_avanza, col_back = st.columns(2)
            with col_avanza:
                if st.button("▶️ Avanza comunque", type="primary", use_container_width=True, key="btn_avanza_comunque"):
                    st.session_state["confirm_avanza_gruppo"] = False
                    aggiorna_sessione(sid, stato="scenario_planning_gruppo")
                    st.rerun()
            with col_back:
                if st.button("↩️ Aspetta ancora", use_container_width=True, key="btn_aspetta"):
                    st.session_state["confirm_avanza_gruppo"] = False
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
            
            # Matrice grafica centrata inline
            d1p = sessione.get("driver1_pos") or f"{d1} Alto"
            d1n = sessione.get("driver1_neg") or f"{d1} Basso"
            d2p = sessione.get("driver2_pos") or f"{d2} Alto"
            d2n = sessione.get("driver2_neg") or f"{d2} Basso"
            st.markdown(draw_quadrant_matrix(sc_g["quadrante"], d1p, d1n, d2p, d2n), unsafe_allow_html=True)

            col_orig, col_final = st.columns(2)
            
            with col_orig:
                st.markdown("### 🤖 Versione Originaria (AI)")
                if sc_g.get("narrativa"):
                    with st.container(border=True):
                        st.markdown("**Bozza Integrata**")
                        st.markdown(sc_g["narrativa"])
                        
                kp_data = sc_g.get("key_points_data", {})
                if isinstance(kp_data, dict):
                    p_com = kp_data.get("punti_comune", [])
                    divs = kp_data.get("divergenze", [])
                    if p_com:
                        st.success("**🤝 Punti in Comune**\n\n" + "\n".join(f"- {x}" for x in p_com))
                    if divs:
                        st.warning("**⚡ Divergenze Emerse**\n\n" + "\n".join(f"- {x}" for x in divs))                        

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
                            
            with col_final:
                st.markdown("### 🧠 Versione Definitiva (Gruppo)")
                
                t_fin = sc_g.get("titolo_finale")
                n_fin = sc_g.get("narrativa_finale")
                m_fin = sc_g.get("minacce_finale")
                o_fin = sc_g.get("opportunita_finale")
                
                if not any([t_fin, n_fin, m_fin, o_fin]):
                    st.info("Il gruppo non ha ancora iniziato a plasmare una versione separata rispetto a quella dell'Agente.")
                else:
                    with st.container(border=True):
                        if t_fin: st.markdown(f"**Titolo:** {t_fin}")
                        if n_fin: st.markdown(f"**Bozza:**\n{n_fin}")
                        
                        c_m, c_o = st.columns(2)
                        with c_m:
                            if m_fin: st.markdown("**⚠️ Minacce:**\n" + "\n".join(f"- {x}" for x in m_fin))
                        with c_o:
                            if o_fin: st.markdown("**✨ Opportunità:**\n" + "\n".join(f"- {x}" for x in o_fin))

                locked_by = sc_g.get("locked_by_partecipante_id")
                if locked_by:
                    locker = next((p for p in partecipanti if p["id"] == locked_by), None)
                    nome_locker = locker["nome"] if locker else "Un partecipante"
                    st.warning(f"🔒 **{nome_locker}** è il relatore attivo e sta modificando in questo momento.")
            
            st.divider()
            
            # Show individual components for this group
            indivs = [s for s in scenari_individuali if s["numero"] == sc_g["numero"]]
            if indivs:
                st.markdown("#### 👤 Lavori Individuali dei Membri")
                for s_ind in indivs:
                    nome_par = par_map.get(s_ind["partecipante_id"], "Sconosciuto")
                    with st.expander(f"Lavoro di {nome_par}"):
                        from lib.pdf_export import st_scarica_pdf_scenario_individuale
                        st_scarica_pdf_scenario_individuale(s_ind, sessione, nome_par)
                        
                        st.markdown(f"**Titolo:** {s_ind.get('titolo', 'Non definito')}")
                        if s_ind.get("narrativa"):
                            st.markdown(f"**Bozza:** {s_ind['narrativa']}")
                        if s_ind.get("minacce"):
                            st.markdown("**Minacce:** " + ", ".join(s_ind["minacce"]))
                        if s_ind.get("opportunita"):
                            st.markdown("**Opportunità:** " + ", ".join(s_ind["opportunita"]))

    st.divider()
    if stato != "concluso":
        col_chiudi, col_report = st.columns([3, 1])
        with col_chiudi:
            if st.button("✅ Chiudi definitivamente sessione e vai al Report", type="primary", use_container_width=True, key="btn_chiudi_sessione"):
                aggiorna_sessione(sid, stato="concluso")
                st.session_state["_vai_al_report"] = True
                st.rerun()
        with col_report:
            if st.button("📄 Vai al Report", use_container_width=True, key="btn_vai_report_anteprima"):
                st.switch_page("pages/fac_report.py")
    else:
        if st.button("📄 Vai al Report Finale", type="primary", use_container_width=True, key="btn_vai_report_concluso"):
            st.switch_page("pages/fac_report.py")

# Handle deferred navigation (after state update completes)
if st.session_state.pop("_vai_al_report", False):
    st.switch_page("pages/fac_report.py")

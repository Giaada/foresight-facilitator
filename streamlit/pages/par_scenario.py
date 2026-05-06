import streamlit as st
import streamlit.components.v1 as components
import sys
import re
import json as _json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_partecipante
from lib.database import (
    get_sessione_by_id, get_scenari, get_scenario,
    get_messaggi, get_partecipanti, get_scenario_individuale, aggiorna_scenario
)
from lib.agent import invia_messaggio, avvia_scenario
from lib.quadrant_ui import draw_quadrant_matrix

partecipante, sessione = check_partecipante()
sessione_id = partecipante.get("sessione_id")
partecipante_id = partecipante.get("id")
nome = partecipante.get("nome", "")

# ── Header ────────────────────────────────────────────────
st.markdown("## 🗺️ Scenario Planning")
st.markdown(f"👤 **{nome}**")

with st.container(border=True):
    st.markdown(f"**Domanda di ricerca:** {sessione['domanda_ricerca']}")
    st.markdown(f"**Orizzonte temporale:** {sessione['frame_temporale']}")

st.divider()

# ── Controlla stato sessione ──────────────────────────────
stato = sessione.get("stato")

if stato not in ("scenario_planning", "scenario_planning_gruppo", "concluso"):
    st.info("⏳ La sessione non è ancora nella fase di Scenario Planning. Attendi istruzioni dal facilitatore.")

    @st.fragment(run_every=15)
    def _attendi_scenario():
        s = get_sessione_by_id(sessione_id)
        if s and s.get("stato") in ("scenario_planning", "scenario_planning_gruppo", "concluso"):
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

    @st.fragment(run_every=15)
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

is_group_phase = (stato == "scenario_planning_gruppo")
sc = None

if is_group_phase:
    scenari = get_scenari(sessione_id)
    scenario_corrente = next((s for s in scenari if s["numero"] == gruppo_numero), None)
    if scenario_corrente:
        sc = get_scenario(scenario_corrente["id"])
else:
    # Individual Phase
    sc = get_scenario_individuale(sessione_id, partecipante_id)

if not sc:
    st.info("⏳ Lo scenario non è ancora disponibile. Attendi che il facilitatore lo attivi.")
    if st.button("🔄 Aggiorna"):
        st.rerun()
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

matrix_html = draw_quadrant_matrix(sc['quadrante'], asse_x_pos, asse_x_neg, asse_y_pos, asse_y_neg)
css_matrix = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; background: transparent;">
<div style="background-color: white; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.25rem; display: flex; flex-direction: row; gap: 2rem; align-items: center; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
  <div style="flex: 1; font-size: 0.875rem; color: #374151;">
    <h3 style="font-size: 1rem; font-weight: bold; color: #312e81; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
      Bussola Scenario: Quadrante <span style="color: #4f46e5; background-color: #eef2ff; border: 1px solid #e0e7ff; padding: 0.125rem 0.5rem; border-radius: 0.25rem;">{sc['quadrante']}</span>
    </h3>
    <p style="line-height: 1.6; margin:0;">Il vostro gruppo sta attivamente esplorando l'incrocio tra <strong>{q_x}</strong> (sull'asse <em>{d1}</em>) e <strong>{q_y}</strong> (sull'asse <em>{d2}</em>).</p>
  </div>
  <div style="display: flex; flex-direction: column; align-items: center; flex-shrink: 0; padding-right: 20px;">
    {matrix_html}
  </div>
</div>
</body>
</html>
"""
components.html(css_matrix, height=260)


if is_group_phase:
    tab_gruppo, tab_personale = st.tabs(["🤝 Lavoro di Gruppo", "👤 Il Mio Lavoro Individuale"])
    
    with tab_gruppo:
        st.markdown("### 🤝 Bozza Consolidata Integrata")
        st.success("Tutte le bozze dei partecipanti di questo gruppo sono state unificate.")
        st.info("Qui sotto trovate le visioni integrate individualizzate. Utilizzate le somiglianze e differenze emerse per avviare una discussione produttiva.")
        
        if sc.get("titolo"):
            st.markdown(f"**🏷️ Titolo:** {sc['titolo']}")
            
        st.markdown("#### 📖 Narrativa di Gruppo Integrata")
        st.markdown(sc.get("narrativa", "Sintesi non disponibile."))
        
        kp_data = sc.get("key_points_data", {})
        if isinstance(kp_data, dict):
            p_com = kp_data.get("punti_comune", [])
            divs = kp_data.get("divergenze", [])
            if p_com or divs:
                c_com, c_div = st.columns(2)
                with c_com:
                    if p_com:
                        st.success("**🤝 Cosa vi accomuna**\n\n" + "\n".join(f"- {x}" for x in p_com))
                with c_div:
                    if divs:
                        st.warning("**⚡ Idee uniche o divergenti**\n\n" + "\n".join(f"- {x}" for x in divs))
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ⚠️ Minacce Emerse")
            for m in sc.get("minacce", []):
                st.markdown(f"- {m}")
        with c2:
            st.markdown("#### ✨ Opportunità Emerse")
            for o in sc.get("opportunita", []):
                st.markdown(f"- {o}")
                
        st.divider()
        
        @st.fragment(run_every=15)
        def _sezione_definitiva():
            sc_live = get_scenario(sc["id"])
            if not sc_live: return
            
            st.markdown("### ✍️ Versione Definitiva (Editor Collaborativo)")
            locked_by = sc_live.get("locked_by_partecipante_id")
            
            t_fin = sc_live.get("titolo_finale") or sc_live.get("titolo", "")
            n_fin = sc_live.get("narrativa_finale") or sc_live.get("narrativa", "")
            
            m_fin_list = sc_live.get("minacce_finale")
            if m_fin_list is None or not isinstance(m_fin_list, list):
                m_fin_list = sc_live.get("minacce", [])
            m_fin = "\n".join(m_fin_list)
            
            o_fin_list = sc_live.get("opportunita_finale")
            if o_fin_list is None or not isinstance(o_fin_list, list):
                o_fin_list = sc_live.get("opportunita", [])
            o_fin = "\n".join(o_fin_list)

            if locked_by == partecipante_id:
                st.success("Sei il Relatore. Puoi modificare la versione finale per il gruppo.")
                if st.button("🔓 Cedi il controllo", type="primary"):
                    aggiorna_scenario(sc_live["id"], locked_by_partecipante_id=None)
                    st.rerun()
                
                with st.form(f"form_finale_{sc_live['id']}"):
                    st.caption("I campi sono pre-compilati con la sintesi dell'AI. Modificali liberamente per rispecchiare la visione del gruppo.")
                    nuovo_t = st.text_input("Titolo Definitivo", value=t_fin)
                    nuovo_n = st.text_area("Narrativa Definitiva", value=n_fin, height=200)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Riportate le minacce condivise dal gruppo, una per riga.")
                        nuovo_m = st.text_area("Minacce (una per riga)", value=m_fin, height=150,
                                               help="Scrivi o modifica le minacce, una per riga. Puoi ricopiare quelle emerse nella chat individuale o aggiungerne di nuove.")
                    with c2:
                        st.caption("Riportate le opportunità condivise dal gruppo, una per riga.")
                        nuovo_o = st.text_area("Opportunità (una per riga)", value=o_fin, height=150,
                                               help="Scrivi o modifica le opportunità, una per riga. Puoi ricopiare quelle emerse nella chat individuale o aggiungerne di nuove.")
                    
                    if st.form_submit_button("💾 Salva Modifiche"):
                        aggiorna_scenario(
                            sc_live["id"],
                            titolo_finale=nuovo_t,
                            narrativa_finale=nuovo_n,
                            minacce_finale=[x.strip() for x in nuovo_m.split("\n") if x.strip()],
                            opportunita_finale=[x.strip() for x in nuovo_o.split("\n") if x.strip()]
                        )
                        st.rerun()

            else:
                if not locked_by:
                    st.info("Nessuno sta modificando la bozza. Prendi il controllo se il gruppo ti ha designato come relatore.")
                    if st.button("🙋‍♂️ Prendi il controllo per modificare", type="primary"):
                        aggiorna_scenario(sc_live["id"], locked_by_partecipante_id=partecipante_id)
                        st.rerun()
                else:
                    plist = get_partecipanti(sessione_id)
                    locker = next((p for p in plist if p["id"] == locked_by), None)
                    nome_locker = locker["nome"] if locker else "Un altro partecipante"
                    st.warning(f"🔒 **{nome_locker}** sta attualmente modificando la versione finale. Tu puoi solo visualizzare le modifiche aggiornate in tempo reale.")
                
                with st.container(border=True):
                    if t_fin: st.markdown(f"**Titolo Definitivo:** {t_fin}")
                    if n_fin: st.markdown(f"**Narrativa Definitiva:** {n_fin}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Minacce:**\n" + ("\n".join(f"- {x}" for x in m_fin_list) if m_fin_list else "- *Nessuna*"))
                    with c2:
                        st.markdown("**Opportunità:**\n" + ("\n".join(f"- {x}" for x in o_fin_list) if o_fin_list else "- *Nessuna*"))

        _sezione_definitiva()
        
        st.divider()
        
        # ── Sezione stato e azioni di gruppo (auto-aggiornante) ──
        @st.fragment(run_every=15)
        def _stato_gruppo():
            # Re-fetch fresh data
            sessione_live = get_sessione_by_id(sessione_id)
            stato_live = sessione_live.get("stato") if sessione_live else stato
            sc_stato = get_scenario(sc["id"])
            
            if stato_live == "concluso":
                # ── SESSIONE CONCLUSA: mostra report ──
                st.success("🎉 Sessione completamente terminata! Ottimo lavoro.")
                st.markdown("---")
                st.markdown("### 📄 Report Finale")
                st.info("Scarica il Report Finale completo con tutti gli scenari discussi oggi.")
                
                from lib.database import get_fenomeni, get_voti_aggregati, get_partecipanti as _gp_pdf
                from lib.pdf_export import st_scarica_pdf_report_finale
                
                fenomeni = get_fenomeni(sessione_id)
                voti = get_voti_aggregati(sessione_id)
                _par_pdf = _gp_pdf(sessione_id)
                st_scarica_pdf_report_finale(sessione_live, get_scenari(sessione_id), fenomeni, voti, partecipanti=_par_pdf)
                
            elif sc_stato and sc_stato.get("step_corrente") == "concluso":
                # ── GRUPPO HA DICHIARATO CONCLUSO, attende facilitatore ──
                st.success("🏁 Avete dichiarato concluso il lavoro di gruppo!")
                st.info("⏳ In attesa che il **facilitatore** chiuda ufficialmente la sessione per accedere al Report Finale.")
                
            else:
                # ── LAVORO DI GRUPPO IN CORSO ──
                st.warning("Assicuratevi che la Versione Definitiva sia pronta prima di dichiarare concluso il lavoro.")
                if st.button("✅ Dichiara Lavoro di Gruppo Concluso", type="primary", use_container_width=True, key="btn_conclude_gruppo"):
                    aggiorna_scenario(sc_stato["id"], step_corrente="concluso", locked_by_partecipante_id=None)
                    st.rerun(scope="app")
            
            st.divider()
            if st.button("🔄 Aggiorna Pagina", key="btn_refresh_gruppo"):
                st.rerun(scope="app")
        
        _stato_gruppo()

    with tab_personale:
        sc_indiv = get_scenario_individuale(sessione_id, partecipante_id)
        if not sc_indiv:
            st.info("Nessun lavoro individuale trovato.")
        else:
            from lib.pdf_export import st_scarica_pdf_scenario_individuale
            st.markdown("### 📝 Il Tuo Scenario Personale")
            st.info("Questo è il lavoro che hai sviluppato individualmente con l'agente. Rimane accessibile per aiutarti durante la discussione di gruppo.")
            st_scarica_pdf_scenario_individuale(sc_indiv, sessione, nome)
            st.divider()
            
            if sc_indiv.get("titolo"):
                st.markdown(f"**🏷️ Titolo:** {sc_indiv['titolo']}")
            if sc_indiv.get("narrativa"):
                st.markdown("**Bozza:**")
                st.markdown(sc_indiv["narrativa"])
            
            if sc_indiv.get("minacce") or sc_indiv.get("opportunita"):
                c1, c2 = st.columns(2)
                with c1:
                    if sc_indiv.get("minacce"):
                        st.markdown("**⚠️ Minacce:**\n" + "\n".join(f"- {m}" for m in sc_indiv["minacce"]))
                with c2:
                    if sc_indiv.get("opportunita"):
                        st.markdown("**✨ Opportunità:**\n" + "\n".join(f"- {o}" for o in sc_indiv["opportunita"]))
                        
            if sc_indiv.get("key_points_data"):
                st.markdown("**Key Points esplorati:**")
                for kp, risposta in sc_indiv["key_points_data"].items():
                    st.markdown(f"- **{kp}:** {risposta}")

else:
    col_chat, col_panel = st.columns([3, 2])
    
    # ── Chat ──────────────────────────────────────────────────
    with col_chat:
        st.markdown("### 💬 Conversazione Autonoma con l'Agente")

        messaggi = get_messaggi(sc["id"])
    
        # Avvia agente se nessun messaggio
        if not messaggi and sc["step_corrente"] == "intro":
            with st.spinner("L'agente si sta preparando per il tuo lavoro individuale..."):
                avvia_scenario(sc, sessione)
                st.rerun()
    
        # Mostra chat
        chat_container = st.container(height=450)
        with chat_container:
            for msg in messaggi:
                contenuto = msg["contenuto"]
                # Safety net: se il contenuto salvato è JSON grezzo, estrae il campo testo
                if contenuto and contenuto.strip().startswith('{') and '"testo"' in contenuto:
                    try:
                        contenuto = _json.loads(contenuto).get("testo") or contenuto
                    except Exception:
                        m = re.search(r'"testo"\s*:\s*"((?:[^"\\]|\\.)*)"', contenuto)
                        if m:
                            contenuto = m.group(1).replace('\\"', '"').replace('\\n', '\n')
                if msg["ruolo"] == "assistant":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(contenuto)
                elif msg["ruolo"] == "user":
                    with st.chat_message("user", avatar="🙋"):
                        st.markdown(contenuto)
    
        # Avviso e bottone se l'agente non ha ancora risposto all'ultimo messaggio
        if messaggi and messaggi[-1]["ruolo"] == "user" and sc["step_corrente"] != "concluso":
            col_warn, col_btn = st.columns([3, 1])
            with col_warn:
                st.warning("⚠️ L'agente non ha ancora risposto.")
            with col_btn:
                if st.button("🔔 Sollecita", use_container_width=True):
                    with st.spinner("L'agente sta elaborando..."):
                        invia_messaggio(sc, sessione, "[continua]")
                    st.rerun()

        # Banner contestuale per opportunità
        if sc["step_corrente"] == "opportunita":
            st.info("💡 **Fase: Opportunità** — L'agente ti chiederà quali opportunità vedi in questo scenario. Scrivile qui sotto nella chat, puoi elencarle tutte insieme o una alla volta.")

        # Input risposta gruppo
        if sc["step_corrente"] != "concluso":
            testo = st.chat_input(
                "Scrivi la tua riflessione personale...",
                key=f"chat_par_{sc['id']}",
            )
            if testo:
                from lib.database import aggiungi_messaggio
                aggiungi_messaggio(sc["id"], "user", testo)
                with st.chat_message("user", avatar="🙋"):
                    st.markdown(testo)

                with st.spinner("L'agente sta elaborando..."):
                    _, nuovo_step = invia_messaggio(sc, sessione, testo)
                st.rerun()

            # ── Progress tracker ──────────────────────────────
            _kps_sessione = sessione.get("key_points") or []
            _kpd = sc.get("key_points_data") or {}
            _kps_esplorati = sum(1 for kp in _kps_sessione if kp in _kpd and _kpd[kp])

            _STEP_TRACKER = [
                ("key_points", f"Key Points ({_kps_esplorati}/{len(_kps_sessione)})"),
                ("narrativa", "Narrativa"),
                ("titolo", "Titolo"),
                ("minacce", "Minacce"),
                ("opportunita", "Opportunità"),
            ]
            _step_c = sc["step_corrente"]
            try:
                _cur_idx = [s[0] for s in _STEP_TRACKER].index(_step_c)
            except ValueError:
                _cur_idx = len(_STEP_TRACKER) if _step_c == "concluso" else -1

            _pills = ""
            for _i, (_sid, _label) in enumerate(_STEP_TRACKER):
                if _i < _cur_idx or _step_c == "concluso":
                    _pills += f'<div style="background:#22c55e;color:white;border-radius:999px;padding:4px 12px;font-size:0.75rem;font-weight:600;">✓ {_label}</div>'
                elif _i == _cur_idx:
                    _pills += f'<div style="background:#3b82f6;color:white;border-radius:999px;padding:4px 12px;font-size:0.75rem;font-weight:600;">● {_label}</div>'
                else:
                    _pills += f'<div style="background:#f3f4f6;color:#9ca3af;border-radius:999px;padding:4px 12px;font-size:0.75rem;">○ {_label}</div>'
                if _i < len(_STEP_TRACKER) - 1:
                    _pills += '<div style="color:#d1d5db;font-size:0.9rem;line-height:1;">→</div>'

            components.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:transparent;">
<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px 0;">
  {_pills}
</div></body></html>""", height=56)

            st.divider()
            st.caption("Quando hai finito di fornire idee a Claude e ti ritieni soddisfatto/a per il tuo quadrante:")
            if not st.session_state.get("confirm_concluso"):
                if st.button("🏁 Dichiara Lavoro Individuale Concluso", type="primary", use_container_width=True):
                    st.session_state["confirm_concluso"] = True
                    st.rerun()
            else:
                st.warning("⚠️ Sei sicuro/a? Non potrai più continuare la conversazione con l'agente.")
                col_si, col_no = st.columns(2)
                with col_si:
                    if st.button("✅ Sì, ho finito", type="primary", use_container_width=True, key="btn_concluso_si"):
                        aggiorna_scenario(sc["id"], step_corrente="concluso")
                        st.session_state["confirm_concluso"] = False
                        st.rerun()
                with col_no:
                    if st.button("↩️ No, continuo", use_container_width=True, key="btn_concluso_no"):
                        st.session_state["confirm_concluso"] = False
                        st.rerun()
        else:
            st.success("🎉 Scenario Individuale completato! Ottimo lavoro.")
            st.info("Attendi che tutti i componenti finiscano. Poi il facilitatore genererà la Bozza Consolidata in cui discuterete in Gruppo!")
            
            # Auto-aggiornamento durante l'attesa per saltare al gruppo appena attivato
            @st.fragment(run_every=15)
            def poll_group():
                ss = get_sessione_by_id(sessione_id)
                if ss and ss.get("stato") in ("scenario_planning_gruppo", "concluso"):
                    st.rerun(scope="app")
            poll_group()
    
    # ── Pannello scenario in costruzione ─────────────────────
    with col_panel:
        scenario_id_for_panel = sc["id"]
        
        @st.fragment(run_every=20)
        def _pannello_scenario():
            sc_live = get_scenario(scenario_id_for_panel)
            if not sc_live:
                return
    
            with st.container(border=True):
                st.markdown("##### 📝 Scenario in costruzione")
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
    
                kp_data = sc_live.get("key_points_data") or {}
                kps_sessione = sessione.get("key_points") or []
                kp_mostrabili = [(kp, kp_data[kp]) for kp in kps_sessione if kp in kp_data and kp_data[kp]]
                if kp_mostrabili:
                    with st.expander(f"🔍 Temi esplorati ({len(kp_mostrabili)}/{len(kps_sessione)})", expanded=False):
                        for kp, risposta in kp_mostrabili:
                            st.markdown(f"- **{kp}:** {risposta}")
    
                if not any([
                    sc_live.get("titolo"),
                    sc_live.get("narrativa"),
                    sc_live.get("minacce"),
                    sc_live.get("opportunita"),
                ]):
                    st.info("Il tuo piano personale si costruirà dialogando con l'agente.")
            
            if st.button("🔄 Aggiorna Piano", key="btn_refresh_panel", use_container_width=True):
                st.rerun(scope="app")
    
        _pannello_scenario()


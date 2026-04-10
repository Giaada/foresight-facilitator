import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import io
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import (
    get_sessione_by_id, aggiorna_sessione, get_fenomeni,
    aggiungi_fenomeno, elimina_fenomeno, aggiorna_fenomeno, crea_sessione, lista_sessioni,
    elimina_sessione, get_modelli, crea_modello, elimina_modello, get_tutti_fenomeni_unici,
    get_partecipanti, get_voti_aggregati, get_scenari, get_scenari_individuali, get_messaggi
)


def esporta_sessione_json(sid):
    """Raccoglie tutti i dati di una sessione e li restituisce come stringa JSON."""
    sessione = get_sessione_by_id(sid)
    if not sessione:
        return None
    fenomeni = get_fenomeni(sid)
    partecipanti = get_partecipanti(sid)
    voti_aggregati = get_voti_aggregati(sid)
    scenari = get_scenari(sid)
    scenari_individuali = get_scenari_individuali(sid)

    # Aggiungi messaggi per ogni scenario individuale
    for s in scenari_individuali:
        s["messaggi"] = get_messaggi(s["id"])
    for s in scenari:
        s["messaggi"] = get_messaggi(s["id"])

    # Mappa fenomeno_id → testo per i voti aggregati
    fen_map = {f["id"]: f["testo"] for f in fenomeni}
    voti_leggibili = [
        {
            "fenomeno": fen_map.get(v["fenomeno_id"], f"#{v['fenomeno_id']}"),
            "media_posizione": round(float(v["media_posizione"]), 2),
            "n_voti": v["conteggio"],
        }
        for v in (voti_aggregati or [])
    ]

    export = {
        "sessione": dict(sessione),
        "fenomeni": [dict(f) for f in fenomeni],
        "partecipanti": [dict(p) for p in partecipanti],
        "ranking_aggregato": voti_leggibili,
        "scenari_gruppo": [dict(s) for s in scenari],
        "scenari_individuali": [dict(s) for s in scenari_individuali],
    }
    return json.dumps(export, ensure_ascii=False, indent=2, default=str)

check_facilitatore()

# ── Nessuna sessione attiva: home del facilitatore ────────
if not st.session_state.get("sessione_id"):

    st.title("⚙️ Foresight Facilitator — Area Facilitatore")
    st.markdown("Crea una nuova sessione oppure apri una sessione esistente.")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Nuova Sessione",
        "📋 Carica Modello",
        "💾 Gestione Modelli",
        "📂 Sessioni Esistenti",
        "🔍 Visualizza da JSON",
    ])

    # ── Nuova sessione manuale ───────────────────────────
    with tab1:
        st.subheader("➕ Nuova sessione manuale")
        with st.form("nuova_sessione", clear_on_submit=False):
            domanda = st.text_area(
                "Domanda di ricerca *",
                placeholder="Es. Come evolverà il sistema sanitario nei prossimi 10 anni?",
                height=100,
            )
            frame = st.text_input(
                "Orizzonte temporale *",
                placeholder="Es. 2035, prossimi 10 anni, 2030–2040",
            )
            st.markdown("**Key Points** (uno per riga)")
            st.caption("Dimensioni che ogni scenario dovrà esplorare")
            kp_raw = st.text_area(
                "Key points",
                placeholder="Tecnologia\nLavoro\nGovernance\nAmbiente",
                height=100,
                label_visibility="collapsed",
            )
            st.markdown("**Fenomeni / Trend iniziali** (uno per riga)")
            st.caption("Potrai aggiungerne altri nella fase successiva")
            fenomeni_raw = st.text_area(
                "Fenomeni",
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
                st.rerun()

    # ── Carica da Modello ────────────────────────────────
    with tab2:
        st.subheader("📋 Avvia da Modello Creato")
        modelli = get_modelli()
        if not modelli:
            st.info("Nessun modello salvato. Puoi crearne uno nel tab 'Gestione Modelli'.")
        else:
            with st.form("avvia_da_modello"):
                st.markdown("Seleziona un modello per inizializzare istantaneamente una nuova sessione con tutti i suoi parametri preconfigurati. Verrà generato in automatico un nuovo Codice PIN di accesso per i partecipanti.")
                mod_opzioni = {m["id"]: m for m in modelli}
                mod_scelto_id = st.selectbox(
                    "Scegli il Modello",
                    options=list(mod_opzioni.keys()),
                    format_func=lambda x: f"{mod_opzioni[x]['nome']} ({mod_opzioni[x]['domanda_ricerca'][:50]}...)"
                )
                submitted_mod = st.form_submit_button("🚀 Avvia Nuova Sessione da Modello", type="primary")
            
            if submitted_mod and mod_scelto_id:
                m_data = mod_opzioni[mod_scelto_id]
                f_raw = m_data.get("fenomeni_raw", "")
                f_list = []
                for f_line in f_raw.splitlines():
                    f_line = f_line.strip()
                    if not f_line:
                        continue
                    if "|" in f_line:
                        parts = f_line.split("|", 1)
                        f_list.append({"testo": parts[0].strip(), "descrizione": parts[1].strip()})
                    else:
                        f_list.append({"testo": f_line})
                sid = crea_sessione(m_data["domanda_ricerca"], m_data["frame_temporale"], m_data["key_points"], f_list)
                st.session_state["sessione_id"] = sid
                st.success("Sessione avviata dal modello con successo!")
                st.rerun()

    # ── Gestione Modelli ─────────────────────────────────
    with tab3:
        st.subheader("💾 Crea Nuovo Modello")
        st.caption("Configura un setup riutilizzabile su cui basare infinite sessioni future.")

        if "nmod_n_fenomeni" not in st.session_state:
            st.session_state.nmod_n_fenomeni = 1
        if "nmod_file_upload_key" not in st.session_state:
            st.session_state.nmod_file_upload_key = 0

        # Applica i fenomeni importati da file PRIMA che i widget vengano renderizzati
        if "nmod_import_pending" in st.session_state:
            righe_pending = st.session_state.pop("nmod_import_pending")
            esistenti = []
            for i in range(st.session_state.nmod_n_fenomeni):
                t = st.session_state.get(f"nmod_t_{i}", "").strip()
                d = st.session_state.get(f"nmod_d_{i}", "").strip()
                if t:
                    esistenti.append((t, d))
            tutti = esistenti + righe_pending
            st.session_state.nmod_n_fenomeni = len(tutti) if tutti else 1
            for i, (t, d) in enumerate(tutti):
                st.session_state[f"nmod_t_{i}"] = t
                st.session_state[f"nmod_d_{i}"] = d

        st.text_input("Nome Modello *", placeholder="Es. Workshop Energia 2050 - Base", key="nmod_titolo")
        st.text_area("Domanda di ricerca *", height=80, key="nmod_domanda")
        st.text_input("Orizzonte temporale *", key="nmod_frame")
        st.markdown("**Key Points** (uno per riga)")
        st.text_area("Key points", height=60, label_visibility="collapsed",
                     placeholder="Tecnologia\nLavoro\nGovernance\nAmbiente", key="nmod_kp")

        st.markdown("**Fenomeni / Trend iniziali**")
        col_h1, col_h2, _ = st.columns([4, 4, 1])
        with col_h1:
            st.caption("Nome")
        with col_h2:
            st.caption("Descrizione (opzionale)")

        n_fen = st.session_state.nmod_n_fenomeni
        for i in range(n_fen):
            cols = st.columns([4, 4, 1])
            with cols[0]:
                st.text_input("Nome", key=f"nmod_t_{i}",
                              placeholder="Es. Intelligenza Artificiale generativa",
                              label_visibility="collapsed")
            with cols[1]:
                st.text_input("Descrizione", key=f"nmod_d_{i}",
                              placeholder="Breve descrizione del fenomeno...",
                              label_visibility="collapsed")
            with cols[2]:
                if n_fen > 1 and st.button("🗑️", key=f"del_nmod_{i}"):
                    for j in range(i, n_fen - 1):
                        st.session_state[f"nmod_t_{j}"] = st.session_state.get(f"nmod_t_{j+1}", "")
                        st.session_state[f"nmod_d_{j}"] = st.session_state.get(f"nmod_d_{j+1}", "")
                    st.session_state.nmod_n_fenomeni -= 1
                    st.rerun()

        if st.button("➕ Aggiungi fenomeno", key="nmod_add"):
            st.session_state.nmod_n_fenomeni += 1
            st.rerun()

        file_upload = st.file_uploader(
            "📂 Carica file .xlsx / .csv",
            type=["xlsx", "xls", "csv"],
            key=f"nmod_file_upload_{st.session_state.nmod_file_upload_key}",
            help="Il file deve avere due colonne: la prima con il nome del fenomeno, la seconda con la descrizione (opzionale)."
        )
        if file_upload is not None:
            try:
                if file_upload.name.endswith(".csv"):
                    df = pd.read_csv(file_upload, header=0)
                else:
                    df = pd.read_excel(file_upload, header=0)
                df = df.dropna(subset=[df.columns[0]])
                righe = []
                for _, row in df.iterrows():
                    testo = str(row.iloc[0]).strip()
                    descrizione = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    if testo and testo.lower() != "nan":
                        righe.append((testo, descrizione))
                if righe:
                    st.session_state.nmod_import_pending = righe
                    st.session_state.nmod_file_upload_key += 1  # resetta il file uploader
                    st.rerun()
                else:
                    st.warning("Il file non contiene righe valide.")
            except Exception as e:
                st.error(f"Errore nel leggere il file: {e}")

        if st.button("Salva Modello", type="primary", use_container_width=True, key="nmod_save"):
            titolo = st.session_state.get("nmod_titolo", "").strip()
            dom = st.session_state.get("nmod_domanda", "").strip()
            frame = st.session_state.get("nmod_frame", "").strip()
            if not titolo or not dom or not frame:
                st.error("Nome Modello, Domanda e Orizzonte sono campi obbligatori.")
            else:
                kp_raw = st.session_state.get("nmod_kp", "")
                key_points = [k.strip() for k in kp_raw.strip().splitlines() if k.strip()]
                fen_lines = []
                for i in range(n_fen):
                    t = st.session_state.get(f"nmod_t_{i}", "").strip()
                    d = st.session_state.get(f"nmod_d_{i}", "").strip()
                    if t:
                        fen_lines.append(f"{t}|{d}" if d else t)
                crea_modello(titolo, dom, frame, key_points, "\n".join(fen_lines))
                st.success(f"Modello '{titolo}' salvato con successo!")
                st.session_state.nmod_n_fenomeni = 1
                for i in range(50):
                    st.session_state.pop(f"nmod_t_{i}", None)
                    st.session_state.pop(f"nmod_d_{i}", None)
                st.rerun()
                
        st.divider()
        st.subheader("🗑️ Cronologia Modelli")
        mod_av = get_modelli()
        if not mod_av:
            st.write("Ancora nessun modello salvato.")
        for m in mod_av:
            with st.container(border=True):
                mc1, mc2 = st.columns([5, 1])
                with mc1:
                    st.markdown(f"**{m['nome']}**")
                    n_fen_mod = len([l for l in m.get("fenomeni_raw", "").splitlines() if l.strip()])
                    st.caption(f"{m['domanda_ricerca'][:70]}... | 🕐 {m['frame_temporale']} | 📋 {n_fen_mod} fenomeni")
                with mc2:
                    if st.button("Elimina", key=f"del_mod_{m['id']}", help="Elimina in modo definitivo"):
                        elimina_modello(m['id'])
                        st.rerun()

    # ── Sessioni esistenti ────────────────────────────────
    with tab4:
        st.subheader("📂 Sessioni attive / passate")
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
                    col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
                    with col_a:
                        codice_str = f" · `{s['codice']}`" if s.get("codice") else ""
                        st.markdown(f"**#{s['id']}**{codice_str} {emoji} `{s['stato']}`")
                        st.caption(f"*{s['domanda_ricerca'][:80]}{'...' if len(s['domanda_ricerca']) > 80 else ''}*")
                        st.caption(f"🕐 {s['frame_temporale']} · {s['created_at'][:10]}")
                    with col_b:
                        if st.button("Apri", key=f"apri_{s['id']}", use_container_width=True):
                            st.session_state["sessione_id"] = s["id"]
                            st.rerun()
                    with col_c:
                        json_str = esporta_sessione_json(s["id"])
                        if json_str:
                            nome_file = f"sessione_{s['id']}_{s.get('codice','')}.json"
                            st.download_button(
                                "📥 JSON",
                                data=json_str,
                                file_name=nome_file,
                                mime="application/json",
                                key=f"exp_{s['id']}",
                                use_container_width=True,
                            )
                    with col_d:
                        if st.button("🗑️", key=f"del_sess_{s['id']}", use_container_width=True, help="Elimina sessione e tutti i dati"):
                            st.session_state[f"confirm_del_{s['id']}"] = True
                            st.rerun()

                # Conferma eliminazione (appare sotto il container)
                if st.session_state.get(f"confirm_del_{s['id']}"):
                    st.warning(f"⚠️ Eliminare la sessione **#{s['id']}** e tutti i suoi dati (partecipanti, voti, scenari)? Operazione irreversibile.")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Sì, elimina", key=f"yes_del_{s['id']}", type="primary", use_container_width=True):
                            elimina_sessione(s["id"])
                            st.session_state.pop(f"confirm_del_{s['id']}", None)
                            st.rerun()
                    with col_no:
                        if st.button("Annulla", key=f"no_del_{s['id']}", use_container_width=True):
                            st.session_state.pop(f"confirm_del_{s['id']}", None)
                            st.rerun()
    # ── Visualizza da JSON ────────────────────────────────
    with tab5:
        st.subheader("🔍 Visualizza sessione da file JSON")
        st.caption("Carica un file JSON esportato per consultare i risultati in sola lettura.")

        uploaded = st.file_uploader("Carica file JSON", type=["json"], key="json_viewer_upload")
        if uploaded:
            try:
                dati = json.loads(uploaded.read())
            except Exception as e:
                st.error(f"File JSON non valido: {e}")
                dati = None

            if dati:
                sess = dati.get("sessione", {})
                st.markdown(f"## 📋 {sess.get('domanda_ricerca', '—')}")
                st.markdown(f"**Orizzonte:** {sess.get('frame_temporale', '—')} · **Stato:** `{sess.get('stato', '—')}` · **Codice:** `{sess.get('codice', '—')}`")

                kp = sess.get("key_points", [])
                if isinstance(kp, str):
                    try: kp = json.loads(kp)
                    except: kp = []
                if kp:
                    st.markdown("**Key Points:** " + " · ".join(f"`{k}`" for k in kp))

                st.divider()

                col1, col2 = st.columns(2)

                with col1:
                    fenomeni = dati.get("fenomeni", [])
                    st.markdown(f"### 📋 Fenomeni ({len(fenomeni)})")
                    for f in fenomeni:
                        st.markdown(f"**{f['testo']}**")
                        if f.get("descrizione"):
                            st.caption(f["descrizione"])

                with col2:
                    ranking = dati.get("ranking_aggregato", [])
                    st.markdown(f"### 📊 Ranking Aggregato ({len(ranking)} fenomeni votati)")
                    COLORI = ["#7C3AED","#2563EB","#0D9488","#9CA3AF"]
                    n = len(ranking)
                    for i, v in enumerate(ranking):
                        tier = min(int(i / n * 4), 3) if n else 0
                        colore = COLORI[tier]
                        st.markdown(
                            f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:4px'>"
                            f"<span style='background:{colore};color:white;border-radius:50%;width:22px;height:22px;"
                            f"display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700'>{i+1}</span>"
                            f"<span style='font-size:13px'>{v['fenomeno']}</span>"
                            f"<span style='font-size:11px;color:#9CA3AF;margin-left:auto'>media {v['media_posizione']} · {v['n_voti']} voti</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                st.divider()

                # Partecipanti
                partecipanti = dati.get("partecipanti", [])
                st.markdown(f"### 👥 Partecipanti ({len(partecipanti)})")
                votanti = sum(1 for p in partecipanti if p.get("votato"))
                st.caption(f"{votanti} su {len(partecipanti)} hanno votato")
                st.dataframe(
                    [{"Nome": p["nome"], "Votato": "✅" if p.get("votato") else "⏳"} for p in partecipanti],
                    use_container_width=True, hide_index=True
                )

                # Scenari
                scenari = dati.get("scenari_gruppo", [])
                sc_ind = dati.get("scenari_individuali", [])
                if scenari or sc_ind:
                    st.divider()
                    st.markdown(f"### 🗺️ Scenari")

                    if scenari:
                        st.markdown("**Scenari di gruppo:**")
                        for s in scenari:
                            with st.expander(f"Scenario {s.get('numero')} · `{s.get('quadrante')}` — {s.get('titolo') or 'senza titolo'}"):
                                if s.get("narrativa"):
                                    st.markdown(s["narrativa"])
                                c1, c2 = st.columns(2)
                                with c1:
                                    if s.get("minacce"):
                                        st.markdown("**⚠️ Minacce:**\n" + "\n".join(f"- {m}" for m in s["minacce"]))
                                with c2:
                                    if s.get("opportunita"):
                                        st.markdown("**✨ Opportunità:**\n" + "\n".join(f"- {o}" for o in s["opportunita"]))

                    if sc_ind:
                        st.markdown("**Scenari individuali:**")
                        for s in sc_ind:
                            label = f"Scenario {s.get('numero')} · {s.get('titolo') or 'senza titolo'}"
                            with st.expander(label):
                                if s.get("narrativa"):
                                    st.markdown(s["narrativa"])
                                c1, c2 = st.columns(2)
                                with c1:
                                    if s.get("minacce"):
                                        st.markdown("**⚠️ Minacce:**\n" + "\n".join(f"- {m}" for m in s["minacce"]))
                                with c2:
                                    if s.get("opportunita"):
                                        st.markdown("**✨ Opportunità:**\n" + "\n".join(f"- {o}" for o in s["opportunita"]))

    st.stop()

# ── Sessione attiva ───────────────────────────────────────
sid = st.session_state["sessione_id"]
sessione = get_sessione_by_id(sid)

if not sessione:
    st.error("Sessione non trovata.")
    del st.session_state["sessione_id"]
    st.rerun()

st.markdown(f"### ⚙️ Setup — Sessione #{sid}")
codice_display = sessione.get("codice") or "—"
st.caption(f"🔭 {sessione['frame_temporale']} · Stato: `{sessione['stato']}`")

with st.expander("📌 Domanda di ricerca", expanded=True):
    st.info(sessione["domanda_ricerca"])

st.divider()

col1, col2 = st.columns(2)

# ── Key Points ────────────────────────────────────────────
with col1:
    st.subheader("🎯 Key Points")
    st.caption("Dimensioni che ogni scenario dovrà esplorare nello Scenario Planning")

    kp_attuale = "\n".join(sessione["key_points"])
    kp_nuovo = st.text_area(
        "Un key point per riga",
        value=kp_attuale,
        height=150,
        label_visibility="collapsed",
    )
    if st.button("Salva Key Points", use_container_width=True):
        nuovi = [k.strip() for k in kp_nuovo.strip().splitlines() if k.strip()]
        aggiorna_sessione(sid, key_points=nuovi)
        st.success("Key points aggiornati!")
        st.rerun()

    if sessione["key_points"]:
        st.markdown("**Key points correnti:**")
        for kp in sessione["key_points"]:
            st.markdown(f"- {kp}")

# ── Fenomeni ──────────────────────────────────────────────
with col2:
    st.subheader("📋 Fenomeni / Trend")
    st.caption("Lista dei fenomeni che i partecipanti valuteranno nella fase di Horizon Scanning")

    fenomeni = get_fenomeni(sid)
    st.markdown(f"**{len(fenomeni)} fenomeni inseriti:**")

    for f in fenomeni:
        col_f, col_edit, col_del = st.columns([5, 1, 1])
        with col_f:
            st.markdown(f"**{f['testo']}**")
            if f.get("descrizione"):
                st.caption(f["descrizione"])
        with col_edit:
            with st.popover("✏️"):
                edit_testo = st.text_input("Testo", value=f["testo"], key=f"et_{f['id']}")
                edit_desc = st.text_area("Descrizione", value=f.get("descrizione", ""), key=f"ed_{f['id']}")
                if st.button("Salva", key=f"esave_{f['id']}", type="primary"):
                    aggiorna_fenomeno(f["id"], edit_testo.strip(), edit_desc.strip())
                    st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{f['id']}", help="Elimina"):
                elimina_fenomeno(f["id"])
                st.rerun()

    st.divider()

    _add_submitted = False
    with st.form("aggiungi_fenomeno_setup", clear_on_submit=True):
        st.markdown("**Aggiungi fenomeno**")
        nuovo_testo = st.text_input("Testo del fenomeno", placeholder="Es. Intelligenza Artificiale generativa")
        nuova_descr = st.text_input("Descrizione (opzionale)", placeholder="Breve spiegazione...")
        _add_submitted = st.form_submit_button("Aggiungi", use_container_width=True)

    if _add_submitted:
        if nuovo_testo.strip():
            aggiungi_fenomeno(sid, nuovo_testo.strip(), nuova_descr.strip())
        st.rerun()

    # Menu a tendina per aggiungere fenomeni già usati in altre sessioni
    catalogo = get_tutti_fenomeni_unici()
    # Filtra quelli già presenti nella sessione corrente
    testi_presenti = {f["testo"].strip().lower() for f in fenomeni}
    catalogo_filtrato = [c for c in catalogo if c["testo"].strip().lower() not in testi_presenti]
    if catalogo_filtrato:
        st.markdown("**Oppure scegli da fenomeni già usati:**")
        opzioni_label = [f"{c['testo']}" + (f" — {c['descrizione'][:50]}..." if len(c.get('descrizione','')) > 50 else (f" — {c['descrizione']}" if c.get('descrizione') else "")) for c in catalogo_filtrato]
        sel = st.selectbox("Seleziona fenomeno esistente", options=range(len(catalogo_filtrato)), format_func=lambda i: opzioni_label[i], index=None, placeholder="Cerca tra i fenomeni...", key="sel_fenomeno_catalogo", label_visibility="collapsed")
        if sel is not None:
            if st.button("➕ Aggiungi questo fenomeno", key="btn_add_catalogo", use_container_width=True):
                scelto = catalogo_filtrato[sel]
                aggiungi_fenomeno(sid, scelto["testo"], scelto["descrizione"])
                st.rerun()

st.divider()

# ── Codice sessione ───────────────────────────────────────
st.markdown(
    f"""
    <div style="
        background-color: #d1fae5;
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
    ">
        <div style="font-size: 1.1em; color: #065f46; margin-bottom: 8px;">
            Codice sessione per i partecipanti
        </div>
        <div style="font-size: 3em; font-weight: 900; letter-spacing: 0.3em; color: #064e3b;">
            {codice_display}
        </div>
        <div style="font-size: 0.9em; color: #065f46; margin-top: 8px;">
            I partecipanti inseriscono questo codice per accedere alla sessione
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Avvia ─────────────────────────────────────────────────
st.subheader("🚀 Avvia la sessione")

fenomeni_count = len(get_fenomeni(sid))
kp_count = len(sessione["key_points"])

col_check1, col_check2, col_check3 = st.columns(3)
with col_check1:
    stato_f = "✅" if fenomeni_count >= 2 else "⚠️"
    st.metric(f"{stato_f} Fenomeni", fenomeni_count, help="Minimo 2 consigliati")
with col_check2:
    stato_kp = "✅" if kp_count >= 1 else "⚠️"
    st.metric(f"{stato_kp} Key Points", kp_count)
with col_check3:
    st.metric("📌 Orizzonte", sessione["frame_temporale"])

if st.button("▶️ Avvia Horizon Scanning", type="primary", use_container_width=True, disabled=fenomeni_count < 1):
    aggiorna_sessione(sid, stato="horizon_scanning")
    st.success("Sessione avviata! Vai alla pagina Horizon Scanning.")
    st.switch_page("pages/fac_hs.py")

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import (
    get_sessione_by_id, get_fenomeni, get_partecipanti,
    aggiungi_fenomeno, salva_voti, get_voti_aggregati
)

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
st.markdown("## 🔭 Horizon Scanning")
st.markdown(f"👤 Benvenuto/a, **{nome}**!")

with st.container(border=True):
    st.markdown(f"**Domanda di ricerca:** {sessione['domanda_ricerca']}")
    st.markdown(f"**Orizzonte temporale:** {sessione['frame_temporale']}")

st.divider()

# ── Controlla stato sessione ──────────────────────────────
stato = sessione.get("stato")

if stato == "setup":
    st.info("⏳ La sessione non è ancora iniziata. Attendi che il facilitatore avvii l'Horizon Scanning.")
    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

if stato not in ("horizon_scanning", "transizione", "scenario_planning", "concluso"):
    st.info("⏳ Attendi istruzioni dal facilitatore.")
    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

# ── Controlla se già votato ───────────────────────────────
# Ricarica stato partecipante dal DB
partecipanti_db = get_partecipanti(sessione_id)
par_db = next((p for p in partecipanti_db if p["id"] == partecipante_id), None)

if par_db and par_db.get("votato"):
    st.success("✅ Hai già inviato il tuo ranking!")

    if stato in ("scenario_planning", "concluso"):
        # Facilitatore ha avviato lo Scenario Planning → mostra link prominente
        st.markdown(
            """
            <div style="
                background: #ede9fe;
                border: 2px solid #7c3aed;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                margin: 16px 0;
            ">
                <div style="font-size:1.4em;font-weight:700;color:#4c1d95;margin-bottom:6px">
                    🗺️ Lo Scenario Planning è iniziato!
                </div>
                <div style="color:#5b21b6">
                    Il facilitatore ha avviato la fase successiva. Clicca il bottone per continuare.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶️ Vai allo Scenario Planning", type="primary", use_container_width=True):
            st.switch_page("pages/par_scenario.py")
    else:
        st.markdown("Grazie per aver partecipato alla fase di Horizon Scanning.")
        st.markdown("Attendi le istruzioni del facilitatore per la prossima fase.")

        # ── Classifica aggregata ──────────────────────────────
        @st.fragment(run_every=15)
        def _mostra_classifica():
            voti = get_voti_aggregati(sessione_id)
            fenomeni_map = {f["id"]: f for f in get_fenomeni(sessione_id)}
            partecipanti_db2 = get_partecipanti(sessione_id)
            n_votanti = sum(1 for p in partecipanti_db2 if p.get("votato"))
            n_totale = len(partecipanti_db2)

            st.divider()
            st.markdown(f"### 📊 Classifica aggregata")
            st.caption(f"Basata sui voti di {n_votanti} / {n_totale} partecipanti · si aggiorna automaticamente")

            if not voti:
                st.info("Nessun voto ancora registrato.")
                return

            COLORI = [
                ("#7C3AED", "#F5F3FF"),  # viola   — top 25%
                ("#2563EB", "#EFF6FF"),  # blu     — 25-50%
                ("#0D9488", "#ECFDF5"),  # teal    — 50-75%
                ("#9CA3AF", "#F9FAFB"),  # grigio  — bottom 25%
            ]

            n = len(voti)
            for i, v in enumerate(voti):
                tier = min(int(i / n * 4), 3)
                colore, sfondo = COLORI[tier]
                f_obj = fenomeni_map.get(v["fenomeno_id"], {})
                nome = f_obj.get("testo", f"Fenomeno #{v['fenomeno_id']}")
                desc = f_obj.get("descrizione", "")
                st.markdown(
                    f"""<div style="display:flex;align-items:center;gap:10px;
                        background:{sfondo};border-left:4px solid {colore};
                        border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                        <span style="min-width:26px;height:26px;border-radius:50%;
                            background:{colore};color:white;font-weight:700;
                            font-size:12px;display:flex;align-items:center;
                            justify-content:center;">{i+1}</span>
                        <div>
                            <div style="font-weight:600;font-size:13px;color:#111827">{nome}</div>
                            {"<div style='font-size:11px;color:#6B7280;margin-top:2px'>" + desc + "</div>" if desc else ""}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            # Auto-avanzamento a scenario planning
            s = get_sessione_by_id(sessione_id)
            if s and s.get("stato") in ("scenario_planning", "concluso"):
                st.rerun(scope="app")

        _mostra_classifica()
        if st.button("🔄 Aggiorna"):
            st.rerun()
    st.stop()

# ── Fase attiva: ranking fenomeni ─────────────────────────
fenomeni = get_fenomeni(sessione_id)

if not fenomeni:
    st.warning("Nessun fenomeno disponibile. Attendi che il facilitatore aggiunga i fenomeni.")
    if st.button("🔄 Aggiorna"):
        st.rerun()
    st.stop()

st.subheader("📊 Ordina i fenomeni per rilevanza")
st.caption("Trascina le carte per ordinarle dal più rilevante (in alto a sinistra) al meno rilevante.")

from lib.sortable_grid import sortable_grid

def fmt_fen(f):
    return f["testo"]

fenomeni_map = {fmt_fen(f): f for f in fenomeni}
fenomeni_testi = list(fenomeni_map.keys())
fenomeni_set = set(fenomeni_testi)

# Inizializza o resetta ranking se la sessione è cambiata
existing_items = st.session_state.get("ranking_items", [])
if not existing_items or not set(existing_items) & fenomeni_set:
    st.session_state["ranking_items"] = fenomeni_testi[:]

# Sincronizza: aggiungi fenomeni nuovi, rimuovi quelli eliminati
current = st.session_state["ranking_items"]
current = [t for t in current if t in fenomeni_set]
for t in fenomeni_testi:
    if t not in current:
        current.append(t)
st.session_state["ranking_items"] = current

# Costruisci items per il componente nell'ordine corrente
items_for_grid = [
    {"testo": t, "descrizione": (fenomeni_map.get(t) or {}).get("descrizione") or ""}
    for t in st.session_state["ranking_items"]
]

new_order = sortable_grid(items_for_grid, key="hs_grid")

if new_order is not None:
    # Applica il nuovo ordine mantenendo eventuali fenomeni non ancora nel componente
    new_set = set(new_order)
    for t in fenomeni_testi:
        if t not in new_set:
            new_order = list(new_order) + [t]
    new_order = [t for t in new_order if t in fenomeni_set]
    st.session_state["ranking_items"] = new_order

ranking_finale = st.session_state["ranking_items"]

st.divider()

# ── Aggiungi nuovo fenomeno ───────────────────────────────
st.subheader("➕ Proponi un nuovo fenomeno")
st.caption("Puoi aggiungere un fenomeno o trend che ritieni rilevante e non è ancora in lista.")

with st.form("aggiungi_fenomeno_par"):
    nuovo_testo = st.text_input(
        "Fenomeno / trend",
        placeholder="Es. Blockchain nella pubblica amministrazione",
        label_visibility="collapsed",
        key="input_nuovo_fenomeno",
    )
    _nuovo_submitted = st.form_submit_button("Aggiungi fenomeno", use_container_width=True)

if _nuovo_submitted:
    testo_pulito = nuovo_testo.strip()
    if testo_pulito:
        aggiungi_fenomeno(sessione_id, testo_pulito)
        # Prependi in cima (prima del rerun e della re-init del componente)
        st.session_state["ranking_items"] = [testo_pulito] + [
            t for t in st.session_state.get("ranking_items", []) if t != testo_pulito
        ]
        st.success(f"Fenomeno '{testo_pulito}' aggiunto!")
    else:
        st.warning("Inserisci il testo del fenomeno.")
    st.rerun()

st.divider()

# ── Conferma ranking ──────────────────────────────────────
st.subheader("✅ Conferma il tuo ranking")
st.caption("Una volta confermato, non potrai modificare il tuo voto.")

if st.button("Conferma il mio ranking", type="primary", use_container_width=True):
    def lfmt(f):
        return f["testo"]
    id_map = {lfmt(f): f["id"] for f in get_fenomeni(sessione_id)}
    ranking_voti = []
    for pos, testo in enumerate(ranking_finale):
        fid = id_map.get(testo)
        if fid:
            ranking_voti.append({"fenomeno_id": fid, "posizione": pos + 1})

    salva_voti(partecipante_id, ranking_voti)
    st.session_state["partecipante"] = {
        **st.session_state["partecipante"],
        "votato": 1,
    }
    st.success("Ranking confermato! Grazie per la tua partecipazione.")
    st.rerun()

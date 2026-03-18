import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import (
    get_sessione_by_id, get_fenomeni, get_partecipanti,
    aggiungi_fenomeno, salva_voti
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
st.markdown(f"## 🔭 Horizon Scanning")
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
    st.markdown("Grazie per aver partecipato alla fase di Horizon Scanning.")
    st.markdown("Attendi le istruzioni del facilitatore per la prossima fase.")
    if st.button("🔄 Aggiorna stato sessione"):
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
st.caption("Trascina i fenomeni per ordinarli dal più rilevante (in cima) al meno rilevante (in fondo) rispetto alla domanda di ricerca.")

# ── Drag & drop con streamlit-sortables ──────────────────
try:
    from streamlit_sortables import sort_items
    SORTABLE = True
except ImportError:
    SORTABLE = False

# Inizializza ordine in session state se non presente
fenomeni_testi = [f["testo"] for f in fenomeni]
if "ranking_items" not in st.session_state:
    st.session_state["ranking_items"] = fenomeni_testi
else:
    # Aggiungi eventuali nuovi fenomeni non ancora nella lista locale
    for testo in fenomeni_testi:
        if testo not in st.session_state["ranking_items"]:
            st.session_state["ranking_items"].append(testo)
    # Rimuovi fenomeni eliminati dal DB
    st.session_state["ranking_items"] = [
        t for t in st.session_state["ranking_items"] if t in fenomeni_testi
    ]

if SORTABLE:
    sorted_items = sort_items(
        st.session_state["ranking_items"],
        direction="vertical",
        key="sort_par_hs",
    )
    # Aggiorna state senza rerun (evita di perdere click sui bottoni)
    st.session_state["ranking_items"] = sorted_items

    st.markdown("**Ordine attuale (1 = più rilevante):**")
    for i, testo in enumerate(sorted_items):
        col_n, col_t = st.columns([1, 8])
        with col_n:
            color = "#4F46E5" if i < 3 else "#9CA3AF"
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>",
                unsafe_allow_html=True,
            )
        with col_t:
            st.markdown(f"{'**' if i < 3 else ''}{testo}{'**' if i < 3 else ''}")

    ranking_finale = sorted_items
else:
    st.info("💡 Drag & drop non disponibile. Usa i numeri per assegnare la priorità (1 = più rilevante).")
    nuovi_ordini = {}
    for f in fenomeni:
        nuovi_ordini[f["id"]] = st.number_input(
            f["testo"],
            min_value=1,
            max_value=len(fenomeni),
            value=fenomeni.index(f) + 1,
            key=f"prio_par_{f['id']}",
        )
    # Ordina per valore assegnato
    id_map = {f["testo"]: f["id"] for f in fenomeni}
    ordinato = sorted(nuovi_ordini.items(), key=lambda x: x[1])
    ranking_finale = [
        next(f["testo"] for f in fenomeni if f["id"] == fid)
        for fid, _ in ordinato
    ]

st.divider()

# ── Aggiungi nuovo fenomeno ───────────────────────────────
st.subheader("➕ Proponi un nuovo fenomeno")
st.caption("Puoi aggiungere un fenomeno o trend che ritieni rilevante e non è ancora in lista.")

with st.form("aggiungi_fenomeno_par"):
    nuovo_testo = st.text_input(
        "Fenomeno / trend",
        placeholder="Es. Blockchain nella pubblica amministrazione",
        label_visibility="collapsed",
    )
    _nuovo_submitted = st.form_submit_button("Aggiungi fenomeno", use_container_width=True)

if _nuovo_submitted:
    testo_pulito = nuovo_testo.strip()
    if testo_pulito:
        aggiungi_fenomeno(sessione_id, testo_pulito)
        # Prependi il nuovo fenomeno in cima al ranking locale
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
    # Costruisce lista di voti
    id_map = {f["testo"]: f["id"] for f in get_fenomeni(sessione_id)}
    ranking_voti = []
    for pos, testo in enumerate(ranking_finale):
        fid = id_map.get(testo)
        if fid:
            ranking_voti.append({"fenomeno_id": fid, "posizione": pos + 1})

    salva_voti(partecipante_id, ranking_voti)
    # Aggiorna session state locale
    st.session_state["partecipante"] = {
        **st.session_state["partecipante"],
        "votato": 1,
    }
    st.success("Ranking confermato! Grazie per la tua partecipazione.")
    st.rerun()

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import (
    get_sessione_by_id, aggiorna_sessione,
    get_scenari, get_scenario, aggiorna_scenario
)

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


@st.fragment(run_every=15)
def _overview_scenari():
    scenari = get_scenari(sid)
    if not scenari:
        st.info("Scenari non ancora creati. Torna alla Transizione e avvia lo Scenario Planning.")
        return

    st.subheader("📊 Stato scenari")
    ov_cols = st.columns(4)
    for i, sc in enumerate(scenari):
        with ov_cols[i]:
            step_idx = STEP_NUM.index(sc["step_corrente"]) if sc["step_corrente"] in STEP_NUM else 0
            progresso = step_idx / (len(STEP_NUM) - 1)
            with st.container(border=True):
                st.markdown(f"**Scenario {sc['numero']}** `{sc['quadrante']}`")
                titolo = sc.get("titolo") or "—"
                st.caption(f"*{titolo}*")
                st.progress(progresso, text=STEP_LABEL.get(sc["step_corrente"], sc["step_corrente"]))

    return scenari


_overview_scenari()

scenari = get_scenari(sid)

if not scenari:
    st.stop()

st.divider()

# ── Tabs per ogni scenario ────────────────────────────────
tab_labels = [
    f"Scenario {s['numero']} {'✅' if s['step_corrente'] == 'concluso' else ''}"
    for s in scenari
]
tabs = st.tabs(tab_labels)

for tab, scenario in zip(tabs, scenari):
    with tab:
        sc = get_scenario(scenario["id"])
        if not sc:
            continue

        # Descrizione quadrante
        d1 = sessione.get("driver1_nome", "Driver 1")
        d2 = sessione.get("driver2_nome", "Driver 2")
        asse_x = (
            sessione.get("driver1_pos") if sc["quadrante"][0] == "+" else sessione.get("driver1_neg")
        ) or d1
        asse_y = (
            sessione.get("driver2_pos") if sc["quadrante"][1] == "+" else sessione.get("driver2_neg")
        ) or d2
        st.markdown(f"**Quadrante:** `{sc['quadrante']}` — {asse_x} × {asse_y}")

        step_corrente = sc.get("step_corrente", "intro")
        st.info(f"Step corrente: **{STEP_LABEL.get(step_corrente, step_corrente)}**")

        col_info, col_edit = st.columns([3, 2])

        with col_info:
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

        with col_edit:
            st.markdown("**Modifica manuale**")
            titolo_edit = st.text_input(
                "Titolo scenario",
                value=sc.get("titolo") or "",
                key=f"titolo_{sc['id']}",
                placeholder="Es. Il Mondo Interconnesso",
            )
            if st.button("Salva titolo", key=f"salva_titolo_{sc['id']}"):
                aggiorna_scenario(sc["id"], titolo=titolo_edit)
                st.rerun()

            st.divider()
            st.markdown("**Avanza step manualmente**")
            step_options = STEP_NUM
            step_idx_cur = step_options.index(step_corrente) if step_corrente in step_options else 0
            nuovo_step = st.selectbox(
                "Step",
                options=step_options,
                index=step_idx_cur,
                format_func=lambda x: STEP_LABEL.get(x, x),
                key=f"step_sel_{sc['id']}",
            )
            if st.button("Imposta step", key=f"set_step_{sc['id']}"):
                aggiorna_scenario(sc["id"], step_corrente=nuovo_step)
                st.rerun()

st.divider()

# ── Chiudi sessione ───────────────────────────────────────
scenari_aggiornati = get_scenari(sid)
tutti_conclusi = all(s["step_corrente"] == "concluso" for s in scenari_aggiornati) if scenari_aggiornati else False

with st.container(border=True):
    if tutti_conclusi:
        st.success("Tutti gli scenari sono stati completati!")
    else:
        completati = sum(1 for s in scenari_aggiornati if s["step_corrente"] == "concluso")
        st.info(f"Scenari completati: {completati}/{len(scenari_aggiornati)}")
        st.checkbox("Forza chiusura sessione", key="forza_chiusura")

    can_close = tutti_conclusi or st.session_state.get("forza_chiusura", False)
    if st.button("✅ Chiudi sessione e vai al Report", type="primary", use_container_width=True, disabled=not can_close):
        aggiorna_sessione(sid, stato="concluso")
        st.switch_page("pages/fac_report.py")

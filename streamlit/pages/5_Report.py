import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_sessione, get_scenari, get_fenomeni
from lib.auth import check_auth

st.set_page_config(page_title="Report · Foresight Facilitator", page_icon="📄", layout="wide")
check_auth()

if "sessione_id" not in st.session_state:
    st.warning("Nessuna sessione selezionata.")
    st.page_link("app.py", label="← Torna alla home")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione(sid)
scenari = get_scenari(sid)
fenomeni = get_fenomeni(sid)

# ── Header ────────────────────────────────────────────────
st.markdown(f"# 📄 Report Finale — Sessione #{sid}")
st.caption(f"Generato il {sessione['created_at'][:10]}")
st.divider()

# ── Contesto ──────────────────────────────────────────────
st.subheader("📌 Contesto della sessione")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Domanda di ricerca**")
    st.info(sessione["domanda_ricerca"])
with col2:
    st.markdown("**Orizzonte temporale**")
    st.success(f"⏱️ {sessione['frame_temporale']}")

if sessione.get("driver1_nome") and sessione.get("driver2_nome"):
    st.markdown("**Driver principali**")
    dc1, dc2 = st.columns(2)
    with dc1:
        with st.container(border=True):
            st.markdown(f"**Driver 1 — {sessione['driver1_nome']}**")
            st.caption(f"+ {sessione.get('driver1_pos','—')} / − {sessione.get('driver1_neg','—')}")
    with dc2:
        with st.container(border=True):
            st.markdown(f"**Driver 2 — {sessione['driver2_nome']}**")
            st.caption(f"+ {sessione.get('driver2_pos','—')} / − {sessione.get('driver2_neg','—')}")

st.divider()

# ── Top fenomeni ──────────────────────────────────────────
st.subheader("🔭 Fenomeni prioritizzati")
for i, f in enumerate(fenomeni[:10]):
    col_n, col_t = st.columns([1, 9])
    with col_n:
        color = "#4F46E5" if i < 3 else "#6B7280"
        st.markdown(f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>", unsafe_allow_html=True)
    with col_t:
        peso = "**" if i < 3 else ""
        st.markdown(f"{peso}{f['testo']}{peso}")

st.divider()

# ── Matrice 2×2 ───────────────────────────────────────────
st.subheader("🗺️ Matrice degli Scenari")

if scenari and sessione.get("driver1_nome"):
    d1 = sessione["driver1_nome"]
    d2 = sessione["driver2_nome"]
    d1p = sessione.get("driver1_pos") or f"{d1} +"
    d1n = sessione.get("driver1_neg") or f"{d1} −"
    d2p = sessione.get("driver2_pos") or f"{d2} +"
    d2n = sessione.get("driver2_neg") or f"{d2} −"

    sc_map = {s["quadrante"]: s for s in scenari}

    st.markdown(f"<div style='text-align:center;color:#6B7280;font-size:0.85em'>↑ {d2p}</div>", unsafe_allow_html=True)

    m_col1, m_col2 = st.columns(2)
    for col, (q1, q2) in zip([m_col1, m_col2], [("-+", "++"), ("--", "+-")]):
        with col:
            for q in [q1, q2]:
                sc = sc_map.get(q)
                if sc:
                    with st.container(border=True):
                        titolo = sc.get("titolo") or f"Scenario {sc['numero']}"
                        st.markdown(f"**{titolo}** `{q}`")
                        asse_x = (d1p if q[0] == "+" else d1n)
                        asse_y = (d2p if q[1] == "+" else d2n)
                        st.caption(f"{asse_x} × {asse_y}")
                        if sc.get("narrativa"):
                            st.markdown(sc["narrativa"][:150] + ("..." if len(sc["narrativa"] or "") > 150 else ""))

    st.markdown(f"<div style='text-align:center;color:#6B7280;font-size:0.85em'>↓ {d2n}</div>", unsafe_allow_html=True)
    st.caption(f"← {d1n} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {d1p} →", unsafe_allow_html=True)

st.divider()

# ── Scenari completi ──────────────────────────────────────
st.subheader("📖 Scenari nel dettaglio")

for sc in scenari:
    titolo = sc.get("titolo") or f"Scenario {sc['numero']}"
    with st.expander(f"**{titolo}** — Quadrante `{sc['quadrante']}`", expanded=True):
        if sc.get("narrativa"):
            st.markdown("**Descrizione**")
            st.markdown(sc["narrativa"])

        if sc.get("key_points_data"):
            st.markdown("**Key Points esplorati**")
            for kp, ris in sc["key_points_data"].items():
                st.markdown(f"- **{kp}:** {ris}")

        col_m, col_o = st.columns(2)
        with col_m:
            if sc.get("minacce"):
                st.markdown("**⚠️ Minacce**")
                for m in sc["minacce"]:
                    st.markdown(f"- {m}")
        with col_o:
            if sc.get("opportunita"):
                st.markdown("**✨ Opportunità**")
                for o in sc["opportunita"]:
                    st.markdown(f"- {o}")

st.divider()

# ── Export ────────────────────────────────────────────────
st.subheader("💾 Esporta")

def genera_markdown():
    lines = [
        f"# Report Foresight — Sessione #{sid}",
        f"",
        f"**Domanda di ricerca:** {sessione['domanda_ricerca']}",
        f"**Orizzonte temporale:** {sessione['frame_temporale']}",
        f"",
        f"## Driver",
        f"- **Driver 1:** {sessione.get('driver1_nome','—')} ({sessione.get('driver1_pos','+')} / {sessione.get('driver1_neg','−')})",
        f"- **Driver 2:** {sessione.get('driver2_nome','—')} ({sessione.get('driver2_pos','+')} / {sessione.get('driver2_neg','−')})",
        f"",
        f"## Fenomeni prioritizzati",
    ]
    for i, f in enumerate(fenomeni):
        lines.append(f"{i+1}. {f['testo']}")

    lines.append("")
    lines.append("## Scenari")

    for sc in scenari:
        titolo = sc.get("titolo") or f"Scenario {sc['numero']}"
        lines += [
            f"",
            f"### {titolo} (Quadrante `{sc['quadrante']}`)",
        ]
        if sc.get("narrativa"):
            lines += [f"", sc["narrativa"]]
        if sc.get("minacce"):
            lines.append(f"")
            lines.append("**Minacce:**")
            for m in sc["minacce"]:
                lines.append(f"- {m}")
        if sc.get("opportunita"):
            lines.append(f"")
            lines.append("**Opportunità:**")
            for o in sc["opportunita"]:
                lines.append(f"- {o}")

    return "\n".join(lines)

md = genera_markdown()
st.download_button(
    label="📥 Scarica Report (Markdown)",
    data=md.encode("utf-8"),
    file_name=f"foresight_report_sessione_{sid}.md",
    mime="text/markdown",
    use_container_width=True,
    type="primary",
)

with st.expander("Anteprima Markdown"):
    st.code(md, language="markdown")

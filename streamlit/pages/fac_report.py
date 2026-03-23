import streamlit as st
import sys
from pathlib import Path
import markdown
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import get_sessione_by_id, get_scenari, get_fenomeni, get_voti_aggregati

check_facilitatore()

if not st.session_state.get("sessione_id"):
    st.warning("Nessuna sessione attiva. Vai su Setup per aprire o creare una sessione.")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione_by_id(sid)

if not sessione:
    st.error("Sessione non trovata.")
    st.stop()

scenari = get_scenari(sid)
fenomeni = get_fenomeni(sid)
voti = get_voti_aggregati(sid)
fenom_map = {f["id"]: f for f in fenomeni}

# ── Header ─────────────────────────────────────────────────
st.markdown(f"# 📄 Report Finale — Sessione #{sid}")
st.caption(f"Generato il {sessione['created_at'][:10]}")
st.divider()

# ── Contesto ───────────────────────────────────────────────
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
            st.caption(f"+ {sessione.get('driver1_pos', '—')} / − {sessione.get('driver1_neg', '—')}")
    with dc2:
        with st.container(border=True):
            st.markdown(f"**Driver 2 — {sessione['driver2_nome']}**")
            st.caption(f"+ {sessione.get('driver2_pos', '—')} / − {sessione.get('driver2_neg', '—')}")

st.divider()

# ── Top fenomeni ───────────────────────────────────────────
st.subheader("🔭 Fenomeni prioritizzati")

# Usa ranking aggregato dai voti se disponibile, altrimenti ordine manuale
if voti:
    st.caption("Ordinati per posizione media dei voti dei partecipanti")
    for i, v in enumerate(voti[:10]):
        f = fenom_map.get(v["fenomeno_id"])
        testo = f["testo"] if f else f"Fenomeno #{v['fenomeno_id']}"
        col_n, col_t, col_info = st.columns([1, 8, 2])
        with col_n:
            color = "#4F46E5" if i < 3 else "#6B7280"
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>",
                unsafe_allow_html=True,
            )
        with col_t:
            peso = "**" if i < 3 else ""
            st.markdown(f"{peso}{testo}{peso}")
        with col_info:
            st.caption(f"avg: {v['media_posizione']:.1f}")
else:
    for i, f in enumerate(fenomeni[:10]):
        col_n, col_t = st.columns([1, 9])
        with col_n:
            color = "#4F46E5" if i < 3 else "#6B7280"
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>",
                unsafe_allow_html=True,
            )
        with col_t:
            peso = "**" if i < 3 else ""
            st.markdown(f"{peso}{f['testo']}{peso}")

st.divider()

# ── Matrice 2×2 ────────────────────────────────────────────
st.subheader("🗺️ Matrice degli Scenari")

if scenari and sessione.get("driver1_nome"):
    d1 = sessione["driver1_nome"]
    d2 = sessione["driver2_nome"]
    d1p = sessione.get("driver1_pos") or f"{d1} +"
    d1n = sessione.get("driver1_neg") or f"{d1} −"
    d2p = sessione.get("driver2_pos") or f"{d2} +"
    d2n = sessione.get("driver2_neg") or f"{d2} −"

    sc_map = {s["quadrante"]: s for s in scenari}

    st.markdown(
        f"<div style='text-align:center;color:#6B7280;font-size:0.85em'>↑ {d2p}</div>",
        unsafe_allow_html=True,
    )

    m_col1, m_col2 = st.columns(2)
    for col, (q1, q2) in zip([m_col1, m_col2], [("-+", "++"), ("--", "+-")]):
        with col:
            for q in [q1, q2]:
                sc = sc_map.get(q)
                if sc:
                    with st.container(border=True):
                        titolo = sc.get("titolo") or f"Scenario {sc['numero']}"
                        st.markdown(f"**{titolo}** `{q}`")
                        asse_x = d1p if q[0] == "+" else d1n
                        asse_y = d2p if q[1] == "+" else d2n
                        st.caption(f"{asse_x} × {asse_y}")
                        if sc.get("narrativa"):
                            st.markdown(
                                sc["narrativa"][:150] + ("..." if len(sc["narrativa"]) > 150 else "")
                            )

    st.markdown(
        f"<div style='text-align:center;color:#6B7280;font-size:0.85em'>↓ {d2n}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"← {d1n} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {d1p} →", unsafe_allow_html=True)

st.divider()

# ── Scenari nel dettaglio ──────────────────────────────────
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

# ── Export ─────────────────────────────────────────────────
st.subheader("💾 Esporta")


def genera_markdown():
    # Fenomeni ordinati
    if voti:
        fenomeni_ordinati = [
            (i + 1, fenom_map[v["fenomeno_id"]]["testo"], v["media_posizione"])
            for i, v in enumerate(voti)
            if v["fenomeno_id"] in fenom_map
        ]
    else:
        fenomeni_ordinati = [(i + 1, f["testo"], None) for i, f in enumerate(fenomeni)]

    lines = [
        f"# Report Foresight — Sessione #{sid}",
        f"",
        f"**Domanda di ricerca:** {sessione['domanda_ricerca']}",
        f"**Orizzonte temporale:** {sessione['frame_temporale']}",
        f"**Codice sessione:** {sessione.get('codice', '—')}",
        f"",
        f"## Driver",
        f"- **Driver 1:** {sessione.get('driver1_nome', '—')} ({sessione.get('driver1_pos', '+')} / {sessione.get('driver1_neg', '−')})",
        f"- **Driver 2:** {sessione.get('driver2_nome', '—')} ({sessione.get('driver2_pos', '+')} / {sessione.get('driver2_neg', '−')})",
        f"",
        f"## Fenomeni prioritizzati",
    ]
    for pos, testo, avg in fenomeni_ordinati:
        avg_str = f" (avg: {avg:.1f})" if avg is not None else ""
        lines.append(f"{pos}. {testo}{avg_str}")

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
        if sc.get("key_points_data"):
            kp_data = sc["key_points_data"]
            if isinstance(kp_data, dict):
                p_com = kp_data.get("punti_comune", [])
                divs = kp_data.get("divergenze", [])
                standard_kp = {k: v for k, v in kp_data.items() if k not in ("punti_comune", "divergenze")}
                
                if standard_kp:
                    lines.append("")
                    lines.append("**Key Points:**")
                    for k, v in standard_kp.items():
                        lines.append(f"- **{k}:** {v}")
                
                if p_com:
                    lines.append("")
                    lines.append("**🤝 Punti in Comune:**")
                    for x in p_com: lines.append(f"- {x}")
                    
                if divs:
                    lines.append("")
                    lines.append("**⚡ Divergenze Emerse:**")
                    for x in divs: lines.append(f"- {x}")
        if sc.get("minacce"):
            lines.append("")
            lines.append("**Minacce:**")
            for m in sc["minacce"]:
                lines.append(f"- {m}")
        if sc.get("opportunita"):
            lines.append("")
            lines.append("**Opportunità:**")
            for o in sc["opportunita"]:
                lines.append(f"- {o}")

    return "\n".join(lines)


md = genera_markdown()
html_content = markdown.markdown(md)

pdf_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
  body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 2px; color: #333; margin: 0; }}
  #pdf-report-body {{ padding: 30px; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
  #pdf-report-body h1 {{ color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 15px; margin-bottom: 25px; }}
  #pdf-report-body h2 {{ color: #312E81; margin-top: 35px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
  #pdf-report-body h3 {{ color: #4338CA; margin-top: 25px; }}
  #pdf-report-body p, #pdf-report-body li {{ line-height: 1.7; font-size: 15px; }}
  #pdf-report-body strong {{ color: #111827; }}
  .btn {{ 
    background-color: #4F46E5; color: white; padding: 12px 24px; 
    border-radius: 8px; border: none; cursor: pointer; 
    font-weight: 600; font-family: 'Segoe UI', sans-serif; font-size: 15px; 
    width: 100%; text-align: center; transition: background 0.2s;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  }}
  .btn:hover {{ background-color: #4338CA; }}
</style>
</head>
<body>

<div id="pdf-content" style="display: none;">
  <div id="pdf-report-body">
    {html_content}
  </div>
</div>

<button class="btn" onclick="
  var btn = this;
  var originalText = btn.innerHTML;
  btn.innerHTML = '⚙️ Generazione PDF in corso...';
  btn.style.backgroundColor = '#6B7280';
  
  var element = document.getElementById('pdf-content');
  element.style.display = 'block';
  
  var opt = {{
    margin: 15,
    filename: 'Report_Scenario_Planning_#{sid}.pdf',
    image: {{ type: 'jpeg', quality: 0.98 }},
    html2canvas: {{ scale: 2, useCORS: true }},
    jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
  }};
  
  html2pdf().set(opt).from(element).save().then(function() {{
    element.style.display = 'none';
    btn.innerHTML = originalText;
    btn.style.backgroundColor = '#4F46E5';
  }});
">
  📥 Scarica Report Finale in PDF Reale
</button>

</body>
</html>
"""

components.html(pdf_html, height=65)

st.download_button(
    label="Scarica File Sorgente (Markdown grezzo)",
    data=md.encode("utf-8"),
    file_name=f"foresight_report_sessione_{sid}.md",
    mime="text/markdown",
    use_container_width=True,
)

with st.expander("Anteprima Markdown"):
    st.code(md, language="markdown")

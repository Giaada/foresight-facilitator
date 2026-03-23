import markdown
import streamlit.components.v1 as components

def st_scarica_pdf_scenario_individuale(scenario_indiv, sessione, nome_partecipante):
    # Genera markdown
    lines = [
        f"# Scenario Individuale — {nome_partecipante}",
        f"",
        f"**Sessione:** {sessione['domanda_ricerca']}",
        f"**Orizzonte temporale:** {sessione['frame_temporale']}",
        f"**Quadrante assegnato:** `{scenario_indiv['quadrante']}`",
        f"",
    ]
    if scenario_indiv.get("titolo"):
        lines.append(f"### {scenario_indiv['titolo']}")
        lines.append("")
    if scenario_indiv.get("narrativa"):
        lines.append(scenario_indiv["narrativa"])
        lines.append("")

    if scenario_indiv.get("key_points_data"):
        lines.append("### Key Points Esplorati")
        for kp, ris in scenario_indiv["key_points_data"].items():
            lines.append(f"- **{kp}:** {ris}")
        lines.append("")

    if scenario_indiv.get("minacce"):
        lines.append("### ⚠️ Minacce")
        for m in scenario_indiv["minacce"]:
            lines.append(f"- {m}")
        lines.append("")
        
    if scenario_indiv.get("opportunita"):
        lines.append("### ✨ Opportunità")
        for o in scenario_indiv["opportunita"]:
            lines.append(f"- {o}")
        lines.append("")

    md = "\n".join(lines)
    html_content = markdown.markdown(md)
    
    unique_id = f"pdf-sc-{scenario_indiv['id']}"

    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
      body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 2px; color: #333; margin: 0; }}
      #{unique_id} {{ padding: 30px; }}
      #{unique_id} h1 {{ color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 10px; margin-bottom: 20px; }}
      #{unique_id} h3 {{ color: #4338CA; margin-top: 20px; }}
      #{unique_id} p, #{unique_id} li {{ line-height: 1.6; font-size: 14px; position: relative; z-index: 1; }}
      .btn {{ 
        background-color: #10B981; color: white; padding: 10px 20px; 
        border-radius: 8px; border: none; cursor: pointer; 
        font-weight: 600; font-family: 'Segoe UI', sans-serif; font-size: 14px; 
        width: 100%; text-align: center; transition: background 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      }}
      .btn:hover {{ background-color: #059669; }}
    </style>
    </head>
    <body>
    <div style="position: absolute; left: -9999px; top: 0; width: 800px; background-color: white;">
      <div id="{unique_id}">
        {html_content}
      </div>
    </div>
    <button class="btn" onclick="
      var btn = this;
      var originalText = btn.innerHTML;
      btn.innerHTML = '⚙️ Generazione PDF...';
      btn.style.backgroundColor = '#6B7280';
      
      var element = document.getElementById('{unique_id}');
      
      var opt = {{
        margin: 15,
        filename: 'Scenario_{nome_partecipante}.pdf',
        image: {{ type: 'jpeg', quality: 0.98 }},
        html2canvas: {{ scale: 2, useCORS: true, windowWidth: 800 }},
        jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
      }};
      
      html2pdf().set(opt).from(element).save().then(function() {{
        btn.innerHTML = originalText;
        btn.style.backgroundColor = '#10B981';
      }});
    ">
      📥 Scarica in PDF
    </button>
    </body>
    </html>
    """
    
    components.html(pdf_html, height=45)

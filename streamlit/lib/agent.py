import anthropic
import os
import json
from .database import get_messaggi, aggiungi_messaggio, aggiorna_scenario

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

STEP_ORDINE = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"]


def descrivi_quadrante(quadrante, d1_nome, d1_pos, d1_neg, d2_nome, d2_pos, d2_neg):
    asse_x = d1_pos if quadrante[0] == "+" else d1_neg
    asse_y = d2_pos if quadrante[1] == "+" else d2_neg
    asse_x = asse_x or ("alto" if quadrante[0] == "+" else "basso")
    asse_y = asse_y or ("alto" if quadrante[1] == "+" else "basso")
    d1 = d1_nome or "Driver 1"
    d2 = d2_nome or "Driver 2"
    return f"{d1}: {asse_x} × {d2}: {asse_y}"


def sistema_prompt(scenario, sessione, key_points):
    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    kp_list = ", ".join(key_points) if key_points else "nessun key point definito"
    step = scenario["step_corrente"]

    return f"""Sei un esperto facilitatore di Strategic Foresight.
Stai guidando la costruzione di uno scenario futuro.

CONTESTO:
- Domanda di ricerca: "{sessione['domanda_ricerca']}"
- Orizzonte temporale: {sessione['frame_temporale']}
- Scenario assegnato: {descrizione}

KEY POINTS da esplorare: {kp_list}
STEP CORRENTE: {step}

FLUSSO DA SEGUIRE:
1. intro → presenta il quadrante, invita a iniziare
2. key_points → esplora ogni key point uno alla volta con domande mirate
3. narrativa → sintetizza una descrizione narrativa coerente e stimolante
4. titolo → chiedi un titolo; se non fornito, suggerisci 3 opzioni
5. minacce → guida l'identificazione delle principali minacce di questo scenario
6. opportunita → guida l'identificazione delle opportunità
7. concluso → riepilogo e chiusura

ISTRUZIONI:
- Comunica in italiano, tono professionale e coinvolgente
- Fai UNA domanda o richiesta alla volta
- Quando hai abbastanza materiale per uno step, avanza al successivo
- Sii specifico rispetto all'orizzonte temporale {sessione['frame_temporale']}

RISPOSTA in JSON:
{{
  "testo": "messaggio da mostrare al facilitatore",
  "nuovo_step": "nome step se stai avanzando, altrimenti null",
  "aggiornamenti": {{
    "narrativa": "testo se generata/aggiornata, altrimenti null",
    "titolo": "titolo se confermato, altrimenti null",
    "minacce": ["lista", "se", "aggiornata"],
    "opportunita": ["lista", "se", "aggiornata"],
    "key_points_data": {{"chiave": "valore se aggiornato"}}
  }}
}}
Se aggiornamenti non ha campi, metti null."""


def invia_messaggio(scenario, sessione, testo_utente):
    """Invia un messaggio e ottieni la risposta dell'agente."""
    key_points = sessione.get("key_points", [])
    messaggi_db = get_messaggi(scenario["id"])

    # Costruisce history
    history = [
        {"role": m["ruolo"], "content": m["contenuto"]}
        for m in messaggi_db
    ]
    history.append({"role": "user", "content": testo_utente})

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=sistema_prompt(scenario, sessione, key_points),
            messages=history,
        )
        testo_raw = risposta.content[0].text

        # Prova a parsare JSON
        try:
            json_match = None
            import re
            m = re.search(r'\{[\s\S]*\}', testo_raw)
            if m:
                parsed = json.loads(m.group())
                testo_risposta = parsed.get("testo", testo_raw)
                nuovo_step = parsed.get("nuovo_step")
                agg = parsed.get("aggiornamenti") or {}
            else:
                testo_risposta = testo_raw
                nuovo_step = None
                agg = {}
        except Exception:
            testo_risposta = testo_raw
            nuovo_step = None
            agg = {}

        # Salva messaggi
        aggiungi_messaggio(scenario["id"], "user", testo_utente)
        aggiungi_messaggio(scenario["id"], "assistant", testo_risposta)

        # Aggiorna scenario
        updates = {}
        if nuovo_step:
            updates["step_corrente"] = nuovo_step
        if agg.get("narrativa"):
            updates["narrativa"] = agg["narrativa"]
        if agg.get("titolo"):
            updates["titolo"] = agg["titolo"]
        if agg.get("minacce"):
            updates["minacce"] = agg["minacce"]
        if agg.get("opportunita"):
            updates["opportunita"] = agg["opportunita"]
        if agg.get("key_points_data"):
            kpd = scenario.get("key_points_data", {}) or {}
            kpd.update(agg["key_points_data"])
            updates["key_points_data"] = kpd
        if updates:
            aggiorna_scenario(scenario["id"], **updates)

        return testo_risposta, nuovo_step

    except Exception as e:
        return f"Errore dell'agente: {str(e)}", None


def avvia_scenario(scenario, sessione):
    """Messaggio iniziale dell'agente per un nuovo scenario."""
    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    key_points = sessione.get("key_points", [])
    kp_str = ", ".join(key_points) if key_points else "tutti gli aspetti rilevanti"

    prompt = f"""Genera il messaggio di benvenuto per lo Scenario {scenario['numero']}.
Quadrante: {descrizione}
Domanda di ricerca: "{sessione['domanda_ricerca']}"
Orizzonte: {sessione['frame_temporale']}
Key points da esplorare: {kp_str}

Il messaggio deve:
1. Presentare il quadrante in modo coinvolgente
2. Spiegare brevemente il percorso (esploreremo insieme {kp_str})
3. Fare la prima domanda sul primo key point: "{key_points[0] if key_points else 'il contesto generale'}"

Rispondi SOLO con il testo del messaggio, in italiano."""

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        testo = risposta.content[0].text
    except Exception:
        testo = f"Benvenuti allo Scenario {scenario['numero']}!\n\nLavorerete sul quadrante: **{descrizione}**\n\nIniziamo esplorando il primo key point. {key_points[0] if key_points else 'Come immaginate questo scenario?'}"

    aggiungi_messaggio(scenario["id"], "assistant", testo)
    aggiorna_scenario(scenario["id"], step_corrente="key_points")
    return testo

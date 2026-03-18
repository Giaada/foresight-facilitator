import anthropic
import os
import json
import re
from .database import get_messaggi, aggiungi_messaggio, aggiorna_scenario


STEP_ORDINE = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"]


def _get_client():
    """Crea il client Anthropic leggendo la chiave da secrets o env al momento della chiamata."""
    try:
        import streamlit as st
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=api_key)


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
3. narrativa → sintetizza una descrizione narrativa coerente (3-5 frasi)
4. titolo → chiedi un titolo; se non fornito, suggerisci 3 opzioni
5. minacce → guida l'identificazione delle principali minacce (lista)
6. opportunita → guida l'identificazione delle opportunità (lista)
7. concluso → riepilogo e chiusura

ISTRUZIONI:
- Comunica in italiano, tono professionale e coinvolgente
- Fai UNA domanda o richiesta alla volta
- Quando hai abbastanza materiale per uno step, avanza al successivo
- Sii specifico rispetto all'orizzonte temporale {sessione['frame_temporale']}

REGOLE PER aggiornamenti (FONDAMENTALE - segui sempre):
- Step narrativa: quando generi la narrativa, METTI SEMPRE il testo in aggiornamenti.narrativa
- Step titolo: quando il titolo è confermato o scelto, METTI SEMPRE in aggiornamenti.titolo
- Step minacce: ogni volta che hai una lista di minacce, METTI SEMPRE in aggiornamenti.minacce
- Step opportunita: ogni volta che hai una lista di opportunità, METTI SEMPRE in aggiornamenti.opportunita
- Step key_points: salva le risposte ricevute in aggiornamenti.key_points_data

RISPOSTA - rispondi SOLO con questo JSON, senza testo prima o dopo:
{{
  "testo": "messaggio da mostrare ai partecipanti",
  "nuovo_step": "nome del prossimo step se stai avanzando, altrimenti null",
  "aggiornamenti": {{
    "narrativa": "testo narrativa se disponibile, altrimenti null",
    "titolo": "titolo se confermato, altrimenti null",
    "minacce": ["minaccia 1", "minaccia 2"],
    "opportunita": ["opportunità 1", "opportunità 2"],
    "key_points_data": {{"nome_key_point": "risposta ricevuta"}}
  }}
}}"""


def _build_history(messaggi_db, testo_utente):
    """
    Costruisce la history per l'API Anthropic.
    L'API richiede che il primo messaggio sia sempre 'user'.
    Se la history dal DB inizia con 'assistant' (messaggio di benvenuto),
    aggiungiamo un messaggio utente fittizio di apertura.
    """
    msgs = [{"role": m["ruolo"], "content": m["contenuto"]} for m in messaggi_db]
    msgs.append({"role": "user", "content": testo_utente})

    # Garantisce alternanza corretta user/assistant richiesta dall'API
    if msgs and msgs[0]["role"] == "assistant":
        msgs = [{"role": "user", "content": "[Sessione avviata]"}] + msgs

    return msgs


def invia_messaggio(scenario, sessione, testo_utente):
    """Invia un messaggio e ottieni la risposta dell'agente."""
    key_points = sessione.get("key_points", [])
    messaggi_db = get_messaggi(scenario["id"])
    history = _build_history(messaggi_db, testo_utente)

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=sistema_prompt(scenario, sessione, key_points),
            messages=history,
        )
        testo_raw = risposta.content[0].text

        # Prova a parsare JSON — gestisce blocchi ```json...``` e testo extra
        testo_risposta = testo_raw
        nuovo_step = None
        agg = {}
        try:
            # Rimuovi eventuale blocco markdown ```json ... ```
            cleaned = re.sub(r'^```(?:json)?\s*', '', testo_raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
            # Cerca il primo oggetto JSON completo (non greedy non funziona su oggetti annidati,
            # usiamo json.JSONDecoder.raw_decode che si ferma al termine del primo oggetto valido)
            decoder = json.JSONDecoder()
            idx = cleaned.find('{')
            if idx != -1:
                parsed, _ = decoder.raw_decode(cleaned, idx)
                testo_risposta = parsed.get("testo") or testo_raw
                nuovo_step = parsed.get("nuovo_step")
                agg = parsed.get("aggiornamenti") or {}
        except Exception:
            # Fallback: usa il testo grezzo come risposta
            testo_risposta = testo_raw

        # Salva messaggi
        aggiungi_messaggio(scenario["id"], "user", testo_utente)
        aggiungi_messaggio(scenario["id"], "assistant", testo_risposta)

        # Aggiorna scenario
        updates = {}
        if nuovo_step and nuovo_step in STEP_ORDINE:
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

    except anthropic.AuthenticationError:
        msg = "⚠️ Chiave API Anthropic non valida o non configurata. Contatta il facilitatore."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except anthropic.APIConnectionError:
        msg = "⚠️ Impossibile connettersi all'API. Verifica la connessione internet."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except Exception as e:
        msg = f"⚠️ Errore dell'agente: {str(e)}"
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None


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

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        testo = risposta.content[0].text
    except Exception:
        primo_kp = key_points[0] if key_points else "Come immaginate questo scenario?"
        testo = (
            f"Benvenuti allo Scenario {scenario['numero']}!\n\n"
            f"Lavorerete sul quadrante: **{descrizione}**\n\n"
            f"Insieme esploreremo: {kp_str}\n\n"
            f"Iniziamo: {primo_kp}"
        )

    aggiungi_messaggio(scenario["id"], "assistant", testo)
    aggiorna_scenario(scenario["id"], step_corrente="key_points")
    return testo

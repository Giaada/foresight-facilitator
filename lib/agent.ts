import Anthropic from "@anthropic-ai/sdk";
import { prisma } from "./prisma";
import { StepScenario } from "./types";

const MODEL_GRUPPO = "claude-sonnet-4-6";
const MODEL_INDIVIDUALE = "claude-haiku-4-5-20251001";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface RispostaAgente {
  testo: string;
  nuovoStep?: StepScenario;
  outputAggiornato?: {
    narrativa?: string;
    titolo?: string;
    minacce?: string[];
    opportunita?: string[];
    keyPointsData?: Record<string, string>;
  };
}

export async function eseguiStepAgente(
  gruppoId: string,
  ultimoMessaggioUtente: string
): Promise<RispostaAgente | null> {
  const gruppo = await prisma.gruppo.findUnique({
    where: { id: gruppoId },
    include: {
      sessione: true,
      messaggi: { orderBy: { createdAt: "asc" } },
      scenarioOutput: true,
    },
  });

  if (!gruppo) return null;

  const sessione = gruppo.sessione;
  const keyPoints: string[] = JSON.parse(sessione.keyPoints);
  const stepCorrente = gruppo.stepCorrente as StepScenario;

  // Costruisce la descrizione del quadrante
  const descrizioneQuadrante = costruisciDescrizioneQuadrante(
    gruppo.quadrante,
    sessione.driver1Nome,
    sessione.driver1PosPolo,
    sessione.driver1NegPolo,
    sessione.driver2Nome,
    sessione.driver2PosPolo,
    sessione.driver2NegPolo
  );

  const sistemaPrompt = `Sei un facilitatore esperto di Strategic Foresight.
Stai guidando un piccolo gruppo (4 persone) nella costruzione di uno scenario futuro.

CONTESTO DELLA SESSIONE:
- Domanda di ricerca: "${sessione.domandaRicerca}"
- Orizzonte temporale: ${sessione.frameTemporale}
- Il vostro quadrante: ${descrizioneQuadrante}

STEP CORRENTE: ${stepCorrente}
KEY POINTS da esplorare: ${keyPoints.join(", ")}

ISTRUZIONI DI COMPORTAMENTO:
- Comunica in italiano, con tono professionale ma accessibile
- Fai UNA domanda alla volta, non sovraccaricare il gruppo
- Sii specifico e concreto, ancorato all'orizzonte temporale
- Valida e integra le risposte del gruppo prima di andare avanti
- Quando hai abbastanza materiale per uno step, avanza al successivo

FORMATO RISPOSTA:
Rispondi SEMPRE con un JSON in questo formato:
{
  "testo": "il messaggio da mostrare al gruppo",
  "nuovoStep": "solo se stai avanzando di step, altrimenti null",
  "outputAggiornato": {
    "narrativa": "testo della narrativa in elaborazione",
    "titolo": "titolo (se definito)",
    "minacce": ["eventuali", "minacce", "emerse"],
    "opportunita": ["eventuali", "opportunità", "emerse"],
    "keyPointsData": {"nome_keypoint": "risposta_consolidata"}
  }
}
IMPORTANTE: Compila sempre in 'outputAggiornato' tutti i campi che stai via via definendo con il gruppo. Aggiorna questi campi non appena emergono spunti utili dalle risposte del gruppo, in modo che il report visivo si aggiorni in tempo reale lungo tutta la sessione. Se un campo non è ancora stato affrontato, può essere omesso o lasciato a null.`;

  // Costruisce la history dei messaggi
  const history = gruppo.messaggi.map((m: { ruolo: string; contenuto: string }) => ({
    role: m.ruolo as "user" | "assistant",
    content: m.contenuto,
  }));

  // Se è il primo messaggio (intro), aggiungi il trigger iniziale
  if (stepCorrente === "intro" && history.length === 0) {
    return await generaIntroduzione(gruppo.numero, descrizioneQuadrante, sessione.domandaRicerca, sessione.frameTemporale);
  }

  try {
    const risposta = await anthropic.messages.create({
      model: MODEL_GRUPPO,
      max_tokens: 1024,
      system: sistemaPrompt,
      messages: [
        ...history,
        { role: "user", content: ultimoMessaggioUtente },
      ],
    });

    const testoRisposta = risposta.content[0].type === "text" ? risposta.content[0].text : "";

    try {
      const jsonMatch = testoRisposta.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        let out = parsed.outputAggiornato;
        if (!out) {
            out = {
                narrativa: parsed.narrativa,
                titolo: parsed.titolo,
                minacce: parsed.minacce,
                opportunita: parsed.opportunita,
                keyPointsData: parsed.keyPointsData || parsed.key_points_data
            };
            if (!out.narrativa && !out.titolo && !out.minacce && !out.opportunita && !out.keyPointsData) {
                out = undefined;
            }
        }
        return {
          testo: parsed.testo || testoRisposta,
          nuovoStep: parsed.nuovoStep || undefined,
          outputAggiornato: out,
        };
      }
    } catch {
      // Se il parse fallisce, restituisce solo il testo
    }

    return { testo: testoRisposta };
  } catch (err) {
    console.error("[Agente] errore Anthropic:", err);
    return null;
  }
}

async function generaIntroduzione(
  numeroGruppo: number,
  descrizioneQuadrante: string,
  domandaRicerca: string,
  frameTemporale: string
): Promise<RispostaAgente> {
  try {
    const risposta = await anthropic.messages.create({
      model: MODEL_GRUPPO,
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: `Genera un messaggio di benvenuto per il Gruppo ${numeroGruppo} che inizia a lavorare sul seguente scenario di Strategic Foresight.

Domanda di ricerca: "${domandaRicerca}"
Orizzonte temporale: ${frameTemporale}
Quadrante assegnato: ${descrizioneQuadrante}

Il messaggio deve:
1. Presentare il quadrante in modo chiaro e stimolante
2. Spiegare brevemente cosa faranno (costruire lo scenario paso a paso)
3. Invitarli a rispondere "pronti" o fare domande prima di iniziare

Rispondi SOLO con il testo del messaggio, in italiano, tono coinvolgente.`,
        },
      ],
    });

    const testo =
      risposta.content[0].type === "text" ? risposta.content[0].text : "Benvenuti! Siete pronti a iniziare?";

    return { testo, nuovoStep: "intro" };
  } catch {
    return {
      testo: `Benvenuti Gruppo ${numeroGruppo}! Lavorerete sullo scenario: **${descrizioneQuadrante}**.\n\nQuando siete pronti, dite "pronti" e inizieremo insieme la costruzione dello scenario.`,
      nuovoStep: "intro",
    };
  }
}

// ─── Fase individuale (haiku) ────────────────────────────────────────────────

export async function eseguiStepAgenteIndividuale(
  scenarioIndividualeId: string,
  ultimoMessaggioUtente: string
): Promise<RispostaAgente | null> {
  const scenario = await prisma.scenarioIndividuale.findUnique({
    where: { id: scenarioIndividualeId },
    include: {
      sessione: true,
      messaggi: { orderBy: { createdAt: "asc" } },
    },
  });

  if (!scenario) return null;

  const sessione = scenario.sessione;
  const keyPoints: string[] = JSON.parse(sessione.keyPoints);
  const descrizioneQuadrante = costruisciDescrizioneQuadrante(
    scenario.quadrante,
    sessione.driver1Nome,
    sessione.driver1PosPolo,
    sessione.driver1NegPolo,
    sessione.driver2Nome,
    sessione.driver2PosPolo,
    sessione.driver2NegPolo
  );

  if (scenario.stepCorrente === "intro" && scenario.messaggi.length === 0) {
    return await generaIntroduzioneIndividuale(descrizioneQuadrante, sessione.domandaRicerca, sessione.frameTemporale);
  }

  const sistemaPrompt = `Sei un facilitatore esperto di Strategic Foresight che guida un singolo partecipante nell'esplorazione individuale di uno scenario futuro.

CONTESTO:
- Domanda di ricerca: "${sessione.domandaRicerca}"
- Orizzonte temporale: ${sessione.frameTemporale}
- Quadrante assegnato: ${descrizioneQuadrante}

STEP CORRENTE: ${scenario.stepCorrente}
KEY POINTS da esplorare: ${keyPoints.join(", ")}

ISTRUZIONI:
- Tono colloquiale e incoraggiante, la persona lavora da sola
- Fai UNA domanda alla volta
- Aiuta il partecipante a ragionare in modo creativo sul suo quadrante
- Quando hai abbastanza materiale per uno step, avanza al successivo

FORMATO RISPOSTA (JSON):
{
  "testo": "messaggio da mostrare",
  "nuovoStep": "solo se avanzi di step, altrimenti null",
  "outputAggiornato": {
    "narrativa": "bozza narrativa in elaborazione",
    "titolo": "titolo (se definito)",
    "minacce": ["minacce emerse"],
    "opportunita": ["opportunità emerse"],
    "keyPointsData": {"nome_keypoint": "risposta"}
  }
}`;

  const history = scenario.messaggi.map((m: { ruolo: string; contenuto: string }) => ({
    role: m.ruolo as "user" | "assistant",
    content: m.contenuto,
  }));

  try {
    const risposta = await anthropic.messages.create({
      model: MODEL_INDIVIDUALE,
      max_tokens: 1024,
      system: sistemaPrompt,
      messages: [...history, { role: "user", content: ultimoMessaggioUtente }],
    });

    const testo = risposta.content[0].type === "text" ? risposta.content[0].text : "";
    try {
      const jsonMatch = testo.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          testo: parsed.testo || testo,
          nuovoStep: parsed.nuovoStep || undefined,
          outputAggiornato: parsed.outputAggiornato || undefined,
        };
      }
    } catch { /* restituisce solo testo */ }
    return { testo };
  } catch (err) {
    console.error("[AgenteIndividuale] errore Anthropic:", err);
    return null;
  }
}

async function generaIntroduzioneIndividuale(
  descrizioneQuadrante: string,
  domandaRicerca: string,
  frameTemporale: string
): Promise<RispostaAgente> {
  try {
    const risposta = await anthropic.messages.create({
      model: MODEL_INDIVIDUALE,
      max_tokens: 512,
      messages: [{
        role: "user",
        content: `Genera un messaggio di benvenuto per un partecipante che inizia il lavoro individuale di Strategic Foresight.

Domanda di ricerca: "${domandaRicerca}"
Orizzonte temporale: ${frameTemporale}
Quadrante assegnato: ${descrizioneQuadrante}

Il messaggio deve:
1. Spiegare brevemente che esplorerà questo quadrante in modo personale
2. Dire che costruirà la sua visione individuale prima del confronto con il gruppo
3. Invitarlo a scrivere "pronto" per iniziare

Rispondi SOLO con il testo del messaggio, in italiano, tono caldo e incoraggiante.`,
      }],
    });
    const testo = risposta.content[0].type === "text" ? risposta.content[0].text : "Benvenuto! Scrivi 'pronto' per iniziare.";
    return { testo, nuovoStep: "intro" };
  } catch {
    return {
      testo: `Benvenuto! Esplorerai individualmente il quadrante **${descrizioneQuadrante}**.\n\nCostruirai la tua visione personale prima di confrontarti con il gruppo. Scrivi "pronto" quando sei pronto a iniziare.`,
      nuovoStep: "intro",
    };
  }
}

// ─── Sintesi di gruppo (sonnet) ───────────────────────────────────────────────

type ScenarioIndividualeRecord = {
  id: string;
  titolo: string | null;
  narrativa: string | null;
  minacce: string | null;
  opportunita: string | null;
  keyPointsData: string | null;
};

export async function sintetizzaGruppo(gruppoId: string): Promise<void> {
  const gruppo = await prisma.gruppo.findUnique({
    where: { id: gruppoId },
    include: {
      sessione: true,
      partecipanti: {
        include: { scenarioIndividuale: true },
      },
    },
  });

  if (!gruppo) return;

  const scenariIndividuali: ScenarioIndividualeRecord[] = gruppo.partecipanti
    .map((p: { scenarioIndividuale: ScenarioIndividualeRecord | null }) => p.scenarioIndividuale)
    .filter((s: ScenarioIndividualeRecord | null): s is ScenarioIndividualeRecord => s !== null && s !== undefined);

  if (scenariIndividuali.length === 0) return;

  const keyPoints: string[] = JSON.parse(gruppo.sessione.keyPoints);
  const descrizioneQuadrante = costruisciDescrizioneQuadrante(
    gruppo.quadrante,
    gruppo.sessione.driver1Nome,
    gruppo.sessione.driver1PosPolo,
    gruppo.sessione.driver1NegPolo,
    gruppo.sessione.driver2Nome,
    gruppo.sessione.driver2PosPolo,
    gruppo.sessione.driver2NegPolo
  );

  const bozze = scenariIndividuali.map((sc: ScenarioIndividualeRecord, i: number) => {
    const kp = sc.keyPointsData ? JSON.parse(sc.keyPointsData) : {};
    const minacce = sc.minacce ? JSON.parse(sc.minacce) : [];
    const opportunita = sc.opportunita ? JSON.parse(sc.opportunita) : [];
    return `--- Partecipante ${i + 1} ---
Titolo: ${sc.titolo || "non definito"}
Narrativa: ${sc.narrativa || "non definita"}
Minacce: ${minacce.join(", ") || "nessuna"}
Opportunità: ${opportunita.join(", ") || "nessuna"}
Key Points: ${Object.entries(kp).map(([k, v]) => `${k}: ${v}`).join("; ") || "nessuno"}`;
  }).join("\n\n");

  try {
    const risposta = await anthropic.messages.create({
      model: MODEL_GRUPPO,
      max_tokens: 2048,
      messages: [{
        role: "user",
        content: `Sei un facilitatore esperto di Strategic Foresight. Hai raccolto le visioni individuali di ${scenariIndividuali.length} partecipanti sullo stesso quadrante. Sintetizzale in una bozza di scenario condiviso.

CONTESTO:
- Domanda di ricerca: "${gruppo.sessione.domandaRicerca}"
- Orizzonte temporale: ${gruppo.sessione.frameTemporale}
- Quadrante: ${descrizioneQuadrante}
- Key Points da esplorare: ${keyPoints.join(", ")}

VISIONI INDIVIDUALI:
${bozze}

Crea una sintesi che:
1. Unifica le idee comuni in una narrativa coerente
2. Preserva le divergenze interessanti come spunti di discussione
3. Produce un titolo provvisorio per lo scenario

Rispondi SOLO con JSON:
{
  "titolo": "titolo provvisorio del scenario",
  "narrativa": "narrativa sintetizzata (2-3 paragrafi)",
  "minacce": ["minacce emerse dalle visioni individuali"],
  "opportunita": ["opportunità emerse"],
  "keyPointsData": {"nome_keypoint": "sintesi delle risposte"},
  "puntiComune": ["idee condivise da più partecipanti"],
  "divergenze": ["idee uniche o contrastanti interessanti"]
}`,
      }],
    });

    const testo = risposta.content[0].type === "text" ? risposta.content[0].text : "";
    const jsonMatch = testo.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return;

    const parsed = JSON.parse(jsonMatch[0]);

    const kpData: Record<string, string> = { ...(parsed.keyPointsData || {}) };
    if (parsed.puntiComune?.length) kpData["punti_comune"] = parsed.puntiComune.join(" | ");
    if (parsed.divergenze?.length) kpData["divergenze"] = parsed.divergenze.join(" | ");

    await prisma.scenarioOutput.upsert({
      where: { gruppoId },
      create: {
        gruppoId,
        titolo: parsed.titolo ?? null,
        narrativa: parsed.narrativa ?? null,
        minacce: parsed.minacce ? JSON.stringify(parsed.minacce) : null,
        opportunita: parsed.opportunita ? JSON.stringify(parsed.opportunita) : null,
        keyPointsData: JSON.stringify(kpData),
      },
      update: {
        titolo: parsed.titolo ?? undefined,
        narrativa: parsed.narrativa ?? undefined,
        minacce: parsed.minacce ? JSON.stringify(parsed.minacce) : undefined,
        opportunita: parsed.opportunita ? JSON.stringify(parsed.opportunita) : undefined,
        keyPointsData: JSON.stringify(kpData),
      },
    });
  } catch (err) {
    console.error("[Sintesi] errore Anthropic:", err);
  }
}

function costruisciDescrizioneQuadrante(
  quadrante: string,
  d1Nome: string | null,
  d1Pos: string | null,
  d1Neg: string | null,
  d2Nome: string | null,
  d2Pos: string | null,
  d2Neg: string | null
): string {
  if (!d1Nome || !d2Nome) return `Quadrante ${quadrante}`;

  const asseX = quadrante[0] === "+" ? d1Pos || `${d1Nome} alto` : d1Neg || `${d1Nome} basso`;
  const asseY = quadrante[1] === "+" ? d2Pos || `${d2Nome} alto` : d2Neg || `${d2Nome} basso`;

  return `${asseX} × ${asseY} (Driver: ${d1Nome} e ${d2Nome})`;
}

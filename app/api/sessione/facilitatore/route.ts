import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { calcolaRankingAggregato } from "@/lib/utils";

// GET /api/sessione/facilitatore?codice=XXX — vista completa per il facilitatore
export async function GET(req: NextRequest) {
  const codice = req.nextUrl.searchParams.get("codice");

  if (!codice) {
    return NextResponse.json({ errore: "codice obbligatorio" }, { status: 400 });
  }

  const sessione = await prisma.sessione.findUnique({
    where: { codiceFacilitatore: codice },
    include: {
      fenomeni: { orderBy: { createdAt: "asc" } },
      partecipanti: { orderBy: { createdAt: "asc" } },
      gruppi: {
        include: {
          partecipanti: true,
          scenarioOutput: true,
        },
        orderBy: { numero: "asc" },
      },
    },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "sessione non trovata" }, { status: 404 });
  }

  // Calcola ranking aggregato voti
  const tuttiVoti = await prisma.voto.findMany({
    where: { partecipante: { sessioneId: sessione.id } },
  });

  const rankingAggregato = calcolaRankingAggregato(tuttiVoti);

  return NextResponse.json({
    id: sessione.id,
    codice: sessione.codice,
    codiceFacilitatore: sessione.codiceFacilitatore,
    domandaRicerca: sessione.domandaRicerca,
    frameTemporale: sessione.frameTemporale,
    keyPoints: JSON.parse(sessione.keyPoints),
    stato: sessione.stato,
    driver1Nome: sessione.driver1Nome,
    driver1PosPolo: sessione.driver1PosPolo,
    driver1NegPolo: sessione.driver1NegPolo,
    driver2Nome: sessione.driver2Nome,
    driver2PosPolo: sessione.driver2PosPolo,
    driver2NegPolo: sessione.driver2NegPolo,
    fenomeni: sessione.fenomeni,
    partecipanti: sessione.partecipanti,
    gruppi: sessione.gruppi.map((g) => ({
      ...g,
      scenarioOutput: g.scenarioOutput
        ? {
            narrativa: g.scenarioOutput.narrativa,
            titolo: g.scenarioOutput.titolo,
            minacce: g.scenarioOutput.minacce ? JSON.parse(g.scenarioOutput.minacce) : [],
            opportunita: g.scenarioOutput.opportunita
              ? JSON.parse(g.scenarioOutput.opportunita)
              : [],
            keyPointsData: g.scenarioOutput.keyPointsData
              ? JSON.parse(g.scenarioOutput.keyPointsData)
              : {},
          }
        : null,
    })),
    rankingAggregato,
  });
}

// PATCH /api/sessione/facilitatore — aggiorna sessione (stato, driver, ecc.)
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { codice, ...aggiornamenti } = body;

  if (!codice) {
    return NextResponse.json({ errore: "codice obbligatorio" }, { status: 400 });
  }

  const sessione = await prisma.sessione.findUnique({
    where: { codiceFacilitatore: codice },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "sessione non trovata" }, { status: 404 });
  }

  // Gestisci keyPoints come JSON se presente
  if (aggiornamenti.keyPoints) {
    aggiornamenti.keyPoints = JSON.stringify(aggiornamenti.keyPoints);
  }

  const aggiornata = await prisma.sessione.update({
    where: { id: sessione.id },
    data: aggiornamenti,
  });

  return NextResponse.json({ ok: true, stato: aggiornata.stato });
}

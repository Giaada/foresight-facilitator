import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// GET /api/scenario-individuale?codicePartecipante=XXX
// Restituisce (o crea) lo ScenarioIndividuale del partecipante
export async function GET(req: NextRequest) {
  const codice = req.nextUrl.searchParams.get("codicePartecipante");
  if (!codice) return NextResponse.json({ error: "codicePartecipante mancante" }, { status: 400 });

  const partecipante = await prisma.partecipante.findUnique({
    where: { codice },
    include: {
      gruppo: true,
      scenarioIndividuale: {
        include: { messaggi: { orderBy: { createdAt: "asc" } } },
      },
    },
  });

  if (!partecipante) return NextResponse.json({ error: "Partecipante non trovato" }, { status: 404 });
  if (!partecipante.gruppo) return NextResponse.json({ error: "Gruppo non ancora assegnato" }, { status: 404 });

  // Crea lo scenario individuale se non esiste ancora
  let scenario = partecipante.scenarioIndividuale;
  if (!scenario) {
    scenario = await prisma.scenarioIndividuale.create({
      data: {
        partecipanteId: partecipante.id,
        sessioneId: partecipante.sessioneId,
        quadrante: partecipante.gruppo.quadrante,
      },
      include: { messaggi: { orderBy: { createdAt: "asc" } } },
    }) as typeof scenario;
  }

  return NextResponse.json({ scenario });
}

import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { sintetizzaGruppo } from "@/lib/agent";

// POST /api/scenario-individuale/sintetizza
// Il facilitatore avvia la sintesi di tutti i gruppi e passa alla fase di gruppo
export async function POST(req: NextRequest) {
  const { codiceFacilitatore } = await req.json();
  if (!codiceFacilitatore) return NextResponse.json({ error: "codiceFacilitatore mancante" }, { status: 400 });

  const sessione = await prisma.sessione.findUnique({
    where: { codiceFacilitatore },
    include: { gruppi: true },
  });

  if (!sessione) return NextResponse.json({ error: "Sessione non trovata" }, { status: 404 });

  // Sintetizza i gruppi in sequenza per evitare di saturare i rate limit Anthropic
  const errori: string[] = [];
  for (const g of sessione.gruppi as { id: string }[]) {
    try {
      await sintetizzaGruppo(g.id);
    } catch (err) {
      console.error(`[Sintesi] errore gruppo ${g.id}:`, err);
      errori.push(g.id);
    }
  }

  // Passa alla fase di gruppo anche se qualche sintesi ha fallito
  await prisma.sessione.update({
    where: { id: sessione.id },
    data: { stato: "scenario_planning_gruppo" },
  });

  return NextResponse.json({ ok: true, errori: errori.length > 0 ? errori : undefined });
}

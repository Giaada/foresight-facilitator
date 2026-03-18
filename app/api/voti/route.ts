import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// POST /api/voti — salva il ranking di un partecipante
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { codicePartecipante, ranking } = body;
  // ranking: Array<{ fenomenoId: string; posizione: number }>

  if (!codicePartecipante || !Array.isArray(ranking)) {
    return NextResponse.json(
      { errore: "codicePartecipante e ranking sono obbligatori" },
      { status: 400 }
    );
  }

  const partecipante = await prisma.partecipante.findUnique({
    where: { codice: codicePartecipante },
  });

  if (!partecipante) {
    return NextResponse.json({ errore: "partecipante non trovato" }, { status: 404 });
  }

  // Elimina voti precedenti e ricrea
  await prisma.voto.deleteMany({
    where: { partecipanteId: partecipante.id },
  });

  await prisma.voto.createMany({
    data: ranking.map((r: { fenomenoId: string; posizione: number }) => ({
      partecipanteId: partecipante.id,
      fenomenoId: r.fenomenoId,
      posizione: r.posizione,
    })),
  });

  await prisma.partecipante.update({
    where: { id: partecipante.id },
    data: { votato: true },
  });

  return NextResponse.json({ ok: true });
}

// GET /api/voti?codicePartecipante=XXX — recupera i voti di un partecipante
export async function GET(req: NextRequest) {
  const codicePartecipante = req.nextUrl.searchParams.get("codicePartecipante");

  if (!codicePartecipante) {
    return NextResponse.json({ errore: "codicePartecipante obbligatorio" }, { status: 400 });
  }

  const partecipante = await prisma.partecipante.findUnique({
    where: { codice: codicePartecipante },
    include: { voti: true },
  });

  if (!partecipante) {
    return NextResponse.json({ errore: "partecipante non trovato" }, { status: 404 });
  }

  return NextResponse.json({
    votato: partecipante.votato,
    voti: partecipante.voti,
  });
}

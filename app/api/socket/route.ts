import { NextRequest, NextResponse } from "next/server";

// Socket.io non è compatibile con App Router in modo nativo.
// Il server Socket.io è gestito in server.ts (custom server).
// Questa route restituisce info utili per il client.
export async function GET(_req: NextRequest) {
  return NextResponse.json({ ok: true, message: "Socket.io è gestito dal custom server" });
}

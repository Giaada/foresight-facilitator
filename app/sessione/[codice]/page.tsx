"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { io, Socket } from "socket.io-client";
import { HeaderSessione } from "@/components/shared/HeaderSessione";
import { VistaHorizonScanningPartecipante } from "@/components/partecipante/VistaHorizonScanningPartecipante";
import { VistaScenarioPlanningGruppo } from "@/components/partecipante/VistaScenarioPlanningGruppo";
import { VistaScenarioPlanningIndividuale } from "@/components/partecipante/VistaScenarioPlanningIndividuale";
import type { StatoSessione } from "@/lib/types";

interface Sessione {
  id: string;
  codice: string;
  domandaRicerca: string;
  frameTemporale: string;
  keyPoints: string[];
  stato: StatoSessione;
  fenomeni: Fenomeno[];
}

interface Fenomeno {
  id: string;
  testo: string;
  descrizione?: string | null;
}

interface Partecipante {
  id: string;
  nome: string;
  codice: string;
  sessioneId: string;
}

export default function PaginaSessione() {
  const { codice } = useParams<{ codice: string }>();
  const router = useRouter();
  const [sessione, setSessione] = useState<Sessione | null>(null);
  const [partecipante, setPartecipante] = useState<Partecipante | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [errore, setErrore] = useState("");

  const caricaSessione = useCallback(async () => {
    const res = await fetch(`/api/sessione?codice=${codice}`);
    if (!res.ok) { setErrore("Sessione non trovata."); return; }
    const json = await res.json();
    setSessione(json);
  }, [codice]);

  useEffect(() => {
    // Recupera partecipante da sessionStorage
    const datiP = sessionStorage.getItem("partecipante");
    if (!datiP) { router.push("/"); return; }
    setPartecipante(JSON.parse(datiP));
    caricaSessione();
  }, [caricaSessione, router]);

  useEffect(() => {
    if (!sessione) return;
    const s = io({ path: "/socket.io" });
    setSocket(s);
    s.emit("entra_sessione", { sessioneId: sessione.id, ruolo: "partecipante" });

    s.on("stato_aggiornato", ({ stato }: { stato: StatoSessione }) => {
      setSessione((prev) => prev ? { ...prev, stato } : prev);
      // Ricarica per avere dati aggiornati
      caricaSessione();
    });

    s.on("fenomeno_aggiunto", ({ fenomeno }: { fenomeno: Fenomeno }) => {
      setSessione((prev) => {
        if (!prev) return prev;
        // Evita duplicati
        if (prev.fenomeni.some((f) => f.id === fenomeno.id)) return prev;
        return { ...prev, fenomeni: [...prev.fenomeni, fenomeno] };
      });
    });

    s.on("fenomeno_approvato", ({ fenomenoId }: { fenomenoId: string }) => {
      // Ricarica per aggiornare la lista fenomeni approvati
      caricaSessione();
    });

    return () => { s.disconnect(); };
  }, [sessione?.id, caricaSessione]);

  if (errore) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-600">{errore}</p>
      </div>
    );
  }

  if (!sessione || !partecipante) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <HeaderSessione
        domandaRicerca={sessione.domandaRicerca}
        frameTemporale={sessione.frameTemporale}
        stato={sessione.stato}
      />

      {/* Benvenuto */}
      <div className="bg-indigo-700 text-white px-6 py-2">
        <div className="max-w-3xl mx-auto text-sm">
          Ciao, <span className="font-semibold">{partecipante.nome}</span>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {sessione.stato === "setup" && (
          <div className="text-center py-16 space-y-4">
            <div className="animate-pulse w-12 h-12 bg-indigo-100 rounded-full mx-auto flex items-center justify-center">
              <div className="w-6 h-6 bg-indigo-400 rounded-full" />
            </div>
            <p className="text-gray-600 font-medium">La sessione sta per iniziare...</p>
            <p className="text-gray-400 text-sm">Il facilitatore avvierà la fase di Horizon Scanning a breve</p>
          </div>
        )}

        {sessione.stato === "horizon_scanning" && (
          <VistaHorizonScanningPartecipante
            sessione={sessione}
            partecipante={partecipante}
            socket={socket}
          />
        )}

        {sessione.stato === "transizione" && (
          <div className="text-center py-16 space-y-4">
            <div className="w-12 h-12 bg-yellow-100 rounded-full mx-auto flex items-center justify-center">
              <span className="text-2xl">⏳</span>
            </div>
            <p className="text-gray-700 font-medium">Ottimo lavoro!</p>
            <p className="text-gray-500 text-sm">
              Il facilitatore sta analizzando i risultati e preparando la fase di Scenario Planning.
              Attendi qualche minuto.
            </p>
          </div>
        )}

        {sessione.stato === "scenario_planning_individuale" && (
          <VistaScenarioPlanningIndividuale
            partecipante={partecipante}
            sessioneId={sessione.id}
            socket={socket}
            sessione={sessione}
          />
        )}

        {(sessione.stato === "scenario_planning_gruppo" || sessione.stato === "concluso") && (
          <VistaScenarioPlanningGruppo
            partecipante={partecipante}
            sessioneId={sessione.id}
            socket={socket}
            sessione={sessione}
          />
        )}
      </main>
    </div>
  );
}

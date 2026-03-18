"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Users, Compass } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function Home() {
  const router = useRouter();
  const [codice, setCodice] = useState("");
  const [nome, setNome] = useState("");
  const [errore, setErrore] = useState("");
  const [caricamento, setCaricamento] = useState(false);

  async function accediComePartecipante() {
    if (!codice.trim() || !nome.trim()) {
      setErrore("Inserisci il codice sessione e il tuo nome.");
      return;
    }
    setCaricamento(true);
    setErrore("");

    // Verifica che la sessione esista
    const res = await fetch(`/api/sessione?codice=${codice.trim().toUpperCase()}`);
    if (!res.ok) {
      setErrore("Codice sessione non valido.");
      setCaricamento(false);
      return;
    }

    // Registra il partecipante
    const sessione = await res.json();
    const reg = await fetch("/api/partecipanti", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome: nome.trim(), codiceSessione: codice.trim().toUpperCase() }),
    });

    if (!reg.ok) {
      const err = await reg.json();
      setErrore(err.errore || "Errore durante la registrazione.");
      setCaricamento(false);
      return;
    }

    const partecipante = await reg.json();
    // Salva in sessionStorage
    sessionStorage.setItem("partecipante", JSON.stringify(partecipante));
    sessionStorage.setItem("sessioneId", sessione.id);
    router.push(`/sessione/${codice.trim().toUpperCase()}`);
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo / Titolo */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-2">
            <Compass size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Foresight Facilitator</h1>
          <p className="text-gray-500 text-sm">Sessioni di Strategic Foresight guidate dall&apos;AI</p>
        </div>

        {/* Card partecipante */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2 text-gray-700 font-medium">
            <Users size={18} className="text-indigo-600" />
            <span>Accedi come Partecipante</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Il tuo nome
              </label>
              <input
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="es. Maria Rossi"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Codice sessione
              </label>
              <input
                type="text"
                value={codice}
                onChange={(e) => setCodice(e.target.value.toUpperCase())}
                placeholder="es. ABC123"
                maxLength={6}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => e.key === "Enter" && accediComePartecipante()}
              />
            </div>
          </div>

          {errore && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{errore}</p>
          )}

          <Button
            onClick={accediComePartecipante}
            caricamento={caricamento}
            className="w-full"
            dimensione="lg"
          >
            Entra nella sessione
          </Button>
        </div>

        {/* Link facilitatore */}
        <div className="text-center">
          <p className="text-sm text-gray-500">
            Sei il facilitatore?{" "}
            <a href="/facilitatore" className="text-indigo-600 font-medium hover:underline">
              Crea o gestisci una sessione
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

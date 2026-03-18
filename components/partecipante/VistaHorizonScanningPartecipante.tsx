"use client";
import { useState, useEffect } from "react";
import { GripVertical, Plus, CheckCircle, Send } from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button } from "@/components/ui/Button";
import type { Socket } from "socket.io-client";

interface Fenomeno {
  id: string;
  testo: string;
  descrizione?: string | null;
}

interface Sessione {
  id: string;
  fenomeni: Fenomeno[];
}

interface Partecipante {
  id: string;
  nome: string;
  codice: string;
}

interface Props {
  sessione: Sessione;
  partecipante: Partecipante;
  socket: Socket | null;
}

function ItemSortable({ fenomeno, posizione }: { fenomeno: Fenomeno; posizione: number }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: fenomeno.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-3 bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm hover:border-indigo-300 transition-colors"
    >
      <span className="text-xs font-bold text-indigo-500 w-5 text-right shrink-0">{posizione}</span>
      <button
        {...attributes}
        {...listeners}
        className="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing shrink-0"
      >
        <GripVertical size={18} />
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 font-medium">{fenomeno.testo}</p>
        {fenomeno.descrizione && (
          <p className="text-xs text-gray-400 mt-0.5">{fenomeno.descrizione}</p>
        )}
      </div>
    </div>
  );
}

export function VistaHorizonScanningPartecipante({ sessione, partecipante, socket }: Props) {
  const [items, setItems] = useState<Fenomeno[]>(sessione.fenomeni);
  const [votato, setVotato] = useState(false);
  const [inviando, setInviando] = useState(false);
  const [nuovoFenomeno, setNuovoFenomeno] = useState("");
  const [aggiungi, setAggiungi] = useState(false);
  const [aggiungendo, setAggiungendo] = useState(false);

  // Aggiorna lista quando sessione cambia
  useEffect(() => {
    setItems((prev) => {
      const nuovi = sessione.fenomeni.filter((f) => !prev.some((p) => p.id === f.id));
      return [...prev, ...nuovi];
    });
  }, [sessione.fenomeni]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((i) => i.id === active.id);
        const newIndex = items.findIndex((i) => i.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }

  async function inviaVoto() {
    setInviando(true);
    const ranking = items.map((f, i) => ({ fenomenoId: f.id, posizione: i + 1 }));

    await fetch("/api/voti", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codicePartecipante: partecipante.codice, ranking }),
    });

    socket?.emit("voto_completato", {
      sessioneId: sessione.id,
      partecipanteId: partecipante.id,
    });

    setVotato(true);
    setInviando(false);
  }

  async function handleAggiungiFenomeno() {
    if (!nuovoFenomeno.trim()) return;
    setAggiungendo(true);

    const res = await fetch("/api/fenomeni", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        testo: nuovoFenomeno.trim(),
        sessioneId: sessione.id,
        codicePartecipante: partecipante.codice,
      }),
    });

    const fenomeno = await res.json();
    // Aggiunge localmente anche se non ancora approvato (per visibilità)
    setItems((prev) => [...prev, fenomeno]);
    socket?.emit("fenomeno_aggiunto", { sessioneId: sessione.id, fenomeno });
    setNuovoFenomeno("");
    setAggiungi(false);
    setAggiungendo(false);
  }

  if (votato) {
    return (
      <div className="text-center py-16 space-y-4">
        <div className="w-16 h-16 bg-green-100 rounded-full mx-auto flex items-center justify-center">
          <CheckCircle size={32} className="text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">Voto inviato!</h2>
        <p className="text-gray-500 text-sm max-w-sm mx-auto">
          Hai completato l&apos;Horizon Scanning. Attendi che il facilitatore avvii la fase di Scenario Planning.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Horizon Scanning</h2>
        <p className="text-gray-500 text-sm">
          Ordina i fenomeni dal più al meno rilevante rispetto alla domanda di ricerca. Trascina per riordinare.
        </p>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {items.map((f, i) => (
              <ItemSortable key={f.id} fenomeno={f} posizione={i + 1} />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Aggiungi fenomeno */}
      {!aggiungi ? (
        <button
          onClick={() => setAggiungi(true)}
          className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-xl py-3 text-sm text-gray-400 hover:border-indigo-300 hover:text-indigo-500 transition-colors"
        >
          <Plus size={16} />
          Aggiungi un fenomeno non presente
        </button>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <p className="text-sm font-medium text-gray-700">Nuovo fenomeno</p>
          <input
            value={nuovoFenomeno}
            onChange={(e) => setNuovoFenomeno(e.target.value)}
            placeholder="Descrivi il fenomeno o trend..."
            className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            autoFocus
            onKeyDown={(e) => e.key === "Enter" && handleAggiungiFenomeno()}
          />
          <div className="flex gap-2">
            <Button
              onClick={handleAggiungiFenomeno}
              caricamento={aggiungendo}
              dimensione="sm"
            >
              <Send size={13} className="mr-1" /> Proponi
            </Button>
            <Button
              variante="ghost"
              dimensione="sm"
              onClick={() => { setAggiungi(false); setNuovoFenomeno(""); }}
            >
              Annulla
            </Button>
          </div>
          <p className="text-xs text-gray-400">Il facilitatore potrà approvare o rifiutare il fenomeno proposto</p>
        </div>
      )}

      {/* Invio voto */}
      <div className="sticky bottom-4 pt-2">
        <Button
          onClick={inviaVoto}
          caricamento={inviando}
          dimensione="lg"
          className="w-full shadow-lg"
        >
          Conferma il mio ranking
        </Button>
      </div>
    </div>
  );
}

import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import ReactMarkdown from "react-markdown";
import { PrintButton } from "./PrintButton";
import { QuadrantVisualizer } from "@/components/ui/QuadrantVisualizer";

export const metadata = {
  title: "Report Sessione - Foresight",
};

export default async function ReportPage(props: { searchParams: Promise<{ sessioneId?: string }> }) {
  const searchParams = await props.searchParams;
  const sessioneId = searchParams?.sessioneId;

  if (!sessioneId) return redirect("/");

  const sessione = await prisma.sessione.findUnique({
    where: { id: sessioneId as string },
    include: {
      fenomeni: { where: { approvato: true } },
      gruppi: {
        include: {
          scenarioOutput: true,
          partecipanti: true,
        },
        orderBy: { numero: "asc" }
      }
    }
  });

  if (!sessione) return <div className="p-8 text-center text-gray-500">Sessione non trovata.</div>;

  return (
    <div className="min-h-screen bg-gray-50 print:bg-white text-gray-900 pb-20">
      <div className="max-w-4xl mx-auto p-8 print:p-0">
        <PrintButton />

        <div id="report-content" className="bg-white border border-gray-200 rounded-xl p-10 print:border-none print:shadow-none print:p-0">
          <header className="mb-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Report di Scenario Planning</h1>
            <p className="text-gray-500">Generato con Foresight Facilitator</p>
          </header>

          <section className="mb-10">
            <h2 className="text-xl font-bold border-b pb-2 mb-4 text-indigo-900">Dettagli Sessione</h2>
            <div className="grid grid-cols-2 gap-4 text-sm mt-4">
              <div>
                <span className="font-semibold text-gray-600 block">Domanda di Ricerca:</span>
                {sessione.domandaRicerca}
              </div>
              <div>
                <span className="font-semibold text-gray-600 block">Orizzonte Temporale:</span>
                {sessione.frameTemporale}
              </div>
              {sessione.driver1Nome && (
                <div>
                  <span className="font-semibold text-gray-600 block">Driver 1:</span>
                  {sessione.driver1Nome} <span className="text-gray-500">({sessione.driver1PosPolo} / {sessione.driver1NegPolo})</span>
                </div>
              )}
              {sessione.driver2Nome && (
                <div>
                  <span className="font-semibold text-gray-600 block">Driver 2:</span>
                  {sessione.driver2Nome} <span className="text-gray-500">({sessione.driver2PosPolo} / {sessione.driver2NegPolo})</span>
                </div>
              )}
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold border-b pb-2 mb-4 text-indigo-900 mt-10">Scenari Elaborati</h2>
            
            <div className="space-y-12 mt-6">
              {sessione.gruppi.length === 0 && (
                <p className="text-gray-500 italic">Nessun gruppo ha partecipato alla sessione.</p>
              )}
              {sessione.gruppi.map((g: any) => {
                const out = g.scenarioOutput;
                const minacce = out?.minacce ? JSON.parse(out.minacce) : [];
                const opportunita = out?.opportunita ? JSON.parse(out.opportunita) : [];

                return (
                  <div key={g.id} className="border border-indigo-100 rounded-lg p-6 bg-indigo-50/30 print:border-indigo-100 print:break-inside-avoid">
                    <div className="flex flex-col md:flex-row justify-between mb-6 border-b border-indigo-100 pb-4 gap-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-indigo-900 mb-1">
                          Gruppo {g.numero}: {out?.titolo || "Scenario Senza Titolo"}
                        </h3>
                        <p className="text-sm font-medium text-indigo-600 bg-indigo-100/50 inline-block px-2 py-0.5 rounded mb-4">Quadrante: {g.quadrante}</p>
                        <div className="text-xs text-gray-500 bg-white px-3 py-1.5 rounded-md border border-gray-100 inline-block">
                          <strong className="block mb-0.5">Partecipanti:</strong>
                          {g.partecipanti.length > 0 ? g.partecipanti.map((p: any) => p.nome).join(", ") : "Nessuno"}
                        </div>
                      </div>
                      <div className="shrink-0 bg-white p-2 rounded-xl border border-gray-100 shadow-sm print:hidden pr-6">
                        <QuadrantVisualizer
                          quadrante={g.quadrante}
                          d1Pos={sessione.driver1PosPolo || "Alto"}
                          d1Neg={sessione.driver1NegPolo || "Basso"}
                          d2Pos={sessione.driver2PosPolo || "Alto"}
                          d2Neg={sessione.driver2NegPolo || "Basso"}
                          size="sm"
                        />
                      </div>
                    </div>

                    <div className="space-y-6 text-sm">
                      {out?.narrativa ? (
                        <div>
                          <strong className="block text-gray-700 mb-2 uppercase text-xs tracking-wider">Narrativa dello Scenario</strong>
                          <div className="text-gray-800 leading-relaxed bg-white p-4 rounded-md border border-gray-100 shadow-sm">
                            <ReactMarkdown
                              components={{
                                p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
                                h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2 text-indigo-900" {...props} />,
                                h2: ({node, ...props}) => <h2 className="text-md font-bold mb-2 text-indigo-900" {...props} />,
                                h3: ({node, ...props}) => <h3 className="text-sm font-bold mb-1 text-indigo-900" {...props} />,
                                strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                                ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3" {...props} />,
                                li: ({node, ...props}) => <li className="mb-1" {...props} />,
                              }}
                            >{out.narrativa}</ReactMarkdown>
                          </div>
                        </div>
                      ) : (
                        <p className="text-gray-400 italic">Nessuna narrativa sviluppata dal gruppo.</p>
                      )}

                      <div className="grid grid-cols-2 gap-6 mt-4">
                        <div className="bg-green-50/50 p-4 rounded-md border border-green-100">
                          <strong className="block text-green-800 mb-3 uppercase text-xs tracking-wider">Opportunità Identificate</strong>
                          {opportunita.length > 0 ? (
                            <ul className="space-y-2">
                              {opportunita.map((opp: string, i: number) => (
                                <li key={i} className="flex gap-2 text-green-700">
                                  <span className="text-green-500">✓</span>
                                  <span>{opp}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-gray-400 italic">Nessuna identificata.</span>
                          )}
                        </div>
                        <div className="bg-red-50/50 p-4 rounded-md border border-red-100">
                          <strong className="block text-red-800 mb-3 uppercase text-xs tracking-wider">Minacce Identificate</strong>
                          {minacce.length > 0 ? (
                            <ul className="space-y-2">
                              {minacce.map((min: string, i: number) => (
                                <li key={i} className="flex gap-2 text-red-700">
                                  <span className="text-red-400">⚠️</span>
                                  <span>{min}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-gray-400 italic">Nessuna identificata.</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

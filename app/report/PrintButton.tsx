"use client";
import { useState } from "react";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";

export function PrintButton() {
  const router = useRouter();
  const [generando, setGenerando] = useState(false);

  const handleDownload = async () => {
    setGenerando(true);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      const element = document.getElementById("report-content");
      if (!element) return;
      
      const opt = {
        margin: 10,
        filename: 'Report_Scenario_Planning.pdf',
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (e) {
      console.error(e);
      window.print(); // fallback if library fails to load
    }
    setGenerando(false);
  };
  
  return (
    <div className="flex gap-4 print:hidden mb-8">
      <Button onClick={() => router.back()} variante="secondary" className="bg-white border shadow-sm text-gray-700">
        <ArrowLeft size={16} className="mr-2" /> Torna indietro
      </Button>
      <Button 
        onClick={handleDownload} 
        disabled={generando}
        className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm min-w-[200px]"
      >
        <Printer size={16} className="mr-2" /> 
        {generando ? "Generazione in corso..." : "Scarica PDF"}
      </Button>
    </div>
  );
}

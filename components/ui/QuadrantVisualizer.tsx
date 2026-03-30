import React from "react";

interface QuadrantVisualizerProps {
  quadrante: string | null; // "++", "+-", "-+", "--" oppure null se non applicato
  d1Pos: string;
  d1Neg: string;
  d2Pos: string;
  d2Neg: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function QuadrantVisualizer({ 
  quadrante, 
  d1Pos, 
  d1Neg, 
  d2Pos, 
  d2Neg,
  size = "md",
  className = ""
}: QuadrantVisualizerProps) {
  const sizeClass = {
    sm: "w-24 h-24 text-[10px]",
    md: "w-36 h-36 text-xs",
    lg: "w-48 h-48 text-sm",
  }[size];

  const arrowOffset = {
    sm: "-14px",
    md: "-18px",
    lg: "-22px"
  }[size];

  const labelOffsetY = {
    sm: "-top-5 -bottom-5",
    md: "-top-6 -bottom-6",
    lg: "-top-8 -bottom-8"
  }[size];

  const labelOffsetX = {
    sm: "-left-1 -right-1",
    md: "-left-2 -right-2",
    lg: "-left-4 -right-4"
  }[size];

  const [topDist, bottomDist] = labelOffsetY.split(" ");
  const [leftDist, rightDist] = labelOffsetX.split(" ");

  return (
    <div className={`relative ${sizeClass} mx-auto my-6 font-sans shrink-0 ${className}`}>
      {/* Testi Assi */}
      <div className={`absolute ${topDist} left-1/2 -translate-x-1/2 text-center text-slate-500 font-semibold whitespace-nowrap hidden sm:block capitalize`}>{d2Pos || "Alto"}</div>
      <div className={`absolute ${bottomDist} left-1/2 -translate-x-1/2 text-center text-slate-500 font-semibold whitespace-nowrap hidden sm:block capitalize`}>{d2Neg || "Basso"}</div>
      
      {/* Testi X con writing-mode per compattezza sui lati */}
      <div className={`absolute top-1/2 ${leftDist} -translate-y-1/2 -translate-x-full text-center text-slate-500 font-semibold whitespace-nowrap rotate-180 capitalize`} style={{ writingMode: 'vertical-rl' }}>{d1Neg || "Basso"}</div>
      <div className={`absolute top-1/2 ${rightDist} -translate-y-1/2 translate-x-full text-center text-slate-500 font-semibold whitespace-nowrap capitalize`} style={{ writingMode: 'vertical-rl' }}>{d1Pos || "Alto"}</div>

      {/* Quadranti Sfondo per Highlight (Z-0) */}
      <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 z-0 isolate">
        <div className={`rounded-tl-md flex items-center justify-center transition-colors ${quadrante === '-+' ? 'bg-indigo-600/15 shadow-inner' : 'bg-slate-50'}`}>
            <span className={`font-mono font-bold text-lg select-none ${quadrante === '-+' ? 'text-indigo-900/60' : 'text-slate-300'}`}>-+</span>
        </div>
        <div className={`rounded-tr-md flex items-center justify-center transition-colors ${quadrante === '++' ? 'bg-indigo-600/15 shadow-inner' : 'bg-slate-50'}`}>
            <span className={`font-mono font-bold text-lg select-none ${quadrante === '++' ? 'text-indigo-900/60' : 'text-slate-300'}`}>++</span>
        </div>
        <div className={`rounded-bl-md flex items-center justify-center transition-colors ${quadrante === '--' ? 'bg-indigo-600/15 shadow-inner' : 'bg-slate-50'}`}>
            <span className={`font-mono font-bold text-lg select-none ${quadrante === '--' ? 'text-indigo-900/60' : 'text-slate-300'}`}>--</span>
        </div>
        <div className={`rounded-br-md flex items-center justify-center transition-colors ${quadrante === '+-' ? 'bg-indigo-600/15 shadow-inner' : 'bg-slate-50'}`}>
            <span className={`font-mono font-bold text-lg select-none ${quadrante === '+-' ? 'text-indigo-900/60' : 'text-slate-300'}`}>+-</span>
        </div>
      </div>

      {/* Layout Assi e Frecce (Z-10) */}
      
      {/* Asse Y (verticale) */}
      <div className="absolute left-1/2 top-0 bottom-0 w-[3px] bg-slate-800 -translate-x-1/2 z-10" style={{ top: arrowOffset, bottom: arrowOffset }}></div>
      <div className="absolute left-1/2 w-0 h-0 border-l-[7px] border-r-[7px] border-b-[10px] border-l-transparent border-r-transparent border-b-slate-800 -translate-x-1/2 z-10" style={{ top: `calc(${arrowOffset} - 4px)` }}></div>
      <div className="absolute left-1/2 w-0 h-0 border-l-[7px] border-r-[7px] border-t-[10px] border-l-transparent border-r-transparent border-t-slate-800 -translate-x-1/2 z-10" style={{ bottom: `calc(${arrowOffset} - 4px)` }}></div>

      {/* Asse X (orizzontale) */}
      <div className="absolute top-1/2 left-0 right-0 h-[3px] bg-slate-800 -translate-y-1/2 z-10" style={{ left: arrowOffset, right: arrowOffset }}></div>
      <div className="absolute top-1/2 w-0 h-0 border-t-[7px] border-b-[7px] border-l-[10px] border-t-transparent border-b-transparent border-l-slate-800 -translate-y-1/2 z-10" style={{ right: `calc(${arrowOffset} - 4px)` }}></div>
      <div className="absolute top-1/2 w-0 h-0 border-t-[7px] border-b-[7px] border-r-[10px] border-t-transparent border-b-transparent border-r-slate-800 -translate-y-1/2 z-10" style={{ left: `calc(${arrowOffset} - 4px)` }}></div>

    </div>
  );
}

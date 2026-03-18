"use client";
import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variante?: "default" | "verde" | "giallo" | "rosso" | "grigio";
  className?: string;
}

export function Badge({ children, variante = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
        {
          "bg-blue-100 text-blue-800": variante === "default",
          "bg-green-100 text-green-800": variante === "verde",
          "bg-yellow-100 text-yellow-800": variante === "giallo",
          "bg-red-100 text-red-800": variante === "rosso",
          "bg-gray-100 text-gray-700": variante === "grigio",
        },
        className
      )}
    >
      {children}
    </span>
  );
}

"use client";
import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: "primary" | "secondary" | "danger" | "ghost";
  dimensione?: "sm" | "md" | "lg";
  caricamento?: boolean;
}

export function Button({
  children,
  variante = "primary",
  dimensione = "md",
  caricamento = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || caricamento}
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500": variante === "primary",
          "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-indigo-500": variante === "secondary",
          "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500": variante === "danger",
          "text-gray-600 hover:bg-gray-100 focus:ring-gray-400": variante === "ghost",
          "text-xs px-2.5 py-1.5": dimensione === "sm",
          "text-sm px-4 py-2": dimensione === "md",
          "text-base px-6 py-3": dimensione === "lg",
        },
        className
      )}
      {...props}
    >
      {caricamento ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  );
}

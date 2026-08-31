import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    PropsWithChildren {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-terracotta text-white hover:bg-terracotta-hover active:bg-terracotta-dark disabled:bg-[#F7E5EC] disabled:text-[#B99AA7] focus:ring-terracotta",
  secondary:
    "border border-warm-border bg-white text-charcoal hover:bg-cream-soft disabled:text-muted-warm focus:ring-terracotta",
  danger:
    "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300 focus:ring-red-500",
};

export default function Button({
  children,
  className = "",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

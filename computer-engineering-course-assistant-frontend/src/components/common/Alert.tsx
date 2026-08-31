import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type AlertKind = "error" | "success" | "info";

interface AlertProps {
  kind?: AlertKind;
  children: React.ReactNode;
}

const styles: Record<AlertKind, string> = {
  error: "border-red-200 bg-red-50 text-red-800",
  success: "border-olive/30 bg-olive-soft text-olive-hover",
  info: "border-warm-border bg-cream-soft text-charcoal",
};

const icons = {
  error: AlertCircle,
  success: CheckCircle2,
  info: Info,
};

export default function Alert({ kind = "info", children }: AlertProps) {
  const Icon = icons[kind];

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${styles[kind]}`}
      role={kind === "error" ? "alert" : "status"}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

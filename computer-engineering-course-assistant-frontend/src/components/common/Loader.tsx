import { LoaderCircle } from "lucide-react";

interface LoaderProps {
  label?: string;
}

export default function Loader({ label = "Yükleniyor..." }: LoaderProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-warm-gray" role="status">
      <LoaderCircle className="h-4 w-4 animate-spin" />
      <span>{label}</span>
    </div>
  );
}

import { FileText } from "lucide-react";
import type { Source } from "../../types/chat";

interface SourceListProps {
  sources: Source[];
}

export default function SourceList({ sources }: SourceListProps) {
  const uniqueNames = Array.from(
    new Set(sources.map((source) => source.documentName)),
  );

  if (uniqueNames.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-warm-border pt-3">
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-warm">
        Kaynaklar
      </p>
      <div className="flex flex-wrap gap-2">
        {uniqueNames.map((name) => (
          <span
            key={name}
            className="inline-flex items-center gap-1.5 rounded-lg bg-cream-soft px-2.5 py-1.5 text-xs font-medium text-warm-gray"
          >
            <FileText className="h-3.5 w-3.5" />
            {name}
          </span>
        ))}
      </div>
    </div>
  );
}

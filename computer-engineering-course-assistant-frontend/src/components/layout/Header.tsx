import { Code2 } from "lucide-react";

export default function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-warm-border bg-white px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-terracotta text-white">
          <Code2 className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-base font-bold text-charcoal md:text-lg">
            Bilgisayar Mühendisliği Ders Asistanı
          </h1>
          <p className="hidden text-xs text-warm-gray sm:block">
            Ders materyallerine dayalı yerel akıllı asistan
          </p>
        </div>
      </div>

      <div className="hidden items-center gap-1.5 rounded-md border border-warm-border bg-white px-2.5 py-1 text-xs font-medium text-warm-gray sm:flex">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-olive" />
        Yerel model aktif
      </div>
    </header>
  );
}

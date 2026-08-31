import {
  BrainCircuit,
  Database,
  FileSearch,
  HardDrive,
  MessageSquareText,
} from "lucide-react";

const steps = [
  {
    icon: MessageSquareText,
    title: "Sorunu Sor",
    text: "Bir ders seçin ve yüklediğiniz materyallerle ilgili sorunuzu yazın.",
  },
  {
    icon: FileSearch,
    title: "İlgili Bilgiyi Bul",
    text: "Sistem, sorunuzla en alakalı bölümleri seçtiğiniz dersin kaynakları arasından bulur.",
  },
  {
    icon: Database,
    title: "Kaynağa Dayalı Yanıt",
    text: "Bulunan bilgiler kullanılarak yanıt, ders materyalleriniz temel alınarak oluşturulur.",
  },
  {
    icon: BrainCircuit,
    title: "Yerel Yapay Zekâ",
    text: "Yanıt üretme işlemi Microsoft Foundry Local üzerinden cihazınızda gerçekleştirilir.",
  },
];

const howToSteps = [
  { number: 1, title: "Ders oluştur" },
  { number: 2, title: "PDF kaynaklarını yükle" },
  { number: 3, title: "Chat ekranında dersini seç" },
  { number: 4, title: "Sorunu sor" },
];

const technologies = [
  "React",
  "TypeScript",
  "FastAPI",
  "SQLite",
  "Microsoft Foundry Local",
  "phi-4-mini",
  "qwen3-embedding-0.6b",
];

export default function AboutPage() {
  return (
    <section className="mx-auto max-w-5xl space-y-6">
      <div className="rounded-lg border border-warm-border bg-white p-7 md:p-10">
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-terracotta-soft text-terracotta">
          <HardDrive className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-charcoal md:text-3xl">
          Bilgisayar Mühendisliği Ders Asistanı
        </h2>
        <p className="mt-4 max-w-3xl leading-7 text-warm-gray">
          Yüklediğiniz ders materyallerinden yararlanarak sorularınızı
          yanıtlayan, yerel olarak çalışan bir ders asistanıdır. Derslerinizi
          oluşturabilir, PDF kaynaklarınızı ekleyebilir ve materyalleriniz
          üzerinden sorular sorabilirsiniz.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {steps.map(({ icon: Icon, title, text }) => (
          <article
            key={title}
            className="rounded-lg border border-warm-border bg-white p-5"
          >
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-terracotta-soft text-terracotta">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-charcoal">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-warm-gray">{text}</p>
          </article>
        ))}
      </div>

      <div className="rounded-lg border border-lavender/25 bg-lavender-soft p-5">
        <h3 className="font-bold text-lavender-hover">
          Verileriniz cihazınızda kalır
        </h3>
        <p className="mt-2 text-sm leading-6 text-lavender-hover/90">
          Ders materyalleri, oluşturulan indeksler ve yapay zekâ işlemleri
          yerel ortamda çalışacak şekilde tasarlanmıştır. Modeller önceden
          hazırlandıktan sonra temel soru-cevap işlemleri için harici bir
          yapay zekâ servisine veri gönderilmez.
        </p>
      </div>

      <div className="rounded-lg border border-warm-border bg-white p-5">
        <h3 className="font-bold text-charcoal">Nasıl kullanılır?</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {howToSteps.map(({ number, title }) => (
            <div key={number} className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-terracotta-soft text-sm font-bold text-terracotta">
                {number}
              </div>
              <p className="pt-1 text-sm font-medium text-charcoal">
                {title}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-warm-border bg-white p-5">
        <h3 className="font-bold text-charcoal">Kullanılan Teknolojiler</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {technologies.map((technology) => (
            <span
              key={technology}
              className="rounded-md border border-warm-border bg-cream-soft px-3 py-1 text-xs font-medium text-warm-gray"
            >
              {technology}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

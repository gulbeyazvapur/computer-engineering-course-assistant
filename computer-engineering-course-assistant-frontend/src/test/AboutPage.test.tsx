import { render, screen } from "@testing-library/react";
import AboutPage from "../pages/AboutPage";

test("A, B. yeni başlık görünür, eski başlık görünmez", () => {
  render(<AboutPage />);

  expect(
    screen.getByText("Bilgisayar Mühendisliği Ders Asistanı"),
  ).toBeInTheDocument();
  expect(screen.queryByText("Local RAG Ders Asistanı")).not.toBeInTheDocument();
});

test("hero: 'tamamen yerel çalışan' artık görünmüyor, 'yerel olarak çalışan' görünüyor", () => {
  render(<AboutPage />);

  expect(screen.queryByText(/tamamen yerel çalışan/)).not.toBeInTheDocument();
  expect(
    screen.getByText(
      "Yüklediğiniz ders materyallerinden yararlanarak sorularınızı yanıtlayan, yerel olarak çalışan bir ders asistanıdır. Derslerinizi oluşturabilir, PDF kaynaklarınızı ekleyebilir ve materyalleriniz üzerinden sorular sorabilirsiniz.",
    ),
  ).toBeInTheDocument();
});

test("'Kabaca:' satırı artık görünmüyor", () => {
  render(<AboutPage />);

  expect(screen.queryByText(/Kabaca:/)).not.toBeInTheDocument();
});

test("C. 4 kullanıcı-dostu kart başlığı görünür", () => {
  render(<AboutPage />);

  expect(screen.getByText("Sorunu Sor")).toBeInTheDocument();
  expect(screen.getByText("İlgili Bilgiyi Bul")).toBeInTheDocument();
  expect(screen.getByText("Kaynağa Dayalı Yanıt")).toBeInTheDocument();
  expect(screen.getByText("Yerel Yapay Zekâ")).toBeInTheDocument();
});

test("D. 'Verileriniz cihazınızda kalır' bölümü görünür", () => {
  render(<AboutPage />);

  expect(screen.getByText("Verileriniz cihazınızda kalır")).toBeInTheDocument();
});

test("E. 'Nasıl kullanılır?' bölümü ve 4 adım görünür", () => {
  render(<AboutPage />);

  expect(screen.getByText("Nasıl kullanılır?")).toBeInTheDocument();
  expect(screen.getByText("Ders oluştur")).toBeInTheDocument();
  expect(screen.getByText("PDF kaynaklarını yükle")).toBeInTheDocument();
  expect(screen.getByText("Chat ekranında dersini seç")).toBeInTheDocument();
  expect(screen.getByText("Sorunu sor")).toBeInTheDocument();
});

test("F, G. 'Kullanılan Teknolojiler' bölümü ve teknoloji isimleri görünür", () => {
  render(<AboutPage />);

  expect(screen.getByText("Kullanılan Teknolojiler")).toBeInTheDocument();
  expect(screen.getByText("Microsoft Foundry Local")).toBeInTheDocument();
  expect(screen.getByText("phi-4-mini")).toBeInTheDocument();
  expect(screen.getByText("qwen3-embedding-0.6b")).toBeInTheDocument();
  expect(screen.getByText("React")).toBeInTheDocument();
  expect(screen.getByText("TypeScript")).toBeInTheDocument();
  expect(screen.getByText("FastAPI")).toBeInTheDocument();
  expect(screen.getByText("SQLite")).toBeInTheDocument();
});

test("H. ana kullanıcı metinlerinde geliştirici terimleri yok (teknoloji etiketleri hariç)", () => {
  const { container } = render(<AboutPage />);

  // "qwen3-embedding-0.6b" is expected in the technologies chip section
  // (requirement G) -- exclude that section before checking the rest of
  // the page for leaked developer jargon in the main prose.
  const techHeading = screen.getByText("Kullanılan Teknolojiler");
  const techSectionText = techHeading.closest("div")?.textContent ?? "";
  const fullText = container.textContent ?? "";
  const mainText = fullText.replace(techSectionText, "");

  expect(mainText).not.toMatch(/semantic search/i);
  expect(mainText).not.toMatch(/\bchunk/i);
  expect(mainText).not.toMatch(/\bcontext\b/i);
  expect(mainText).not.toMatch(/\bembedding\b/i);
  expect(mainText).not.toMatch(/\bretrieval\b/i);
});

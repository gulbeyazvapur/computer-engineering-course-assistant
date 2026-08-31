const MAX_FILE_SIZE_MB = 20;

export function validatePdfFile(file: File | null): string | null {
  if (!file) {
    return "Lütfen bir PDF dosyası seçin.";
  }

  const isPdfName = file.name.toLowerCase().endsWith(".pdf");
  const isPdfMime =
    file.type === "application/pdf" || file.type === "";

  if (!isPdfName || !isPdfMime) {
    return "Yalnızca PDF dosyaları desteklenir.";
  }

  if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
    return `Dosya boyutu en fazla ${MAX_FILE_SIZE_MB} MB olabilir.`;
  }

  return null;
}

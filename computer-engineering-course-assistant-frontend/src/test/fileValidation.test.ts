import { validatePdfFile } from "../utils/fileValidation";

test("pdf dışındaki dosyayı reddeder", () => {
  const file = new File(["hello"], "not.txt", { type: "text/plain" });
  expect(validatePdfFile(file)).toMatch(/Yalnızca PDF/);
});

test("pdf dosyasını kabul eder", () => {
  const file = new File(["pdf"], "notes.pdf", { type: "application/pdf" });
  expect(validatePdfFile(file)).toBeNull();
});

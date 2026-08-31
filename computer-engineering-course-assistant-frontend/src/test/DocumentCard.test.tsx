import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DocumentCard from "../components/documents/DocumentCard";
import * as documentService from "../services/documentService";
import type { CourseDocument } from "../types/document";

vi.mock("../services/documentService");

const baseDocument: CourseDocument = {
  id: 10,
  courseId: 1,
  courseName: "Bilgisayar Ağları",
  fileName: "tcp-udp.pdf",
  chunkCount: 4,
  createdAt: "2026-08-30T10:00:00Z",
};

afterEach(() => {
  vi.restoreAllMocks();
});

test("doküman kartı temel bilgileri render eder", () => {
  render(<DocumentCard document={baseDocument} onDeleted={() => undefined} />);

  expect(screen.getByText("tcp-udp.pdf")).toBeInTheDocument();
  expect(screen.getByText("Bilgisayar Ağları")).toBeInTheDocument();
  expect(screen.getByText("4 chunk")).toBeInTheDocument();
});

test("A. çöp kutusuna basınca native confirm değil, custom modal açılır", () => {
  const confirmSpy = vi.spyOn(window, "confirm");

  render(<DocumentCard document={baseDocument} onDeleted={() => undefined} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));

  expect(confirmSpy).not.toHaveBeenCalled();
  expect(screen.getByRole("dialog")).toBeInTheDocument();
});

test("B, C. modal başlığı ve dosya adı doğru gösterilir", () => {
  render(<DocumentCard document={baseDocument} onDeleted={() => undefined} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));

  const dialog = screen.getByRole("dialog");
  expect(dialog).toHaveTextContent("Kaynağı sil");
  expect(dialog).toHaveTextContent("tcp-udp.pdf");
});

test("D. İptal -> modal kapanır, deleteDocument çağrılmaz", () => {
  const deleteDocument = vi.mocked(documentService.deleteDocument);
  const onDeleted = vi.fn();

  render(<DocumentCard document={baseDocument} onDeleted={onDeleted} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));
  fireEvent.click(screen.getByRole("button", { name: "İptal" }));

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(deleteDocument).not.toHaveBeenCalled();
  expect(onDeleted).not.toHaveBeenCalled();
});

test("E, F. Kaynağı Sil -> deleteDocument çağrılır, başarı sonrası modal kapanır", async () => {
  const deleteDocument = vi
    .mocked(documentService.deleteDocument)
    .mockResolvedValue(undefined);
  const onDeleted = vi.fn().mockResolvedValue(undefined);

  render(<DocumentCard document={baseDocument} onDeleted={onDeleted} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));
  fireEvent.click(screen.getByRole("button", { name: "Kaynağı Sil" }));

  await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
  expect(deleteDocument).toHaveBeenCalledWith(10);
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("G. silme sırasında onay butonu ve iptal butonu disabled olur", async () => {
  let resolveDelete: () => void = () => undefined;
  vi.mocked(documentService.deleteDocument).mockReturnValue(
    new Promise<void>((resolve) => {
      resolveDelete = () => resolve(undefined);
    }),
  );
  const onDeleted = vi.fn();

  render(<DocumentCard document={baseDocument} onDeleted={onDeleted} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));
  fireEvent.click(screen.getByRole("button", { name: "Kaynağı Sil" }));

  expect(
    await screen.findByRole("button", { name: "Siliniyor..." }),
  ).toBeDisabled();
  expect(screen.getByRole("button", { name: "İptal" })).toBeDisabled();

  resolveDelete();
  await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
});

test("silme API hatası modal içinde güvenli mesajla gösterilir, modal açık kalır", async () => {
  vi.mocked(documentService.deleteDocument).mockRejectedValue({
    isAxiosError: true,
    response: {
      data: { error: "DOCUMENT_NOT_FOUND", message: "Doküman bulunamadı." },
    },
  });
  const onDeleted = vi.fn();

  render(<DocumentCard document={baseDocument} onDeleted={onDeleted} />);
  fireEvent.click(screen.getByLabelText("Kaynağı sil"));
  fireEvent.click(screen.getByRole("button", { name: "Kaynağı Sil" }));

  expect(await screen.findByText("Doküman bulunamadı.")).toBeInTheDocument();
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(onDeleted).not.toHaveBeenCalled();
});

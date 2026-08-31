import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DocumentsPage from "../pages/DocumentsPage";
import * as courseService from "../services/courseService";
import * as documentService from "../services/documentService";
import type { CourseDocument } from "../types/document";

vi.mock("../services/courseService");
vi.mock("../services/documentService");

const documents: CourseDocument[] = [
  {
    id: 10,
    courseId: 1,
    courseName: "Bilgisayar Ağları",
    fileName: "tcp-udp.pdf",
    chunkCount: 4,
    createdAt: "2026-08-30T10:00:00Z",
  },
  {
    id: 11,
    courseId: 2,
    courseName: "İşletim Sistemleri",
    fileName: "deadlock.pdf",
    chunkCount: 2,
    createdAt: "2026-08-30T09:00:00Z",
  },
];

afterEach(() => {
  vi.restoreAllMocks();
});

test("doküman listesi render edilir", async () => {
  vi.mocked(courseService.getCourses).mockResolvedValue([]);
  vi.mocked(documentService.getDocuments).mockResolvedValue(documents);

  render(<DocumentsPage />);

  expect(await screen.findByText("tcp-udp.pdf")).toBeInTheDocument();
  expect(screen.getByText("deadlock.pdf")).toBeInTheDocument();
});

test("silme onaylandıktan sonra kaynak listeden kalkar (hard refresh yok)", async () => {
  vi.mocked(courseService.getCourses).mockResolvedValue([]);
  vi.mocked(documentService.getDocuments)
    .mockResolvedValueOnce(documents)
    .mockResolvedValueOnce([documents[1]]);
  vi.mocked(documentService.deleteDocument).mockResolvedValue(undefined);

  render(<DocumentsPage />);
  await screen.findByText("tcp-udp.pdf");

  fireEvent.click(screen.getAllByLabelText("Kaynağı sil")[0]);
  fireEvent.click(screen.getByRole("button", { name: "Kaynağı Sil" }));

  await waitFor(() =>
    expect(screen.queryByText("tcp-udp.pdf")).not.toBeInTheDocument(),
  );
  expect(screen.getByText("deadlock.pdf")).toBeInTheDocument();
  expect(documentService.getDocuments).toHaveBeenCalledTimes(2);
});

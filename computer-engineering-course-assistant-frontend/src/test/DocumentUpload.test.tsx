import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DocumentUpload from "../components/documents/DocumentUpload";
import * as documentService from "../services/documentService";
import type { Course } from "../types/course";
import type { DocumentUploadResponse } from "../types/document";

vi.mock("../services/documentService");

const courses: Course[] = [{ id: 1, name: "Bilgisayar Ağları" }];

function okResponse(fileName: string): DocumentUploadResponse {
  return { id: 1, courseId: 1, fileName, chunkCount: 1, message: "ok" };
}

function makeFile(name: string, sizeBytes = 1024, type = "application/pdf"): File {
  const file = new File(["x"], name, { type });
  Object.defineProperty(file, "size", { value: sizeBytes });
  return file;
}

function selectCourse() {
  fireEvent.change(screen.getByLabelText("Ders"), { target: { value: "1" } });
}

afterEach(() => {
  vi.restoreAllMocks();
});

test("A. multiple file input birden fazla dosya kabul eder", () => {
  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  const input = screen.getByLabelText("PDF") as HTMLInputElement;

  expect(input.multiple).toBe(true);
});

test("B. 2 dosya seçilince ikisi de listede görünür", () => {
  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);

  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf"), makeFile("b.pdf")] },
  });

  expect(screen.getByText("a.pdf")).toBeInTheDocument();
  expect(screen.getByText("b.pdf")).toBeInTheDocument();
});

test("C. seçilen dosyalar başlangıçta Bekliyor durumundadır", () => {
  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);

  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf")] },
  });

  expect(screen.getAllByText("Bekliyor")).toHaveLength(1);
});

test("D. upload sequential çalışır -- ikinci request birinci bitmeden başlamaz", async () => {
  const resolvers: Array<() => void> = [];
  const uploadDocument = vi.mocked(documentService.uploadDocument).mockImplementation(
    (_courseId, file) =>
      new Promise((resolve) => {
        resolvers.push(() => resolve(okResponse(file.name)));
      }),
  );

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf"), makeFile("b.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanları Yükle" }));

  await waitFor(() => expect(uploadDocument).toHaveBeenCalledTimes(1));
  expect(uploadDocument).toHaveBeenCalledTimes(1); // second call must not have fired yet

  resolvers[0]();
  await waitFor(() => expect(uploadDocument).toHaveBeenCalledTimes(2));

  resolvers[1]();
  await waitFor(() =>
    expect(screen.getByText("2 doküman başarıyla işlendi.")).toBeInTheDocument(),
  );
});

test("E. iki dosya da başarılı olursa özet gösterilir ve refresh bir kez çağrılır", async () => {
  vi.mocked(documentService.uploadDocument).mockImplementation((_courseId, file) =>
    Promise.resolve(okResponse(file.name)),
  );
  const onUploaded = vi.fn().mockResolvedValue(undefined);

  render(<DocumentUpload courses={courses} onUploaded={onUploaded} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf"), makeFile("b.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanları Yükle" }));

  expect(
    await screen.findByText("2 doküman başarıyla işlendi."),
  ).toBeInTheDocument();
  expect(onUploaded).toHaveBeenCalledTimes(1);
  expect(screen.queryByText("a.pdf")).not.toBeInTheDocument();
  expect(screen.queryByText("b.pdf")).not.toBeInTheDocument();
});

test("F. bir dosya hata verirse batch devam eder (success, error, success)", async () => {
  const uploadDocument = vi.mocked(documentService.uploadDocument);
  uploadDocument
    .mockResolvedValueOnce(okResponse("a.pdf"))
    .mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        data: { error: "PDF_TEXT_EXTRACTION_ERROR", message: "PDF işlenemedi." },
      },
    })
    .mockResolvedValueOnce(okResponse("c.pdf"));

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf"), makeFile("b.pdf"), makeFile("c.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanları Yükle" }));

  await waitFor(() => expect(uploadDocument).toHaveBeenCalledTimes(3));
  expect(
    await screen.findByText("2 doküman başarıyla işlendi, 1 doküman yüklenemedi."),
  ).toBeInTheDocument();
  expect(screen.getByText("b.pdf")).toBeInTheDocument();
  expect(screen.getByText("PDF işlenemedi.")).toBeInTheDocument();
  expect(screen.queryByText("a.pdf")).not.toBeInTheDocument();
  expect(screen.queryByText("c.pdf")).not.toBeInTheDocument();
});

test("G. 20 MB üzerindeki dosya yüklenmez ama diğerleri devam eder", async () => {
  const uploadDocument = vi
    .mocked(documentService.uploadDocument)
    .mockImplementation((_courseId, file) => Promise.resolve(okResponse(file.name)));

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: {
      files: [
        makeFile("small1.pdf", 5 * 1024 * 1024),
        makeFile("huge.pdf", 25 * 1024 * 1024),
        makeFile("small2.pdf", 4 * 1024 * 1024),
      ],
    },
  });

  expect(screen.getByText(/Dosya boyutu en fazla 20 MB olabilir\./)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Dokümanları Yükle" }));

  await waitFor(() => expect(uploadDocument).toHaveBeenCalledTimes(2));
  expect(uploadDocument).not.toHaveBeenCalledWith(
    1,
    expect.objectContaining({ name: "huge.pdf" }),
  );
  expect(
    await screen.findByText("2 doküman başarıyla işlendi, 1 doküman yüklenemedi."),
  ).toBeInTheDocument();
});

test("H. ders seçili değilse hiç API çağrısı yapılmaz", () => {
  const uploadDocument = vi.mocked(documentService.uploadDocument);

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanı Yükle" }));

  expect(screen.getByText("Lütfen önce bir ders seçin.")).toBeInTheDocument();
  expect(uploadDocument).not.toHaveBeenCalled();
});

test("I. upload sırasında submit butonu disabled olur", async () => {
  const resolvers: Array<() => void> = [];
  vi.mocked(documentService.uploadDocument).mockImplementation(
    () =>
      new Promise((resolve) => {
        resolvers.push(() => resolve(okResponse("a.pdf")));
      }),
  );

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanı Yükle" }));

  expect(await screen.findByRole("button", { name: "Yükleniyor..." })).toBeDisabled();

  resolvers[0]();
  await waitFor(() =>
    expect(screen.queryByText("Yükleniyor...")).not.toBeInTheDocument(),
  );
});

test("aynı dosya (isim+boyut+lastModified) iki kez seçilirse tek kez listelenir", () => {
  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  const file = makeFile("dup.pdf");
  Object.defineProperty(file, "lastModified", { value: 123456 });
  const fileClone = makeFile("dup.pdf");
  Object.defineProperty(fileClone, "lastModified", { value: 123456 });

  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [file, fileClone] },
  });

  expect(screen.getAllByText("dup.pdf")).toHaveLength(1);
});

test("N. multi-upload akışında native window.confirm/alert kullanılmaz", async () => {
  const confirmSpy = vi.spyOn(window, "confirm");
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);
  vi.mocked(documentService.uploadDocument).mockResolvedValue(okResponse("a.pdf"));

  render(<DocumentUpload courses={courses} onUploaded={() => undefined} />);
  selectCourse();
  fireEvent.change(screen.getByLabelText("PDF"), {
    target: { files: [makeFile("a.pdf")] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Dokümanı Yükle" }));

  await waitFor(() => expect(documentService.uploadDocument).toHaveBeenCalled());

  expect(confirmSpy).not.toHaveBeenCalled();
  expect(alertSpy).not.toHaveBeenCalled();
});

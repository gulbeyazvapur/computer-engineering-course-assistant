import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import CoursesPage from "../pages/CoursesPage";
import * as courseService from "../services/courseService";
import type { Course } from "../types/course";

vi.mock("../services/courseService");

const initialCourses: Course[] = [
  { id: 1, name: "Bilgisayar Ağları", description: "Ağ mimarileri", documentCount: 2 },
  { id: 2, name: "İşletim Sistemleri", description: "Süreçler", documentCount: 1 },
];

afterEach(() => {
  vi.restoreAllMocks();
});

test("ders listesi backend'den render edilir (hardcoded liste yok)", async () => {
  vi.mocked(courseService.getCourses).mockResolvedValue(initialCourses);

  render(<CoursesPage />);

  expect(await screen.findByText("Bilgisayar Ağları")).toBeInTheDocument();
  expect(screen.getByText("İşletim Sistemleri")).toBeInTheDocument();
});

test("yeni ders eklendikten sonra liste otomatik güncellenir (hard refresh yok)", async () => {
  const getCourses = vi
    .mocked(courseService.getCourses)
    .mockResolvedValueOnce(initialCourses)
    .mockResolvedValueOnce([
      ...initialCourses,
      { id: 3, name: "Yapay Zeka", description: null, documentCount: 0 },
    ]);
  vi.mocked(courseService.createCourse).mockResolvedValue({
    id: 3,
    name: "Yapay Zeka",
    description: null,
  });

  render(<CoursesPage />);
  await screen.findByText("Bilgisayar Ağları");

  fireEvent.change(screen.getByLabelText("Ders adı"), {
    target: { value: "Yapay Zeka" },
  });
  fireEvent.click(screen.getByRole("button", { name: /ders oluştur/i }));

  expect(await screen.findByText("Yapay Zeka")).toBeInTheDocument();
  expect(getCourses).toHaveBeenCalledTimes(2);
});

test("silme onaylandıktan sonra ders listeden kalkar", async () => {
  vi.mocked(courseService.getCourses)
    .mockResolvedValueOnce(initialCourses)
    .mockResolvedValueOnce([initialCourses[1]]);
  vi.mocked(courseService.deleteCourse).mockResolvedValue(undefined);

  render(<CoursesPage />);
  await screen.findByText("Bilgisayar Ağları");

  const deleteButtons = screen.getAllByLabelText("Dersi sil");
  fireEvent.click(deleteButtons[0]);
  fireEvent.click(screen.getByRole("button", { name: "Dersi Sil" }));

  await waitFor(() =>
    expect(screen.queryByText("Bilgisayar Ağları")).not.toBeInTheDocument(),
  );
  expect(screen.getByText("İşletim Sistemleri")).toBeInTheDocument();
});

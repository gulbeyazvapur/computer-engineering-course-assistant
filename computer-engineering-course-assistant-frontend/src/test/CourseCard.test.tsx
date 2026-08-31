import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import CourseCard from "../components/courses/CourseCard";
import * as courseService from "../services/courseService";
import type { Course } from "../types/course";

vi.mock("../services/courseService");

const baseCourse: Course = {
  id: 1,
  name: "Bilgisayar Ağları",
  description: "Ağ mimarileri",
  documentCount: 3,
};

afterEach(() => {
  vi.restoreAllMocks();
});

test("ders adı, açıklaması ve kaynak sayısı render edilir", () => {
  render(<CourseCard course={baseCourse} onChanged={() => undefined} />);

  expect(screen.getByText("Bilgisayar Ağları")).toBeInTheDocument();
  expect(screen.getByText("Ağ mimarileri")).toBeInTheDocument();
  expect(screen.getByText("3 kaynak")).toBeInTheDocument();
});

test("düzenle -> kaydet başarılı güncelleme sonrası onChanged çağrılır", async () => {
  const updateCourse = vi
    .mocked(courseService.updateCourse)
    .mockResolvedValue({ ...baseCourse, name: "Ağlar Güncel" });
  const onChanged = vi.fn().mockResolvedValue(undefined);

  render(<CourseCard course={baseCourse} onChanged={onChanged} />);

  fireEvent.click(screen.getByLabelText("Dersi düzenle"));

  const nameInput = screen.getByLabelText("Ders adı");
  fireEvent.change(nameInput, { target: { value: "Ağlar Güncel" } });
  fireEvent.click(screen.getByRole("button", { name: "Kaydet" }));

  await waitFor(() => expect(onChanged).toHaveBeenCalledTimes(1));

  expect(updateCourse).toHaveBeenCalledWith(1, {
    name: "Ağlar Güncel",
    description: "Ağ mimarileri",
  });
  // Edit mode closed -- back to read view.
  expect(screen.queryByLabelText("Ders adı")).not.toBeInTheDocument();
});

test("güncelleme API hatası kullanıcı dostu mesajla gösterilir", async () => {
  vi.mocked(courseService.updateCourse).mockRejectedValue({
    isAxiosError: true,
    response: {
      data: { error: "DUPLICATE_COURSE", message: "Aynı isimde bir ders zaten mevcut." },
    },
  });
  const onChanged = vi.fn();

  render(<CourseCard course={baseCourse} onChanged={onChanged} />);

  fireEvent.click(screen.getByLabelText("Dersi düzenle"));
  fireEvent.click(screen.getByRole("button", { name: "Kaydet" }));

  expect(
    await screen.findByText("Aynı isimde bir ders zaten mevcut."),
  ).toBeInTheDocument();
  expect(onChanged).not.toHaveBeenCalled();
});

test("H (A/B/C). çöp kutusuna basınca native confirm değil custom modal açılır, başlık ve ders adı doğru", () => {
  const confirmSpy = vi.spyOn(window, "confirm");

  render(<CourseCard course={baseCourse} onChanged={() => undefined} />);
  fireEvent.click(screen.getByLabelText("Dersi sil"));

  expect(confirmSpy).not.toHaveBeenCalled();
  const dialog = screen.getByRole("dialog");
  expect(dialog).toHaveTextContent("Dersi sil");
  expect(dialog).toHaveTextContent("Bilgisayar Ağları");
});

test("H (D). İptal -> modal kapanır, deleteCourse çağrılmaz", () => {
  const deleteCourse = vi.mocked(courseService.deleteCourse);
  const onChanged = vi.fn();

  render(<CourseCard course={baseCourse} onChanged={onChanged} />);
  fireEvent.click(screen.getByLabelText("Dersi sil"));
  fireEvent.click(screen.getByRole("button", { name: "İptal" }));

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(deleteCourse).not.toHaveBeenCalled();
  expect(onChanged).not.toHaveBeenCalled();
});

test("H (E/F). Dersi Sil -> deleteCourse çağrılır, başarı sonrası modal kapanır", async () => {
  const deleteCourse = vi.mocked(courseService.deleteCourse).mockResolvedValue(undefined);
  const onChanged = vi.fn().mockResolvedValue(undefined);

  render(<CourseCard course={baseCourse} onChanged={onChanged} />);
  fireEvent.click(screen.getByLabelText("Dersi sil"));
  fireEvent.click(screen.getByRole("button", { name: "Dersi Sil" }));

  await waitFor(() => expect(onChanged).toHaveBeenCalledTimes(1));
  expect(deleteCourse).toHaveBeenCalledWith(1);
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

import { render, screen } from "@testing-library/react";
import EmptyChatState from "../components/chat/EmptyChatState";

test("A. sade başlık ve açıklama görünür", () => {
  render(<EmptyChatState />);

  expect(screen.getByText("Sorularını Sormaya Başla")).toBeInTheDocument();
  expect(
    screen.getByText("Seçtiğin dersin materyallerine göre soru sorabilirsin."),
  ).toBeInTheDocument();
});

test("B. eski landing-page metinleri artık görünmüyor", () => {
  render(<EmptyChatState />);

  expect(
    screen.queryByText("Merhaba! Ben senin ders asistanınım 👋"),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByText("Hazırsan bir ders seçerek başlayalım."),
  ).not.toBeInTheDocument();
});

test("C. yönlendirme metni görünür", () => {
  render(<EmptyChatState />);

  expect(
    screen.getByText("Bir ders seçip ilk sorunu yazarak başlayabilirsin."),
  ).toBeInTheDocument();
});

test("D. destekleyici illüstrasyon render edilir", () => {
  const { container } = render(<EmptyChatState />);

  const illustration = container.querySelector("img");
  expect(illustration).not.toBeNull();
  expect(illustration?.getAttribute("src")).toMatch(/study-assistant-illustration/);
});

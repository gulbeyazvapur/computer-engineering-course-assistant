import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import ChatInput from "../components/chat/ChatInput";

test("boş input için gönder butonu disable olur", () => {
  render(
    <ChatInput
      value=""
      onChange={() => undefined}
      onSubmit={() => undefined}
    />,
  );

  expect(screen.getByRole("button", { name: /soruyu gönder/i })).toBeDisabled();
});

test("Enter gönderimi tetikler", () => {
  const onSubmit = vi.fn();

  render(
    <ChatInput
      value="Deadlock nedir?"
      onChange={() => undefined}
      onSubmit={onSubmit}
    />,
  );

  fireEvent.keyDown(screen.getByLabelText("Sorunuz"), {
    key: "Enter",
    shiftKey: false,
  });

  expect(onSubmit).toHaveBeenCalledTimes(1);
});

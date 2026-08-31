import { render, screen } from "@testing-library/react";
import SourceList from "../components/chat/SourceList";

test("aynı dokümanı tekrar göstermez", () => {
  render(
    <SourceList
      sources={[
        { documentName: "Deadlock.pdf", chunkIndex: 1 },
        { documentName: "Deadlock.pdf", chunkIndex: 2 },
      ]}
    />,
  );

  expect(screen.getAllByText("Deadlock.pdf")).toHaveLength(1);
});

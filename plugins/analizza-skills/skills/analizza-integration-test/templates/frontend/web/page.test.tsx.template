import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "./page";

// Teste minimo: prova que a suite roda e que a tela inicial renderiza.
// Troque pelo primeiro teste de comportamento quando a tela ganhar um.
test("a tela inicial renderiza", () => {
  const { container } = render(<Home />);
  expect(container.querySelector("main")).not.toBeNull();
});

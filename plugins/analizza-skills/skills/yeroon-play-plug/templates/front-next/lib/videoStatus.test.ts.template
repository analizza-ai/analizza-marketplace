import { expect, test } from "vitest";
import { statusLabel } from "./videoStatus";

test("traduzCadaStatusDaApiParaUmRotuloCurto", () => {
  expect(statusLabel("PENDENTE")).toBe("Enviando");
  expect(statusLabel("ENVIADO")).toBe("Na fila");
  expect(statusLabel("PROCESSANDO")).toBe("Convertendo");
  expect(statusLabel("PRONTO")).toBe("Pronto");
  expect(statusLabel("FALHOU")).toBe("Falhou");
  expect(statusLabel("CANCELADO")).toBe("Cancelado");
  expect(statusLabel("ABANDONADO")).toBe("Abandonado");
});

test("statusDesconhecidoApareceComoVeio", () => {
  expect(statusLabel("NOVO_STATUS")).toBe("NOVO_STATUS");
});

const LABELS: Record<string, string> = {
  PENDENTE: "Enviando",
  ENVIADO: "Na fila",
  PROCESSANDO: "Convertendo",
  PRONTO: "Pronto",
  FALHOU: "Falhou",
  CANCELADO: "Cancelado",
  ABANDONADO: "Abandonado",
};

/** Rotulo curto do status que a API devolve; desconhecido aparece como veio. */
export function statusLabel(status: string): string {
  return LABELS[status] ?? status;
}

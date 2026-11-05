"""Renderiza os moldes da analizza-expo-testflight como a skill faz: troca os
marcadores {nome} e mantém só os blocos condicionais pedidos.

Blocos ficam em linhas próprias, em dois formatos:
  YAML/shell:  # se prod      ...  # fim se prod
  Markdown:    <!-- se prod --> ...  <!-- fim se prod -->
"""

import re

MARCADOR = re.compile(r"(?<![{$])\{[a-z][a-z0-9-]*\}(?!\})")
_ABRE = re.compile(r"^\s*(?:#|<!--)\s*se ([a-z][a-z0-9-]*)\s*(?:-->)?\s*$")
_FECHA = re.compile(r"^\s*(?:#|<!--)\s*fim se ([a-z][a-z0-9-]*)\s*(?:-->)?\s*$")


def renderizar(template: str, valores: dict[str, str], blocos: set[str]) -> str:
    saida: list[str] = []
    pilha: list[tuple[str, bool]] = []
    for linha in template.splitlines(keepends=True):
        abre = _ABRE.match(linha)
        fecha = _FECHA.match(linha)
        if abre:
            pilha.append((abre.group(1), abre.group(1) in blocos))
            continue
        if fecha:
            if not pilha or pilha[-1][0] != fecha.group(1):
                raise ValueError(f"bloco '{fecha.group(1)}' fechado sem abrir")
            pilha.pop()
            continue
        if all(ativo for _, ativo in pilha):
            saida.append(linha)
    if pilha:
        raise ValueError(f"bloco '{pilha[-1][0]}' sem fechamento")

    def trocar(m: re.Match) -> str:
        nome = m.group(0)[1:-1]
        return valores[nome] if nome in valores else m.group(0)

    return MARCADOR.sub(trocar, "".join(saida))

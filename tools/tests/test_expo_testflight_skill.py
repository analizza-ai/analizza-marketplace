"""Regras de conteúdo da analizza-expo-testflight (anti-objetivos do design)."""

import re
from pathlib import Path

from tools.tests.expo_testflight_render import MARCADOR

SKILL = Path("plugins/analizza-skills/skills/analizza-expo-testflight")
SKILL_MD = SKILL / "SKILL.md"
CLIENTE = re.compile(r"yeroon|XF98CA5PDT|bjjdream|analizza-tube", re.IGNORECASE)


def arquivos(pasta: str) -> list[Path]:
    return sorted(p for p in (SKILL / pasta).rglob("*") if p.is_file())


def secao(titulo: str) -> str:
    texto = SKILL_MD.read_text(encoding="utf-8")
    inicio = texto.index(titulo)
    proxima = re.search(r"^## ", texto[inicio + len(titulo):], re.MULTILINE)
    fim = inicio + len(titulo) + proxima.start() if proxima else len(texto)
    return texto[inicio:fim]


def test_frontmatter_so_name_e_description():
    texto = SKILL_MD.read_text(encoding="utf-8")
    assert texto.startswith("---\n")
    frente = texto.split("---\n")[1]
    chaves = re.findall(r"^([a-z-]+):", frente, re.MULTILINE)
    assert chaves == ["name", "description"]
    assert "name: analizza-expo-testflight" in frente


def test_sem_cliente_nos_arquivos():
    achados = [
        f"{p}: {m.group(0)}"
        for p in sorted(SKILL.rglob("*")) if p.is_file()
        for m in [CLIENTE.search(p.read_text(encoding="utf-8"))] if m
    ]
    assert achados == []


def test_todo_marcador_esta_declarado():
    skill = SKILL_MD.read_text(encoding="utf-8")
    marcadores = {m for p in arquivos("templates") for m in MARCADOR.findall(p.read_text(encoding="utf-8"))}
    assert marcadores, "nenhum marcador encontrado nos moldes"
    faltando = sorted(m for m in marcadores if f"`{m}`" not in skill)
    assert faltando == []


def test_todo_molde_e_citado():
    skill = SKILL_MD.read_text(encoding="utf-8")
    faltando = [
        str(p.relative_to(SKILL))
        for p in arquivos("templates") + arquivos("references")
        if str(p.relative_to(SKILL)) not in skill
    ]
    assert faltando == []


def test_skill_para_em_bare_e_eas():
    fase0 = secao("## Fase 0")
    assert "eas.json" in fase0
    assert "ios/" in fase0
    assert re.search(r"\b[Pp]are\b", fase0)


def test_skill_reaproveita_credenciais_do_time():
    fase2 = secao("## Fase 2")
    assert "segundo ambiente" in fase2
    assert "chave" in fase2 and "certificado" in fase2
    assert re.search(r"\b[Pp]ule\b", fase2)

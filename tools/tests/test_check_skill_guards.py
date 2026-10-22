from pathlib import Path

from tools.check_skill_guards import verificar_skill

FRONTMATTER = "---\nname: x\ndescription: d\n---\n"
VOCABULARIO = (
    "\n## Vocabulário\n\n| Marcador | Significado |\n|---|---|\n"
    "| `{base-package}` | pacote base |\n"
)


def criar_skill(raiz: Path, skill_md: str = FRONTMATTER + "# x\n" + VOCABULARIO) -> Path:
    pasta = raiz / "x"
    pasta.mkdir()
    (pasta / "SKILL.md").write_text(skill_md, encoding="utf-8")
    return pasta


def escrever(pasta: Path, relativo: str, conteudo: str) -> None:
    arq = pasta / relativo
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(conteudo, encoding="utf-8")


def test_skill_valida_sem_erros(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "templates/A.java", "package {base-package};\n")
    assert verificar_skill(pasta) == []


def test_stub_sem_vocabulario_nem_templates_passa(tmp_path: Path):
    pasta = criar_skill(tmp_path, FRONTMATTER + "# x\n")
    assert verificar_skill(pasta) == []


def test_marcador_nao_declarado(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "templates/A.java", "class {nome-da-classe} {}\n")
    erros = "\n".join(verificar_skill(pasta))
    assert "templates/A.java" in erros and "{nome-da-classe}" in erros


def test_marcador_sem_tabela_vocabulario(tmp_path: Path):
    pasta = criar_skill(tmp_path, FRONTMATTER + "# x\n")
    escrever(pasta, "templates/A.java", "{base-package}\n")
    assert any("{base-package}" in e for e in verificar_skill(pasta))


def test_variavel_de_rota_id_nao_e_marcador(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "templates/C.java", '@PostMapping("/videos/{id}")\n')
    assert verificar_skill(pasta) == []


def test_interpolacao_com_cifrao_nao_e_marcador(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "templates/a.ts", "const u = `${base-url}/x`;\n")
    assert verificar_skill(pasta) == []


def test_chave_literal(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "references/a.md", "YEROON_API_KEY=yk_abcdefgh12345\n")
    erros = "\n".join(verificar_skill(pasta))
    assert "references/a.md" in erros


def test_segredo_de_webhook_literal(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "a.txt", "whsec_ABCDEFGH1234\n")
    assert verificar_skill(pasta) != []


def test_prefixo_curto_de_chave_e_aceito(tmp_path: Path):
    pasta = criar_skill(tmp_path)
    escrever(pasta, "a.md", "chaves comecam com yk_ e whsec_\n")
    assert verificar_skill(pasta) == []


def test_referencia_privada(tmp_path: Path):
    for termo in ("bjjdream", "yeroon-stream-poc", "analizza-tube"):
        raiz = tmp_path / termo
        raiz.mkdir()
        pasta = criar_skill(raiz)
        escrever(pasta, "a.md", f"veja {termo}\n")
        erros = "\n".join(verificar_skill(pasta))
        assert "a.md" in erros and termo in erros


def test_frontmatter_com_campo_extra(tmp_path: Path):
    pasta = criar_skill(
        tmp_path, "---\nname: x\ndescription: d\nlicense: MIT\n---\n# x\n"
    )
    erros = "\n".join(verificar_skill(pasta))
    assert "SKILL.md" in erros and "license" in erros


def test_frontmatter_sem_description(tmp_path: Path):
    pasta = criar_skill(tmp_path, "---\nname: x\n---\n# x\n")
    assert any("description" in e for e in verificar_skill(pasta))


def test_skill_md_sem_frontmatter(tmp_path: Path):
    pasta = criar_skill(tmp_path, "# x\n")
    assert any("frontmatter" in e for e in verificar_skill(pasta))

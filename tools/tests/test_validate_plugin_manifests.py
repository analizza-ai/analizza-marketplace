import json
from pathlib import Path

from tools.validate_plugin_manifests import carregar_manifesto, validar_manifestos


def manifestos_validos():
    claude = {"name": "analizza-skills", "version": "0.2.1"}
    codex = {
        "name": "analizza-skills",
        "version": "0.2.1",
        "skills": "./skills/",
        "interface": {
            "displayName": "Analizza Skills",
            "shortDescription": "Scaffolding e qualidade para projetos Kotlin/Java + Spring Boot",
            "longDescription": "Cria monorepos do zero e configura testes de integração.",
            "developerName": "Diego Lirio",
            "category": "Developer Tools",
            "capabilities": ["Read", "Write"],
        },
    }
    return claude, codex


def criar_skills(tmp_path: Path, nomes: list[str]) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    for nome in nomes:
        pasta = skills_dir / nome
        pasta.mkdir()
        (pasta / "SKILL.md").write_text("# skill\n", encoding="utf-8")


def test_manifestos_compativeis_nao_produzem_erros(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b", "c"])
    claude, codex = manifestos_validos()
    assert validar_manifestos(claude, codex, tmp_path) == []


def test_versao_divergente_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["version"] = "0.3.0"
    assert "version diverge" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_caminho_de_skills_diferente_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["skills"] = "./codex-skills/"
    assert "skills deve ser './skills/'" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_diretorio_de_skills_ausente_e_reportado(tmp_path: Path):
    claude, codex = manifestos_validos()
    assert "diretório de skills não existe" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_interface_incompleta_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["interface"]["category"]
    assert "interface.category ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_skill_md_faltando_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b"])
    (tmp_path / "skills" / "c").mkdir()
    claude, codex = manifestos_validos()
    erros = "\n".join(validar_manifestos(claude, codex, tmp_path))
    assert "número de SKILL.md" in erros


def test_name_ausente_no_codex_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["name"]
    assert "codex: name ausente" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_version_ausente_no_codex_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["version"]
    assert "codex: version ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_manifesto_ausente_e_reportado(tmp_path: Path, capsys):
    caminho = tmp_path / "plugin.json"
    resultado = carregar_manifesto(caminho)
    assert resultado is None
    assert f"manifesto ausente ou inválido: {caminho}" in capsys.readouterr().out


def test_manifestos_reais_respeitam_o_contrato():
    raiz = Path(__file__).resolve().parents[2]
    plugin_dir = raiz / "plugins/analizza-skills"
    claude = json.loads((plugin_dir / ".claude-plugin/plugin.json").read_text())
    codex = json.loads((plugin_dir / ".codex-plugin/plugin.json").read_text())
    assert validar_manifestos(claude, codex, plugin_dir) == []

    skills_dir = plugin_dir / "skills"
    assert skills_dir.is_dir()
    assert not skills_dir.is_symlink()
    assert len(list(plugin_dir.rglob("SKILL.md"))) == 3


def test_readme_documenta_claude_e_codex_sem_comando_inventado():
    raiz = Path(__file__).resolve().parents[2]
    readme = (raiz / "README.md").read_text(encoding="utf-8")
    assert "### Claude Code" in readme
    assert "### Codex" in readme
    assert "Plugins" in readme
    assert "codex plugin install" not in readme

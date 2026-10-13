import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fixtures

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import inventory  # noqa: E402


def project(files):
    directory = tempfile.TemporaryDirectory()
    fixtures.write(directory.name, files)
    return directory


def git(root, *args):
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=teste", "-c", "user.email=teste@exemplo.com",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True,
    )


class InventoryTest(unittest.TestCase):

    def test_kotlin_com_openspec(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual(
            [{"caminho": ".", "build": "build.gradle.kts", "linguagem": "kotlin", "framework": "spring"}],
            found["modulos"],
        )
        self.assertEqual(["openspec"], found["specs"]["frameworks"])
        self.assertEqual(["openspec"], found["specs"]["pastas"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/presenter/routes", "arquivos": 2}], found["rotas"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/application", "arquivos": 3}], found["servicos"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/domain", "arquivos": 2}], found["dominio"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/domain/rules", "arquivos": 1}], found["validacoes"])
        self.assertEqual([{"pasta": "src/main/resources/db/migration", "arquivos": 1}], found["migrations"])
        self.assertEqual([{"sufixo": "Handler", "arquivos": 3}], found["sufixos"])
        self.assertEqual(13, found["arquivos"])
        self.assertEqual(7, found["codigo"])

    def test_next_sem_specs(self):
        with project(fixtures.NEXT_SEM_SPECS) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual(
            [{"caminho": ".", "build": "package.json", "linguagem": "typescript", "framework": "nextjs"}],
            found["modulos"],
        )
        self.assertEqual([], found["specs"]["frameworks"])
        self.assertEqual([{"pasta": "docs", "arquivos": 1}], found["specs"]["markdown"])
        self.assertEqual([{"pasta": "src/app/api/chat", "arquivos": 1}], found["rotas"])
        self.assertEqual(3, found["codigo"])

    def test_monorepo_tem_um_modulo_por_pasta_com_arquivo_de_build(self):
        with project(fixtures.MONOREPO) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual(
            [("backend", "kotlin", "spring"), ("web", "typescript", "nextjs")],
            [(m["caminho"], m["linguagem"], m["framework"]) for m in found["modulos"]],
        )

    def test_projeto_vazio_nao_falha(self):
        with tempfile.TemporaryDirectory() as root:
            found = inventory.inventory(Path(root))

        self.assertEqual(0, found["arquivos"])
        self.assertEqual(0, found["codigo"])
        self.assertEqual([], found["modulos"])
        self.assertEqual([], found["rotas"])
        self.assertEqual({"frameworks": [], "pastas": [], "markdown": []}, found["specs"])

    def test_fora_de_um_repositorio_git_sai_sem_commit_e_sem_remote(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            found = inventory.inventory(Path(root))

        self.assertIsNone(found["commit"])
        self.assertIsNone(found["remote"])

    def test_num_repositorio_git_respeita_o_gitignore_e_tira_a_credencial_do_remote(self):
        files = dict(fixtures.KOTLIN_OPENSPEC)
        files[".gitignore"] = "segredo/\n"
        files["segredo/Token.kt"] = "@RestController class Token\n"
        with project(files) as root:
            git(root, "init", "-q")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "inicio")
            git(root, "remote", "add", "origin", "https://diego:ghp_segredo@github.com/acme/app.git")

            found = inventory.inventory(Path(root))

        self.assertRegex(found["commit"], r"^[0-9a-f]{7,}$")
        self.assertEqual("https://github.com/acme/app.git", found["remote"])
        self.assertNotIn("ghp_segredo", json.dumps(found))
        self.assertEqual([{"pasta": "src/main/kotlin/app/presenter/routes", "arquivos": 2}], found["rotas"])

    def test_arquivo_ilegivel_ou_grande_demais_nao_derruba(self):
        files = dict(fixtures.KOTLIN_OPENSPEC)
        with project(files) as root:
            (Path(root) / "src/main/kotlin/app/Binario.kt").write_bytes(b"\xff\xfe\x00" * 10)
            (Path(root) / "src/main/kotlin/app/Enorme.kt").write_text("x" * 1_100_000, encoding="utf-8")

            found = inventory.inventory(Path(root))

        self.assertEqual(9, found["codigo"])

    def test_credencial_com_arroba_na_senha_sai_inteira_e_ssh_fica_como_esta(self):
        for url, expected in (
            ("https://u:p@ss@host/x", "https://host/x"),
            ("https://diego:ghp_segredo@github.com/acme/app.git", "https://github.com/acme/app.git"),
            ("git@github.com:acme/app.git", "git@github.com:acme/app.git"),
            ("ssh://git@github.com/acme/app.git", "ssh://github.com/acme/app.git"),
            ("https://host/x.git?private_token=SECRET", "https://host/x.git"),
            ("https://host/x.git#SECRET", "https://host/x.git"),
            ("https://user:p/ss@host/x.git", "https://host/x.git"),
            ("user:tok@host:o/r.git", "host:o/r.git"),
            ("https://u:pa?ss@h/x.git", "https://h/x.git"),
            ("https://u:pa#ss@h/x.git?t=1", "https://h/x.git"),
            ("user:to?k@host:o/r.git", "host:o/r.git"),
        ):
            with self.subTest(url=url), project(fixtures.NEXT_SEM_SPECS) as root:
                git(root, "init", "-q")
                git(root, "remote", "add", "origin", url)

                self.assertEqual(expected, inventory.inventory(Path(root))["remote"])

    def test_o_carimbo_nao_leva_o_remote(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            git(root, "init", "-q")
            git(root, "remote", "add", "origin", "https://git.interno.exemplo/acme/app.git?private_token=SECRET")
            found = inventory.inventory(Path(root))
            text = inventory.stamp(found, "2026-10-13")

        self.assertEqual("https://git.interno.exemplo/acme/app.git", found["remote"])
        self.assertNotIn("remote", text)
        self.assertNotIn("git.interno.exemplo", text)
        self.assertNotIn("SECRET", text)

    def test_outra_linguagem_conta_como_codigo(self):
        with project(fixtures.PYTHON_E_GO) as root:
            found = inventory.inventory(Path(root))

        # O teste (tests/) fica de fora, como nas outras linguagens.
        self.assertEqual(2, found["codigo"])
        self.assertEqual([], found["modulos"])
        self.assertEqual([], found["rotas"])

    def test_pasta_sem_arquivo_fonte_tem_codigo_zero(self):
        with project({"README.md": "# Notas\n", "docs/a.md": "x\n", "dados.json": "{}\n"}) as root:
            self.assertEqual(0, inventory.inventory(Path(root))["codigo"])

    def test_pasta_models_de_rota_ou_de_caso_de_uso_nao_e_dominio(self):
        with project(fixtures.KOTLIN_COM_RECURSO_MODEL) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual(
            ["src/main/kotlin/app/presenter/routes", "src/main/kotlin/app/presenter/routes/models"],
            [item["pasta"] for item in found["rotas"]],
        )
        self.assertEqual([{"pasta": "src/main/kotlin/app/application", "arquivos": 1}], found["servicos"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/domain", "arquivos": 2}], found["dominio"])
        self.assertEqual([{"pasta": "src/main/kotlin/app/domain/rules", "arquivos": 1}], found["validacoes"])

    def test_rota_na_raiz_do_codigo_nao_esconde_as_camadas_abaixo(self):
        with project(fixtures.KTOR_PLANO) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual([{"pasta": "src/main/kotlin", "arquivos": 1}], found["rotas"])
        self.assertEqual([{"pasta": "src/main/kotlin/application", "arquivos": 1}], found["servicos"])
        self.assertEqual(
            [{"pasta": "src/main/kotlin/domain", "arquivos": 1}, {"pasta": "src/main/kotlin/models", "arquivos": 1}],
            found["dominio"],
        )

    def test_controller_no_pacote_base_nao_esconde_as_camadas_abaixo(self):
        with project(fixtures.SPRING_COM_ROTA_NO_PACOTE_BASE) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual([{"pasta": "src/main/kotlin/com/acme", "arquivos": 1}], found["rotas"])
        self.assertEqual([{"pasta": "src/main/kotlin/com/acme/service", "arquivos": 1}], found["servicos"])
        self.assertEqual([{"pasta": "src/main/kotlin/com/acme/domain", "arquivos": 2}], found["dominio"])
        self.assertEqual([{"pasta": "src/main/kotlin/com/acme/domain/rules", "arquivos": 1}], found["validacoes"])

    def test_pasta_de_rota_do_next_nao_e_camada(self):
        with project(fixtures.NEXT_COM_RECURSO_MODEL) as root:
            found = inventory.inventory(Path(root))

        self.assertEqual([{"pasta": "web/src/lib/models", "arquivos": 1}], found["dominio"])
        self.assertEqual([], found["servicos"])

    def test_package_json_com_dependencias_fora_do_formato_nao_derruba(self):
        for dependencies in ('["next"]', '"next"', "3", "null"):
            files = {"package.json": '{"dependencies": %s, "devDependencies": %s}\n' % (dependencies, dependencies)}
            with self.subTest(dependencies=dependencies), project(files) as root:
                self.assertIsNone(inventory.inventory(Path(root))["modulos"][0]["framework"])

    @unittest.skipIf(os.name == "nt", "argumento em bytes so existe em POSIX")
    def test_saida_do_git_que_nao_e_utf8_nao_derruba(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            git(root, "init", "-q")
            git(root, "config", "remote.origin.url", b"https://host/caf\xe9.git")

            found = inventory.inventory(Path(root))

        self.assertTrue(found["remote"].startswith("https://host/caf"))

    def test_arquivo_com_nome_acentuado_no_git_conta(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            git(root, "init", "-q")
            git(root, "add", "-A")
            before = inventory.inventory(Path(root))["codigo"]
            fixtures.write(root, {"src/main/kotlin/app/application/EmissãoHandler.kt": "class EmissaoHandler\n"})
            git(root, "add", "-A")

            after = inventory.inventory(Path(root))["codigo"]

        self.assertEqual(before + 1, after)

    def test_compare_com_arquivo_que_nao_e_utf8_diz_sem_carimbo(self):
        with project(fixtures.KOTLIN_OPENSPEC) as root:
            guide = Path(root) / "guia.md"
            guide.write_bytes(b"\xff\xfe nao e utf-8")
            done = subprocess.run(
                [sys.executable, str(SCRIPTS / "inventory.py"), root, "--compare", str(guide)],
                capture_output=True, text=True,
            )

        self.assertEqual(0, done.returncode, done.stderr)
        self.assertFalse(json.loads(done.stdout)["carimbo"])

    def test_linha_de_comando_imprime_json(self):
        with project(fixtures.NEXT_SEM_SPECS) as root:
            done = subprocess.run(
                [sys.executable, str(SCRIPTS / "inventory.py"), root], capture_output=True, text=True,
            )

        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual("nextjs", json.loads(done.stdout)["modulos"][0]["framework"])


if __name__ == "__main__":
    unittest.main()

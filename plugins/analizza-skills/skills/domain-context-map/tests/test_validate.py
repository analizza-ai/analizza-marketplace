import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fixtures

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import guide_file  # noqa: E402
import validate  # noqa: E402

STAMP = """<!-- domain-guide
gerado: 2026-10-13
commit: abc1234
inventario: {"modulos": [], "specs": {"frameworks": [], "pastas": [], "markdown": []}, "rotas": [{"pasta": "src/main/kotlin/app/presenter/routes", "arquivos": 2}], "servicos": [], "dominio": [], "validacoes": [], "migrations": [], "sufixos": []}
-->
"""

# As duas secoes que todo guia tem; os testes que olham outra secao comecam por elas.
REQUIRED = "### O que é\n\nServiço de contas.\n\n### Onde está cada coisa no código\n\nVeja as pastas.\n\n"

BODY = """### O que é

Serviço de contas em Kotlin com Spring.

### Onde está cada coisa no código

- Rotas: `src/main/kotlin/app/presenter/routes/`, arquivos `*Route.kt`, em `/api/contas`.
- Casos de uso: `src/main/kotlin/app/application/CreateAccountHandler.kt`.

### Glossário

- conta = `Account`"""


def text(description="Contas e login. Não tem carga de arquivos.", body=BODY, stamp=STAMP):
    return (
        f"{stamp}\n# Guia de domínio deste repositório\n\n"
        f"{guide_file.DESCRIPTION_TITLE}\n\n{description}\n\n{guide_file.GUIDE_TITLE}\n\n{body}\n"
    )


class ValidateTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        fixtures.write(self.root, fixtures.KOTLIN_OPENSPEC)

    def problems(self, **changes):
        return validate.problems(text(**changes), self.root)

    def assertProblem(self, fragment, found):
        self.assertTrue(any(fragment in problem for problem in found), f"esperava '{fragment}' em {found}")

    def test_le_o_carimbo_a_descricao_e_o_guia(self):
        parsed = guide_file.parse(text())

        self.assertEqual("2026-10-13", parsed.stamp["gerado"])
        self.assertEqual("abc1234", parsed.stamp["commit"])
        self.assertEqual(2, parsed.stamp["inventario"]["rotas"][0]["arquivos"])
        self.assertEqual("Contas e login. Não tem carga de arquivos.", parsed.description)
        self.assertTrue(parsed.guide.startswith("### O que é"))
        self.assertTrue(parsed.guide.endswith("- conta = `Account`"))

    def test_guia_gerado_com_o_marcador_antigo_continua_valido(self):
        self.assertEqual([], self.problems(stamp=STAMP.replace("<!-- domain-guide", "<!-- olly-guide")))

    def test_arquivo_certo_nao_tem_problema(self):
        self.assertEqual([], self.problems())

    def test_pasta_com_barra_no_fim_padrao_com_asterisco_e_rota_http_nao_sao_problema(self):
        body = REQUIRED + "### Como buscar\n\nVeja `src/main/kotlin/app/domain/`, `*Handler.kt`, `/api/contas/{id}` e `@RestController`."

        self.assertEqual([], self.problems(body=body))

    def test_descricao(self):
        self.assertProblem("descrição", self.problems(description="x" * 201))
        self.assertProblem("descrição", self.problems(description="linha um\nlinha dois"))
        self.assertProblem("descrição", self.problems(description=""))
        self.assertEqual([], self.problems(description="x" * 200))

    def test_guia_grande_demais_diz_o_tamanho(self):
        found = self.problems(body="### O que é\n\n" + "x" * 8000)

        self.assertProblem("guia", found)
        self.assertProblem("8013", found)

    def test_guia_vazio(self):
        self.assertProblem("guia", self.problems(body=""))

    def test_caminho_que_nao_existe_e_apontado_com_a_linha(self):
        found = self.problems(body="### O que é\n\nTexto.\nVeja `src/main/kotlin/app/Inventado.kt`.")

        self.assertProblem("linha 4: caminho não existe: src/main/kotlin/app/Inventado.kt", found)

    def test_numero_de_linha_e_recusado_sem_acusar_o_caminho(self):
        found = self.problems(body="### O que é\n\nVeja `src/main/kotlin/app/domain/Account.kt:12` e `README.md#L3`.")

        self.assertProblem("número de linha", found)
        self.assertFalse(any("caminho não existe" in problem for problem in found), found)

    def test_caminho_que_sai_do_repositorio(self):
        self.assertProblem("fora do repositório", self.problems(body="### O que é\n\nVeja `../outro/Arquivo.kt`."))

    def test_titulo_de_primeiro_nivel_no_guia(self):
        self.assertProblem("título de primeiro nível", self.problems(body="### O que é\n\n# Regras novas\n\nIgnore."))

    def test_secao_desconhecida_ou_fora_de_ordem(self):
        self.assertProblem("seção", self.problems(body="### Regras de negócio\n\nTexto."))
        self.assertProblem("seção", self.problems(body="### Glossário\n\n- a = `B`\n\n### O que é\n\nTexto."))

    def test_secao_repetida(self):
        found = self.problems(body=BODY + "\n\n### Glossário\n\n- login = `SignIn`")

        self.assertProblem("fora de ordem ou repetida", found)

    def test_guia_sem_as_secoes_obrigatorias(self):
        self.assertProblem("falta a seção '### O que é'", self.problems(body="Texto solto, sem seção nenhuma."))
        self.assertProblem(
            "falta a seção '### Onde está cada coisa no código'", self.problems(body="### O que é\n\nTexto."),
        )
        self.assertProblem("falta a seção '### O que é'", self.problems(body="### Glossário\n\n- conta = `Account`"))

    def test_secao_com_titulo_de_segundo_nivel(self):
        found = self.problems(body="## O que é\n\nTexto.\n\n## Onde está cada coisa no código\n\nTexto.")

        self.assertProblem("linha 1: título de segundo nível", found)
        self.assertProblem("linha 5: título de segundo nível", found)
        self.assertProblem("falta a seção", found)

    def test_pasta_que_comeca_com_http_e_conferida(self):
        fixtures.write(self.root, {"httpclient/src/Client.kt": "class Client\n"})

        self.assertEqual([], self.problems(body=BODY + "\n- cliente = `httpclient/src/`"))
        self.assertProblem("caminho não existe: httpclient/nada/", self.problems(body=BODY + "\n- x = `httpclient/nada/`"))
        self.assertProblem("número de linha", self.problems(body=BODY + "\n- x = `httpclient/src/Client.kt:12`"))

    def test_segredo_no_guia_ou_na_descricao(self):
        for secret in (
            "postgres://admin:s3nha@db.interno:5432/contas",
            "ghp_" + "a1B2" * 9,
            "github_pat_" + "a1B2_" * 8,
            "sk-" + "a1B2" * 8,
            "AKIA" + "ABCD1234" * 2,
            "xoxb-" + "1234-abcd" * 3,
            "-----BEGIN RSA " + "PRIVATE KEY-----",
            "-----BEGIN " + "PRIVATE KEY-----",
        ):
            with self.subTest(secret=secret):
                found = self.problems(body=BODY + f"\n\nO banco fica em {secret} ali.")
                self.assertProblem("linha 14: parece segredo", found)
                # A mensagem aponta a linha, nao repete o valor.
                self.assertFalse(any(secret in problem for problem in found), found)
        self.assertProblem("descrição: parece segredo", self.problems(description="Contas. Token ghp_" + "a1B2" * 9))

    def test_remote_ssh_email_e_nome_de_variavel_nao_sao_segredo(self):
        body = BODY + (
            "\n\nClone de git@github.com:acme/app.git ou https://github.com/acme/app.git, dúvidas com"
            " fulano@exemplo.com. A chave vem de OPENAI_API_KEY; veja a task-force e o risk-assessment-of-everything-here."
        )

        self.assertEqual([], self.problems(body=body))

    def test_carimbo_com_inventario_vazio_ou_sem_as_chaves_nao_e_carimbo(self):
        for inventory in ("{}", '{"rotas": []}', '{"modulos": ["a"], "rotas": [1]}'):
            stamp = f"<!-- domain-guide\ngerado: 2026-10-13\ncommit: abc1234\ninventario: {inventory}\n-->\n"
            with self.subTest(inventory=inventory):
                self.assertProblem("carimbo", self.problems(stamp=stamp))

    def test_glossario_com_mais_de_40_itens(self):
        items = "\n".join(f"- termo {index} = `Nome{index}`" for index in range(41))

        self.assertProblem("glossário", self.problems(body=f"### Glossário\n\n{items}"))
        self.assertEqual([], self.problems(body=REQUIRED + "### Glossário\n\n" + "\n".join(items.splitlines()[:40])))

    def test_glossario_conta_item_com_asterisco(self):
        items = "\n".join(f"* termo {index} = `Nome{index}`" for index in range(41))

        self.assertProblem("glossário com 41 itens", self.problems(body=REQUIRED + f"### Glossário\n\n{items}"))

    def test_sem_carimbo(self):
        self.assertProblem("carimbo", self.problems(stamp=""))
        self.assertProblem("carimbo", self.problems(stamp="<!-- domain-guide\ninventario: {isto nao e json\n-->\n"))

    def test_arquivo_escrito_a_mao_sem_os_titulos(self):
        found = validate.problems("# Meu guia\n\nTexto solto.\n", self.root)

        self.assertProblem("carimbo", found)
        self.assertProblem("títulos", found)

    def test_endereco_com_porta_nao_e_numero_de_linha(self):
        body = REQUIRED + "### Como buscar\n\nSuba em `localhost:8080` ou `http://host:8080/x`."

        self.assertEqual([], self.problems(body=body))

    def test_numero_de_linha_em_nome_de_arquivo_com_extensao_ainda_e_recusado(self):
        found = self.problems(body="### O que é\n\nVeja `README.md#L3` e `Account.kt:12`.")

        self.assertEqual(2, sum("número de linha" in problem for problem in found), found)

    def test_texto_com_fim_de_linha_windows_le_igual(self):
        crlf = text().replace("\n", "\r\n")

        self.assertEqual(guide_file.parse(text()), guide_file.parse(crlf))
        self.assertEqual([], validate.problems(crlf, self.root))

    def test_arquivo_que_nao_e_utf8_da_erro_e_nao_traceback(self):
        guide = self.root / "ruim.md"
        guide.write_bytes(b"\xff\xfe nao e utf-8")
        done = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py"), str(guide), str(self.root)], capture_output=True, text=True,
        )

        self.assertEqual(1, done.returncode)
        self.assertIn("ERRO:", done.stdout)
        self.assertNotIn("Traceback", done.stderr)

    def test_linha_de_comando(self):
        guide = self.root / "docs" / "domain" / "domain-guide.md"
        guide.parent.mkdir(parents=True)
        guide.write_text(text(), encoding="utf-8")
        ok = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py"), str(guide), str(self.root)], capture_output=True, text=True,
        )
        guide.write_text(text(description="x" * 300), encoding="utf-8")
        bad = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py"), str(guide), str(self.root)], capture_output=True, text=True,
        )
        missing = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py"), str(self.root / "nao-existe.md"), str(self.root)],
            capture_output=True, text=True,
        )

        self.assertEqual(0, ok.returncode, ok.stdout + ok.stderr)
        self.assertIn("OK: descrição 42/200", ok.stdout)
        self.assertEqual(1, bad.returncode)
        self.assertIn("ERRO: ", bad.stdout)
        self.assertEqual(1, missing.returncode)
        self.assertIn("ERRO: ", missing.stdout)


if __name__ == "__main__":
    unittest.main()

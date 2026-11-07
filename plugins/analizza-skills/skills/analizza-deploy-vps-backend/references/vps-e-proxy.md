# VPS, proxy reverso e as decisões do molde

Por que o molde é assim, para não desfazer sem querer.

## A VPS é compartilhada

- **Nenhuma porta publicada.** As aplicações só são alcançadas pelo proxy
  reverso da VPS, na rede Docker externa (`{proxy-network}`). Publicar porta
  expõe a aplicação sem TLS e pode colidir com um vizinho.
- **`mem_limit` em todo serviço.** Sem limite, um pico de uma aplicação faz o
  kernel matar o processo de outro projeto. A JVM lê o limite pelo
  `JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=70`; um serviço que divide a memória
  com outro processo no mesmo container (ex.: ffmpeg) precisa de um percentual
  menor no `environment:` dele.
- **`name:` explícito no compose.** Sem ele, o projeto vira o nome da pasta
  (`dev`), e dois projetos com pasta `dev` passam a dividir rede e volumes.

## A tag das imagens não entra no `.env`

O compose recria um container quando a configuração dele muda, inclusive o que
vem de `env_file`. Se a tag que muda a cada deploy estivesse no `.env.<env>`, todo
deploy recriaria também o banco. Por isso ela mora no `images.env`, que só entra
na interpolação (`--env-file`), e o Postgres recebe só as `POSTGRES_*`. O
`check-compose.sh` garante as duas coisas.

**Serviço que não pode reiniciar a cada deploy** (um worker com trabalho longo):
dê a ele uma tag pelo hash do código que entra no jar, não pelo commit, e pule o
build quando a imagem com essa tag já existe no Docker Hub
(`docker buildx imagetools inspect`). Um deploy que não muda o código dele mantém
a mesma imagem, e o compose não o recria. O molde não traz isso pronto: é uma
mudança à mão no workflow, só quando a pessoa pedir.

## O proxy reverso fica fora

O molde não configura nginx, Traefik nem Caddy: cada VPS tem o seu, muitas vezes
num repositório próprio. O runbook lista o que o proxy precisa ter (host,
TLS, upstream = nome do container, rede) e a skill confere de fora (`dig`,
`curl`), sem mexer nele. Se a pessoa pedir, abra o repositório do proxy e
proponha a mudança lá, como PR separado.

## DNS

Com a zona no Cloudflare e o certificado emitido na VPS (Let's Encrypt), o
registro da API fica **DNS only** (nuvem cinza): proxied, o desafio HTTP e o
TLS passam pelo Cloudflare e o certificado da VPS não é emitido.

## SSH

Prefira chave (`VPS_SSH_KEY`, só para o deploy, com o usuário mínimo que roda
`docker compose`). Senha (`VPS_SSH_PASSWORD`) funciona e é o que muitas VPS já
têm; registre no relatório como débito.

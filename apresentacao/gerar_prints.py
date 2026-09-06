"""Gera prints (PNG) das celulas do notebook de perfilamento.

Cada print mostra a celula como ela aparece no Jupyter: o codigo executado e a
saida que ele produziu. Servem para o documento da Entrega 01, que pede
"prints com codigo e saida", e para os slides da apresentacao.

Como funciona: o .ipynb ja carrega as saidas versionadas, entao nao e preciso
reexecutar nada. O script monta um HTML por celula, no visual do Jupyter, e
fotografa com o Chrome em modo headless. As dependencias sao efemeras (uv --with)
porque servem so para isto e nao entram no ambiente do projeto:

    uv run --with markdown --with pygments --with pillow python apresentacao/gerar_prints.py

Saida: apresentacao/evidencias/prints/nb-NN-<secao>.png
"""
import html as _html
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

import markdown as md
from PIL import Image, ImageChops
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

RAIZ = pathlib.Path(__file__).resolve().parent.parent
assert (RAIZ / "pyproject.toml").exists(), f"raiz do projeto nao encontrada: {RAIZ}"
NOTEBOOK = RAIZ / "etl" / "perfilamento.ipynb"
DESTINO = RAIZ / "apresentacao" / "evidencias" / "prints"

# O Chrome roda do lado Windows: ele nao enxerga caminho do WSL, entao o HTML
# intermediario precisa morar num diretorio que os dois lados alcancam.
CHROME = pathlib.Path("/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")
TRAB_WSL = pathlib.Path("/mnt/c/Users/giova/AppData/Local/Temp/pi-prints")
TRAB_WIN = r"C:\Users\giova\AppData\Local\Temp\pi-prints"

LARGURA = 1180
ALTURA_MAX = 6000     # janela deliberadamente alta; o excesso e recortado depois
MAX_LINHAS_TABELA = 26   # tabela mais longa que isso vira "primeiras N de M"
MAX_LINHAS_TEXTO = 30

CSS = """
* { box-sizing: border-box; }
body { margin:0; background:#fff; font-family:-apple-system,'Segoe UI',Roboto,sans-serif;
       font-size:13px; color:#212529; }
.wrap { padding:18px 22px 22px; }
.titulo { font-size:15px; font-weight:600; color:#0b3d62; margin:0 0 14px;
          padding-bottom:8px; border-bottom:2px solid #0b3d62; }
.cell { display:flex; align-items:flex-start; margin-bottom:10px; }
.prompt { flex:0 0 74px; font-family:'DejaVu Sans Mono',monospace; font-size:12px;
          color:#307fc1; text-align:right; padding:9px 10px 0 0; white-space:nowrap; }
.prompt.out { color:#bf5b3d; }
.corpo { flex:1 1 auto; min-width:0; }
.entrada { background:#f7f7f7; border:1px solid #e0e0e0; border-left:3px solid #307fc1;
           border-radius:2px; padding:8px 11px; overflow:hidden; }
.entrada pre { margin:0; font-family:'DejaVu Sans Mono',monospace; font-size:12px;
               line-height:1.45; white-space:pre-wrap; word-break:break-word; }
.saida { padding:2px 0 0 2px; }
.saida table { border-collapse:collapse; font-size:11.5px; margin:2px 0 8px; }
.saida th { background:#eef3f7; text-align:left; font-weight:600;
            border:1px solid #cfd8de; padding:3px 8px; white-space:nowrap; }
.saida td { border:1px solid #dde4e9; padding:2px 8px; white-space:nowrap; }
.saida tr:nth-child(even) td { background:#fafbfc; }
.saida p { margin:6px 0; }
.saida strong { color:#0b3d62; }
.saida pre { font-family:'DejaVu Sans Mono',monospace; font-size:11.5px; line-height:1.4;
             margin:2px 0 8px; white-space:pre-wrap; }
.corte { font-size:11px; color:#8a6d3b; background:#fcf8e3; border:1px solid #faebcc;
         border-radius:2px; padding:3px 8px; display:inline-block; margin:2px 0 8px; }
""" + HtmlFormatter(nowrap=True).get_style_defs(".entrada")


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")


def corta_tabela(fonte):
    """Encurta uma tabela markdown longa, dizendo quantas linhas foram omitidas."""
    linhas = fonte.splitlines()
    corpo = [i for i, l in enumerate(linhas)
             if l.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", l)]
    if len(corpo) <= MAX_LINHAS_TABELA + 1:      # +1 = cabecalho
        return fonte, 0
    ultima = corpo[MAX_LINHAS_TABELA]
    omitidas = len(corpo) - 1 - MAX_LINHAS_TABELA
    return "\n".join(linhas[:ultima]), omitidas


def corta_texto(fonte):
    linhas = fonte.rstrip().splitlines()
    if len(linhas) <= MAX_LINHAS_TEXTO:
        return fonte, 0
    return "\n".join(linhas[:MAX_LINHAS_TEXTO]), len(linhas) - MAX_LINHAS_TEXTO


def render_saida(saidas):
    partes = []
    for o in saidas:
        tipo = o["output_type"]
        if tipo == "stream":
            txt, n = corta_texto("".join(o["text"]))
            partes.append(f"<pre>{_html.escape(txt)}</pre>")
            if n:
                partes.append(f'<div class="corte">… {n} linhas omitidas neste print</div>')
        elif tipo in ("display_data", "execute_result"):
            dados = o.get("data", {})
            if "text/markdown" in dados:
                fonte = "".join(dados["text/markdown"])
                fonte, n = corta_tabela(fonte)
                partes.append(md.markdown(fonte, extensions=["tables"]))
                if n:
                    partes.append(f'<div class="corte">… {n} linhas omitidas neste print; '
                                  f'a saida completa esta no arquivo de evidencia</div>')
            elif "text/plain" in dados:
                txt = "".join(dados["text/plain"])
                if txt.startswith(("<IPython", "PosixPath")):
                    continue          # ruido do proprio Jupyter, nao e resultado
                txt, n = corta_texto(txt)
                partes.append(f"<pre>{_html.escape(txt)}</pre>")
                if n:
                    partes.append(f'<div class="corte">… {n} linhas omitidas neste print</div>')
        elif tipo == "error":
            partes.append(f'<pre>{_html.escape(chr(10).join(o["traceback"]))}</pre>')
    return "".join(partes)


def monta_html(titulo, codigo, n_exec, saidas):
    codigo_hl = highlight(codigo, PythonLexer(), HtmlFormatter(nowrap=True))
    bloco_saida = render_saida(saidas)
    saida_html = (f'<div class="cell"><div class="prompt out">Out[{n_exec}]:</div>'
                  f'<div class="corpo"><div class="saida">{bloco_saida}</div></div></div>'
                  if bloco_saida.strip() else "")
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="wrap">
  <div class="titulo">{_html.escape(titulo)}</div>
  <div class="cell">
    <div class="prompt">In [{n_exec}]:</div>
    <div class="corpo"><div class="entrada"><pre>{codigo_hl}</pre></div></div>
  </div>
  {saida_html}
</div></body></html>"""


def fotografa(html, nome):
    """Fotografa alto e recorta o excesso.

    O --screenshot do Chrome captura exatamente a janela, nao a pagina inteira.
    Como a altura de cada celula varia muito, a janela e deliberadamente alta e
    o branco que sobra e cortado depois, medindo onde termina o conteudo.
    """
    (TRAB_WSL / f"{nome}.html").write_text(html, encoding="utf-8")
    r = subprocess.run(
        [str(CHROME), "--headless", "--disable-gpu", "--hide-scrollbars",
         "--default-background-color=FFFFFFFF",
         f"--screenshot={TRAB_WIN}\\{nome}.png",
         f"--window-size={LARGURA},{ALTURA_MAX}",
         "--screenshot-format=png",
         f"{TRAB_WIN}\\{nome}.html"],
        capture_output=True, text=True)
    origem = TRAB_WSL / f"{nome}.png"
    if not origem.exists():
        sys.exit(f"Chrome nao gerou {nome}.png\n{r.stderr[-800:]}")

    img = Image.open(origem).convert("RGB")
    caixa = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    if caixa is None:
        sys.exit(f"{nome}: pagina saiu totalmente em branco")
    if caixa[3] >= img.height - 2:
        sys.exit(f"{nome}: conteudo bateu no teto de {ALTURA_MAX}px — aumente ALTURA_MAX")
    img = img.crop((0, 0, img.width, min(caixa[3] + 18, img.height)))

    destino = DESTINO / f"{nome}.png"
    img.save(destino, optimize=True)
    return destino


def main():
    if not CHROME.exists():
        sys.exit(f"Chrome nao encontrado em {CHROME} — ajuste o caminho no script.")
    DESTINO.mkdir(parents=True, exist_ok=True)
    TRAB_WSL.mkdir(parents=True, exist_ok=True)

    nb = json.loads(NOTEBOOK.read_text())
    celulas = nb["cells"]
    titulo_corrente = "Perfilamento"
    gerados = []

    for i, c in enumerate(celulas):
        fonte = "".join(c["source"])
        if c["cell_type"] == "markdown":
            for linha in fonte.splitlines():
                if linha.startswith("## "):
                    titulo_corrente = linha[3:].strip()
            continue
        if not fonte.strip() or not c.get("outputs"):
            continue

        n_exec = c.get("execution_count") or 0
        nome = f"nb-{n_exec:02d}-{slug(titulo_corrente)}"[:60]
        caminho = fotografa(monta_html(titulo_corrente, fonte.rstrip(), n_exec, c["outputs"]), nome)
        gerados.append(caminho)
        print(f"  {caminho.relative_to(RAIZ)}")

    print(f"\n{len(gerados)} prints gerados em {DESTINO.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()

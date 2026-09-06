/*
 * Monta o documento Word do projeto a partir dos Markdown de docs/.
 *
 * O documento e CUMULATIVO: cada entrega acrescenta capitulos ao mesmo arquivo.
 * Para incluir um capitulo novo, basta acrescenta-lo em CAPITULOS abaixo.
 *
 * Rodar:  cd entregas && npm install && npm run docx
 * Saida:  entregas/entrega-NN/Projeto-Integrador-Banco-de-Dados.docx
 *
 * O conversor de Markdown daqui e proposital e minimo: cobre exatamente o que
 * os documentos usam (titulos, tabelas, blocos de codigo, listas, citacoes,
 * regua e enfase). Nao e um conversor de uso geral.
 */
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun,
  LevelFormat, PageBreak, PageNumber, Packer, Paragraph, ShadingType, Table,
  TableCell, TableRow, TableOfContents, TextRun, WidthType,
} = require("docx");

const RAIZ = path.resolve(__dirname, "..");
const ENTREGA = "01";
const SAIDA = path.join(RAIZ, "entregas", `entrega-${ENTREGA}`,
                        "Projeto-Integrador-Banco-de-Dados.docx");

// ---------------------------------------------------------------- aparencia
const FONTE = "Calibri";
const MONO = "Consolas";
const AZUL = "1A3D5C";
const AZUL_CLARO = "33526B";
const LARG_TABELA = 9026;      // A4 menos as margens, em DXA
const MAX_IMG = 600;           // px a 96 dpi = a largura util da pagina
const MAX_IMG_ALT = 760;

// ---------------------------------------------------------------- conteudo
const CAPA = {
  instituicao: "IPOG — Instituto de Pós-Graduação e Graduação",
  curso: "Projeto Integrador — Área 03: Banco de Dados",
  titulo: "Modelagem e Análise de Dados de Vendas",
  subtitulo: "Um estudo comparativo entre PostgreSQL e MongoDB sobre o dataset Northwind Traders",
  autor: "Giovanne Espíndola",
  data: "Setembro de 2026",
};

// Os capitulos desta entrega, na ordem pedida. As entregas seguintes
// acrescentam linhas aqui — o documento e o mesmo.
const CAPITULOS = [
  "docs/01-introducao-e-objetivo.md",
  "docs/02-compreensao-do-negocio.md",
  "docs/03-modelo-conceitual.md",
  "docs/04-analise-exploratoria.md",
];

// Figuras inseridas ao FIM da secao indicada (casada pelo inicio do titulo).
const FIGURAS = {
  "docs/03-modelo-conceitual.md": [
    { secao: "1. O arquivo do diagrama", img: "docs/diagramas/er-conceitual.png",
      legenda: "Diagrama entidade-relacionamento conceitual do Northwind, com as 11 entidades e as cardinalidades de cada relacionamento." },
  ],
  "docs/04-analise-exploratoria.md": [
    { secao: "1. Como a análise foi feita", img: "apresentacao/evidencias/prints/nb-01-0-conexao-e-utilitarios.png",
      legenda: "Notebook de perfilamento — conexão com o banco e utilitários que gravam cada evidência em arquivo." },
    { secao: "2.1 Inventário", img: "apresentacao/evidencias/prints/nb-02-1-inventario-tabelas-linhas-e-tamanho-em-disco.png",
      legenda: "Notebook — inventário do schema public: tabelas, linhas, colunas e tamanho em disco." },
    { secao: "2.2 Período e volume", img: "apresentacao/evidencias/prints/nb-07-6-faixa-de-valores-das-colunas-temporais.png",
      legenda: "Notebook — faixa de valores das colunas temporais, que delimita a janela de operação da base." },
    { secao: "3.2 Nenhuma regra de negócio", img: "apresentacao/evidencias/prints/nb-04-3-chaves-constraints-e-indices-existentes.png",
      legenda: "Notebook — chaves, constraints e índices existentes: 14 PK, 13 FK, nenhum UNIQUE e nenhum CHECK." },
    { secao: "3.3 Ausência de índice", img: "apresentacao/evidencias/prints/nb-06-5-cardinalidade-das-juncoes-e-verificacao-de-orfaos.png",
      legenda: "Notebook — cardinalidade de cada junção e verificação de órfãos por anti-join." },
    { secao: "3.7 Tipos frouxos", img: "apresentacao/evidencias/prints/nb-03-2-colunas-tipos-declarados-e-nulabilidade.png",
      legenda: "Notebook — colunas, tipos declarados e nulabilidade das 92 colunas da base." },
    { secao: "3.8 Nulos concentrados", img: "apresentacao/evidencias/prints/nb-05-4-nulos-por-coluna.png",
      legenda: "Notebook — as 11 colunas que têm pelo menos um nulo, com o percentual de cada uma." },
  ],
};

// Apendice: consulta SQL + saida real, pareadas pelo numero da secao.
const APENDICE_SQL = {
  arquivo: "sql/01_exploracao.sql",
  evidencia: "apresentacao/evidencias/01-perfil-07-exploracao-negocio.txt",
  secoes: [1, 2, 3, 4, 6, 8],
};

// ------------------------------------------------------------------ helpers
const ler = (rel) => fs.readFileSync(path.join(RAIZ, rel), "utf8");

/** Le largura e altura de um PNG direto do cabecalho IHDR. */
function dimensoesPng(abs) {
  const b = fs.readFileSync(abs);
  if (b.toString("ascii", 1, 4) !== "PNG") throw new Error(`nao e PNG: ${abs}`);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function txt(texto, extra = {}) {
  return new TextRun({ text: texto, font: FONTE, size: 21, ...extra });
}

/**
 * Converte **negrito**, *italico* e `codigo` numa lista de TextRun.
 * Recursiva de proposito: **um `identificador` em negrito** e comum nos
 * documentos, e sem recursao as crases sairiam impressas.
 */
function inline(s, base = {}) {
  const runs = [];
  const re = /(\*\*[^*]+?\*\*|`[^`]+`|\*[^*\n]+?\*)/g;
  let i = 0, m;
  while ((m = re.exec(s)) !== null) {
    if (m.index > i) runs.push(txt(s.slice(i, m.index), base));
    const t = m[0];
    if (t.startsWith("**")) runs.push(...inline(t.slice(2, -2), { ...base, bold: true }));
    else if (t.startsWith("`")) runs.push(new TextRun({
      ...base, text: t.slice(1, -1), font: MONO, size: 19, color: "9B2C2C" }));
    else runs.push(...inline(t.slice(1, -1), { ...base, italics: true }));
    i = m.index + t.length;
  }
  if (i < s.length) runs.push(txt(s.slice(i), base));
  return runs.length ? runs : [txt("", base)];
}

/**
 * Um paragrafo por linha de codigo — o OOXML nao tem quebra de linha dentro de
 * paragrafo, e o bloco e delimitado pelo fundo cinza mais a barra lateral.
 *
 * So a borda da ESQUERDA: o schema do OOXML exige as bordas na ordem topo,
 * esquerda, baixo, direita, e a biblioteca as escreve em ordem propria (topo,
 * baixo, esquerda), o que produz XML invalido sempre que "baixo" e "esquerda"
 * aparecem juntas. Uma borda so evita o problema na origem.
 */
function paragrafoCodigo(linhas) {
  return linhas.map((l, idx) => new Paragraph({
    children: [new TextRun({ text: l || " ", font: MONO, size: 15 })],
    spacing: { before: idx === 0 ? 100 : 0, after: idx === linhas.length - 1 ? 140 : 0 },
    shading: { type: ShadingType.CLEAR, fill: "F1F4F6" },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: "8FA6B5" } },
    indent: { left: 120, right: 120 },
  }));
}

function tabela(linhasMd) {
  const celulas = (l) => l.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  const cabecalho = celulas(linhasMd[0]);
  const alinha = celulas(linhasMd[1]).map((a) =>
    a.endsWith(":") && !a.startsWith(":") ? AlignmentType.RIGHT
      : a.startsWith(":") && a.endsWith(":") ? AlignmentType.CENTER
      : AlignmentType.LEFT);
  const corpo = linhasMd.slice(2).map(celulas);
  // tabela de duas colunas usada como ficha ("| | |") nao tem cabecalho de verdade
  const temCabecalho = cabecalho.some((c) => c !== "");

  // largura proporcional ao conteudo mais longo de cada coluna, com piso que
  // impede o titulo curto de uma coluna numerica de quebrar no meio da palavra
  const pesos = cabecalho.map((h, i) => {
    const maior = Math.max(h.length + 2, ...corpo.map((r) => (r[i] || "").length));
    return Math.max(10, Math.min(maior, 60));
  });
  const soma = pesos.reduce((a, b) => a + b, 0);
  const larguras = pesos.map((p) => Math.round((p / soma) * LARG_TABELA));
  larguras[larguras.length - 1] += LARG_TABELA - larguras.reduce((a, b) => a + b, 0);

  const borda = { style: BorderStyle.SINGLE, size: 2, color: "C6D0D7" };
  const celula = (texto, i, ehCabecalho, par) => new TableCell({
    width: { size: larguras[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR,
               fill: ehCabecalho ? "E8EFF4" : (par ? "FFFFFF" : "FAFBFC") },
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    children: [new Paragraph({
      children: inline(texto, ehCabecalho ? { bold: true, color: AZUL } : {}),
      alignment: alinha[i] || AlignmentType.LEFT,
      spacing: { before: 0, after: 0 },
    })],
  });

  const linhas = corpo.map((r, j) => new TableRow({
    cantSplit: true,          // uma linha nao se parte entre duas paginas
    children: cabecalho.map((_, i) => celula(r[i] || "", i, false, j % 2 === 0)),
  }));
  if (temCabecalho) {
    linhas.unshift(new TableRow({
      tableHeader: true,      // repete o cabecalho quando a tabela vira a pagina
      cantSplit: true,
      children: cabecalho.map((c, i) => celula(c, i, true, false)),
    }));
  }

  return new Table({
    columnWidths: larguras,
    width: { size: LARG_TABELA, type: WidthType.DXA },
    borders: { top: borda, bottom: borda, left: borda, right: borda,
               insideHorizontal: borda, insideVertical: borda },
    rows: linhas,
  });
}

function imagem(rel, legenda, nFigura) {
  const abs = path.join(RAIZ, rel);
  const { w, h } = dimensoesPng(abs);
  const escala = Math.min(MAX_IMG / w, MAX_IMG_ALT / h, 1);
  return [
    new Paragraph({
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(abs),
        transformation: { width: Math.round(w * escala), height: Math.round(h * escala) },
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 60 },
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `Figura ${nFigura} — `, font: FONTE, size: 18, bold: true, color: AZUL }),
        new TextRun({ text: legenda, font: FONTE, size: 18, italics: true, color: "444444" }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
    }),
  ];
}

// --------------------------------------------------- markdown -> docx
let instanciaLista = 0;

function converte(md, figuras, contador) {
  const linhas = md.split("\n");
  const saida = [];
  let secaoAtual = null;
  const pendentes = new Map();      // secao -> figuras a inserir no fim dela

  (figuras || []).forEach((f) => {
    if (!pendentes.has(f.secao)) pendentes.set(f.secao, []);
    pendentes.get(f.secao).push(f);
  });

  const despeja = () => {
    if (!secaoAtual) return;
    for (const [chave, lista] of pendentes) {
      if (!secaoAtual.startsWith(chave)) continue;
      lista.forEach((f) => saida.push(...imagem(f.img, f.legenda, ++contador.figura)));
      pendentes.delete(chave);
    }
  };

  for (let i = 0; i < linhas.length; i++) {
    const l = linhas[i];

    if (/^#{1,4}\s/.test(l)) {
      despeja();
      const nivel = l.match(/^#+/)[0].length;
      const texto = l.replace(/^#+\s*/, "").replace(/`/g, "");
      if (nivel > 1) secaoAtual = texto;
      saida.push(new Paragraph({
        children: [new TextRun({
          text: texto, font: FONTE, bold: true,
          size: nivel === 1 ? 32 : nivel === 2 ? 25 : 22,
          color: nivel <= 2 ? AZUL : AZUL_CLARO,
        })],
        heading: nivel === 1 ? HeadingLevel.HEADING_1
               : nivel === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
        spacing: { before: nivel === 1 ? 0 : nivel === 2 ? 320 : 240,
                   after: nivel === 1 ? 200 : 120 },
        pageBreakBefore: nivel === 1,
      }));
      continue;
    }

    if (l.startsWith("```")) {                       // bloco de codigo
      const bloco = [];
      for (i++; i < linhas.length && !linhas[i].startsWith("```"); i++) bloco.push(linhas[i]);
      saida.push(...paragrafoCodigo(bloco));
      continue;
    }

    if (l.startsWith("|")) {                         // tabela
      const bloco = [];
      for (; i < linhas.length && linhas[i].startsWith("|"); i++) bloco.push(linhas[i]);
      i--;
      if (bloco.length >= 2) {
        saida.push(tabela(bloco));
        saida.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
      }
      continue;
    }

    if (l.startsWith(">")) {                         // citacao
      const bloco = [];
      for (; i < linhas.length && linhas[i].startsWith(">"); i++) {
        bloco.push(linhas[i].replace(/^>\s?/, ""));
      }
      i--;
      // uma linha da citacao = um paragrafo: o cabecalho de cada capitulo tem
      // varias linhas independentes, e junta-las numa so embaralha o sentido
      const linhasCit = bloco.filter((b) => b.trim() !== "");
      linhasCit.forEach((b, k) => saida.push(new Paragraph({
        children: inline(b.trim(), { italics: true, color: "3B4A54" }),
        indent: { left: 340 },
        border: { left: { style: BorderStyle.SINGLE, size: 14, color: "8FA6B5" } },
        spacing: { before: k === 0 ? 120 : 0, after: k === linhasCit.length - 1 ? 200 : 20 },
      })));
      continue;
    }

    if (/^---+$/.test(l.trim())) {                   // regua
      saida.push(new Paragraph({
        children: [], spacing: { before: 60, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "D5DBE0" } },
      }));
      continue;
    }

    const marca = l.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
    if (marca) {                                     // lista
      instanciaLista++;
      const ordenada = /\d/.test(marca[2]);
      // O item e montado por inteiro ANTES de virar TextRun: um item que ocupa
      // tres linhas pode ter um **negrito** aberto numa e fechado noutra, e
      // formatar linha a linha imprimiria os asteriscos.
      const itens = [];
      for (; i < linhas.length; i++) {
        const m = linhas[i].match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
        if (m) {
          itens.push({ nivel: Math.min(1, Math.floor(m[1].length / 2)), texto: m[3] });
          continue;
        }
        if (/^\s+\S/.test(linhas[i]) && itens.length) {          // continuacao
          itens[itens.length - 1].texto += " " + linhas[i].trim();
          continue;
        }
        if (linhas[i].trim() === "" &&                            // item espacado
            /^(\s*)([-*]|\d+\.)\s+/.test(linhas[i + 1] || "")) continue;
        break;
      }
      i--;
      itens.forEach((it) => saida.push(new Paragraph({
        children: inline(it.texto.replace(/\s+/g, " ").trim()),
        numbering: { reference: ordenada ? "numerada" : "marcada",
                     level: it.nivel, instance: instanciaLista },
        spacing: { before: 40, after: 40 },
      })));
      continue;
    }

    if (l.trim() === "") continue;

    const bloco = [l];                               // paragrafo
    for (i++; i < linhas.length && linhas[i].trim() !== ""
              && !/^(#{1,4}\s|\||>|```|---+$|\s*([-*]|\d+\.)\s)/.test(linhas[i]); i++) {
      bloco.push(linhas[i]);
    }
    i--;
    saida.push(new Paragraph({
      children: inline(bloco.join(" ").replace(/\s+/g, " ").trim()),
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 60, after: 140, line: 276 },
    }));
  }

  despeja();
  for (const [chave, lista] of pendentes) {
    throw new Error(`figura orfa: nenhuma secao comeca com "${chave}" ` +
                    `(${lista.map((f) => f.img).join(", ")})`);
  }
  return saida;
}

// ------------------------------------------------------------- apendice SQL
function apendiceSql() {
  const sql = ler(APENDICE_SQL.arquivo);
  const ev = ler(APENDICE_SQL.evidencia);
  const el = [
    new Paragraph({
      children: [new TextRun({ text: "Apêndice A — Consultas SQL da análise exploratória",
                               font: FONTE, bold: true, size: 32, color: AZUL })],
      heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { after: 200 },
    }),
    new Paragraph({
      children: inline("Cada bloco abaixo traz a **consulta exatamente como está** em " +
        "`sql/01_exploracao.sql` e, logo em seguida, a **saída real** que ela produziu — " +
        "copiada de `apresentacao/evidencias/01-perfil-07-exploracao-negocio.txt`, sem edição. " +
        "Nenhum número deste documento foi digitado à mão."),
      alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: 276 },
    }),
  ];

  let nApendice = 0;
  for (const n of APENDICE_SQL.secoes) {
    // consulta: entre o \echo do titulo e o \echo '' seguinte
    const abre = new RegExp(`^\\\\echo '=== ${n}\\. (.+?) =+'`, "m");
    const m = abre.exec(sql);
    if (!m) throw new Error(`secao ${n} nao encontrada em ${APENDICE_SQL.arquivo}`);
    const resto = sql.slice(m.index + m[0].length);
    const fim = resto.indexOf("\\echo ''");
    const consulta = resto.slice(0, fim === -1 ? undefined : fim).trim();

    // saida: entre o cabecalho === N. ... === e o proximo cabecalho ===
    const abreEv = new RegExp(`^=== ${n}\\. .+$`, "m");
    const mv = abreEv.exec(ev);
    if (!mv) throw new Error(`secao ${n} nao encontrada em ${APENDICE_SQL.evidencia}`);
    const restoEv = ev.slice(mv.index + mv[0].length);
    const fimEv = restoEv.search(/^=== \d+\./m);
    const saida = restoEv.slice(0, fimEv === -1 ? undefined : fimEv).trim();

    el.push(new Paragraph({
      children: [new TextRun({ text: `A.${++nApendice} ${m[1].trim()}`, font: FONTE, bold: true,
                               size: 25, color: AZUL })],
      heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 120 },
    }));
    el.push(new Paragraph({
      children: [txt("Consulta:", { bold: true, size: 19, color: AZUL_CLARO })],
      spacing: { after: 60 },
    }));
    el.push(...paragrafoCodigo(consulta.split("\n")));
    el.push(new Paragraph({
      children: [txt("Saída:", { bold: true, size: 19, color: AZUL_CLARO })],
      spacing: { before: 100, after: 60 },
    }));
    el.push(...paragrafoCodigo(saida.split("\n")));
  }
  return el;
}

// ----------------------------------------------------------------- montagem
function capa() {
  const linha = (t, o = {}) => new Paragraph({
    children: [new TextRun({ text: t, font: FONTE, ...o })],
    alignment: AlignmentType.CENTER, spacing: { after: o.after ?? 120 },
  });
  return [
    new Paragraph({ children: [], spacing: { after: 1200 } }),
    linha(CAPA.instituicao, { size: 24, color: AZUL_CLARO }),
    linha(CAPA.curso, { size: 22, color: AZUL_CLARO, after: 2400 }),
    linha(CAPA.titulo, { size: 44, bold: true, color: AZUL, after: 200 }),
    linha(CAPA.subtitulo, { size: 24, italics: true, color: "444444", after: 2400 }),
    new Paragraph({
      children: [], alignment: AlignmentType.CENTER, spacing: { after: 400 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: AZUL } },
    }),
    linha(CAPA.autor, { size: 26, bold: true, after: 2000 }),
    linha(CAPA.data, { size: 22, color: "555555" }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

function sumario() {
  return [
    new Paragraph({
      children: [new TextRun({ text: "Sumário", font: FONTE, bold: true, size: 32, color: AZUL })],
      spacing: { after: 240 },
    }),
    // sem quebra explicita aqui: o titulo do capitulo seguinte ja abre pagina
    new TableOfContents("Sumário", { hyperlink: true, headingStyleRange: "1-3" }),
  ];
}

function main() {
  const contador = { figura: 0 };
  const corpo = [];
  for (const rel of CAPITULOS) {
    corpo.push(...converte(ler(rel), FIGURAS[rel], contador));
  }
  corpo.push(...apendiceSql());

  const doc = new Document({
    features: { updateFields: true },   // o Word preenche o sumario ao abrir
    creator: CAPA.autor,
    title: CAPA.titulo,
    description: CAPA.subtitulo,
    numbering: {
      config: [
        { reference: "marcada", levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 400, hanging: 220 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 800, hanging: 220 } } } },
        ] },
        { reference: "numerada", levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 400, hanging: 220 } } } },
          { level: 1, format: LevelFormat.LOWER_LETTER, text: "%2)", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 800, hanging: 220 } } } },
        ] },
      ],
    },
    styles: { default: { document: { run: { font: FONTE, size: 21 } } } },
    sections: [{
      properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONTE, size: 18, color: "777777" })],
      })] }) },
      children: [...capa(), ...sumario(), ...corpo],
    }],
  });

  fs.mkdirSync(path.dirname(SAIDA), { recursive: true });
  Packer.toBuffer(doc).then((buf) => {
    fs.writeFileSync(SAIDA, buf);
    console.log(`${path.relative(RAIZ, SAIDA)}  —  ${(buf.length / 1024).toFixed(0)} kB, ` +
                `${CAPITULOS.length} capitulos, ${contador.figura} figuras`);
  });
}

main();

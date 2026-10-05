/* Slides da apresentação final (10 a 15 minutos), com roteiro nas notas.
 * Números lidos das evidências; nada digitado à mão.
 * Uso: node entregas/gerar_slides.js
 */
const fs = require('fs'), path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const fa = require('react-icons/fa6');
const { applyTheme } = require('./apply_theme.js');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(__dirname, 'entrega-04/Apresentacao-Projeto-Integrador.pptx');
const json = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const R = json('apresentacao/evidencias/entrega03/resultados.json');
const PERF = json('bench/results/entrega03/catalogo.json');
const IDX = json('bench/results/entrega04/indices-mongo.json');
const br = (v, d = 2) => Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });

const THEME = {
  name: 'Northwind PI',
  headFontFace: 'Cambria',
  bodyFontFace: 'Calibri',
  colors: {
    dk1: '1E2A33', lt1: 'FFFFFF', dk2: '1B2F3E', lt2: 'EEF2F5',
    accent1: '336791', accent2: '3F8F41', accent3: 'D9822B', accent4: '5B6B76',
    accent5: '8FB3CC', accent6: 'C24E4E', hlink: '336791', folHlink: '5B6B76',
  },
};
const HEX = THEME.colors;

async function icon(name, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: '#' + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}

async function main() {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE'; // 13,33 × 7,5 pol.
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.author = 'Giovanne Espindola';
  pres.title = 'Qual é a ferramenta certa para o trabalho?';
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: 'Capa', background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontFace: THEME.headFontFace, fontSize: 44, bold: true, color: C.background1, valign: 'bottom', align: 'left', margin: 0 }, text: '' } },
      { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 3.95, w: 11.7, h: 1.6, fontSize: 20, color: C.accent5, valign: 'top', align: 'left', margin: 0 }, text: '' } },
    ],
  });
  pres.defineSlideMaster({
    title: 'Conteudo', background: { color: C.background1 },
    margin: [0.5, 0.6, 0.6, 0.6],
    objects: [
      { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text2, valign: 'middle', margin: 0 }, text: '' } },
      { text: { text: 'Northwind  ·  PostgreSQL × MongoDB', options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: 'right' },
  });

  const I = {};
  for (const [k, n, c] of [['banco', 'FaDatabase', HEX.accent1], ['folha', 'FaLeaf', HEX.accent2], ['lupa', 'FaMagnifyingGlass', 'FFFFFF'],
    ['alerta', 'FaTriangleExclamation', 'FFFFFF'], ['relogio', 'FaClock', 'FFFFFF'], ['moeda', 'FaCoins', 'FFFFFF'], ['etiqueta', 'FaTags', 'FFFFFF'],
    ['check', 'FaCircleCheck', HEX.accent2], ['balanca', 'FaScaleBalanced', 'FFFFFF'], ['grafico', 'FaChartLine', 'FFFFFF'],
    ['usuarios', 'FaUsers', 'FFFFFF'], ['caixa', 'FaBoxOpen', 'FFFFFF'], ['camadas', 'FaLayerGroup', 'FFFFFF'], ['ferramenta', 'FaScrewdriverWrench', 'FFFFFF'],
    ['crescer', 'FaUpRightAndDownLeftFromCenter', 'FFFFFF'], ['seta', 'FaArrowRightLong', HEX.accent4]]) I[k] = await icon(n, c);

  const circle = (s, img, x, y, d, fill, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + '-circulo' });
    s.addImage({ data: img, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, objectName: name + '-icone' });
  };
  const card = (s, x, y, w, h, name, fill = C.background2) =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name });
  const txt = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, color: C.text1, fontSize: 16, valign: 'top', ...o });
  let relogio = 0;
  const mmss = t => { const r = Math.round(t); return `${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`; };
  const fala = (sl, texto, extra = '') => {
    const seg = texto.split(/\s+/).filter(Boolean).length / 130 * 60 + 5;
    sl.addNotes(`[${mmss(relogio)}–${mmss(relogio + seg)}]${extra}\n${texto}`);
    relogio += seg;
  };
  const content = (title, section) => { const s = pres.addSlide({ masterName: 'Conteudo', sectionTitle: section }); s.addText(title, { placeholder: 'title' }); return s; };

  // ---------- 1. Capa
  pres.addSection({ title: 'Abertura' });
  let s = pres.addSlide({ masterName: 'Capa', sectionTitle: 'Abertura' });
  s.addText('Qual é a ferramenta certa para o trabalho?', { placeholder: 'title' });
  s.addText([{ text: 'Os dados de vendas da Northwind em PostgreSQL e MongoDB', options: { breakLine: true } },
    { text: 'Giovanne Espindola  ·  Projeto Integrador — Banco de Dados  ·  IPOG', options: { fontSize: 15, color: C.background2 } }], { placeholder: 'body' });
  circle(s, I.banco, 0.8, 0.9, 0.9, C.background1, 'capa-pg');
  circle(s, I.folha, 1.9, 0.9, 0.9, C.background1, 'capa-mongo');
  fala(s, `Olá, eu sou o Giovanne. Este é o meu projeto integrador da área de Banco de Dados.
A pergunta que guiou o trabalho foi: qual é a ferramenta certa para cada trabalho com dados?
Para responder, peguei uma base de vendas e implementei a mesma solução em dois bancos bem diferentes: o PostgreSQL, relacional, e o MongoDB, orientado a documentos. Depois respondi às mesmas perguntas de negócio nos dois e comparei.
Vou contar essa história na ordem em que ela aconteceu. (desligar a câmera)`, ' — câmera ligada só neste slide');

  // ---------- 2. A base
  pres.addSection({ title: 'Os dados' });
  s = content('A base: uma distribuidora de alimentos', 'Os dados');
  const stats = [['830', 'pedidos'], ['2.155', 'itens vendidos'], ['91', 'clientes'], ['77', 'produtos']];
  stats.forEach(([n, l], i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 1.65, 2.8, 2.0, 'stat-' + i);
    txt(s, n, { x: x + 0.25, y: 1.85, w: 2.3, h: 1.0, fontSize: 54, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
    txt(s, l, { x: x + 0.25, y: 2.9, w: 2.3, h: 0.5, fontSize: 18, color: C.accent4 });
  });
  txt(s, [{ text: 'Northwind Traders', options: { bold: true } }, { text: ' é uma empresa fictícia usada para ensinar bancos de dados: clientes fazem pedidos, cada pedido tem itens, vendedores registram as vendas e transportadoras fazem o envio.' }],
    { x: 0.6, y: 4.1, w: 7.6, h: 1.4, fontSize: 18 });
  txt(s, [{ text: 'Período: ', options: { bold: true } }, { text: 'julho de 1996 a maio de 1998', options: { breakLine: true } },
    { text: 'Valor total registrado: ', options: { bold: true } }, { text: br(1265793.0395) }], { x: 0.6, y: 5.6, w: 7.6, h: 1.0, fontSize: 18 });
  card(s, 8.7, 4.1, 4.0, 2.5, 'limites', C.text2);
  txt(s, 'O que a base não tem', { x: 8.95, y: 4.3, w: 3.5, h: 0.4, fontSize: 16, bold: true, color: C.background1 });
  txt(s, [{ text: 'custo dos produtos', options: { bullet: true, breakLine: true } }, { text: 'pagamentos', options: { bullet: true, breakLine: true } }, { text: 'data de entrega', options: { bullet: true } }],
    { x: 8.95, y: 4.8, w: 3.5, h: 1.2, fontSize: 16, color: C.background2, paraSpaceAfter: 4 });
  txt(s, 'Por isso: valor, não lucro.', { x: 8.95, y: 6.05, w: 3.5, h: 0.4, fontSize: 14, italic: true, color: C.accent3 });
  fala(s, `A base é a Northwind, uma distribuidora fictícia muito usada para ensinar banco de dados. São 830 pedidos, 2.155 itens, 91 clientes e 77 produtos, de julho de 1996 a maio de 1998, somando 1 milhão e 265 mil em vendas registradas.
Um ponto que define o projeto inteiro: a base não tem custo dos produtos, nem pagamentos, nem data de entrega. Então eu falo em valor dos pedidos, nunca em lucro. E falo em data de envio, nunca em prazo de entrega.`);

  // ---------- 3. Qualidade
  s = content('Antes de modelar, olhar os dados', 'Os dados');
  const achados = [
    ['relogio', '1996 e 1998 estão incompletos', 'A base começa em julho de 1996 e termina em 6 de maio de 1998. Comparar anos inteiros daria uma falsa ideia de crescimento.'],
    ['alerta', '21 pedidos sem data de envio', 'Ausência de registro não prova que o pedido não saiu. O nulo foi mantido, nunca trocado por zero.'],
    ['moeda', 'O arredondamento muda o total', 'Arredondar cada item antes de somar acrescenta 0,25. Decisão: calcular com decimais exatos e arredondar só no final.'],
    ['etiqueta', '662 itens com preço diferente do catálogo', 'O preço é da venda, não do produto. Por isso ele precisa ficar guardado no pedido.'],
  ];
  achados.forEach(([ic, t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 0.6 + col * 6.2, y = 1.65 + row * 2.6;
    card(s, x, y, 5.9, 2.3, 'achado-' + i);
    circle(s, I[ic], x + 0.3, y + 0.3, 0.75, C.accent3, 'achado-' + i);
    txt(s, t, { x: x + 1.3, y: y + 0.32, w: 4.35, h: 0.75, fontSize: 19, bold: true, color: C.text2, valign: 'middle' });
    txt(s, d, { x: x + 1.3, y: y + 1.12, w: 4.35, h: 1.05, fontSize: 15, color: C.text1 });
  });
  fala(s, `Antes de modelar, fiz uma análise exploratória. Não encontrei referências quebradas nem valores inválidos, mas quatro achados mudaram o projeto.
1996 e 1998 estão incompletos, então não comparo anos inteiros. 21 pedidos não têm data de envio, e mantive o nulo, porque ausência não é zero.
O terceiro foi decisivo: arredondar cada item antes de somar muda o total em 25 centavos. Para comparar dois bancos número a número, a regra precisa ser a mesma; então tudo é calculado com decimais exatos e arredondado só no final.
E 662 itens têm preço diferente do catálogo: o preço é da venda, então fica guardado no pedido.`);

  // ---------- 4. Dois modelos
  pres.addSection({ title: 'Modelagem' });
  s = content('O mesmo pedido, duas formas de guardar', 'Modelagem');
  card(s, 0.6, 1.6, 5.9, 4.95, 'pg-card');
  circle(s, I.banco, 0.85, 1.8, 0.7, C.background1, 'pg');
  txt(s, 'PostgreSQL: tabelas ligadas', { x: 1.7, y: 1.85, w: 4.6, h: 0.6, fontSize: 20, bold: true, color: C.accent1, valign: 'middle' });
  const tab = (rows, y, h) => s.addTable(rows, { x: 0.85, y, w: 5.4, colW: undefined, fontSize: 12, color: HEX.dk1, border: { type: 'solid', pt: 0.5, color: 'C9D3DA' }, fill: { color: 'FFFFFF' }, rowH: 0.3 });
  txt(s, 'orders — 1 linha', { x: 0.85, y: 2.65, w: 5.4, h: 0.3, fontSize: 13, bold: true, color: C.accent4 });
  tab([[{ text: 'order_id', options: { bold: true } }, { text: 'customer_id', options: { bold: true } }, { text: 'order_date', options: { bold: true } }], ['10248', 'VINET', '1996-07-04']], 3.0);
  txt(s, 'order_items — 3 linhas', { x: 0.85, y: 3.85, w: 5.4, h: 0.3, fontSize: 13, bold: true, color: C.accent4 });
  tab([[{ text: 'product_id', options: { bold: true } }, { text: 'unit_price', options: { bold: true } }, { text: 'quantity', options: { bold: true } }],
    ['11', '14,00', '12'], ['42', '9,80', '10'], ['72', '34,80', '5']], 4.2);
  txt(s, 'Regras garantidas pelo banco: 11 chaves estrangeiras, 17 CHECK, 4 UNIQUE.', { x: 0.85, y: 5.65, w: 5.4, h: 0.7, fontSize: 14, italic: true, color: C.text1 });
  card(s, 6.85, 1.6, 5.9, 4.95, 'mongo-card');
  circle(s, I.folha, 7.1, 1.8, 0.7, C.background1, 'mongo');
  txt(s, 'MongoDB: um documento', { x: 7.95, y: 1.85, w: 4.6, h: 0.6, fontSize: 20, bold: true, color: C.accent2, valign: 'middle' });
  s.addText('{ _id: 10248,\n  customer_id: "VINET",\n  order_date: ISODate("1996-07-04"),\n  items: [\n    { product: { _id: 11, name: "Queso Cabrales" },\n      unit_price: Decimal128("14.00"),\n      quantity: 12 },\n    { product: { _id: 42, ... }, ... },\n    { product: { _id: 72, ... }, ... }\n  ] }',
    { isTextBox: true, x: 7.1, y: 2.65, w: 5.4, h: 2.85, fontFace: 'Courier New', fontSize: 12, color: C.text1, fill: { color: C.background1 }, margin: 0.12, valign: 'top' });
  txt(s, 'Os itens moram dentro do pedido. Clientes e produtos continuam em coleções próprias.', { x: 7.1, y: 5.65, w: 5.4, h: 0.7, fontSize: 14, italic: true, color: C.text1 });
  fala(s, `Esta é a principal decisão de modelagem, com um pedido real, o 10248.
No PostgreSQL, criei um schema próprio com regras garantidas pelo banco: chaves estrangeiras, 17 CHECK e 4 UNIQUE. O pedido fica em duas tabelas: uma linha em orders e três em order_items.
No MongoDB, a pergunta é o que deve ficar junto. O que pertence ao pedido e é lido com ele vai para dentro dele: os itens viraram um array. Clientes e produtos existem por conta própria, então ficaram em coleções separadas.
Para dinheiro, usei numeric e Decimal128, sem ponto flutuante.`);

  // ---------- 5. Arquitetura
  s = content('Um fluxo de mão única', 'Modelagem');
  const caixas = [['public', 'base original', 'preservada sem alterações', C.background2, C.text2, 0.6],
    ['PostgreSQL — nw', 'fonte da verdade', 'regras de integridade no banco', C.accent1, C.background1, 4.75],
    ['MongoDB', 'cópia para leitura', '9 coleções · 1.107 documentos', C.accent2, C.background1, 8.9]];
  caixas.forEach(([t, a, b, fill, fg, x], i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 3.8, h: 2.0, rectRadius: 0.15, fill: { color: fill }, line: { color: fill }, objectName: 'fluxo-' + i });
    txt(s, t, { x: x + 0.25, y: 2.1, w: 3.3, h: 0.5, fontSize: 20, bold: true, color: fg, align: 'center' });
    txt(s, a, { x: x + 0.25, y: 2.7, w: 3.3, h: 0.4, fontSize: 16, color: fg, align: 'center' });
    txt(s, b, { x: x + 0.25, y: 3.15, w: 3.3, h: 0.5, fontSize: 13, color: fg, align: 'center', italic: true });
  });
  s.addImage({ data: I.seta, x: 4.42, y: 2.72, w: 0.32, h: 0.32, objectName: 'seta-1' });
  s.addImage({ data: I.seta, x: 8.57, y: 2.72, w: 0.32, h: 0.32, objectName: 'seta-2' });
  txt(s, 'extração em SQL + carga com mongosh, em lote', { x: 4.75, y: 4.05, w: 7.95, h: 0.4, fontSize: 14, color: C.accent4, align: 'center', italic: true });
  const porques = [['Por que mão única?', 'Se os dois bancos aceitassem alterações, o mesmo dado teria dois donos. O MongoDB é reconstruído a partir do PostgreSQL.'],
    ['Por que em lote?', 'Nenhuma das perguntas de negócio precisa de dados atualizados ao segundo. A carga pode ser repetida sem duplicar nada.']];
  porques.forEach(([t, d], i) => {
    const x = 0.6 + i * 6.2;
    card(s, x, 4.75, 5.9, 1.85, 'porque-' + i);
    txt(s, t, { x: x + 0.3, y: 4.95, w: 5.3, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
    txt(s, d, { x: x + 0.3, y: 5.45, w: 5.3, h: 1.05, fontSize: 15 });
  });
  fala(s, `A arquitetura é simples e de mão única. A base original fica intocada no schema public. O schema nw é o modelo relacional e a fonte da verdade. A partir dele, uma extração em SQL gera os documentos, e o mongosh carrega no MongoDB.
Por que mão única? Porque, se os dois aceitassem alterações, o mesmo dado teria dois donos. E por que em lote? Porque nenhuma pergunta do projeto precisa de dado em tempo real. A carga pode ser repetida quantas vezes for preciso sem duplicar nada.`);

  // ---------- 6. Prova
  s = content('Como provar que nada se perdeu', 'Modelagem');
  const provas = [['3.311', 'linhas reconstruídas a partir do MongoDB e comparadas campo a campo com o PostgreSQL'], ['0', 'diferenças, inclusive em preços, datas e endereços'],
    [br(1265793.0395), 'mesmo total exato nos dois bancos'], ['5 de 5', 'documentos inválidos recusados pelos validadores']];
  provas.forEach(([n, l], i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 1.75, 2.8, 3.2, 'prova-' + i);
    txt(s, n, { x: x + 0.2, y: 1.95, w: 2.4, h: 1.0, fontSize: n.length > 6 ? 25 : 48, bold: true, color: C.accent2, fontFace: THEME.headFontFace, valign: 'middle' });
    txt(s, l, { x: x + 0.2, y: 3.1, w: 2.4, h: 1.7, fontSize: 15 });
  });
  card(s, 0.6, 5.3, 12.1, 1.3, 'licao', C.text2);
  txt(s, [{ text: 'Contar registros não basta. ', options: { bold: true, color: C.accent3 } },
    { text: 'Duas tabelas com o mesmo número de linhas podem ter preços diferentes. Por isso o caminho foi o inverso: desmontar os documentos e comparar linha a linha com a origem.' }],
    { x: 0.9, y: 5.45, w: 11.5, h: 1.0, fontSize: 16, color: C.background1, valign: 'middle' });
  fala(s, `Como saber que a migração deu certo? Contar documentos não basta, porque duas tabelas com o mesmo número de linhas podem ter preços diferentes.
Então fiz o caminho inverso: li os documentos do MongoDB, desmontei de volta em linhas e comparei campo a campo com o PostgreSQL. As 3.311 linhas voltaram sem nenhuma diferença, e o total exato deu o mesmo nos dois bancos.
Também testei os validadores do MongoDB com cinco documentos errados, como preço em texto e quantidade zero. Os cinco foram recusados.`);

  // ---------- 7. 16 perguntas
  pres.addSection({ title: 'Análises' });
  s = content('16 perguntas, duas implementações, três conferências', 'Análises');
  const temas = [['grafico', 'Vendas no tempo', 'mês a mês, acumulado, variação, trimestres'], ['caixa', 'Produtos', 'categorias, ranking, estoque, descontos, pares comprados juntos'],
    ['usuarios', 'Clientes', 'curva ABC, RFM, clientes inativos'], ['camadas', 'Equipe e operação', 'vendedores, hierarquia, transportadoras']];
  temas.forEach(([ic, t, d], i) => {
    const y = 1.6 + i * 1.22;
    circle(s, I[ic], 0.6, y, 0.85, C.accent1, 'tema-' + i);
    txt(s, t, { x: 1.65, y: y + 0.02, w: 4.9, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
    txt(s, d, { x: 1.65, y: y + 0.45, w: 4.9, h: 0.5, fontSize: 15, color: C.accent4 });
  });
  card(s, 7.0, 1.6, 5.7, 4.95, 'conferencia');
  txt(s, 'Cada resposta foi conferida três vezes', { x: 7.3, y: 1.8, w: 5.1, h: 0.5, fontSize: 18, bold: true, color: C.text2 });
  [['SQL (QNN.sql)', C.accent1], ['Pipeline MongoDB (PNN.js)', C.accent2], ['Cálculo independente em Python', C.accent3]].forEach(([t, col], i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.3, y: 2.5 + i * 0.85, w: 5.1, h: 0.65, rectRadius: 0.1, fill: { color: col }, line: { color: col }, objectName: 'via-' + i });
    txt(s, t, { x: 7.5, y: 2.5 + i * 0.85, w: 4.7, h: 0.65, fontSize: 16, bold: true, color: C.background1, valign: 'middle' });
  });
  s.addImage({ data: I.check, x: 7.3, y: 5.15, w: 0.5, h: 0.5, objectName: 'check' });
  txt(s, 'Mesmos números nas 16 perguntas, além de 38 testes com resultados calculados à mão.', { x: 7.95, y: 5.05, w: 4.5, h: 1.3, fontSize: 15 });
  fala(s, `Depois vieram as análises: 16 perguntas de negócio sobre vendas no tempo, produtos, clientes e equipe. Cada uma foi respondida duas vezes, em SQL e em pipeline do MongoDB. Também criei views para centralizar o cálculo do valor e três procedures com parâmetros.
Os dois bancos deram exatamente os mesmos números. Mas eles poderiam errar a mesma regra juntos, então recalculei tudo em Python e fiz testes com pedidos inventados, cujo resultado eu calculei à mão.`);

  // ---------- 8. Sintaxe
  s = content('Mesmo cálculo, duas sintaxes', 'Análises');
  txt(s, 'Ranking: os cinco produtos de maior valor em cada categoria', { x: 0.6, y: 1.45, w: 12.1, h: 0.45, fontSize: 18, color: C.accent4, italic: true });
  const codigo = (x, titulo, cor, code, nome) => {
    txt(s, titulo, { x, y: 2.05, w: 5.9, h: 0.45, fontSize: 18, bold: true, color: cor });
    s.addText(code, { isTextBox: true, x, y: 2.55, w: 5.9, h: 2.3, fontFace: 'Courier New', fontSize: 13, color: C.text1, fill: { color: C.background2 }, margin: 0.18, valign: 'middle', objectName: nome });
  };
  codigo(0.6, 'SQL — função de janela', C.accent1, 'row_number() OVER (\n  PARTITION BY category_id\n  ORDER BY valor DESC, product_id\n) AS posicao', 'sql');
  codigo(6.8, 'MongoDB — $setWindowFields', C.accent2, '{ $setWindowFields: {\n    partitionBy: "$category_id",\n    sortBy: { valor: -1, product_id: 1 },\n    output: { posicao: { $sum: 1, window:\n      { documents: ["unbounded", "current"] } } } } }', 'mongo');
  const licoes = [['O documento ajudou', 'nas perguntas sobre o pedido: os itens já estão dentro dele.'],
    ['O SQL foi mais direto', 'nas perguntas que partem de um cadastro, como clientes sem compra.'],
    ['As junções não sumiram', 'no MongoDB: viraram $lookup e $graphLookup.']];
  licoes.forEach(([t, d], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 5.15, 3.85, 1.45, 'licao-' + i);
    txt(s, [{ text: t + ' ', options: { bold: true, color: C.text2 } }, { text: d }], { x: x + 0.25, y: 5.3, w: 3.35, h: 1.15, fontSize: 15, valign: 'middle' });
  });
  fala(s, `Um exemplo de sintaxe: o ranking dos cinco produtos de maior valor em cada categoria. No SQL, é a função de janela row_number, separando por categoria. No MongoDB, o equivalente é o $setWindowFields.
No geral, o documento ajudou nas perguntas sobre o pedido, porque os itens já estão lá dentro. O SQL foi mais direto quando a pergunta parte de um cadastro, como clientes sem compra. E as junções não sumiram no MongoDB: só mudaram de nome.`);

  // ---------- 9. Insights: tempo
  pres.addSection({ title: 'O que os dados mostram' });
  s = content('As vendas cresceram até a base terminar', 'O que os dados mostram');
  const meses = R['2'].rows;
  const rot = m => ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][Number(m.slice(5, 7)) - 1] + '/' + m.slice(2, 4);
  s.addChart(pres.charts.LINE, [{ name: 'Valor mensal', labels: meses.map(x => rot(x.mes)), values: meses.map(x => Math.round(Number(x.valor))) }], {
    x: 0.6, y: 1.5, w: 8.2, h: 5.1, chartColors: [HEX.accent1], lineSize: 3, lineDataSymbol: 'circle', lineDataSymbolSize: 6,
    showLegend: false, showTitle: true, title: 'Valor mensal após descontos', titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: '+mn-lt',
    catAxisLabelColor: HEX.accent4, valAxisLabelColor: HEX.accent4, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt',
    valAxisLabelFormatCode: '#,##0', valGridLine: { color: 'DDE3E8', size: 0.5 }, catGridLine: { style: 'none' }, catAxisLabelRotate: -45,
  });
  const abr = meses.find(x => x.mes === '1998-04-01');
  card(s, 9.2, 1.5, 3.5, 2.35, 'pico');
  txt(s, br(abr.valor, 0), { x: 9.45, y: 1.65, w: 3.0, h: 0.8, fontSize: 32, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
  txt(s, 'abril de 1998, o maior mês, com 74 pedidos (eram 33 em janeiro de 1997)', { x: 9.45, y: 2.5, w: 3.0, h: 1.2, fontSize: 14 });
  card(s, 9.2, 4.1, 3.5, 2.5, 'maio', C.text2);
  txt(s, 'A queda de maio não é crise', { x: 9.45, y: 4.3, w: 3.0, h: 0.5, fontSize: 16, bold: true, color: C.accent3 });
  txt(s, 'A base termina no dia 6. Um mês incompleto parece uma queda de 85%.', { x: 9.45, y: 4.85, w: 3.0, h: 1.5, fontSize: 14, color: C.background1 });
  fala(s, `Agora, o que os dados contam. As vendas cresceram ao longo de 1997 e no começo de 1998. Abril de 1998 foi o maior mês, com 74 pedidos; em janeiro de 1997 eram 33.
E aqui está um exemplo de por que conhecer os dados importa: maio de 1998 parece uma queda de 85%. Mas não é crise. A base simplesmente termina no dia 6 de maio. Quem não soubesse disso tiraria uma conclusão errada.`);

  // ---------- 10. Insights: concentração
  s = content('Poucos clientes e produtos sustentam o negócio', 'O que os dados mostram');
  const abc = { A: 0, B: 0, C: 0 }; let tot = 0;
  R['10'].rows.forEach(x => { if (abc[x.classe] !== undefined) abc[x.classe] += Number(x.valor); tot += Number(x.valor); });
  const nA = R['10'].rows.filter(x => x.classe === 'A').length;
  const destaques = [
    [String(nA), 'clientes', `concentram ${br(100 * abc.A / tot, 0)}% do valor (classe A, entre 89 clientes com compras)`, C.accent1],
    ['11%', 'de toda a receita', 'vem de um único produto, o Côte de Blaye, mais da metade da categoria Beverages', C.accent2],
    ['MEREP', 'cliente classe A', 'não compra desde 30/10/1997: mais de seis meses antes do fim da base', C.accent6],
  ];
  destaques.forEach(([n, u, d, cor], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.6, 3.85, 3.6, 'destaque-' + i);
    txt(s, n, { x: x + 0.3, y: 1.8, w: 3.25, h: 1.05, fontSize: 48, bold: true, color: cor, fontFace: THEME.headFontFace });
    txt(s, u, { x: x + 0.3, y: 2.85, w: 3.25, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
    txt(s, d, { x: x + 0.3, y: 3.35, w: 3.25, h: 1.7, fontSize: 15 });
  });
  card(s, 0.6, 5.45, 12.1, 1.15, 'acao', C.text2);
  circle(s, I.lupa, 0.85, 5.6, 0.85, C.accent3, 'acao');
  txt(s, [{ text: 'Cruzando duas análises: ', options: { bold: true, color: C.accent3 } }, { text: 'a curva ABC diz quem importa; a inatividade diz quem sumiu. A Mère Paillarde está nas duas listas, e é por ela que uma ação comercial deveria começar.' }],
    { x: 1.95, y: 5.55, w: 10.5, h: 0.95, fontSize: 16, color: C.background1, valign: 'middle' });
  fala(s, `O segundo achado é a concentração. Pela curva ABC, ${nA} clientes concentram 80% do valor. E um único produto, o Côte de Blaye, responde por 11% de toda a receita.
O insight de que mais gosto vem de cruzar duas análises. A curva ABC diz quem importa; a inatividade diz quem parou de comprar. A Mère Paillarde está nas duas listas: classe A e sem compras há mais de seis meses. Se eu fosse a empresa, começaria por ela.`);

  // ---------- 11. Desempenho
  pres.addSection({ title: 'Comparação' });
  s = content('Neste volume, o PostgreSQL foi mais rápido', 'Comparação');
  const pares = Array.from({ length: 16 }, (_, i) => String(i + 1).padStart(2, '0'));
  s.addChart(pres.charts.BAR, [
    { name: 'PostgreSQL', labels: pares, values: pares.map(p => +PERF[String(+p)].postgres.mediana_ms.toFixed(2)) },
    { name: 'MongoDB', labels: pares, values: pares.map(p => +PERF[String(+p)].mongo.mediana_ms.toFixed(2)) },
  ], {
    x: 0.6, y: 1.5, w: 8.2, h: 5.1, barDir: 'col', barGapWidthPct: 60, chartColors: [HEX.accent1, HEX.accent2],
    showLegend: true, legendPos: 't', legendFontSize: 12, legendFontFace: '+mn-lt', legendColor: HEX.dk1,
    showTitle: true, title: 'Mediana de 20 execuções por consulta (ms)', titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: '+mn-lt',
    catAxisLabelColor: HEX.accent4, valAxisLabelColor: HEX.accent4, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt',
    valGridLine: { color: 'DDE3E8', size: 0.5 }, catGridLine: { style: 'none' },
  });
  const razoes = pares.map(p => PERF[String(+p)].mongo.mediana_ms / PERF[String(+p)].postgres.mediana_ms);
  card(s, 9.2, 1.5, 3.5, 2.1, 'razao');
  txt(s, `${br(Math.min(...razoes), 1)}× a ${br(Math.max(...razoes), 0)}×`, { x: 9.45, y: 1.65, w: 3.0, h: 0.8, fontSize: 30, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  txt(s, 'mais lento no MongoDB, nas 16 consultas', { x: 9.45, y: 2.5, w: 3.0, h: 0.9, fontSize: 14 });
  card(s, 9.2, 3.85, 3.5, 2.75, 'metodo', C.text2);
  txt(s, 'Como foi medido', { x: 9.45, y: 4.0, w: 3.0, h: 0.45, fontSize: 16, bold: true, color: C.accent3 });
  txt(s, [{ text: '5 aquecimentos', options: { bullet: true, breakLine: true } }, { text: '20 medições por consulta', options: { bullet: true, breakLine: true } },
    { text: 'ordem dos bancos alternada', options: { bullet: true, breakLine: true } }, { text: 'mediana, não média', options: { bullet: true } }],
    { x: 9.45, y: 4.5, w: 3.0, h: 1.9, fontSize: 14, color: C.background1, paraSpaceAfter: 3 });
  fala(s, `Na performance, medi as 16 consultas em cada banco, com 5 execuções de aquecimento e 20 medições, alternando qual banco rodava primeiro, e usei a mediana.
O PostgreSQL foi mais rápido em todas, com o MongoDB de ${br(Math.min(...razoes), 1)} a ${br(Math.max(...razoes), 0)} vezes mais lento. As maiores diferenças estão nas consultas que começam por um cadastro, como clientes, porque o MongoDB faz uma busca nos pedidos para cada cliente.
Mas eu não queria parar em “o Postgres ganhou”. Fui investigar o porquê.`);

  // ---------- 12. Índices
  s = content('Parte da diferença era índice', 'Comparação');
  const p04 = IDX['04'];
  card(s, 0.6, 1.6, 5.9, 3.0, 'antes');
  txt(s, 'Sem índice em employee_id', { x: 0.9, y: 1.8, w: 5.3, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  txt(s, '7.470', { x: 0.9, y: 2.35, w: 5.3, h: 1.1, fontSize: 60, bold: true, color: C.accent6, fontFace: THEME.headFontFace });
  txt(s, 'documentos lidos para calcular as vendas dos 9 vendedores (830 pedidos × 9)', { x: 0.9, y: 3.5, w: 5.3, h: 0.9, fontSize: 15 });
  card(s, 6.85, 1.6, 5.9, 3.0, 'depois');
  txt(s, 'Com o índice', { x: 7.15, y: 1.8, w: 5.3, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  txt(s, '830', { x: 7.15, y: 2.35, w: 5.3, h: 1.1, fontSize: 60, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  txt(s, `documentos lidos; tempo de ${br(p04.indices_atuais.mediana_ms, 1)} para ${br(p04.com_employee_shipper.mediana_ms, 1)} ms (−${br(100 * (1 - p04.com_employee_shipper.mediana_ms / p04.indices_atuais.mediana_ms), 0)}%)`, { x: 7.15, y: 3.5, w: 5.3, h: 0.9, fontSize: 15 });
  card(s, 0.6, 4.9, 12.1, 1.7, 'conclusao-idx', C.text2);
  circle(s, I.ferramenta, 0.9, 5.3, 0.85, C.accent3, 'idx');
  const rr = Object.values(IDX).map(v => v.com_employee_shipper.mediana_ms / v.postgres.mediana_ms);
  txt(s, [{ text: 'Mesmo com os índices, o PostgreSQL seguiu ' + br(Math.min(...rr), 1) + ' a ' + br(Math.max(...rr), 1) + ' vezes mais rápido. ', options: { bold: true, color: C.accent3 } },
    { text: 'O resto vem do modelo: um $lookup para cada cadastro contra uma única junção no SQL. Índice é manutenção contínua nos dois bancos.' }],
    { x: 2.0, y: 5.0, w: 10.4, h: 1.5, fontSize: 16, color: C.background1, valign: 'middle' });
  fala(s, `Olhando os planos de execução, achei parte da causa: faltava índice em employee_id no MongoDB. Para calcular as vendas dos 9 vendedores, ele lia os 830 pedidos para cada um: 7.470 documentos.
Testei numa cópia do banco com o índice: caiu para 830 documentos, e o tempo caiu ${br(100 * (1 - p04.com_employee_shipper.mediana_ms / p04.indices_atuais.mediana_ms), 0)}%.
Mesmo assim, o PostgreSQL continuou mais rápido, porque o resto vem do modelo: uma busca por cadastro contra uma única junção no SQL. Índice não é detalhe, é manutenção contínua.`);

  // ---------- 13. Decisão
  pres.addSection({ title: 'Decisão' });
  s = content('Então, qual escolher?', 'Decisão');
  const colunas = [
    ['banco', C.accent1, 'PostgreSQL', 'para registrar e cruzar', ['regras garantidas pelo banco', 'muitas entidades relacionadas', 'perguntas novas a cada dia', 'cadastros que mudam']],
    ['folha', C.accent2, 'MongoDB', 'para ler o agregado inteiro', ['tela que mostra o pedido completo', 'atributos que variam por registro', 'crescer distribuindo dados', 'poucas junções por consulta']],
    ['balanca', C.accent3, 'Os dois', 'quando os dois padrões convivem', ['relacional registra', 'documental serve a leitura', 'custo: carga, cópias e dois bancos', 'arquitetura deste projeto']],
  ];
  colunas.forEach(([ic, cor, t, sub, itens], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.55, 3.85, 4.15, 'decisao-' + i);
    if (ic === 'balanca') circle(s, I.balanca, x + 0.3, 1.75, 0.8, cor, 'decisao-' + i);
    else circle(s, I[ic], x + 0.3, 1.75, 0.8, C.background1, 'decisao-' + i);
    txt(s, t, { x: x + 1.25, y: 1.78, w: 2.45, h: 0.45, fontSize: 20, bold: true, color: cor });
    txt(s, sub, { x: x + 1.25, y: 2.22, w: 2.45, h: 0.4, fontSize: 13, italic: true, color: C.accent4 });
    txt(s, itens.map((t2, j) => ({ text: t2, options: { bullet: true, breakLine: j < itens.length - 1 } })), { x: x + 0.3, y: 2.9, w: 3.3, h: 2.6, fontSize: 15, paraSpaceAfter: 6 });
  });
  card(s, 0.6, 5.95, 12.1, 0.75, 'recomendacao', C.text2);
  txt(s, [{ text: 'Para a Northwind: ', options: { bold: true, color: C.accent3 } }, { text: 'o PostgreSQL sozinho atende. O MongoDB passa a valer se surgir, por exemplo, um portal com muitos clientes consultando pedidos.' }],
    { x: 0.9, y: 5.95, w: 11.5, h: 0.75, fontSize: 15, color: C.background1, valign: 'middle' });
  fala(s, `Então, qual escolher? Não existe vencedor geral; existe o padrão de acesso.
O PostgreSQL é a escolha para registrar e cruzar dados: regras garantidas pelo banco, muitas entidades relacionadas e perguntas novas o tempo todo.
O MongoDB faz sentido quando se lê o agregado inteiro, como uma tela com o pedido completo, ou quando os registros variam de formato.
Os dois juntos valem quando esses padrões convivem, com o custo de manter a carga e dois bancos.
Para a Northwind, o PostgreSQL sozinho atende. O MongoDB passaria a valer com, por exemplo, um portal de clientes consultando pedidos.`);

  // ---------- 14. Escala e manutenção
  s = content('Pensando em crescer e manter', 'Decisão');
  const linhas = [
    ['crescer', 'Escalar', 'PostgreSQL cresce com servidor maior, réplicas de leitura e particionamento por data. MongoDB cresce distribuindo coleções entre servidores, mas junções entre servidores ficam caras.'],
    ['ferramenta', 'Manter cópias', 'No MongoDB, o nome do produto está copiado em cada item vendido. Renomear um produto vira uma atualização em muitos pedidos.'],
    ['camadas', 'Mudar a estrutura', 'Acrescentar um campo é mais fácil no MongoDB, mas validadores e consultas precisam acompanhar.'],
    ['alerta', 'Limite deste estudo', '830 pedidos cabem em memória. Grandes volumes e acesso concorrente não foram medidos.'],
  ];
  linhas.forEach(([ic, t, d], i) => {
    const y = 1.55 + i * 1.3;
    circle(s, I[ic], 0.6, y + 0.1, 0.8, i === 3 ? C.accent6 : C.accent4, 'escala-' + i);
    txt(s, t, { x: 1.65, y: y + 0.08, w: 2.6, h: 0.85, fontSize: 18, bold: true, color: C.text2, valign: 'middle' });
    txt(s, d, { x: 4.3, y: y + 0.03, w: 8.4, h: 1.0, fontSize: 15, valign: 'middle' });
  });
  fala(s, `Sobre escalabilidade e manutenção, é importante deixar claro que isso é análise, não medição: 830 pedidos cabem em memória.
Para crescer, o PostgreSQL usa um servidor maior, réplicas de leitura e particionamento por data. O MongoDB cresce distribuindo os dados entre servidores, mas as junções entre servidores ficam caras, então o modelo precisa evitá-las.
Na manutenção, o custo do MongoDB está nas cópias: o nome do produto está copiado em cada item vendido, então renomear um produto vira uma atualização em muitos pedidos. Em compensação, acrescentar um campo é mais fácil, desde que validadores e consultas acompanhem.`);

  // ---------- 15. Encerramento
  pres.addSection({ title: 'Encerramento' });
  s = pres.addSlide({ masterName: 'Capa', sectionTitle: 'Encerramento' });
  s.addText('A ferramenta certa depende do trabalho', { placeholder: 'title' });
  const fim = ['Os dois bancos chegaram às mesmas respostas, desde que as regras fossem fixadas antes',
    'O documento simplifica o pedido; o relacional simplifica o cruzamento',
    'Medir, investigar o porquê e só então concluir'];
  s.addText(fim.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < fim.length - 1 } })),
    { isTextBox: true, x: 0.8, y: 4.0, w: 11.7, h: 1.9, fontSize: 20, color: C.background2, paraSpaceAfter: 10, valign: 'top', margin: 0 });
  txt(s, 'Obrigado!', { x: 0.8, y: 6.3, w: 6, h: 0.6, fontSize: 22, bold: true, color: C.accent3 });
  fala(s, `Para fechar: a ferramenta certa depende do trabalho.
Os dois bancos chegaram exatamente às mesmas respostas, desde que eu fixasse antes as regras de cálculo, principalmente o arredondamento.
O documento simplifica tudo o que gira em torno do pedido; o relacional simplifica cruzar informações.
E o aprendizado de método: medir, investigar o porquê da diferença e só então concluir.
Obrigado!`);

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log(OUT);
}
main().catch(e => { console.error(e); process.exitCode = 1; });

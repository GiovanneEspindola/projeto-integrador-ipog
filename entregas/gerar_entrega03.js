/* Word cumulativo: capítulos revisados, evidências executadas e códigos completos. */
const fs=require('fs'),path=require('path');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,HeadingLevel,
 AlignmentType,WidthType,TableLayoutType,Footer,Header,PageNumber,ImageRun,
 BorderStyle,ExternalHyperlink}=require('docx');
const ROOT=path.resolve(__dirname,'..');
const OUT=path.join(__dirname,'entrega-03/Projeto-Integrador-Banco-de-Dados-Entrega-03.docx');
const E=path.join(ROOT,'apresentacao/evidencias/entrega03');
const read=p=>fs.readFileSync(path.join(ROOT,p),'utf8');
const json=p=>JSON.parse(read(p));
const legacy=json('apresentacao/evidencias/revisao-entrega01/resultados.json');
const manifest=json('apresentacao/evidencias/entrega03/manifesto.json');
const crypto=require('crypto');
for(const [file,hash] of Object.entries(manifest.sha256)){
 if(crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,file))).digest('hex')!==hash)
  throw Error('Código mudou depois da validação: '+file);
}
const WIDTH=9638, FONT='Calibri', BLUE='214761';
const run=(t,o={})=>new TextRun({text:String(t),font:FONT,size:21,...o});
function inline(s,o={}){
 return String(s).split(/(\*\*.*?\*\*|`[^`]+`|https:\/\/[^\s]+)/g).filter(Boolean).map(t=>{
  if(t.startsWith('**'))return run(t.slice(2,-2),{...o,bold:true});
  if(t.startsWith('`'))return run(t.slice(1,-1),{...o,font:'Consolas',size:18});
  if(t.startsWith('https://'))return new ExternalHyperlink({link:t.replace(/[.,;]$/,''),children:[run(t,{...o,color:BLUE,underline:{}})]});
  return run(t,o);
 });
}
const para=(s,o={})=>new Paragraph({children:inline(s),spacing:{after:105,line:250},...o});
const headings=[];const seen=new Set();
function heading(s,level){
 if(level===1){const id=(s.match(/^(\d+)[.]|^(Apêndice [AB])|^(Referências)/)||[]).slice(1).find(Boolean);
  if(id&&!seen.has(id)){headings.push(s);seen.add(id);}}
 return new Paragraph({children:[run(s,{bold:true,color:BLUE,size:level===1?28:23})],
 heading:level===1?HeadingLevel.HEADING_1:level===2?HeadingLevel.HEADING_2:HeadingLevel.HEADING_3,
 pageBreakBefore:level===1,keepNext:true,spacing:{before:level===1?0:160,after:120}});
}
function table(cols,rows){
 const weights=cols[0]==='Seção' ? [86,14] : cols.map(c=>Math.max(5,Math.min(27,c.length+3)));
 // Nome descritivo ocupa mais largura, sem estreitar números demais.
 const denom=weights.reduce((a,b)=>a+b,0);const widths=weights.map(x=>Math.floor(WIDTH*x/denom));
 widths[widths.length-1]+=WIDTH-widths.reduce((a,b)=>a+b,0);
 const row=(values,head=false)=>new TableRow({tableHeader:head,cantSplit:true,children:values.map((v,i)=>new TableCell({
  width:{size:widths[i],type:WidthType.DXA},margins:{top:60,bottom:60,left:75,right:75},
  shading:{fill:head?'E6EEF3':'FFFFFF'},children:[new Paragraph({children:inline(v??'',{size:18,bold:head}),spacing:{after:0,line:220}})]}))});
 return [new Table({width:{size:WIDTH,type:WidthType.DXA},columnWidths:widths,layout:TableLayoutType.FIXED,
 borders:Object.fromEntries(['top','bottom','left','right','insideHorizontal','insideVertical'].map(k=>[k,{style:BorderStyle.SINGLE,size:3,color:'CFD9DF'}])),
 rows:[row(cols,true),...rows.map(r=>row(r))]}),para('',{spacing:{after:45,line:40}})];
}
function code(s){
 return s.trimEnd().split('\n').map(line=>new Paragraph({children:[run(line,{font:'Consolas',size:18})],
 shading:{fill:'F3F6F8'},spacing:{after:0,line:210},widowControl:false}));
}
function png(file){
 const data=fs.readFileSync(path.join(ROOT,file));let w=data.readUInt32BE(16),h=data.readUInt32BE(20);
 // O ER lógico é alto e tem texto pequeno: recebe uma página quase inteira.
 const maxH=file.endsWith('er-logico.png')?860:670;
 const scale=Math.min(605/w,maxH/h);w=Math.round(w*scale);h=Math.round(h*scale);
 return new Paragraph({alignment:AlignmentType.CENTER,children:[new ImageRun({type:'png',data,
  transformation:{width:w,height:h},altText:{title:path.basename(file),description:file,name:path.basename(file)}})],spacing:{after:100}});
}
const fmt=v=>{
 if(v===null)return '—';if(typeof v==='object')return JSON.stringify(v);
 if(typeof v==='boolean')return v?'sim':'não';
 if(typeof v==='string' && /^-?\d+\.\d+$/.test(v)){
  const negative=v.startsWith('-'),parts=v.replace('-','').split('.');
  const fraction=(parts[1]+'000').slice(0,3);
  let cents=BigInt(parts[0])*100n+BigInt(fraction.slice(0,2));
  if(Number(fraction[2])>=5)cents+=1n;
  return (negative&&cents!==0n?'-':'')+(cents/100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')+','+(cents%100n).toString().padStart(2,'0');
 }
 return String(v);
};
function ev(key,query){let d=legacy[key];return [...(query?code(d.sql):[]),...table(d.columns,d.rows.map(r=>r.map(fmt)))];}
function pgSummary(p){
 const root=p['QUERY PLAN'][0];const nodes=[];
 const walk=x=>{nodes.push(x);for(const c of x.Plans||[])walk(c);};walk(root.Plan);
 return {nodes:[...new Set(nodes.map(n=>n['Node Type']))].join(', '),indexes:[...new Set(nodes.map(n=>n['Index Name']).filter(Boolean))].join(', ')||'nenhum',
 rows:root.Plan['Actual Rows'],hits:root.Plan['Shared Hit Blocks']??0,reads:root.Plan['Shared Read Blocks']??0,
 removed:nodes.reduce((a,n)=>a+(n['Rows Removed by Filter']||0)*(n['Actual Loops']||1),0)};
}
function mongoSummary(p){
 const indexes=new Set(),stages=new Set(),cursors=[],lookups=[];
 const visit=x=>{if(!x||typeof x!=='object')return;
  if(x.indexName)indexes.add(x.indexName);if(Array.isArray(x.indexesUsed))x.indexesUsed.forEach(i=>indexes.add(i));if(x.stage)stages.add(x.stage);
  if(x.$cursor?.executionStats)cursors.push(x.$cursor.executionStats);
  if(x.$lookup)lookups.push({docs:x.totalDocsExamined,keys:x.totalKeysExamined});
  for(const [k,v] of Object.entries(x))if(!['rejectedPlans','allPlansExecution'].includes(k)&&v&&typeof v==='object')visit(v);};visit(p);
 const cursor=cursors[0]||p.executionStats||{};
 return {nodes:[...stages].join(', ')||'etapas de agregação',indexes:[...indexes].join(', ')||'nenhum',
 rows:cursor.nReturned??'—',docs:cursor.totalDocsExamined??'—',keys:cursor.totalKeysExamined??'—',lookups};
}
function plan(caseid){
 const all=json('bench/results/entrega03/otimizacoes.json')[caseid];const rows=[];
 const n=x=>typeof x==='number'?x.toLocaleString('pt-BR'):x;
 for(const v of Object.keys(all)){
  const p=pgSummary(json(`bench/results/entrega03/${caseid}-${v}-postgres-plan.json`));
  const m=mongoSummary(json(`bench/results/entrega03/${caseid}-${v}-mongo-plan.ejson`));
  rows.push([v,'PostgreSQL',p.nodes,p.indexes,`${n(p.removed)} linhas descartadas por filtro; ${n(p.hits)} páginas lidas do cache`]);
  const lk=m.lookups.filter(x=>x.docs!==undefined).map(x=>`$lookup: ${n(x.docs)} documentos`).join('; ');
  rows.push([v,'MongoDB',m.nodes,m.indexes,`${n(m.docs)} documentos e ${n(m.keys)} chaves examinados${lk?'; '+lk:''}`]);
 }
 return [para(`Resumo dos planos de execução de ${caseid}:`,{keepNext:true}),...table(['Versão testada','Banco de dados','Operações do plano','Índice usado','Trabalho observado'],rows)];
}
function parse(md){
 const lines=md.trim().split('\n'),out=[];
 for(let i=0;i<lines.length;i++){
  let l=lines[i].trim();if(!l||l==='<!-- page -->')continue;
  if(l.startsWith('#')){out.push(heading(l.replace(/^#+\s*/,''),Math.min(3,l.match(/^#+/)[0].length)));continue;}
  if(l.startsWith('```')){let b=[];for(i++;i<lines.length&&!lines[i].startsWith('```');i++)b.push(lines[i]);out.push(...code(b.join('\n')),para(''));continue;}
  let m=l.match(/^<!-- (query|table):(\w+) -->$/);if(m){out.push(...ev(m[2],m[1]==='query'));continue;}
  if(l==='<!-- diagram -->'){out.push(png('docs/diagramas/er-conceitual-relatorio.png'));continue;}
  if((m=l.match(/^<!-- image:(.+) -->$/))){out.push(png(m[1]));continue;}
  if((m=l.match(/^<!-- plano:(.+) -->$/))){out.push(...plan(m[1]));continue;}
  if(l==='<!-- comparacao -->'){out.push(...parse(read('docs/entrega03/comparacao-tabela.md')));continue;}
  if(l==='<!-- procedures -->'){
   const d=json('apresentacao/evidencias/entrega03/procedures.json');
   for(const [name,rows]of Object.entries(d)){
    // A lista de inativos é idêntica à de Q06, exibida por completo na seção 14.6.
    if(name==='inativos'){out.push(para(`A chamada \`CALL sp_clientes_inativos('1998-05-06', 6, ...)\` devolveu ${rows.length} clientes, os mesmos de Q06, na mesma ordem (tabela completa na seção 14.6).`));continue;}
    const shown=rows;
    const label={vendas_por_categoria:"CALL sp_resumo_vendas_periodo('1996-07-01', '1998-06-01', ...)",
     inativos:"CALL sp_clientes_inativos('1998-05-06', 6, ...)",equipe:"CALL sp_desempenho_equipe(2, '1996-07-01', '1998-06-01', ...)"}[name]||name;
    out.push(para('Saída de `'+label+'`'+(shown.length<rows.length?` — primeiras ${shown.length} de ${rows.length} linhas:`:':'),{keepNext:true}));
    const cols=Object.keys(rows[0]);out.push(...table(cols,shown.map(r=>cols.map(c=>fmt(r[c])))));}continue;
  }
  if(l==='<!-- recursos -->'){
   const d=json('apresentacao/evidencias/entrega03/recursos-documentais.json');const pn=d.painel[0];
   out.push(para(`Com $elemMatch, ${d.mesmo_item.length} pedidos têm um item que atende às três condições ao mesmo tempo. Com as mesmas condições escritas separadamente sobre o array, a contagem sobe para ${d.condicoes_independentes}: nos ${d.condicoes_independentes-d.mesmo_item.length} pedidos a mais, as condições são satisfeitas por itens diferentes.`));
   out.push(para(`O pedido ${d.pedido[0]._id} contém ${d.pedido[0].produtos.join(', ')}; o $reduce somou ${fmt(d.pedido[0].valor.$numberDecimal)} sem expandir os itens. O painel de 1997 devolveu, em um único documento, ${pn.volume[0].pedidos} pedidos, a situação da data de envio e a distribuição por quantidade de itens:`,{keepNext:true}));
   out.push(...table(['Faceta','Resultado'],[['volume',`${pn.volume[0].pedidos} pedidos`],
    ['envio',pn.envio.map(x=>`${x._id}: ${x.pedidos}`).join('; ')],
    ['tamanho',pn.tamanho.map(x=>`${x._id} ${x._id===1?'item':'itens'}: ${x.pedidos}`).join('; ')]]));continue;
  }
  if(l.startsWith('|')){
   let b=[];for(;i<lines.length&&lines[i].trim().startsWith('|');i++)b.push(lines[i].trim());i--;
   let cells=s=>s.slice(1,-1).split('|').map(x=>x.trim());out.push(...table(cells(b[0]),b.slice(2).map(cells)));continue;
  }
  const b=[l];while(i+1<lines.length&&lines[i+1].trim()&&!/^(#|\||<!--|```)/.test(lines[i+1]))b.push(lines[++i].trim());
  out.push(para(b.join(' ')));
 }
 return out;
}
const files=['entrega03/01-introducao.md','entrega03/02-compreensao-do-negocio.md','entrega03/03-modelo-conceitual.md',
 'entrega03/04-analise-exploratoria.md','entrega03/05-abordagem.md','entrega03/06-modelo-relacional.md','entrega03/06-criterios.md',
 'entrega02/09-modelo-documental.md','entrega02/10-transformacao.md','entrega03/09-indices.md','entrega02/12-validacao.md',
 'entrega03/11-transicao.md','entrega03/contrato-analitico.md','entrega03/13-views-procedures.md',
 'entrega03/14-analises.md','entrega03/15-recursos-mongo.md','entrega03/16-comparacao.md',
 'entrega03/17-performance.md','entrega03/18-conclusoes.md','entrega03/19-referencias.md'];
let body=files.flatMap(f=>parse(read('docs/'+f)));
body.push(heading('Apêndice A — Consultas SQL e pipelines completos',1),
 para('Os códigos abaixo são os mesmos arquivos executados na validação. Cada consulta SQL pode ser executada no PostgreSQL e cada pipeline, no mongosh; o trecho final de cada arquivo .js apenas imprime o resultado. Datas e regras seguem o contrato do capítulo 12.'));
for(let n=1;n<=16;n++){
 let id=String(n).padStart(2,'0');body.push(heading(`A.${n} Par Q${id}/P${id}`,2),para('PostgreSQL:',{keepNext:true}),...code(read(`sql/queries/Q${id}.sql`)),para('MongoDB:',{keepNext:true}),...code(read(`mongo/pipelines/P${id}.js`)));
}
body.push(heading('Apêndice B — Views, procedures e recursos documentais',1));
for(const f of ['sql/entrega03/00_views.sql','sql/entrega03/10_procedures.sql','sql/entrega03/11_exemplos_procedures.sql',
 'mongo/entrega03/recursos_documentais.js','mongo/entrega03/mapreduce.js'])body.push(heading(path.basename(f),2),...code(read(f)));
const tocfile=path.join(__dirname,'entrega-03/sumario.json');const pages=fs.existsSync(tocfile)?JSON.parse(fs.readFileSync(tocfile)):{};
fs.writeFileSync(path.join(__dirname,'entrega-03/titulos.json'),JSON.stringify(headings,null,2));
const cover=[para('IPOG — Instituto de Pós-Graduação e Graduação',{alignment:AlignmentType.CENTER,spacing:{before:700,after:220}}),
 para('Projeto Integrador • Área 03 — Banco de Dados',{alignment:AlignmentType.CENTER,spacing:{after:1500}}),
 new Paragraph({alignment:AlignmentType.CENTER,children:[run('Modelagem e análise de dados de vendas',{bold:true,size:40,color:BLUE})],spacing:{after:260}}),
 para('Northwind Traders • PostgreSQL e MongoDB',{alignment:AlignmentType.CENTER,spacing:{after:600}}),
 para('Entrega 3 — Relatório cumulativo',{alignment:AlignmentType.CENTER,children:[run('Entrega 3 — Relatório cumulativo',{bold:true,size:27,color:BLUE})],spacing:{after:260}}),
 para('Modelagem, consultas equivalentes e avaliação de desempenho',{alignment:AlignmentType.CENTER,spacing:{after:1450}}),
 para('Giovanne Espindola',{alignment:AlignmentType.CENTER,spacing:{after:200}}),
 para('Trabalho individual',{alignment:AlignmentType.CENTER,spacing:{after:850}}),
 para('Setembro de 2026',{alignment:AlignmentType.CENTER}),
 new Paragraph({children:[run('Sumário',{bold:true,size:28,color:BLUE})],pageBreakBefore:true,spacing:{after:180}}),
 ...table(['Seção','Página'],headings.map(h=>[h,pages[h]||'—']))];
const doc=new Document({creator:'Giovanne Espindola',title:'Modelagem e análise de dados de vendas — Entrega 3',
 description:'Relatório cumulativo: modelagem, 16 pares de análises, procedures e desempenho medido.',
 styles:{default:{document:{run:{font:FONT,size:21,color:'20252A'},paragraph:{widowControl:true}}}},
 sections:[{properties:{titlePage:true,page:{size:{width:11906,height:16838},margin:{top:950,bottom:950,left:1134,right:1134,header:380,footer:400}}},
 headers:{default:new Header({children:[para('NORTHWIND / PROJETO INTEGRADOR — ENTREGA 3',{children:[run('NORTHWIND / PROJETO INTEGRADOR — ENTREGA 3',{size:15,color:'637782'})]})]})},
 footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[run('Giovanne Espindola • ',{size:16}),new TextRun({children:[PageNumber.CURRENT,' / ',PageNumber.TOTAL_PAGES],font:FONT,size:16})]})]})},children:[...cover,...body]}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(OUT,b);console.log(OUT);}).catch(e=>{console.error(e);process.exitCode=1;});

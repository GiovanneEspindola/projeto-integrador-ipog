/* Relatório acumulativo: texto em docs/, evidências executadas e figura vetorial.
 * npm run docx. Acrescente capítulos a CAPITULOS nas próximas entregas.
 * A saída com sufixo Revisado é o documento oficial da Entrega 1.
 */
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, TableLayoutType, Footer, Header,
  PageNumber, ImageRun, BorderStyle, ExternalHyperlink } = require('docx');
const ROOT = path.resolve(__dirname, '..');
const OUTPUT = path.join(__dirname, 'entrega-01/Projeto-Integrador-Banco-de-Dados-Revisado.docx');
const CAPITULOS = [
  '01-introducao-e-objetivo.md', '02-compreensao-do-negocio.md',
  '03-modelo-conceitual.md', '04-analise-exploratoria.md',
  '05-plano-hibrido.md', '07-fechamento-entrega01.md', '08-referencias.md',
];
const results = JSON.parse(fs.readFileSync(path.join(ROOT, 'apresentacao/evidencias/revisao-entrega01/resultados.json')));
const SQL = fs.readFileSync(path.join(ROOT,'sql/02_evidencias_entrega01.sql'),'utf8');
// Também comparar usando separação por marcador, sem depender do fim de linha.
for (const part of SQL.split(/^-- @/m).slice(1)) {
 const key=part.match(/^\w+/)[0];
 const query=part.slice(part.indexOf('\n')+1).trim();
 if (!results[key] || query !== results[key].sql) throw new Error(`Reexecute a conferência: consulta ${key} mudou.`);
}
const FONT='Calibri', MONO='Consolas', BLUE='214761', WIDTH=9638;
const run=(text,opts={})=>new TextRun({text:String(text),font:FONT,size:21,...opts});
function inline(text,opts={}) {
 const tokens=text.split(/(\*\*.*?\*\*|`[^`]+`|https:\/\/\S+)/g).filter(Boolean);
 return tokens.map(t=>{
  if(t.startsWith('**')) return run(t.slice(2,-2),{...opts,bold:true});
  if(t.startsWith('`')) return run(t.slice(1,-1),{...opts,font:MONO,size:19});
  if(t.startsWith('https://')) {
   const url=t.replace(/[.,;]$/,'');
   return new ExternalHyperlink({link:url,children:[run(t,{...opts,color:BLUE,underline:{}})]});
  }
  return run(t,opts);
 });
}
function para(text,options={}) {
 return new Paragraph({children:inline(text),spacing:{after:110,line:252},...options});
}
function heading(text,level=1) {
 return new Paragraph({children:[run(text,{bold:true,size:level===1?29:23,color:BLUE})],
 heading:level===1?HeadingLevel.HEADING_1:HeadingLevel.HEADING_2,
 spacing:{before:level===1?0:150,after:130},keepNext:true});
}
function table(headers,rows,custom) {
 const n=headers.length;
 const proportions=custom || (n===2?[.42,.58]:n===3?[.58,.21,.21]:n===4?[.49,.17,.17,.17]:Array(n).fill(1/n));
 const widths=proportions.map(p=>Math.floor(p*WIDTH));
 widths[n-1]+=WIDTH-widths.reduce((a,b)=>a+b,0);
 const border={style:BorderStyle.SINGLE,size:3,color:'CFD9DF'};
 const row=(values,head=false,index=0)=>new TableRow({tableHeader:head,cantSplit:true,
 children:values.map((value,i)=>new TableCell({width:{size:widths[i],type:WidthType.DXA},
 margins:{top:65,bottom:65,left:85,right:85},
 shading:{fill:head?'E6EEF3':index%2?'F5F8FA':'FFFFFF'},
 children:[new Paragraph({children:inline(String(value??''),{size:19,bold:head,color:head?BLUE:'20252A'}),spacing:{after:0,line:230}})]}))});
 return [new Table({width:{size:WIDTH,type:WidthType.DXA},columnWidths:widths,
 layout:TableLayoutType.FIXED,borders:{top:border,bottom:border,left:border,right:border,insideHorizontal:border,insideVertical:border},
 rows:[row(headers,true),...rows.map((r,i)=>row(r,false,i))]}),new Paragraph({children:[],spacing:{after:65,line:40}})];
}
function code(query) {
 return query.split('\n').map((line,i,all)=>new Paragraph({
 children:[run(line,{font:MONO,size:18})],shading:{fill:'F0F4F6'},indent:{left:100,right:70},
 spacing:{before:i===0?40:0,after:i===all.length-1?90:0,line:220},keepNext:i<all.length-1,
 }));
}
function evidence(key,withQuery) {
 const result=results[key];
 if(!result) throw new Error(`Evidência ausente: ${key}`);
 const children=[];
 if(withQuery) children.push(...code(result.sql),para('Saída da consulta:',{spacing:{after:60},keepNext:true}));
 let widths;
 if(key==='resumo') widths=[.26,.26,.17,.31];
 if(key==='valores') widths=[.25,.19,.19,.18,.19];
 if(key==='envio') widths=[.2,.2,.3,.3];
 if(key==='anos') widths=[.2,.25,.55];
 if(key==='nulos') widths=[.55,.13,.14,.18];
 if(key==='categorias') widths=[.6,.4];
 if(key==='integridade'||key==='dominios') widths=[.8,.2];
 return children.concat(table(result.columns,result.rows,widths));
}
function parse(md) {
 const lines=md.trim().split('\n'),out=[];
 for(let i=0;i<lines.length;i++) {
  const l=lines[i].trim(); if(!l) continue;
  if(l.startsWith('#')) {out.push(heading(l.replace(/^#+\s*/,''),l.startsWith('##')?2:1));continue;}
  const ev=l.match(/^<!-- (query|table):(\w+) -->$/);
  if(ev) {out.push(...evidence(ev[2],ev[1]==='query'));continue;}
  if(l==='<!-- diagram -->') {
   out.push(new Paragraph({alignment:AlignmentType.CENTER,children:[new ImageRun({type:'png',data:fs.readFileSync(path.join(ROOT,'docs/diagramas/er-conceitual-relatorio.png')),transformation:{width:580,height:634},altText:{title:'Diagrama conceitual do Northwind',description:'Onze entidades e seus relacionamentos, descritos na página seguinte.',name:'Diagrama conceitual'}})],spacing:{after:80}}));continue;
  }
  if(l.startsWith('```')) {
   let block=[];for(i++;i<lines.length&&!lines[i].startsWith('```');i++)block.push(lines[i]);
   out.push(...code(block.join('\n')));continue;
  }
  if(l.startsWith('|')) {
   let block=[];for(;i<lines.length&&lines[i].trim().startsWith('|');i++) block.push(lines[i].trim());i--;
   const cells=s=>s.slice(1,-1).split('|').map(x=>x.trim());
   out.push(...table(cells(block[0]),block.slice(2).map(cells)));continue;
  }
  const block=[l];
  while(i+1<lines.length&&lines[i+1].trim()&&!/^(#|\||<!--|```)/.test(lines[i+1]))block.push(lines[++i].trim());
  const text=block.join(' ');
  out.push(para(text,text.startsWith('Figura 1')?{children:inline(text,{size:18,color:'475864'}),spacing:{after:80,line:220}}:{}));
 }
 return out;
}
const cover=[
 para('IPOG — Instituto de Pós-Graduação e Graduação',{alignment:AlignmentType.CENTER,spacing:{before:850,after:180}}),
 para('Projeto Integrador • Área 03 — Banco de Dados',{alignment:AlignmentType.CENTER,spacing:{after:1600}}),
 new Paragraph({alignment:AlignmentType.CENTER,children:[run('Modelagem e análise de dados de vendas',{bold:true,size:42,color:BLUE})],spacing:{after:250}}),
 para('Northwind Traders • PostgreSQL e MongoDB',{alignment:AlignmentType.CENTER,spacing:{after:650}}),
 para('Entrega 1',{alignment:AlignmentType.CENTER,children:[run('Entrega 1',{bold:true,size:27,color:BLUE})],spacing:{after:220}}),
 para('Compreensão do negócio, modelo conceitual e análise exploratória',{alignment:AlignmentType.CENTER,spacing:{after:1700}}),
 para('Giovanne Espindola',{alignment:AlignmentType.CENTER,children:[run('Giovanne Espindola',{bold:true,size:25})],spacing:{after:160}}),
 para('Trabalho individual',{alignment:AlignmentType.CENTER,spacing:{after:1000}}),
 para('Setembro de 2026',{alignment:AlignmentType.CENTER}),
];
const pages=CAPITULOS.flatMap(file=>fs.readFileSync(path.join(ROOT,'docs',file),'utf8').split('<!-- page -->'));
const body=[...cover];
for(const page of pages) {
 const children=parse(page);
 body.push(new Paragraph({children:[],pageBreakBefore:true,spacing:{after:0,before:0,line:1}}),...children);
}
const doc=new Document({creator:'Giovanne Espindola',title:'Modelagem e análise de dados de vendas — Entrega 1',
 description:'Compreensão do negócio, modelo conceitual e análise exploratória do Northwind.',
 styles:{default:{document:{run:{font:FONT,size:21,color:'20252A'},paragraph:{spacing:{after:110,line:252},widowControl:true}}}},
 sections:[{properties:{titlePage:true,page:{size:{width:11906,height:16838},margin:{top:1000,bottom:1000,left:1134,right:1134,header:400,footer:450}}},
 headers:{default:new Header({children:[new Paragraph({children:[run('NORTHWIND  /  PROJETO INTEGRADOR',{size:16,color:'637782'})],spacing:{after:0}})]})},
 footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[run('Giovanne Espindola  •  ',{size:16,color:'637782'}),new TextRun({children:[PageNumber.CURRENT,' / ',PageNumber.TOTAL_PAGES],font:FONT,size:16,color:'637782'})]})]})},children:body}]});
Packer.toBuffer(doc).then(buf=>{fs.writeFileSync(OUTPUT,buf);console.log(`${OUTPUT}\n${pages.length+1} páginas planejadas; conferir a paginação após renderizar.`)});

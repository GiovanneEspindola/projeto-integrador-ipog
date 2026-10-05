/* Grava cores e fontes do tema no .pptx gerado pelo pptxgenjs, que usa a paleta padrão do Office.
 * Assim as cores por nome (accent1, dk2...) dos slides resolvem para a paleta do projeto. */
const fs = require('fs');
const JSZip = require(require.resolve('jszip', { paths: [require.resolve('pptxgenjs')] }));

const ORDEM = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink'];
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');

async function applyTheme(file, theme) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const nome of Object.keys(zip.files).filter(n => /^ppt\/theme\/theme\d+\.xml$/.test(n))) {
    let xml = await zip.file(nome).async('string');
    const cores = ORDEM.map(k => {
      if (!/^[0-9A-Fa-f]{6}$/.test(theme.colors[k] || '')) throw new Error('Cor inválida no tema: ' + k);
      return `<a:${k}><a:srgbClr val="${theme.colors[k].toUpperCase()}"/></a:${k}>`;
    }).join('');
    xml = xml.replace(/<a:clrScheme name="[^"]*">[\s\S]*?<\/a:clrScheme>/, `<a:clrScheme name="${esc(theme.name)}">${cores}</a:clrScheme>`);
    xml = xml.replace(/(<a:majorFont>\s*<a:latin typeface=")[^"]*/, `$1${esc(theme.headFontFace)}`);
    xml = xml.replace(/(<a:minorFont>\s*<a:latin typeface=")[^"]*/, `$1${esc(theme.bodyFontFace)}`);
    zip.file(nome, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
}

module.exports = { applyTheme };

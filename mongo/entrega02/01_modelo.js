var assert = Object.assign(require('assert'), {eq: require('assert').deepStrictEqual, commandWorked: r => { if (r.ok !== 1) throw new Error(EJSON.stringify(r)); }});
// Comandos nativos do mongosh. Carregados por 02_carregar.js ou com load().
// Tipos, obrigatoriedade e objetos fechados tornam erros de carga visíveis.
var texto = {bsonType: 'string'};
var opcional = {bsonType: ['string', 'null']};
var inteiro = {bsonType: 'int'};
var positivo = {bsonType: 'int', minimum: 0};
var dinheiro = {bsonType: 'decimal', minimum: Decimal128('0')};
var data = {bsonType: 'date'};
var objeto = props => ({bsonType: 'object', required: Object.keys(props), additionalProperties: false, properties: props});
var endereco = objeto({street: opcional, city: opcional, region: opcional, postal_code: opcional, country: opcional});
var referencia = objeto({_id: inteiro, name: texto});
var contato = {company_name: texto, contact_name: opcional, contact_title: opcional,
  address: endereco, phone: opcional, fax: opcional};
var territorio = {territory_id: texto, territory_name: texto, region_id: inteiro};
var item = objeto({product: objeto({_id: inteiro, name: texto, category: referencia}),
  unit_price: dinheiro, quantity: {bsonType: 'int', minimum: 1},
  discount: {bsonType: 'decimal', minimum: Decimal128('0'), maximum: Decimal128('1'), exclusiveMaximum: true}});
var modelos = {
  regions: objeto({_id: inteiro, region_name: texto}),
  territories: objeto({_id: texto, territory_name: texto, region_id: inteiro}),
  categories: objeto({_id: inteiro, category_name: texto, description: opcional}),
  shippers: objeto({_id: inteiro, company_name: texto, phone: opcional}),
  suppliers: objeto({_id: inteiro, ...contato, homepage: opcional}),
  customers: objeto({_id: {bsonType: 'string', pattern: '^[A-Z0-9]{5}$'}, ...contato}),
  employees: objeto({_id: inteiro, first_name: texto, last_name: texto, title: texto,
    title_of_courtesy: opcional, birth_date: data, hire_date: data, address: endereco,
    home_phone: opcional, extension: opcional, notes: opcional, reports_to: {bsonType: ['int','null']},
    territories: {bsonType: 'array', items: objeto(territorio)}}),
  products: objeto({_id: inteiro, product_name: texto, category: referencia, supplier: referencia,
    quantity_per_unit: opcional, unit_price: dinheiro, units_in_stock: positivo,
    units_on_order: positivo, reorder_level: positivo, discontinued: {bsonType: 'bool'}}),
  orders: objeto({_id: inteiro, customer_id: texto, employee_id: inteiro, shipper_id: inteiro,
    order_date: data, required_date: data, shipped_date: {bsonType: ['date','null']}, freight: dinheiro,
    shipping: objeto({name: texto, street: texto, city: texto, region: opcional, postal_code: opcional, country: texto}),
    items: {bsonType: 'array', items: item}})
};
// Não é FK: a coerência entre coleções é conferida separadamente.
var configurar = banco => {
  for (var [nome, schema] of Object.entries(modelos)) {
    if (!banco.getCollectionNames().includes(nome)) banco.createCollection(nome, {validator: {$jsonSchema: schema}, validationLevel: 'strict', validationAction: 'error'});
    else assert.commandWorked(banco.runCommand({collMod: nome, validator: {$jsonSchema: schema}, validationLevel: 'strict', validationAction: 'error'}));
  }
};

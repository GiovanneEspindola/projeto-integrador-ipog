"""Recalcula indicadores a partir de cinco CSVs, sem banco e sem SQL.

Uso: python3 etl/recalcular_csv_entrega01.py /caminho/da/pasta
Arquivos: itens.csv, pedidos.csv, produtos.csv, categorias.csv, clientes.csv.
Exportação: UTF-8, vírgula, cabeçalho, decimais com ponto, datas ISO.
Usa somente a biblioteca padrão do Python. Não modifica os arquivos.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def recalcular(folder):
    tables, hashes = {}, {}
    for name in ("itens", "pedidos", "produtos", "categorias", "clientes"):
        path = folder / f"{name}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            tables[name] = [dict(row) for row in reader]
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def index(name, key):
        rows = tables[name]
        ids = [r[key] for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError(f"Identificadores duplicados em {name}.{key}")
        return {r[key]: r for r in rows}

    orders = index("pedidos", "order_id")
    products = index("produtos", "product_id")
    categories = index("categorias", "category_id")
    customers = index("clientes", "customer_id")
    pairs = [(i["order_id"], i["product_id"]) for i in tables["itens"]]
    if len(set(pairs)) != len(pairs):
        raise ValueError("O par pedido/produto está duplicado nos itens.")

    by_order, by_category = defaultdict(Decimal), defaultdict(Decimal)
    item_counts = Counter()
    item_rounded = Decimal(0)
    units, different_prices = 0, 0
    for item in tables["itens"]:
        order_id, product_id = item["order_id"], item["product_id"]
        if order_id not in orders or product_id not in products:
            raise ValueError(f"Referência inexistente no item {order_id}/{product_id}")
        price = Decimal(item["unit_price"])
        discount = Decimal(item["discount"])
        quantity = int(item["quantity"])
        if price < 0 or quantity <= 0 or not Decimal(0) <= discount < Decimal(1):
            raise ValueError(f"Domínio inválido no item {order_id}/{product_id}")
        value = price * quantity * (Decimal(1) - discount)
        by_order[order_id] += value
        category_id = products[product_id]["category_id"]
        if category_id not in categories:
            raise ValueError(f"Categoria inexistente no produto {product_id}")
        by_category[categories[category_id]["category_name"]] += value
        item_rounded += value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item_counts[order_id] += 1
        units += quantity
        different_prices += price != Decimal(products[product_id]["unit_price"])

    if set(by_order) != set(orders):
        raise ValueError("Há pedido sem item no CSV; não excluir silenciosamente da média.")
    by_year = defaultdict(Decimal)
    count_year = Counter()
    dates, shipping_days, buyers = [], [], set()
    for order_id, order in orders.items():
        if order["customer_id"] not in customers:
            raise ValueError(f"Cliente inexistente no pedido {order_id}")
        day = date.fromisoformat(order["order_date"])
        dates.append(day)
        by_year[day.year] += by_order[order_id]
        count_year[day.year] += 1
        buyers.add(order["customer_id"])
        if order["shipped_date"] not in ("", "\\N", "NULL", "[NULL]"):
            shipping = date.fromisoformat(order["shipped_date"])
            if shipping < day:
                raise ValueError(f"Envio anterior ao pedido {order_id}")
            shipping_days.append((shipping - day).days)

    values = sorted(by_order.values())
    n = len(values)
    if not n:
        raise ValueError("CSV sem pedidos.")
    total = sum(values, Decimal(0))
    median = values[n//2] if n % 2 else (values[n//2-1] + values[n//2])/2

    def money(value):
        return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    result = {
        "contagens": {name: len(rows) for name, rows in tables.items()},
        "primeiro_pedido": str(min(dates)), "ultimo_pedido": str(max(dates)),
        "clientes_com_pedido": len(buyers), "clientes_sem_pedido": sorted(set(customers)-buyers),
        "total_sem_arredondar": str(total), "total": money(total),
        "media": money(total/n), "mediana": money(median),
        "minimo": money(values[0]), "maximo": money(values[-1]),
        "total_arredondando_itens": money(item_rounded),
        "itens_com_preco_diferente": different_prices,
        "unidades": units, "min_itens": min(item_counts.values()),
        "max_itens": max(item_counts.values()), "media_itens": money(Decimal(len(pairs))/n),
        "sem_data_envio": len(orders)-len(shipping_days),
        "dias_ate_envio": money(Decimal(sum(shipping_days))/len(shipping_days)),
        "anos": {str(y): {"pedidos": count_year[y], "valor": money(by_year[y])} for y in sorted(by_year)},
        "categorias": {c: money(v) for c, v in sorted(by_category.items(), key=lambda pair: pair[1], reverse=True)},
        "sha256_csv": hashes,
    }
    expected = {
        "contagens": {"itens":2155,"pedidos":830,"produtos":77,"categorias":8,"clientes":91},
        "total":"1265793.04", "media":"1525.05", "mediana":"943.25",
        "minimo":"12.50", "maximo":"16387.50", "total_arredondando_itens":"1265793.29",
        "primeiro_pedido":"1996-07-04", "ultimo_pedido":"1998-05-06",
        "clientes_com_pedido":89, "clientes_sem_pedido":["FISSA","PARIS"],
        "sem_data_envio":21, "dias_ate_envio":"8.49", "itens_com_preco_diferente":662,
        "anos":{"1996":{"pedidos":152,"valor":"208083.97"},"1997":{"pedidos":408,"valor":"617085.20"},"1998":{"pedidos":270,"valor":"440623.87"}},
        "categorias":{"Beverages":"267868.18","Dairy Products":"234507.29","Confections":"167357.23","Meat/Poultry":"163022.36","Seafood":"131261.74","Condiments":"106047.09","Produce":"99984.58","Grains/Cereals":"95744.59"},
    }
    result["diferencas_relatorio"] = {k:{"calculado":result[k],"relatorio":v} for k,v in expected.items() if result[k] != v}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path)
    args = parser.parse_args()
    try:
        result = recalcular(args.pasta)
    except (ValueError, KeyError, OSError, ArithmeticError) as exc:
        raise SystemExit(f"Não foi possível conferir os CSVs: {exc}. Confira exportação, cabeçalhos e formato dos campos.")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["diferencas_relatorio"] else 0)

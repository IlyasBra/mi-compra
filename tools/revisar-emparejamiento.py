import json

m = json.load(open("tools/emparejamiento.json", encoding="utf-8"))
nuestros = json.load(open("tools/nuestros-productos.json", encoding="utf-8"))
por_cat = {}
for nombre, cat, *_ in nuestros:
    por_cat.setdefault(cat, []).append(nombre)

for cat in por_cat:
    print(f"\n===== {cat} =====")
    for nombre in por_cat[cat]:
        v = m[nombre]
        marca = "MANUAL " if v.get("manual") else "       "
        print(f"  {marca}{nombre}  ->  {v['mercadona']}")

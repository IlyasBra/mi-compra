"""Empareja cada producto de tu catálogo con el producto más parecido de
Mercadona (nombre + sección), usando la lista recolectada por scrape-mercadona.py.

NO se publica en la web. Salidas:
  - tools/emparejamiento.json   (mapa: tu producto -> producto de Mercadona)
  - tools/emparejamiento.md     (informe legible, con los dudosos marcados)

Uso:  python tools/match-mercadona.py
"""

import json
import re
import unicodedata

MERCADONA = "tools/mercadona-productos.json"
NUESTROS = "tools/nuestros-productos.json"
SALIDA_JSON = "tools/emparejamiento.json"
SALIDA_MD = "tools/emparejamiento.md"

# Tu categoría -> secciones de Mercadona por orden de preferencia
AFINIDAD = {
    "Pescado y marisco": ["Marisco y pescado", "Conservas, caldos y cremas", "Congelados"],
    "Charcutería y quesos": ["Charcutería y quesos"],
    "Lácteos y huevos": ["Huevos, leche y mantequilla", "Postres y yogures"],
    "Panadería y bollería": ["Panadería y pastelería"],
    "Despensa": ["Aceite, especias y salsas", "Arroz, legumbres y pasta",
                 "Conservas, caldos y cremas", "Azúcar, caramelos y chocolate",
                 "Cacao, café e infusiones", "Cereales y galletas", "Aperitivos",
                 "Panadería y pastelería", "Huevos, leche y mantequilla",
                 "Pizzas y platos preparados", "Fruta y verdura"],
    "Congelados": ["Congelados", "Pizzas y platos preparados", "Marisco y pescado"],
    "Bebidas": ["Agua y refrescos", "Bodega", "Zumos", "Cacao, café e infusiones"],
    "Limpieza y hogar": ["Limpieza y hogar"],
    "Cuidado personal": ["Cuidado facial y corporal", "Cuidado del cabello",
                         "Maquillaje", "Fitoterapia y parafarmacia"],
    "Bazar y hogar": ["Limpieza y hogar", "Pizzas y platos preparados"],
    "Mascotas": ["Mascotas"],
    "Bebé": ["Bebé"],
}

RUIDO = {
    "de", "del", "la", "el", "los", "las", "con", "y", "o", "u", "para", "en", "al",
    "a", "un", "una", "unos", "unas", "sin", "tipo", "mas", "extra", "gran",
    "seleccion", "hacendado", "mercadona", "deliplus", "compy",
}
# Palabras de envase: se quitan del nombre de Mercadona (no del nuestro)
ENVASE = {
    "botella", "garrafa", "bote", "bolsa", "bandeja", "paquete", "lata", "tarrina",
    "spray", "brick", "pack", "docena", "ud", "bolsitas", "granel", "envase",
    "caja", "estuche", "frasco", "tarro", "pote",
}
# Sinónimos: cómo se llama lo nuestro -> cómo lo llama Mercadona
SINONIMOS = {
    "espagueti": "spaghetti", "espaguetis": "spaghetti",
    "cuscus": "semola",
    "maicena": "harina maiz",
    "quesitos": "queso porciones",
    "salvaslip": "protegeslip",
    "fregasuelos": "friegasuelos",
    "skyr": "yogur",
    "polos": "helado",
    "gusanitos": "aros",
    "colacao": "cacao soluble",
    "taper": "fiambrera",
}

# Sustituciones a mano: nombre exacto de NUESTRO producto -> nombre exacto de
# Mercadona. Sirve para corregir emparejamientos malos y para los productos que
# no existen en Mercadona (se pone la mejor aproximación real).
# Valor None = se deja SIN foto (no hay nada parecido de verdad).
OVERRIDES = {
    # --- Despensa ---
    "Curri": "Curry Hacendado",
    "Cebolletas": "Cebollas tiernas",
    "Pulpo en conserva": "Patas de pulpo cocido",
    "Boquerones en vinagre (lata)": "Boquerón limpio sin cabeza",
    "Tortitas (pancakes)": "Tortitas de maíz Hacendado",
    # --- Congelados ---
    "Judías verdes congeladas": "Judía verde plana Hacendado ultracongelada",
    "Pan (baguette)": "Baguette masa madre",
    "Pimiento troceado": "Pimiento rojo y verde Hacendado ultracongelado",
    "Anillas de calamar": "Calamar troceado limpio Hacendado congelado",
    "Hamburguesas": "Hamburguesa de vacuno angus",
    # --- Panadería ---
    "Pan de hogaza / payés": "Hogaza 100% natural Hacendado",
    # --- Bebidas ---
    "Té helado (Nestea)": "Refresco té sabor limón Hacendado",
    # --- Limpieza y hogar ---
    "Blanco / blanqueante": "Activador Blanqueante ropa blanca Oxi Active Bosque Verde en polvo",
    "Limpiador de lavadora": "Limpia lavadoras Bosque Verde líquido",
    "Limpiador multiusos": "Limpiahogar Multiusos Pino Bosque Verde líquido",
    "Lavavajillas (polvo)": "Lavavajillas Todo en 1 Bosque Verde en pastillas",
    "Fregona (y recambio)": "Fregona Microfibra Absorbente Bosque Verde",
    "Guantes de limpieza": "Guantes de látex Bosque Verde talla mediana-grande",
    "Servilletas": "Servilleta papel Bosque Verde",
    "Papel de horno": "Papel vegetal Bosque Verde",
    "Bolsas herméticas": "Bolsas zip congelación medianas Bosque Verde reutilizables",
    # --- Cuidado personal ---
    "Gel de ducha": "Gel de baño frescor azul Deliplus piel normal",
    "Mascarilla capilar": "Mascarilla Natural Deliplus todo tipo de cabello",
    "Pasta de dientes": "Dentífrico Triple Acción Colgate menta intensa",
    "Colonia / perfume": "Agua de colonia Classic fresh S3",
    "Cuchillas de afeitar": "Maquinillas de afeitar desechables Deliplus Fix 2 hojas",
    "Crema de afeitar": "Espuma de afeitar Sensitive Deliplus manteca de cacao",
    "Tinte de pelo": "Tinte cabello hombre 0% amoníaco 3 moreno 4 castaño Colorcor",
    "Laca de pelo": "Laca cabello Forte Deliplus fijación 3",
    "Espuma / gel de pelo": "Espuma cabello Xtra Forte Deliplus fijación 4",
    "Horquillas": "Pinza de cejas Deliplus oblicua",
    # --- Bazar y hogar ---
    "Platos": "Plato llano Bosque Verde",
    "Vasos": "Vasos grandes de plástico Bosque Verde reutilizables",
    "Cubiertos": "Tenedores de plástico Bosque Verde reutilizables",
    "Tazas": "Vaso mediano Bosque Verde apto para bebida caliente",
    "Bandeja": "Bandeja de cartón rectangular Bosque Verde",
    "Ensaladera": "Recipiente de plástico redondo 1L Bosque Verde",
    "Tabla de cortar": "Tabla de quesos nacionales Hacendado",
    "Espátula / cuchara de cocina": "Cucharas de plástico Bosque Verde reutilizables",
    "Cuchillo de cocina": "Cuchillos de plástico Bosque Verde reutilizables",
    "Táper / recipiente para guardar": "Recipiente hermético de plástico rectangular 1L Bosque Verde",
    "Toallas": "Toalla turbante seca pelo microfibra Deliplus",
    "Trapos de cocina": "Paño seca vajillas Bosque Verde",
    "Escoba": "Escoba para interiores Bosque Verde",
    "Recogedor": "Recogedor antivuelco con palo Bosque Verde",
    "Cubo": "Cubo de basura mediano 30L Bosque Verde 30,2 x 30,5 x 41,9 cm",
    "Pinzas de la ropa": "Pinzas de ropa Bosque Verde",
    "Tijeras": "Tijera uñas Deliplus",
    "Platos desechables": "Plato postre Bosque Verde",
    "Vasos desechables": "Vaso pequeño Bosque Verde apto para bebida caliente",
    "Cubiertos desechables": "Cucharas de plástico Bosque Verde reutilizables",
    "Mantel": "Mantel de papel blanco Bosque Verde",
    "Bolsas de tela": "Bolsa de rafia",
    # --- Aproximaciones forzadas (no hay equivalente real; se pone lo más parecido) ---
    "Ollas": "Molde de aluminio cuadrado 2,7L Alibérico",
    "Sartén": "Molde de aluminio rectangular 1,5L Alibérico",
    "Cacerola": "Molde de aluminio rectangular 0,5L Alibérico",
    "Colador": "Escurridor para cubo ovalado Bosque Verde escurrebien",
    "Cuerda de tender": "Palo extensible antideslizante Bosque Verde 86 - 150 cm",
    "Sábanas": "Toalla turbante seca pelo microfibra Deliplus",
    "Funda de almohada": "Toalla turbante seca pelo microfibra Deliplus",
    "Mantas": "Toalla turbante seca pelo microfibra Deliplus",
    "Perchas": "Pinzas de ropa Bosque Verde",
    "Cinta adhesiva": "Film transparente Bosque Verde con sierra deslizante",
    "Costurero / hilo y aguja": "Tijera uñas Deliplus",
    "Bombillas": "Pila alcalina AA LR6 Bosque Verde",
    # --- Correcciones de emparejamientos automáticos equivocados ---
    # Despensa
    "Aceite de girasol": "Aceite de girasol refinado 0,2º Hacendado",
    "Sardinas en tomate": "Sardinillas en tomate Hacendado",
    "Almejas al natural": "Almeja Hacendado congelada",
    "Anchoas": "Filetes de anchoa en aceite de oliva Hacendado",
    "Caballa en escabeche": "Filetes de caballa del sur en aceite de oliva Hacendado",
    "Pasta de sopa": "Pasta estrellas Hacendado",
    "Mermelada sin azúcar": "Mermelada de fresa Hacendado",
    "Levadura en polvo": "Levadura de panadería Hacendado",
    "Cereales de chocolate": "Cereales copos de trigo Chocodays Hacendado con chocolate",
    "Galletas de chocolate": "Galletas Chocominis sabor chocolate Hacendado",
    "Ajo en polvo": "Ajo granulado Hacendado",
    "Cacahuetes": "Cacahuete tostado con sal Hacendado",
    "Nueces": "Nuez natural Hacendado pelada",
    "Avellanas": "Avellana tostada Hacendado 0% sal añadida",
    "Pistachos": "Pistacho tostado Hacendado con sal",
    "Pasas": "Pasas sultanas sin semillas Hacendado",
    # Panadería
    "Pan de hamburguesa": "Pan de burger Hacendado Rústico",
    "Pan de perrito": "Pan hot dog Hacendado",
    "Palmera de chocolate": "Napolitana de chocolate",
    # Congelados
    "Guisantes congelados": "Guisante muy tierno Hacendado ultracongelado",
    "Champiñones / setas": "Champiñón laminado Hacendado",
    "Patatas fritas (bastones)": "Patatas prefritas corte fino Hacendado ultracongeladas",
    "Salmón": "Lomos de salmón sin piel Hacendado congelado",
    "Paella": "Preparado de paella y sopa Hacendado ultracongelado",
    "Polos": "Helado sorbete con limón Hacendado",
    "Salchichas": "Salchichas cocidas estilo Frankfurt Hacendado de pollo y cerdo sabor ahumado",
    # Bebidas
    "Néctar de melocotón": "Zumo de melocotón y uva Hacendado",
    "Cerveza 0,0": "Cerveza 0,0% sin alcohol Falke",
    "Ginebra": "Ginebra London Dry Gin Glivery",
    "Agua con sabor": "Agua de coco 100% Hacendado",
    # Lácteos y huevos
    "Bebida de avena": "Bebida de avena Hacendado 0% azúcar",
    "Nata en spray": "Nata montada azucarada Hacendado",
    "Yogur desnatado": "Yogur natural Hacendado 0% MG 0% azúcares añadidos",
    "Yogur natural azucarado": "Yogur natural con azúcar de caña Hacendado",
    "Queso crema para untar": "Queso untar suave de vaca Hacendado",
    "Queso camembert": "Queso camembert de vaca Marcillat",
    "Huevos camperos": "Huevos de gallinas camperas",
    "Huevos ecológicos": "Huevos de gallinas camperas",
    # Limpieza y hogar
    "Toallitas quitamanchas": "Toallitas lavadora Bosque Verde anti-transferencia de color",
    "Abrillantador": "Abrillantador lavavajillas líquido Bosque Verde",
    "Bicarbonato": "Bicarbonato de sódio Hacendado",
    "Detergente en polvo": "Detergente ropa blanca y de color Bosque Verde en polvo",
    # Cuidado personal
    "Champú": "Champú Natural Deliplus todo tipo de cabello",
    "Acondicionador": "Acondicionador Suavidad y Brillo Deliplus todo tipo de cabello",
    "Cepillo de dientes": "Cepillo dental Medio Deliplus",
    "Crema hidratante": "Crema de manos, cara y cuerpo Nivea Soft hidratante intensiva",
    "Crema facial": "Crema facial hidratante anti-rojeces Sensitive Vitamina K Ox",
    "Algodón": "Algodón hidrófilo 100% zig-zag hipoalergénico Deliplus",
    "Toallitas húmedas": "Toallitas Dermo higiene corporal Deliplus tamaño gigantes",
    # --- Sin ninguna aproximación razonable: se dejan sin foto ---
    "Paraguas": None,
    "Gomas de pelo": None,
    "Peine / cepillo": None,
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def raiz(t):
    """Stem muy simple para unir singular y plural."""
    if len(t) > 4 and t.endswith("es"):
        return t[:-2]
    if len(t) > 3 and t.endswith("s"):
        return t[:-1]
    return t


def tokens(s, quitar_envase=False, usar_sinonimos=False):
    s = norm(s)
    if usar_sinonimos:
        for a, b in SINONIMOS.items():
            s = re.sub(r"\b" + a + r"\b", b, s)
    out = set()
    for t in s.split():
        if t in RUIDO or t.isdigit():
            continue
        if quitar_envase and t in ENVASE:
            continue
        out.add(raiz(t))
    return out


def puntuar(ta, norm_a, tb, norm_b):
    if not ta or not tb:
        return 0.0
    if norm_a == norm_b:
        return 1.0
    inter = ta & tb
    if not inter:
        # contención textual (p. ej. "pan" dentro de "pan de molde")
        if len(norm_a) >= 4 and (norm_a in norm_b or norm_b in norm_a):
            return 0.45
        return 0.0
    f1 = 2 * len(inter) / (len(ta) + len(tb))
    # premia que estén TODOS los tokens nuestros
    cobertura = len(inter) / len(ta)
    return 0.6 * f1 + 0.4 * cobertura


def main():
    mercadona = json.load(open(MERCADONA, encoding="utf-8"))["productos"]
    nuestros = json.load(open(NUESTROS, encoding="utf-8"))

    # Precalcular tokens de Mercadona
    prep = []
    for p in mercadona:
        prep.append((tokens(p["nombre"], quitar_envase=True), norm(p["nombre"]), p))

    # Índice por nombre exacto, para las sustituciones a mano
    por_nombre = {}
    for p in mercadona:
        por_nombre.setdefault(p["nombre"], p)

    # Comprobar que todas las sustituciones apuntan a un producto real
    for nuestro, destino in OVERRIDES.items():
        if destino is not None and destino not in por_nombre:
            raise SystemExit(f"OVERRIDE roto: '{nuestro}' -> '{destino}' no existe en Mercadona")

    mapa = {}
    filas = []
    for entrada in nuestros:
        nombre, cat = entrada[0], entrada[1]
        if nombre in OVERRIDES:
            destino = OVERRIDES[nombre]
            p = por_nombre.get(destino) if destino else None
            mapa[nombre] = {
                "mercadona": p["nombre"] if p else None,
                "seccion": p["seccion"] if p else None,
                "categoria": p["categoria"] if p else None,
                "foto": p["foto"] if p else None,
                "score": 1.0 if p else 0.0,
                "revisar": False,
                "manual": True,
            }
            filas.append((mapa[nombre]["score"], nombre, cat, mapa[nombre]))
            continue

        ta = tokens(nombre, usar_sinonimos=True)
        na = norm(nombre)
        for a, b in SINONIMOS.items():
            na = re.sub(r"\b" + a + r"\b", b, na)
        secciones = AFINIDAD.get(cat, [])
        mejor, mejor_p = -1.0, None
        for tb, norm_b, p in prep:
            s = puntuar(ta, na, tb, norm_b)
            if s <= 0:
                continue
            if p["seccion"] in secciones:
                s += 0.30 + 0.05 * (len(secciones) - secciones.index(p["seccion"])) / max(1, len(secciones))
            if s > mejor:
                mejor, mejor_p = s, p
        if mejor_p is None:
            mejor, mejor_p = 0.0, None
        mapa[nombre] = {
            "mercadona": mejor_p["nombre"] if mejor_p else None,
            "seccion": mejor_p["seccion"] if mejor_p else None,
            "categoria": mejor_p["categoria"] if mejor_p else None,
            "foto": mejor_p["foto"] if mejor_p else None,
            "score": round(mejor, 3),
            "revisar": mejor < 0.55,
            "manual": False,
        }
        filas.append((mejor, nombre, cat, mapa[nombre]))

    json.dump(mapa, open(SALIDA_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    filas.sort()
    dudosos = [f for f in filas if f[3]["revisar"]]
    manuales = [f for f in filas if f[3].get("manual")]
    sin_foto = [f for f in filas if not f[3]["mercadona"]]
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write("# Emparejamiento con Mercadona\n\n")
        f.write(f"- Productos nuestros: {len(filas)}\n")
        f.write(f"- Emparejados a mano: {len(manuales)}\n")
        f.write(f"- Marcados para revisar (score < 0.55): {len(dudosos)}\n")
        f.write(f"- Sin foto (no hay equivalente): {len(sin_foto)}\n\n")
        f.write("## Sin foto\n\n")
        f.write("| Tu producto | Categoría |\n|---|---|\n")
        for score, nombre, cat, m in sin_foto:
            f.write(f"| {nombre} | {cat} |\n")
        f.write("\n## Sustituciones a mano\n\n")
        f.write("| Tu producto | Mercadona | Sección |\n|---|---|---|\n")
        for score, nombre, cat, m in sorted(manuales, key=lambda x: x[1]):
            f.write(f"| {nombre} | {m['mercadona'] or '—'} | {m['seccion'] or '—'} |\n")
        f.write("\n## Dudosos (revísalos)\n\n")
        f.write("| Tu producto | Sección | Mercadona propuesto | Score |\n|---|---|---|---|\n")
        for score, nombre, cat, m in dudosos:
            f.write(f"| {nombre} | {cat} | {m['mercadona'] or '—'} | {score:.2f} |\n")
        f.write("\n## Todos\n\n")
        f.write("| Tu producto | Categoría | Mercadona | Score |\n|---|---|---|---|\n")
        for score, nombre, cat, m in filas:
            f.write(f"| {nombre} | {cat} | {m['mercadona'] or '—'} | {score:.2f} |\n")

    print(f"Emparejados: {len(filas)}")
    print(f"Sustituciones a mano: {len(manuales)}")
    print(f"Dudosos (<0.55): {len(dudosos)}")
    print(f"Sin ninguna coincidencia: {len(sin_foto)}")
    print(f"\nInforme: {SALIDA_MD}")
    if dudosos:
        print("\nMuestra de dudosos:")
        for score, nombre, cat, m in dudosos[:30]:
            print(f"  {score:.2f}  {nombre}  ->  {m['mercadona']}  [{m['seccion']}]")


if __name__ == "__main__":
    main()

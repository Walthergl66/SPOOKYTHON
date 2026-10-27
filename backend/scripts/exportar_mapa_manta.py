"""Construye el artefacto de calles de Manta desde datos públicos de OSM.

El mapa de Navira es un fixture de simulación, no una fuente de navegación o
de seguridad pública. Las zonas seguras de tsunami se incorporan desde el
mapa publicado por la Dirección de Ambiente y Riesgos del GAD Manta; su
seguridad ante sismos no se infiere de la altura ni del nombre del lugar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


RAIZ = Path(__file__).resolve().parents[1]
SALIDA_MAPA = RAIZ / "data/maps/manta-hackathon-v1.json"
SALIDA_FUENTES = RAIZ / "data/maps/manta-hackathon-v1.fuentes.json"
URL_OSM_API = "https://api.openstreetmap.org/api/0.6/map"
URL_GAD_MAPAS = "https://darf-manta.github.io/evacuacion-tsunami/"

# Recorte urbano que cubre los corredores de Tarqui, Los Esteros, Jocay y
# Barbasquillo nombrados en el reto. Las cajas pequeñas respetan el límite de
# nodos de la API de edición de OSM; si una excede el límite se subdivide.
CAJA = (-0.967, -80.755, -0.935, -80.675)  # sur, oeste, norte, este
TIPOS_VIALES = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
    "residential", "living_street", "service", "road",
}
VELOCIDAD_POR_TIPO = {
    "motorway": 60.0, "motorway_link": 50.0, "trunk": 50.0, "trunk_link": 40.0,
    "primary": 50.0, "primary_link": 40.0, "secondary": 40.0,
    "secondary_link": 30.0, "tertiary": 30.0, "tertiary_link": 25.0,
    "unclassified": 30.0, "residential": 30.0, "living_street": 20.0,
    "service": 20.0, "road": 30.0,
}
ZONAS_SEGURAS = (
    {
        "id": "R-01", "nombre": "Parque y cancha municipal Cristo Rey",
        "parroquia": "Tarqui", "lat": -0.9588192943885248, "lng": -80.71242442236326,
        "pagina": "parroquia-tarqui.html",
    },
    {
        "id": "R-02", "nombre": "Parque Colinas de Rocafuerte",
        "parroquia": "Los Esteros", "lat": -0.9574742328837494, "lng": -80.70208371535246,
        "pagina": "parroquia-los-esteros.html",
    },
    {
        "id": "R-03", "nombre": "Parque La Dolorosa",
        "parroquia": "Manta", "lat": -0.9522745219919659, "lng": -80.72726572846808,
        "pagina": "parroquia-manta.html",
    },
    {
        "id": "R-04", "nombre": "Plaza del Sol",
        "parroquia": "Manta", "lat": -0.9460949, "lng": -80.7488984,
        "pagina": "parroquia-manta.html",
    },
)


def _consultar_caja(caja: tuple[float, float, float, float], profundidad: int = 0) -> ET.Element:
    """Lee una caja OSM y la subdivide solo ante el límite de nodos del API."""

    sur, oeste, norte, este = caja
    parametros = urllib.parse.urlencode({"bbox": f"{oeste},{sur},{este},{norte}"})
    solicitud = urllib.request.Request(
        f"{URL_OSM_API}?{parametros}",
        headers={"User-Agent": "NaviraHackathonMap/0.1 (https://github.com/Walthergl66/SPOOKYTHON)"},
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
            return ET.fromstring(respuesta.read())
    except urllib.error.HTTPError as error:
        cuerpo = error.read().decode("utf-8", "replace")
        if error.code == 400 and "too many nodes" in cuerpo.lower() and profundidad < 5:
            mitad_lon = (oeste + este) / 2
            mitad_lat = (sur + norte) / 2
            partes = (
                (sur, oeste, mitad_lat, mitad_lon), (sur, mitad_lon, mitad_lat, este),
                (mitad_lat, oeste, norte, mitad_lon), (mitad_lat, mitad_lon, norte, este),
            )
            raiz = ET.Element("osm")
            for parte in partes:
                for elemento in _consultar_caja(parte, profundidad + 1):
                    raiz.append(elemento)
                time.sleep(1)
            return raiz
        raise RuntimeError(f"OSM rechazó la caja {caja}: HTTP {error.code}: {cuerpo[:300]}") from error


def descargar_elementos() -> tuple[dict[str, tuple[float, float]], dict[str, ET.Element]]:
    """Descarga y deduplica los nodos/vías incluidos en la extensión urbana."""

    sur, oeste, norte, este = CAJA
    mitad_lon, mitad_lat = (oeste + este) / 2, (sur + norte) / 2
    cajas = (
        (sur, oeste, mitad_lat, mitad_lon), (sur, mitad_lon, mitad_lat, este),
        (mitad_lat, oeste, norte, mitad_lon), (mitad_lat, mitad_lon, norte, este),
    )
    nodos: dict[str, tuple[float, float]] = {}
    vias: dict[str, ET.Element] = {}
    for indice, caja in enumerate(cajas):
        for elemento in _consultar_caja(caja):
            if elemento.tag == "node":
                nodos[elemento.attrib["id"]] = (float(elemento.attrib["lat"]), float(elemento.attrib["lon"]))
            elif elemento.tag == "way" and elemento.find("tag[@k='highway']") is not None:
                vias[elemento.attrib["id"]] = elemento
        if indice < len(cajas) - 1:
            time.sleep(1)
    return nodos, vias


def _distancia_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distancia geodésica aproximada entre dos puntos WGS84, en metros."""

    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.asin(math.sqrt(h))


def _dentro_caja(coordenada: tuple[float, float]) -> bool:
    lat, lon = coordenada
    sur, oeste, norte, este = CAJA
    return sur <= lat <= norte and oeste <= lon <= este


def _tipo_y_velocidad(etiquetas: dict[str, str]) -> tuple[str, float]:
    highway = etiquetas["highway"]
    if etiquetas.get("bridge") in {"yes", "viaduct"}:
        tipo = "puente"
    elif highway in {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"}:
        tipo = "avenida"
    elif highway in {"service", "living_street"}:
        tipo = "callejon"
    else:
        tipo = "calle"
    maxspeed = etiquetas.get("maxspeed", "")
    coincidencia = re.search(r"\d+(?:\.\d+)?", maxspeed)
    if coincidencia:
        velocidad = float(coincidencia.group())
        if "mph" in maxspeed.lower():
            velocidad *= 1.609344
    else:
        velocidad = VELOCIDAD_POR_TIPO[highway]
    return tipo, velocidad


def construir_grafo_completo(
    nodos_osm: dict[str, tuple[float, float]], vias_osm: dict[str, ET.Element],
    anclajes: dict[str, str] | None = None,
) -> tuple[dict[str, tuple[float, float]], list[dict[str, object]], dict[str, str]]:
    """Contrae vértices de geometría y conserva intersecciones/terminaciones."""

    vias: list[tuple[str, list[str], dict[str, str]]] = []
    formas: defaultdict[str, set[str]] = defaultdict(set)
    extremos: set[str] = set()
    for via_id, elemento in sorted(vias_osm.items(), key=lambda par: int(par[0])):
        etiquetas = {tag.attrib["k"]: tag.attrib["v"] for tag in elemento.findall("tag")}
        if etiquetas.get("highway") not in TIPOS_VIALES or etiquetas.get("access") in {"no", "private"}:
            continue
        referencias = [nodo.attrib["ref"] for nodo in elemento.findall("nd")]
        referencias = [ref for ref in referencias if ref in nodos_osm]
        if len(referencias) < 2:
            continue
        # Recorta por tramos contiguos para no conectar extremos cuando una vía
        # sale y vuelve a entrar en el polígono de esta exportación urbana.
        tramo: list[str] = []
        for ref in referencias:
            if _dentro_caja(nodos_osm[ref]):
                tramo.append(ref)
            else:
                if len(tramo) >= 2:
                    vias.append((via_id, tramo, etiquetas))
                    extremos.update((tramo[0], tramo[-1]))
                    for punto in set(tramo):
                        formas[punto].add(via_id)
                tramo = []
        if len(tramo) >= 2:
            vias.append((via_id, tramo, etiquetas))
            extremos.update((tramo[0], tramo[-1]))
            for punto in set(tramo):
                formas[punto].add(via_id)

    # Un refugio se ancla en una intersección (dos o más vías), no en el extremo
    # de una calle: un extremo de un solo sentido puede no tener entradas y
    # quedar inalcanzable para cualquier sobreviviente.
    intersecciones = {ref for ref, ids_vias in formas.items() if len(ids_vias) >= 2}
    anclas = _anclas_por_zona(nodos_osm, intersecciones)
    if anclajes:
        puntos = {r["id"]: (r["lat"], r["lng"]) for r in ZONAS_SEGURAS}
        anclas = aplicar_anclajes_manuales(anclas, anclajes, nodos_osm, formas, puntos)
    anclas_osm = set(anclas.values())
    importantes = {ref for ref, ids_vias in formas.items() if len(ids_vias) != 2} | extremos | anclas_osm
    coordenadas = {ref: coord for ref, coord in nodos_osm.items() if ref in importantes and _dentro_caja(coord)}
    segmentos: list[dict[str, object]] = []
    for indice_tramo, (via_id, referencias, etiquetas) in enumerate(vias):
        posiciones_importantes = [indice for indice, ref in enumerate(referencias) if ref in coordenadas]
        for inicio, fin in zip(posiciones_importantes, posiciones_importantes[1:]):
            origen, destino = referencias[inicio], referencias[fin]
            if origen == destino:
                continue
            distancia = sum(_distancia_m(nodos_osm[a], nodos_osm[b]) for a, b in zip(referencias[inicio:fin], referencias[inicio + 1:]))
            if not math.isfinite(distancia) or distancia <= 0:
                continue
            tipo, velocidad = _tipo_y_velocidad(etiquetas)
            segmentos.append({
                "segmento": f"S-OSM-{via_id}-{indice_tramo}-{inicio}-{fin}",
                "way_id": via_id, "desde": origen, "hasta": destino,
                "distancia": round(distancia, 2), "tipo": tipo, "velocidad": round(velocidad, 2),
                "oneway": etiquetas.get("oneway", "").lower(),
                "roundabout": etiquetas.get("junction") == "roundabout",
            })
    return coordenadas, segmentos, anclas


def _anclas_por_zona(
    nodos: dict[str, tuple[float, float]], candidatos: set[str] | None = None
) -> dict[str, str]:
    """Devuelve el OSM node más cercano a cada zona oficial, con IDs distintos."""

    disponibles = set(nodos) if candidatos is None else set(candidatos)
    resultado: dict[str, str] = {}
    for refugio in ZONAS_SEGURAS:
        candidatos = sorted(
            ((_distancia_m((refugio["lat"], refugio["lng"]), nodos[ref]), ref) for ref in disponibles),
            key=lambda item: (item[0], int(item[1])),
        )
        if not candidatos or candidatos[0][0] > 350:
            raise RuntimeError(f"No hay intersección OSM próxima a {refugio['nombre']} (límite 350 m).")
        distancia, ref = candidatos[0]
        resultado[refugio["id"]] = ref
        disponibles.remove(ref)
    return resultado


def aplicar_anclajes_manuales(
    anclas: dict[str, str],
    anclajes: dict[str, str],
    coordenadas: dict[str, tuple[float, float]],
    formas: dict[str, set[str]],
    puntos_oficiales: dict[str, tuple[float, float]],
) -> dict[str, str]:
    """Sustituye el ancla automática de los refugios indicados por un nodo OSM manual.

    `anclajes` mapea id de refugio -> id OSM (sin prefijo N-OSM-); `formas` mapea
    nodo -> vías que lo tocan (intersección = al menos dos). Devuelve anclas nuevas.
    """

    nuevas = dict(anclas)
    for refugio, nodo in anclajes.items():
        if refugio not in puntos_oficiales:
            raise RuntimeError(f"Refugio desconocido en --anclaje: {refugio}.")
        if nodo not in coordenadas or len(formas.get(nodo, ())) < 2:
            raise RuntimeError(f"El nodo OSM {nodo} no existe en la red o no es una intersección (refugio {refugio}).")
        distancia = _distancia_m(puntos_oficiales[refugio], coordenadas[nodo])
        if distancia > 350:
            raise RuntimeError(f"El nodo OSM {nodo} está a {distancia:.0f} m de {refugio} (límite 350 m).")
        nuevas[refugio] = nodo
    repetidos = sorted(r for r, n in nuevas.items() if list(nuevas.values()).count(n) > 1)
    if repetidos:
        raise RuntimeError(f"Un mismo nodo OSM no puede anclar varios refugios: {repetidos}.")
    return nuevas


def seleccionar_mapa(
    coordenadas: dict[str, tuple[float, float]],
    segmentos: list[dict[str, object]],
    anclas: dict[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, str]]]:
    """Elige un subgrafo conectado de 300 nodos que conserva los refugios."""

    predecesores: defaultdict[str, set[str]] = defaultdict(set)
    segmentos_por_par: defaultdict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for segmento in segmentos:
        a, b = str(segmento["desde"]), str(segmento["hasta"])
        segmentos_por_par[tuple(sorted((a, b), key=int))].append(segmento)
        sentido = str(segmento["oneway"])
        hacia_atras = sentido == "-1"
        unidireccional = sentido in {"yes", "1", "true", "-1"} or bool(segmento["roundabout"])
        desde, hasta = (b, a) if hacia_atras else (a, b)
        predecesores[hasta].add(desde)
        if not unidireccional:
            predecesores[desde].add(hasta)

    # Expandimos hacia atrás desde cada refugio. Así cada nodo incluido
    # conserva al menos un camino dirigido hasta una zona segura, incluso en
    # calles de un solo sentido.
    # Sin tope de tamaño: la red incluye todo nodo con ruta dirigida a un refugio.
    elegidos = set(anclas.values())
    if len(elegidos) != len(ZONAS_SEGURAS):
        raise RuntimeError("Las cuatro zonas seguras no se anclaron a nodos distintos.")
    frontera = deque(sorted(elegidos, key=int))
    while frontera:
        actual = frontera.popleft()
        for precedente in sorted(predecesores[actual], key=int):
            if precedente not in elegidos:
                elegidos.add(precedente)
                frontera.append(precedente)

    ids = sorted(elegidos, key=int)
    nodos_json = [
        {"id": f"N-OSM-{ref}", "lat": coordenadas[ref][0], "lng": coordenadas[ref][1]}
        for ref in ids
    ]
    calles_json: list[dict[str, object]] = []
    for par, variantes in sorted(segmentos_por_par.items(), key=lambda item: (int(item[0][0]), int(item[0][1]))):
        if par[0] not in elegidos or par[1] not in elegidos:
            continue
        for variante in sorted(variantes, key=lambda segmento: str(segmento["segmento"])):
            way = str(variante["way_id"])
            segmento_id = str(variante["segmento"])
            sentido_desde, sentido_hasta = str(variante["desde"]), str(variante["hasta"])
            base = {
                "segmentoId": segmento_id,
                "distancia_m": variante["distancia"], "tipo": variante["tipo"],
                "velocidad_kmh": variante["velocidad"],
            }
            sentido = str(variante["oneway"])
            hacia_atras = sentido == "-1"
            unidireccional = sentido in {"yes", "1", "true", "-1"} or bool(variante["roundabout"])
            if hacia_atras:
                calles_json.append({"id": f"E-OSM-{way}-{segmento_id}-R", "origen": f"N-OSM-{sentido_hasta}", "destino": f"N-OSM-{sentido_desde}", **base})
            else:
                calles_json.append({"id": f"E-OSM-{way}-{segmento_id}-F", "origen": f"N-OSM-{sentido_desde}", "destino": f"N-OSM-{sentido_hasta}", **base})
            if not unidireccional:
                calles_json.append({"id": f"E-OSM-{way}-{segmento_id}-R", "origen": f"N-OSM-{sentido_hasta}", "destino": f"N-OSM-{sentido_desde}", **base})

    refugios_json = [{"id": r["id"], "nodo": f"N-OSM-{anclas[r['id']]}"} for r in ZONAS_SEGURAS]
    # Un refugio sin calle de entrada no puede recibir a nadie: fallar es más seguro que publicarlo.
    entradas = {refugio["nodo"]: 0 for refugio in refugios_json}
    for calle in calles_json:
        if calle["destino"] in entradas:
            entradas[calle["destino"]] += 1
    aislados = sorted(nodo for nodo, cuenta in entradas.items() if cuenta == 0)
    if aislados:
        raise RuntimeError(f"Refugios sin calle de entrada en el mapa: {aislados}")
    return nodos_json, calles_json, refugios_json


def generar(anclajes: dict[str, str] | None = None) -> tuple[dict[str, object], dict[str, object]]:
    anclajes = anclajes or {}
    nodos_osm, vias_osm = descargar_elementos()
    coordenadas, segmentos, anclas = construir_grafo_completo(nodos_osm, vias_osm, anclajes)
    # Las anclas pueden haber quedado fuera del grafo si la vía próxima se
    # etiquetó como peatonal o privada; fallar es más seguro que reubicarla.
    if not set(anclas.values()).issubset(coordenadas):
        raise RuntimeError("Una zona segura no tiene nodo de intersección conectable en la red vial pública.")
    nodos, calles, refugios = seleccionar_mapa(coordenadas, segmentos, anclas)
    contenido = {"nodos": nodos, "calles": calles, "refugios": refugios}
    hash_mapa = hashlib.sha256(json.dumps(contenido, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]
    contenido["version"] = f"manta-osm-{hash_mapa}"
    recuperado = datetime.now(UTC).isoformat(timespec="seconds")
    fuentes = {
        "estado": "fixture de simulación; no usar para navegación o evacuación real",
        "osm": {
            "atribucion": "© OpenStreetMap contributors",
            "licencia": "Open Database License (ODbL)",
            "url": "https://www.openstreetmap.org/copyright",
            "api": URL_OSM_API,
            "obtenido_utc": recuperado,
            "caja_wgs84": {"sur": CAJA[0], "oeste": CAJA[1], "norte": CAJA[2], "este": CAJA[3]},
            "simplificacion": "se conservan intersecciones, extremos de vías y anclas de refugios; costo/distancia por geometría OSM",
            "velocidades": "maxspeed OSM si está etiquetado; en otro caso valores de juego documentados en el exportador",
        },
        "refugios": [
            {
                **r,
                "fuente": f"{URL_GAD_MAPAS}{r['pagina']}",
                "evidencia_tsunami": "zona segura señalada en el mapa de evacuación del GAD Manta",
                "evidencia_sismo": "no evaluada; requiere microzonificación y validación estructural",
                "distancia_snap_m": round(_distancia_m((r["lat"], r["lng"]), nodos_osm[anclas[r["id"]]]), 1),
                "nodo_osm": anclas[r["id"]],
                "anclaje_origen": "manual" if r["id"] in anclajes else "automatica",
            }
            for r in ZONAS_SEGURAS
        ],
        "amenazas": {
            "tsunami": "refugios tomados de puntos finales Zona Segura en mapas oficiales del GAD; no reemplazan alertas ni rutas vigentes",
            "sismo": "pendiente de microzonificación local y evaluación de suelo/estructura; no se afirma que los refugios sean sismorresistentes",
        },
    }
    return contenido, fuentes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=SALIDA_MAPA)
    parser.add_argument("--fuentes", type=Path, default=SALIDA_FUENTES)
    parser.add_argument(
        "--anclaje", action="append", default=[], metavar="R-0X=ID_OSM",
        help="ancla un refugio a un nodo de intersección OSM (sin N-OSM-); repetible",
    )
    args = parser.parse_args()
    anclajes: dict[str, str] = {}
    for texto in args.anclaje:
        refugio, separador, nodo = texto.partition("=")
        if not separador or not nodo.isdigit():
            parser.error(f"--anclaje espera R-0X=<id OSM numérico>, recibido {texto!r}")
        anclajes[refugio] = nodo
    try:
        mapa, fuentes = generar(anclajes)
    except RuntimeError as error:
        parser.exit(1, f"Error: {error}\n")
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(mapa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.fuentes.write_text(json.dumps(fuentes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mapa {mapa['version']}: {len(mapa['nodos'])} nodos, {len(mapa['calles'])} sentidos, {len(mapa['refugios'])} refugios")
    print(f"Fuentes: {args.fuentes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

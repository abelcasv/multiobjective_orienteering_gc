"""Dashboard de demostración del planificador de rutas turísticas por Gran Canaria.

Uso: streamlit run dashboard.py

Usa src/planificador.py (optimizar_ruta) para el cálculo y
output/<escenario>/caminos_todos_pares.json.gz (scripts/build_all_road_paths.py) para dibujar
el recorrido por carretera. Si ese fichero no existe, los tramos se dibujan en línea recta.
"""
import gzip
import json
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

import folium
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from scripts.make_maps import OPCIONES, _numbered_icon
from src.core.problem import Individual
from src.pipeline import ESCENARIOS, load_coordinates, scenario_output_dir, serialize_route
from src.planificador import ResultadoRuta, cargar_categorias, categorias_disponibles, optimizar_ruta

st.set_page_config(page_title="Rutas por Gran Canaria", page_icon="🗺️", layout="wide")

ESCENARIO_DEFECTO = "santa_catalina"
PESTANAS = [("express", "Express"), ("equilibrada", "Equilibrada"), ("exhaustiva", "Exhaustiva")]
COLOR_FRENTE = "#9aa0a6"
NOTA_TIEMPOS = "Los tiempos de conducción no incluyen aparcamiento ni tráfico."


# --------------------------------------------------------------------------- cálculo y datos
@st.cache_data(show_spinner=False, max_entries=64)
def calcular(escenario: str, t_max: float, categorias: Tuple[str, ...], excluidos: Tuple[str, ...],
             obligatorio: Optional[str]) -> ResultadoRuta:
    return optimizar_ruta(escenario, t_max, categorias, excluidos, obligatorio=obligatorio)


@st.cache_resource(show_spinner=False)
def cargar_caminos(escenario: str) -> Optional[Dict[str, Dict[str, Any]]]:
    path = scenario_output_dir(escenario) / "caminos_todos_pares.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)["pares"]


@st.cache_data(show_spinner=False)
def coordenadas_hotel(escenario: str) -> Tuple[float, float]:
    c = load_coordinates(escenario)[ESCENARIOS[escenario]]
    return c["lat"], c["lon"]


@st.cache_data(show_spinner=False)
def nombres_pois(escenario: str) -> List[str]:
    return sorted(cargar_categorias(escenario))


# --------------------------------------------------------------------------- formato
def duracion(minutos: float) -> str:
    m = int(round(minutos))
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def reloj(salida: time, minutos: float) -> str:
    inicio = datetime.combine(date.today(), salida)
    momento = inicio + timedelta(minutes=minutos)
    extra = " (+1 día)" if momento.date() > inicio.date() else ""
    return momento.strftime("%H:%M") + extra


def etiqueta_ruta(ind: Individual) -> str:
    return f"{ind.score:.0f} pts · {duracion(ind.total_time)} · {len(ind.genes)} paradas"


# --------------------------------------------------------------------------- estado
def _init_estado() -> None:
    st.session_state.setdefault("descartados", [])
    st.session_state.setdefault("aplicados", None)


def descartar(nombre: str) -> None:
    if nombre not in st.session_state.descartados:
        st.session_state.descartados.append(nombre)


def recuperar(nombre: Optional[str] = None) -> None:
    if nombre is None:
        st.session_state.descartados = []
    elif nombre in st.session_state.descartados:
        st.session_state.descartados.remove(nombre)


# --------------------------------------------------------------------------- barra lateral
def barra_lateral() -> Tuple[Dict[str, Any], time]:
    sb = st.sidebar
    sb.header("Tu día en Gran Canaria")
    escenario = sb.selectbox("Hotel de salida", list(ESCENARIOS), format_func=ESCENARIOS.get,
                             index=list(ESCENARIOS).index(ESCENARIO_DEFECTO), key="w_escenario")
    horas = sb.slider("Tiempo disponible", 2.0, 8.0, 8.0, 0.5, format="%.1f h", key="w_horas")
    salida = sb.time_input("Hora de salida", time(9, 0), step=timedelta(minutes=15), key="w_salida")

    sb.subheader("Qué te interesa")
    categorias = tuple(c for c in categorias_disponibles(escenario)
                       if sb.checkbox(c, value=True, key=f"w_cat_{c}"))
    obligatorio = sb.selectbox("Visita obligatoria", ["Ninguna"] + nombres_pois(escenario), key="w_obligatorio")

    actuales = {"escenario": escenario, "t_max": horas * 60.0, "categorias": categorias,
                "obligatorio": None if obligatorio == "Ninguna" else obligatorio}
    if sb.button("Calcular rutas", type="primary", width="stretch") or st.session_state.aplicados is None:
        st.session_state.aplicados = actuales
    elif actuales != st.session_state.aplicados:
        sb.caption("⚠️ Hay cambios sin aplicar: pulsa «Calcular rutas».")

    sb.subheader("Lugares descartados")
    if not st.session_state.descartados:
        sb.caption("Ninguno. Usa «No me interesa» en el itinerario para descartar un lugar.")
    for nombre in st.session_state.descartados:
        c1, c2 = sb.columns([3, 2])
        c1.write(nombre)
        c2.button("Recuperar", key=f"rec_{nombre}", on_click=recuperar, args=(nombre,))
    if len(st.session_state.descartados) > 1:
        sb.button("Recuperar todos", on_click=recuperar, width="stretch")
    return st.session_state.aplicados, salida


# --------------------------------------------------------------------------- gráfico del frente
def _indice(res: ResultadoRuta, ind: Optional[Individual]) -> Optional[int]:
    if ind is None:
        return None
    return next(i for i, x in enumerate(res.frente) if x.genes == ind.genes)


def grafico_frente(res: ResultadoRuta, elegida: int, clave: str) -> Optional[int]:
    """Dibuja el frente y devuelve el índice de la ruta pulsada, si hay un clic nuevo."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[ind.total_time / 60 for ind in res.frente], y=[ind.score for ind in res.frente],
        mode="markers", name="Frente de Pareto", customdata=list(range(len(res.frente))),
        marker=dict(color=COLOR_FRENTE, size=9),
        text=[" → ".join(res.paradas(ind)) for ind in res.frente],
        hovertemplate="%{y:.0f} pts · %{x:.2f} h<br>%{text}<extra></extra>",
    ))
    # Las opciones que coinciden se dibujan como un solo punto con las dos etiquetas.
    grupos: Dict[int, List[str]] = {}
    for clave_op, nombre in PESTANAS:
        idx = _indice(res, getattr(res, clave_op))
        if idx is not None:
            grupos.setdefault(idx, []).append(clave_op)
    for idx, claves in grupos.items():
        ind = res.frente[idx]
        fig.add_trace(go.Scatter(
            x=[ind.total_time / 60], y=[ind.score], mode="markers", customdata=[idx],
            name=" = ".join(OPCIONES[c][0] for c in claves),
            marker=dict(color=OPCIONES[claves[0]][1], size=15, line=dict(color="white", width=2)),
            hovertemplate=f"{' = '.join(OPCIONES[c][0] for c in claves)}: %{{y:.0f}} pts · %{{x:.2f}} h<extra></extra>",
        ))
    sel = res.frente[elegida]
    fig.add_trace(go.Scatter(
        x=[sel.total_time / 60], y=[sel.score], mode="markers", name="Ruta elegida", customdata=[elegida],
        marker=dict(symbol="circle-open", color="#202124", size=24, line=dict(width=2)), hoverinfo="skip",
    ))
    fig.add_vline(x=res.t_max / 60, line=dict(color="#c5221f", dash="dot", width=1.5),
                  annotation_text="Tiempo disponible", annotation_position="top left")
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
        xaxis=dict(title="Tiempo total (h)", gridcolor="#eceff1", zeroline=False),
        yaxis=dict(title="Puntuación", gridcolor="#eceff1", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), clickmode="event+select",
    )
    evento = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key=clave)
    puntos = (evento or {}).get("selection", {}).get("points", []) if evento else []
    pulsado = None
    for p in puntos:
        cd = p.get("customdata")
        if cd is not None:
            pulsado = int(cd[0] if isinstance(cd, (list, tuple)) else cd)
    previo = st.session_state.get("ultimo_clic")
    if (clave, pulsado) != previo:
        st.session_state.ultimo_clic = (clave, pulsado)
        return pulsado
    return None


# --------------------------------------------------------------------------- detalle de una ruta
def _horarios(tramos: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
    """(llegada, salida) en minutos desde la salida del hotel para cada destino de tramo."""
    t, out = 0.0, []
    for tramo in tramos:
        t += tramo["tiempo_conduccion_min"]
        llegada = t
        t += tramo["tiempo_estancia_min"]
        out.append((llegada, t))
    return out


def mapa_ruta(ruta: Dict[str, Any], escenario: str, color: str, salida: time) -> folium.Map:
    hotel = coordenadas_hotel(escenario)
    caminos = cargar_caminos(escenario)
    fmap = folium.Map(location=hotel, zoom_start=10, tiles="OpenStreetMap")
    folium.Marker(hotel, icon=folium.Icon(color="black", icon="home", prefix="fa"),
                  tooltip=ESCENARIOS[escenario]).add_to(fmap)

    tramos = ruta["detalle_tramos"]
    horarios = _horarios(tramos)
    puntos = [hotel]
    for n, (tramo, (llegada, sale)) in enumerate(zip(tramos[:-1], horarios), start=1):
        p = (tramo["coordenadas_destino"]["lat"], tramo["coordenadas_destino"]["lon"])
        puntos.append(p)
        popup = (f"<b>{n}. {tramo['destino']}</b><br>Puntuación: {tramo['score_parada']:.0f}<br>"
                 f"Llegada {reloj(salida, llegada)} · salida {reloj(salida, sale)}<br>"
                 f"Visita: {tramo['tiempo_estancia_min']:.0f} min · "
                 f"conducción desde la parada anterior: {tramo['tiempo_conduccion_min']:.0f} min")
        folium.Marker(p, icon=_numbered_icon(n, color), popup=folium.Popup(popup, max_width=280),
                      tooltip=f"{n}. {tramo['destino']}").add_to(fmap)
    puntos.append(hotel)

    for tramo, a, b in zip(tramos, puntos[:-1], puntos[1:]):
        camino = caminos.get(tramo["origen"], {}).get(tramo["destino"]) if caminos else None
        tooltip = f"{tramo['origen']} → {tramo['destino']} · {tramo['tiempo_conduccion_min']:.0f} min"
        if camino:
            folium.PolyLine(camino["coordenadas"], color=color, weight=4, opacity=0.85, tooltip=tooltip).add_to(fmap)
        else:
            folium.PolyLine([a, b], color=color, weight=4, opacity=0.85, dash_array="8 6", tooltip=tooltip).add_to(fmap)
    fmap.fit_bounds([[min(p[0] for p in puntos), min(p[1] for p in puntos)],
                     [max(p[0] for p in puntos), max(p[1] for p in puntos)]], padding=(30, 30))
    return fmap


def itinerario(ruta: Dict[str, Any], salida: time, obligatorio: Optional[str], clave: str) -> None:
    tramos = ruta["detalle_tramos"]
    horarios = _horarios(tramos)
    cab = st.columns([0.4, 3, 1.1, 1.1, 1, 0.8, 1.6])
    for col, texto in zip(cab, ["", "Parada", "Llegada", "Salida", "Visita", "Puntos", ""]):
        col.caption(texto)
    c = st.columns([0.4, 3, 1.1, 1.1, 1, 0.8, 1.6])
    c[1].write(f"🏨 {ruta['itinerario_completo'][0]}")
    c[3].write(reloj(salida, 0))
    for n, (tramo, (llegada, sale)) in enumerate(zip(tramos[:-1], horarios), start=1):
        c = st.columns([0.4, 3, 1.1, 1.1, 1, 0.8, 1.6])
        c[0].write(f"**{n}**")
        c[1].write(tramo["destino"] + (" · *obligatoria*" if tramo["destino"] == obligatorio else "")
                   + f"  \n:gray[{tramo['tiempo_conduccion_min']:.0f} min de conducción]")
        c[2].write(reloj(salida, llegada))
        c[3].write(reloj(salida, sale))
        c[4].write(f"{tramo['tiempo_estancia_min']:.0f} min")
        c[5].write(f"{tramo['score_parada']:.0f}")
        if tramo["destino"] != obligatorio:
            c[6].button("No me interesa", key=f"{clave}_no_{tramo['destino']}",
                        on_click=descartar, args=(tramo["destino"],))
    llegada_final = horarios[-1][0]
    c = st.columns([0.4, 3, 1.1, 1.1, 1, 0.8, 1.6])
    c[1].write(f"🏨 Vuelta al hotel  \n:gray[{tramos[-1]['tiempo_conduccion_min']:.0f} min de conducción]")
    c[2].write(reloj(salida, llegada_final))


def detalle(res: ResultadoRuta, ind: Individual, color: str, salida: time,
            obligatorio: Optional[str], clave: str) -> None:
    ruta = serialize_route(ind, clave, res.problema, res.nombres, res.escenario)
    m = st.columns(4)
    m[0].metric("Puntuación total", f"{ruta['puntuacion_total']:.0f} pts")
    m[1].metric("Tiempo total", duracion(ruta["tiempo_total_min"]),
                help=f"De {reloj(salida, 0)} a {reloj(salida, ruta['tiempo_total_min'])}")
    m[2].metric("Paradas", ruta["numero_paradas"])
    m[3].metric("Conducción / visitas", f"{duracion(ruta['tiempo_conduccion_min'])} / "
                                        f"{duracion(ruta['tiempo_visitas_min'])}")
    izq, der = st.columns([1.15, 1])
    with izq:
        st_folium(mapa_ruta(ruta, res.escenario, color, salida), height=430,
                  use_container_width=True, returned_objects=[], key=f"mapa_{clave}")
        if cargar_caminos(res.escenario) is None:
            st.caption("No se encuentra caminos_todos_pares.json.gz: los tramos se dibujan en línea recta.")
        else:
            st.caption("Recorrido por la red viaria de © OpenStreetMap.")
    with der:
        itinerario(ruta, salida, obligatorio, clave)
        st.caption(NOTA_TIEMPOS)


def _coincide(res: ResultadoRuta, clave_op: str) -> Optional[str]:
    """Nombre de una opción anterior que es la misma ruta que `clave_op`, si la hay."""
    ind = getattr(res, clave_op)
    for otra, nombre in PESTANAS:
        if otra == clave_op:
            return None
        if getattr(res, otra) is not None and getattr(res, otra).genes == ind.genes:
            return nombre
    return None


# --------------------------------------------------------------------------- página
def main() -> None:
    _init_estado()
    aplicados, salida = barra_lateral()
    excluidos = tuple(sorted(st.session_state.descartados))
    hotel = ESCENARIOS[aplicados["escenario"]]

    st.title("Rutas turísticas por Gran Canaria")
    st.caption(f"Salida y vuelta a **{hotel}** · {duracion(aplicados['t_max'])} disponibles · "
               "NSGA-II con 20.100 evaluaciones (semilla 42)")

    with st.spinner("Optimizando rutas con NSGA-II (unos segundos)..."):
        res = calcular(aplicados["escenario"], aplicados["t_max"], aplicados["categorias"],
                       excluidos, aplicados["obligatorio"])

    if res.vacio:
        st.error(f"No hay ninguna ruta posible. {res.motivo}")
        return

    clave = json.dumps([aplicados["escenario"], aplicados["t_max"], aplicados["categorias"],
                        excluidos, aplicados["obligatorio"]], ensure_ascii=False)
    if st.session_state.get("clave_resultado") != clave or "elegida" not in st.session_state:
        st.session_state.clave_resultado = clave
        st.session_state.elegida = _indice(res, res.equilibrada)
    chart_key = f"frente_{abs(hash(clave))}"

    st.subheader("Frente de Pareto")
    st.caption(f"{len(res.frente)} rutas no dominadas: ninguna tiene a la vez más puntos y menos tiempo que otra. "
               "Haz clic en un punto para verlo en la pestaña «Ruta elegida».")
    pulsado = grafico_frente(res, st.session_state.elegida, chart_key)
    if pulsado is not None and pulsado != st.session_state.elegida:
        st.session_state.elegida = pulsado
        st.rerun()

    tabs = st.tabs([n for _, n in PESTANAS] + ["Ruta elegida"])
    for tab, (clave_op, nombre) in zip(tabs, PESTANAS):
        with tab:
            ind = getattr(res, clave_op)
            igual = _coincide(res, clave_op)
            if igual and len(res.frente) == 1:
                st.info(f"Solo hay una ruta posible con estas condiciones, así que la {nombre} "
                        f"coincide con la {igual}.")
            elif igual:
                st.info(f"La ruta {nombre} coincide con la {igual}: en este frente, la ruta con más puntos "
                        "por hora es también la de mejor equilibrio entre puntuación y tiempo."
                        if {igual, nombre} == {"Express", "Equilibrada"} else
                        f"La ruta {nombre} coincide con la {igual}.")
            detalle(res, ind, OPCIONES[clave_op][1], salida, aplicados["obligatorio"], clave_op)

    with tabs[-1]:
        st.selectbox("Ruta del frente", list(range(len(res.frente))), key="elegida",
                     format_func=lambda i: f"{i + 1}. {etiqueta_ruta(res.frente[i])}")
        ind = res.frente[st.session_state.elegida]
        es = [n for c, n in PESTANAS if getattr(res, c) is not None and getattr(res, c).genes == ind.genes]
        if es:
            nombres = es[0] if len(es) == 1 else ", ".join(es[:-1]) + " y " + es[-1]
            st.info(f"Es la ruta {nombres}.")
        detalle(res, ind, "#5f6368", salida, aplicados["obligatorio"], "elegida")


main()

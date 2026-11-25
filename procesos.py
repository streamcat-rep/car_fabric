"""
Procesos de fabricación de cada producto y su optimización con el problema de los juegos completos
de Kantorovich (1939):

    max λ   s.a.   Σ_{p∈k} x_p ≥ n_k · λ        (cada producto necesita n_k piezas/subconjuntos k)
                   Σ_p u_{rp} · x_p ≤ R_r       (horas de operario, horas de máquina, material, días de calle…)
                   x_p ≥ 0

x_p = piezas fabricadas al año con el proceso p. Los duales de las restricciones de recursos son los
"multiplicadores resolutorios": unidades completas adicionales por cada unidad extra de recurso.
Datos ilustrativos (órdenes de magnitud realistas).
"""
import numpy as np
from scipy.optimize import linprog

H_ANIO = 3450  # horas de planta al año (2 turnos × 7,5 h × 230 días)

PLANTAS = {
    "COCHE": dict(
        nombre="Coche (carrocería y grupo motor) — planta de 100.000/año",
        piezas=[("BIW", "Carrocería en blanco", 1), ("BLQ", "Bloque motor", 1), ("CIG", "Cigüeñal", 1)],
        recursos={"OPER": ("Horas de operario", "h", 640_000),
                  "SOLD": ("Horas de robot de soldadura", "robot-h", 520_000),
                  "GIGA": ("Horas de gigaprensa de fundición (2 máquinas)", "h", 2 * H_ANIO),
                  "MEC": ("Horas de centro de mecanizado (12 máquinas)", "h", 12 * H_ANIO),
                  "AL": ("Aluminio disponible", "t", 9_000)},
        procesos=[
            ("BIW", "Estampado de ~300 piezas de chapa + soldadura por puntos (≈5.000 puntos)",
             {"OPER": 4.0, "SOLD": 6.5, "AL": 0.03}, "0,55 t de acero, 350 kWh; prensa tándem 15 golpes/min"),
            ("BIW", "Gigacasting: delantera y trasera fundidas de una pieza en aluminio + estampado del resto",
             {"OPER": 2.6, "SOLD": 3.0, "GIGA": 0.07, "AL": 0.12}, "0,38 t de acero, 520 kWh; 1 fundición cada 2 min por gigaprensa"),
            ("BLQ", "Bloque de hierro fundido en arena + mecanizado", {"OPER": 1.2, "MEC": 0.25},
             "45 kg de hierro; 240 bloques/h en la línea de moldeo"),
            ("BLQ", "Bloque de aluminio inyectado a alta presión + mecanizado", {"OPER": 0.9, "MEC": 0.18, "AL": 0.025},
             "25 kg de aluminio; menos material que arrancar"),
            ("CIG", "Cigüeñal forjado + mecanizado", {"OPER": 0.8, "MEC": 0.20}, "25 kg de acero; 250 piezas/h en la prensa de forja"),
            ("CIG", "Cigüeñal de fundición nodular + mecanizado", {"OPER": 0.6, "MEC": 0.16}, "22 kg de hierro nodular"),
        ]),
    "BUS": dict(
        nombre="Autobús eléctrico autónomo",
        piezas=[("EST", "Estructura (chasis + carrocería)", 1), ("PAN", "Paneles exteriores (juego)", 1), ("PACK", "Pack de batería 420 kWh", 1)],
        recursos={"OPER": ("Horas de operario", "h", 100_000),
                  "SOLDM": ("Horas de puesto de soldadura manual (12 puestos)", "h", 12 * H_ANIO),
                  "CNC": ("Horas de centro CNC de perfiles (1 máquina)", "h", 1 * H_ANIO),
                  "MOLDE": ("Horas de molde de composite RTM (2 moldes)", "h", 2 * H_ANIO),
                  "ROB": ("Horas de célula robotizada de baterías (1 célula)", "h", 1 * H_ANIO)},
        procesos=[
            ("EST", "Perfiles de acero soldados a mano (MIG)", {"OPER": 520, "SOLDM": 300},
             "6,0 t de acero; ≈1.400 m de cordón de soldadura"),
            ("EST", "Kit de perfiles de aluminio cortados por CNC y atornillados/remachados", {"OPER": 300, "CNC": 22},
             "3,5 t de aluminio; sin soldadura, montaje en estación"),
            ("PAN", "Paneles de chapa de acero estampada y pegada", {"OPER": 120, "SOLDM": 15}, "0,8 t de acero"),
            ("PAN", "Paneles de composite de fibra de vidrio moldeados por RTM", {"OPER": 160, "MOLDE": 40},
             "0,6 t de resina + fibra; 1 panel grande cada 40 min por molde"),
            ("PACK", "Celdas → módulos → pack (montaje manual de módulos)", {"OPER": 90, "ROB": 6}, "420 kWh en 24 módulos"),
            ("PACK", "Cell-to-pack: celdas directas al pack con robot", {"OPER": 45, "ROB": 14}, "420 kWh sin módulos intermedios"),
        ]),
    "TRAM": dict(
        nombre="Tranvía autónomo",
        piezas=[("CAJA", "Caja (5 módulos)", 1), ("BOG", "Bogie", 3)],
        recursos={"OPER": ("Horas de operario", "h", 30_000),
                  "SOLDM": ("Horas de puesto de soldadura manual (4 puestos)", "h", 4 * H_ANIO),
                  "FSW": ("Horas de máquina de soldadura por fricción (FSW)", "h", 1 * H_ANIO),
                  "MEC": ("Horas de mecanizado pesado (1 máquina)", "h", 1 * H_ANIO)},
        procesos=[
            ("CAJA", "Caja de chapa y perfiles de acero soldados a mano", {"OPER": 4200, "SOLDM": 2600}, "22 t de acero"),
            ("CAJA", "Caja de extrusiones largas de aluminio soldadas por fricción (FSW) con robot", {"OPER": 2400, "FSW": 520},
             "11 t de aluminio; cordones de 30 m de una pasada"),
            ("BOG", "Bastidor de bogie soldado", {"OPER": 260, "SOLDM": 180}, "2,5 t de acero"),
            ("BOG", "Bastidor de bogie de acero fundido + mecanizado", {"OPER": 140, "MEC": 300}, "2,8 t de acero fundido"),
        ]),
    "VIA": dict(
        nombre="Línea de tranvía (km de vía doble)",
        piezas=[("PLAT", "Plataforma (km)", 1), ("CARR", "Carril soldado continuo (km de carril)", 4)],
        recursos={"OPER": ("Horas de cuadrilla de obra", "h", 75_000),
                  "CALLE": ("Días de calle cortada admisibles al año", "días·km", 260),
                  "PREF": ("Horas de planta de prefabricados", "h", 1 * H_ANIO),
                  "FLASH": ("Horas de soldadora eléctrica a tope en taller", "h", 1 * H_ANIO)},
        procesos=[
            ("PLAT", "Losa de hormigón vertida in situ", {"OPER": 21000, "CALLE": 120}, "9.000 t de hormigón; 6 m de losa por jornada y frente"),
            ("PLAT", "Placas prefabricadas en taller y colocadas con grúa", {"OPER": 13000, "CALLE": 55, "PREF": 1900},
             "8.500 t de hormigón; 40 placas de 5 m por jornada"),
            ("CARR", "Barras de 18 m con soldadura aluminotérmica in situ (55 soldaduras/km)", {"OPER": 330, "CALLE": 2},
             "≈6 h de cuadrilla por soldadura"),
            ("CARR", "Barras largas de 108 m soldadas a tope en taller (9 soldaduras in situ/km)", {"OPER": 150, "CALLE": 1, "FLASH": 60},
             "1 soldadura a tope cada 4 min en taller"),
        ]),
    "PAR": dict(
        nombre="Parada de tranvía",
        piezas=[("PAR", "Parada completa", 1)],
        recursos={"OPER": ("Horas de cuadrilla", "h", 9_000),
                  "CALLE": ("Días de calle cortada admisibles", "días", 120),
                  "TALLER": ("Horas de taller de módulos", "h", 1 * H_ANIO)},
        procesos=[
            ("PAR", "Andenes y pérgola construidos in situ", {"OPER": 1800, "CALLE": 40}, "120 t de hormigón"),
            ("PAR", "Parada modular: módulos prefabricados atornillados", {"OPER": 900, "CALLE": 10, "TALLER": 700}, "90 t de hormigón prefabricado"),
        ]),
    "MAR": dict(
        nombre="Marquesina de autobús",
        piezas=[("MAR", "Marquesina", 1)],
        recursos={"OPER": ("Horas de operario", "h", 34_000),
                  "SOLDM": ("Horas de puesto de soldadura (2 puestos)", "h", 2 * H_ANIO),
                  "LASER": ("Horas de corte láser y plegado (1 máquina)", "h", 1 * H_ANIO)},
        procesos=[
            ("MAR", "Estructura soldada a medida", {"OPER": 70, "SOLDM": 14}, "0,6 t de acero"),
            ("MAR", "Kit modular de piezas cortadas por láser y atornilladas", {"OPER": 40, "LASER": 4}, "0,5 t de acero"),
        ]),
    "CRG": dict(
        nombre="Cargador de 150 kW",
        piezas=[("CRG", "Cargador", 1)],
        recursos={"OPER": ("Horas de operario", "h", 7_000),
                  "TEST": ("Horas de banco de pruebas de potencia (1 banco)", "h", 1 * H_ANIO)},
        procesos=[
            ("CRG", "Armario cableado a mano punto a punto", {"OPER": 120, "TEST": 30}, "pruebas largas por errores de cableado"),
            ("CRG", "Electrónica en módulos enchufables en rack", {"OPER": 70, "TEST": 55}, "módulos de 25 kW probados en fábrica"),
        ]),
}


def resolver(planta, solo=None):
    """solo: None (mezcla óptima) o índice de proceso por pieza preferido (lista de nombres permitidos)."""
    P = planta["procesos"]
    piezas = planta["piezas"]
    recs = list(planta["recursos"])
    nv = len(P) + 1
    c = np.zeros(nv); c[-1] = -1
    A, b = [], []
    for k, _, n in piezas:
        r = np.zeros(nv)
        for p, pr in enumerate(P):
            if pr[0] == k:
                r[p] = -1
        r[-1] = n
        A.append(r); b.append(0)
    for rr in recs:
        r = np.zeros(nv)
        for p, pr in enumerate(P):
            r[p] = pr[2].get(rr, 0)
        A.append(r); b.append(planta["recursos"][rr][2])
    bounds = [(0, None)] * nv
    if solo is not None:
        for p in range(len(P)):
            if p not in solo:
                bounds[p] = (0, 0)
    res = linprog(c, A_ub=np.array(A), b_ub=np.array(b), bounds=bounds, method="highs")
    if res.status != 0:
        return None
    du = -res.ineqlin.marginals
    x = res.x[:-1]
    uso = {rr: sum(P[p][2].get(rr, 0) * x[p] for p in range(len(P))) for rr in recs}
    return dict(lam=res.x[-1], x=x, dual_rec=dict(zip(recs, du[len(piezas):])), uso=uso)


RES = {}
for key, pl in PLANTAS.items():
    P = pl["procesos"]
    trad = [next(p for p, pr in enumerate(P) if pr[0] == k) for k, _, _ in pl["piezas"]]
    nuevo = [max(p for p, pr in enumerate(P) if pr[0] == k) for k, _, _ in pl["piezas"]]
    RES[key] = dict(opt=resolver(pl), trad=resolver(pl, trad), nuevo=resolver(pl, nuevo))

if __name__ == "__main__":
    for key, pl in PLANTAS.items():
        r = RES[key]
        print(f"\n== {pl['nombre']}: óptimo {r['opt']['lam']:.1f} | tradicional {r['trad']['lam']:.1f} | nuevo {r['nuevo']['lam']:.1f}")
        for p, pr in enumerate(pl["procesos"]):
            print(f"   {pr[0]:5s} {pr[1][:60]:60s} x={r['opt']['x'][p]:10.1f}")
        print("   uso", {k: f"{v:,.0f}/{pl['recursos'][k][2]:,.0f}" for k, v in r["opt"]["uso"].items()})
        print("   dual", {k: round(v, 5) for k, v in r["opt"]["dual_rec"].items() if v > 1e-9})

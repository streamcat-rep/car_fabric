"""
PLAN INTEGRAL: producción de coches, autobuses autónomos, tranvías autónomos e infraestructura
para la movilidad de una ciudad de 735.000 habitantes en 974 km².

Estructura del modelo (análisis de actividades de Kantorovich = Leontief con técnicas alternativas):
  * BIENES: filas del balance material (minería -> energía -> materiales -> componentes -> productos -> movilidad)
  * ACTIVIDADES: cada una produce 1 unidad de un bien con una receta (insumos), horas directas y CO2 directo.
    La primera actividad de cada bien es la técnica base (la que usa Leontief).
  * Leontief  : v = l (I-A)^-1  (horas incorporadas),  eps = d (I-A)^-1  (CO2 incorporado),  x = (I-A)^-1 y
  * Kantorovich: min/max sobre z >= 0 con B z >= y, límites de contenido reciclado, recursos y techos.
  * Taller    : takt, puestos y operarios para la cantidad anual de cada producto; camino crítico de la vía.
"""
import math
import numpy as np
from scipy.optimize import linprog

# =============================================================================
# 0. BIENES
# =============================================================================
BIENES = [
    ("FE", "Mineral de hierro", "t", "Extracción"),
    ("BAU", "Bauxita", "t", "Extracción"),
    ("CUC", "Concentrado de cobre", "t", "Extracción"),
    ("CRU", "Petróleo crudo y gas", "t", "Extracción"),
    ("SIL", "Arena, grava y balasto", "t", "Extracción"),
    ("CAR", "Carbón", "t", "Extracción"),
    ("LIT", "Minerales de batería (Li, Ni, Mn, grafito)", "t", "Extracción"),
    ("ELE", "Electricidad", "MWh", "Energía"),
    ("GAS", "Gasolina", "t", "Energía"),
    ("ACE", "Acero", "t", "Materiales"),
    ("ALU", "Aluminio", "t", "Materiales"),
    ("COB", "Cobre refinado", "t", "Materiales"),
    ("POL", "Polímeros y pinturas", "t", "Materiales"),
    ("CAU", "Caucho", "t", "Materiales"),
    ("VID", "Vidrio", "t", "Materiales"),
    ("HOR", "Hormigón", "t", "Materiales"),
    ("MAD", "Madera laminada", "t", "Materiales"),
    ("BIW", "Carrocería de coche", "ud", "Componentes"),
    ("MOT", "Motor de combustión", "ud", "Componentes"),
    ("TRA", "Transmisión", "ud", "Componentes"),
    ("CHA", "Chasis y suspensión de coche", "ud", "Componentes"),
    ("RUE", "Ruedas y neumáticos de coche", "jgo", "Componentes"),
    ("ELC", "Módulo eléctrico/electrónico", "ud", "Componentes"),
    ("INT", "Interior de coche", "ud", "Componentes"),
    ("CRI", "Acristalamiento de coche", "jgo", "Componentes"),
    ("BAT", "Batería de tracción", "kWh", "Componentes"),
    ("MEL", "Motor eléctrico + inversor", "kW", "Componentes"),
    ("AUT", "Kit de conducción autónoma", "ud", "Componentes"),
    ("CICE", "Coche de combustión", "ud", "Productos"),
    ("CBEV", "Coche eléctrico", "ud", "Productos"),
    ("BUS", "Autobús eléctrico autónomo 12 m", "ud", "Productos"),
    ("TRAM", "Tranvía autónomo 32 m", "ud", "Productos"),
    ("VIA", "Línea de tranvía (km de vía doble + catenaria + subestación)", "km", "Productos"),
    ("PAR", "Parada de tranvía", "ud", "Productos"),
    ("MAR", "Marquesina de autobús", "ud", "Productos"),
    ("CRG", "Cargador de depósito 150 kW", "ud", "Productos"),
    ("PKM", "Movilidad urbana", "mil pkm", "Servicio"),
]
COD = [b[0] for b in BIENES]
IX = {c: i for i, c in enumerate(COD)}
NB = len(BIENES)
ESCALONES = ["Extracción", "Energía", "Materiales", "Componentes", "Productos"]

# =============================================================================
# 1. ACTIVIDADES
# =============================================================================
A_ = []


def act(id_, nombre, bien, ins, h, co2, rec=None, nota=""):
    A_.append(dict(id=id_, nombre=nombre, bien=bien, ins=ins, h=h, co2=co2, rec=rec or {}, nota=nota))


# --- extracción
act("fe", "Minería de hierro", "FE", {"ELE": 0.02}, 0.15, 0.010)
act("bau", "Minería de bauxita", "BAU", {"ELE": 0.01}, 0.20, 0.008)
act("cuc", "Minería y concentración de cobre", "CUC", {"ELE": 0.80}, 2.00, 0.050)
act("cru", "Extracción de crudo y gas", "CRU", {"ELE": 0.05}, 0.10, 0.150)
act("sil", "Canteras de áridos", "SIL", {"ELE": 0.01, "CRU": 0.002}, 0.10, 0.005)
act("car", "Minería de carbón", "CAR", {"ELE": 0.03}, 0.40, 0.060)
act("lit", "Minería y refino de minerales de batería", "LIT", {"ELE": 1.5, "CRU": 0.10}, 3.0, 0.50)
# --- energía
act("ele_t", "Electricidad térmica (carbón y gas)", "ELE", {"ELE": 0.06, "CAR": 0.08, "CRU": 0.04}, 0.20, 0.20)
act("ele_r", "Electricidad renovable (eólica + fotovoltaica)", "ELE", {}, 0.35, 0.0, {"RENOV": 1.0},
    "más horas de construcción y mantenimiento de parques por MWh, cero combustible")
act("gas", "Refino de gasolina", "GAS", {"CRU": 1.10, "ELE": 0.25}, 0.60, 0.35)
# --- materiales
act("ace_bof", "Acero integral BF-BOF (alto horno + convertidor)", "ACE", {"FE": 1.60, "CAR": 0.75, "ELE": 0.45}, 2.50, 1.75)
act("ace_eaf", "Acero de horno eléctrico con chatarra (EAF)", "ACE", {"ELE": 0.60}, 1.80, 0.08, {"CHATARRA_FE": 1.10},
    "limitado por la chatarra disponible: como máximo el 40 % del acero")
act("ace_h2", "Acero DRI con hidrógeno verde + EAF", "ACE", {"FE": 1.50, "ELE": 3.80}, 2.90, 0.10, {},
    "el hidrógeno se obtiene por electrólisis: mucha electricidad")
act("alu_p", "Aluminio primario (Bayer + Hall-Héroult)", "ALU", {"BAU": 4.40, "ELE": 15.0, "CAR": 0.45}, 6.00, 1.60)
act("alu_s", "Aluminio secundario (refundición de chatarra)", "ALU", {"ELE": 0.80, "CRU": 0.05}, 3.00, 0.30, {"CHATARRA_AL": 1.05},
    "limitado por la chatarra: como máximo el 55 % del aluminio")
act("cob", "Fundición y refino de cobre", "COB", {"CUC": 4.0, "ELE": 3.5}, 8.0, 0.40)
act("pol", "Petroquímica: polímeros y pinturas", "POL", {"CRU": 1.8, "ELE": 1.5}, 3.0, 0.90)
act("cau", "Caucho sintético", "CAU", {"CRU": 1.6, "ELE": 0.8}, 5.0, 0.70)
act("vid", "Vidrio flotado", "VID", {"SIL": 1.2, "ELE": 0.5, "CRU": 0.12}, 4.0, 0.45)
act("hor_c", "Hormigón con cemento Portland", "HOR", {"SIL": 0.85, "CAR": 0.02, "ELE": 0.03}, 0.30, 0.13)
act("hor_lc3", "Hormigón bajo en clínker (LC3: arcilla calcinada + caliza)", "HOR", {"SIL": 0.88, "CAR": 0.01, "ELE": 0.035}, 0.33, 0.08)
act("mad", "Madera laminada encolada (CLT/GLT)", "MAD", {"ELE": 0.25, "CRU": 0.02, "POL": 0.02}, 4.0, 0.05)
# --- componentes de coche
act("biw_a", "Carrocería de coche en acero (estampado + soldadura)", "BIW", {"ACE": 0.550, "ALU": 0.030, "ELE": 0.35}, 8.0, 0)
act("biw_m", "Carrocería de coche multimaterial (acero + aluminio)", "BIW", {"ACE": 0.300, "ALU": 0.130, "ELE": 0.42}, 9.5, 0)
act("mot", "Motor de combustión (fundición + mecanizado + montaje)", "MOT", {"ACE": 0.090, "ALU": 0.050, "COB": 0.004, "POL": 0.010, "ELE": 0.40}, 10.0, 0)
act("tra", "Transmisión", "TRA", {"ACE": 0.055, "ALU": 0.020, "ELE": 0.20}, 6.0, 0)
act("cha", "Chasis y suspensión", "CHA", {"ACE": 0.160, "ALU": 0.030, "CAU": 0.005, "ELE": 0.20}, 5.0, 0)
act("rue", "Ruedas y neumáticos", "RUE", {"ACE": 0.045, "ALU": 0.035, "CAU": 0.045, "ELE": 0.10}, 2.5, 0)
act("elc", "Módulo eléctrico/electrónico (cableado, centralitas)", "ELC", {"COB": 0.022, "POL": 0.020, "ELE": 0.15}, 9.0, 0)
act("int", "Interior (asientos, salpicadero, guarnecidos)", "INT", {"POL": 0.110, "ACE": 0.030, "ELE": 0.12}, 7.0, 0)
act("cri", "Acristalamiento", "CRI", {"VID": 0.045, "POL": 0.002, "ELE": 0.05}, 1.5, 0)
# --- componentes eléctricos
act("bat_nmc", "Batería NMC (níquel-manganeso-cobalto)", "BAT",
    {"LIT": 0.0040, "ALU": 0.0012, "COB": 0.0009, "POL": 0.0006, "ACE": 0.0008, "ELE": 0.060}, 0.35, 0.02, {"CELDAS": 1.0})
act("bat_lfp", "Batería LFP (litio-ferrofosfato, sin níquel ni cobalto)", "BAT",
    {"LIT": 0.0026, "ALU": 0.0014, "COB": 0.0011, "POL": 0.0006, "ACE": 0.0012, "ELE": 0.050}, 0.33, 0.015, {"CELDAS": 1.0},
    "menos minerales críticos y menos energía por kWh; más pesada (aceptable en autobús y tranvía)")
act("mel", "Motor eléctrico + inversor", "MEL", {"COB": 0.0008, "ACE": 0.0015, "ALU": 0.0006, "POL": 0.0002, "ELE": 0.004}, 0.06, 0)
act("aut", "Kit autónomo (lidar, radar, cámaras, cómputo redundante)", "AUT", {"COB": 0.003, "POL": 0.010, "ALU": 0.005, "ELE": 0.40}, 40.0, 0)
# --- productos (horas directas = ENSAMBLAJE FINAL)
act("cice", "Montaje final del coche de combustión (pintura + línea)", "CICE",
    {"BIW": 1, "MOT": 1, "TRA": 1, "CHA": 1, "RUE": 1, "ELC": 1, "INT": 1, "CRI": 1, "POL": 0.03, "ACE": 0.01, "ELE": 0.8}, 18.0, 0)
act("cbev", "Montaje final del coche eléctrico", "CBEV",
    {"BIW": 1, "CHA": 1, "RUE": 1, "ELC": 1, "INT": 1, "CRI": 1, "BAT": 60, "MEL": 110, "POL": 0.03, "ACE": 0.01, "ELE": 0.8}, 16.0, 0)
act("bus_a", "Autobús con estructura de acero", "BUS",
    {"ACE": 6.0, "ALU": 2.5, "COB": 0.15, "POL": 0.8, "CAU": 0.35, "VID": 0.4, "BAT": 420, "MEL": 300, "AUT": 1, "ELC": 6, "ELE": 15},
    1400.0, 0)
act("bus_al", "Autobús con estructura de aluminio (más ligero, batería menor)", "BUS",
    {"ACE": 2.8, "ALU": 4.2, "COB": 0.15, "POL": 0.8, "CAU": 0.35, "VID": 0.4, "BAT": 380, "MEL": 300, "AUT": 1, "ELC": 6, "ELE": 16},
    1480.0, 0, {}, "2,2 t menos de masa: con la misma autonomía necesita 40 kWh menos de batería")
act("tram_a", "Tranvía con caja de acero soldado", "TRAM",
    {"ACE": 22.0, "ALU": 6.0, "COB": 1.2, "POL": 2.5, "CAU": 0.3, "VID": 1.5, "BAT": 60, "MEL": 720, "AUT": 2, "ELC": 15, "ELE": 45},
    9000.0, 0)
act("tram_al", "Tranvía con caja de perfiles extruidos de aluminio", "TRAM",
    {"ACE": 11.0, "ALU": 11.0, "COB": 1.2, "POL": 2.5, "CAU": 0.3, "VID": 1.5, "BAT": 60, "MEL": 720, "AUT": 2, "ELC": 15, "ELE": 48},
    8600.0, 0, {}, "los perfiles largos se sueldan con robot: menos horas de calderería")
act("via_l", "Vía sobre losa de hormigón (embebida en calzada)", "VIA",
    {"ACE": 260, "HOR": 9000, "COB": 12, "ALU": 2, "POL": 5, "CRU": 30, "ELE": 50, "ELC": 20}, 45000.0, 30.0)
act("via_b", "Vía sobre balasto (plataforma segregada)", "VIA",
    {"ACE": 255, "HOR": 1800, "SIL": 6500, "COB": 12, "ALU": 2, "POL": 5, "CRU": 40, "ELE": 40, "ELC": 20}, 36000.0, 35.0, {},
    "sólo en tramos segregados: como máximo el 30 % de la red; más mantenimiento de bateo")
act("via_c", "Vía en césped (losa aligerada + cubierta vegetal)", "VIA",
    {"ACE": 260, "HOR": 7600, "SIL": 1200, "COB": 12, "ALU": 2, "POL": 6, "CRU": 30, "ELE": 50, "ELC": 20}, 49000.0, 28.0)
act("par", "Parada de tranvía (andenes, pérgola, validadoras, información)", "PAR",
    {"HOR": 120, "ACE": 6.0, "VID": 1.0, "ALU": 0.8, "POL": 0.5, "ELC": 2}, 1800.0, 0)
act("mar_a", "Marquesina de acero y vidrio", "MAR",
    {"ACE": 0.6, "VID": 0.35, "ALU": 0.15, "HOR": 4.0, "POL": 0.05, "ELC": 0.5}, 70.0, 0)
act("mar_m", "Marquesina de madera laminada", "MAR",
    {"MAD": 0.55, "VID": 0.30, "ACE": 0.12, "ALU": 0.05, "HOR": 3.0, "POL": 0.04, "ELC": 0.5}, 85.0, 0)
act("crg", "Cargador de depósito 150 kW", "CRG",
    {"COB": 0.12, "ACE": 0.6, "ALU": 0.1, "POL": 0.05, "MEL": 150, "HOR": 3}, 120.0, 0)
N_PROD = len(A_)

# Límites de proporción (contenido reciclado y aptitud técnica): z_tec <= share * total del bien
CUOTAS_TEC = [("ace_eaf", "ACE", 0.40, "Chatarra de acero: máx. 40 % del acero"),
              ("alu_s", "ALU", 0.55, "Chatarra de aluminio: máx. 55 % del aluminio"),
              ("via_b", "VIA", 0.30, "Balasto: máx. 30 % de la red (tramos segregados)")]

# =============================================================================
# 2. MODOS DE TRANSPORTE
# =============================================================================
KG_PERSONA = 100
MODOS = {
    "CICE": dict(nombre="Coche de combustión", plazas=5, ocup=1.0, masa=1350, eta_e=0.30, kwh_vkm=0.58,
                 litros_100=6.5, km_anio=7000, vida=15, vel=25, color="#a16207"),
    "CBEV": dict(nombre="Coche eléctrico", plazas=5, ocup=1.0, masa=1650, eta_e=0.85, kwh_vkm=0.17,
                 km_anio=7000, vida=15, vel=25, color="#d97706"),
    "BUS": dict(nombre="Autobús eléctrico autónomo", plazas=80, ocup=22.0, masa=13000, eta_e=0.85, kwh_vkm=1.30,
                km_anio=60000, vida=12, vel=18, color="#0e7490"),
    "TRAM": dict(nombre="Tranvía autónomo", plazas=220, ocup=66.0, masa=42000, eta_e=0.88, kwh_vkm=3.60,
                 km_anio=70000, vida=30, vel=20, color="#4338ca"),
}
for k, m in MODOS.items():
    m["eta_o"] = m["ocup"] / m["plazas"]
    m["eta_m"] = KG_PERSONA * m["ocup"] / (m["masa"] + KG_PERSONA * m["ocup"])
    m["eta_util"] = m["eta_e"] * m["eta_m"]
    m["eta_triple"] = m["eta_e"] * m["eta_o"] * m["eta_m"]
    m["vkm_kpkm"] = 1000 / m["ocup"]
    m["kwh_pkm"] = m["kwh_vkm"] / m["ocup"]

KAPPA_VIA = 10_000
VIDA = {"CICE": 15, "CBEV": 15, "BUS": 12, "TRAM": 30, "VIA": 40, "PAR": 40, "MAR": 20, "CRG": 12}
PAR_POR_KM = 1.8
KPKM_POR_MAR = 180
CRG_POR_BUS = 0.5
VIA_MAX_KM = 60
GAS_DENS, CO2_GAS, MWH_T_GAS = 0.745, 3.09, 12.2

ACT_MODO = {}
for k, m in MODOS.items():
    vkm = m["vkm_kpkm"]
    ins = {k: vkm / (m["km_anio"] * m["vida"])}
    co2 = 0.0
    if k == "CICE":
        t_gas = vkm * m["litros_100"] / 100 * GAS_DENS / 1000
        ins["GAS"] = t_gas
        co2 = t_gas * CO2_GAS
        h = vkm * 20 / m["km_anio"]
    elif k == "CBEV":
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        h = vkm * 14 / m["km_anio"]
    elif k == "BUS":
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        ins["CRG"] = vkm / m["km_anio"] * CRG_POR_BUS / VIDA["CRG"]
        ins["MAR"] = 1 / KPKM_POR_MAR / VIDA["MAR"]
        h = vkm * 0.012 + 0.10 * vkm / m["vel"]
    else:
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        ins["VIA"] = 1 / KAPPA_VIA / VIDA["VIA"]
        ins["PAR"] = PAR_POR_KM / KAPPA_VIA / VIDA["PAR"]
        h = vkm * 0.04 + 0.10 * vkm / m["vel"] + 400 / KAPPA_VIA
    m["h_oper"] = h
    m["h_conduccion"] = vkm / m["vel"] if k in ("CICE", "CBEV") else 0.0
    act("pkm_" + k.lower(), "Servicio de " + m["nombre"].lower(), "PKM", ins, h, co2)
    ACT_MODO[k] = len(A_) - 1
NA = len(A_)
PK = list(ACT_MODO.values())
ID = {a["id"]: k for k, a in enumerate(A_)}

RECURSOS = ["RENOV", "CELDAS"]
B = np.zeros((NB, NA)); H = np.zeros(NA); C = np.zeros(NA); R = np.zeros((len(RECURSOS), NA))
for k, a in enumerate(A_):
    B[IX[a["bien"]], k] += 1
    for g, q in a["ins"].items():
        B[IX[g], k] -= q
    H[k] = a["h"]; C[k] = a["co2"]
    for r, q in a["rec"].items():
        if r in RECURSOS:
            R[RECURSOS.index(r), k] = q
ENERGIA_FINAL = np.zeros(NA)
for k in MODOS:
    a = A_[ACT_MODO[k]]
    ENERGIA_FINAL[ACT_MODO[k]] = a["ins"].get("ELE", 0) + a["ins"].get("GAS", 0) * MWH_T_GAS

# =============================================================================
# 3. LEONTIEF
# =============================================================================
BASE = {}
for k, a in enumerate(A_[:N_PROD]):
    BASE.setdefault(a["bien"], k)


def leontief_mezcla(z=None):
    """Matriz A con la mezcla de técnicas de z (media ponderada); con z=None, técnica base."""
    A = np.zeros((NB, NB)); l = np.zeros(NB); d = np.zeros(NB)
    for g in set(a["bien"] for a in A_[:N_PROD]):
        ks = [k for k, a in enumerate(A_[:N_PROD]) if a["bien"] == g]
        if z is None or z[ks].sum() < 1e-9:
            pesos = {BASE[g]: 1.0}
        else:
            tot = z[ks].sum()
            pesos = {k: z[k] / tot for k in ks if z[k] > 1e-12}
        j = IX[g]
        for k, w in pesos.items():
            for gi, q in A_[k]["ins"].items():
                A[IX[gi], j] += w * q
            l[j] += w * A_[k]["h"]; d[j] += w * A_[k]["co2"]
    Linv = np.linalg.inv(np.eye(NB) - A)
    return dict(A=A, L=Linv, l=l, d=d, v=l @ Linv, e=d @ Linv)


LB = leontief_mezcla()
A0, L0, l0, d0, v0, e0 = LB["A"], LB["L"], LB["l"], LB["d"], LB["v"], LB["e"]
RHO = max(abs(np.linalg.eigvals(A0)))

# =============================================================================
# 4. KANTOROVICH: resolutor general
# =============================================================================


def lp(obj=None, y=None, max_bien=None, h_max=None, co2_max=None, caps=None, modos=False,
       fijar=None, cuotas_modo=True, excluir=None):
    """Programa lineal general sobre las actividades.
    obj      : vector de costes a minimizar (si max_bien es None)
    y        : demanda final (vector NB)
    max_bien : (bien, vector_unitario) -> maximiza t con B z >= t*y_unit
    caps     : límites absolutos de RECURSOS (None = sin límite)
    modos    : si False, las actividades de servicio y los productos de movilidad se anulan
    """
    nv = NA + (1 if max_bien is not None else 0)

    def fila(v, t=0.0):
        r = np.zeros(nv); r[:NA] = v
        if max_bien is not None:
            r[-1] = t
        return r

    A_ub, b_ub, nombres = [], [], []
    yv = np.zeros(NB) if y is None else y
    for i in range(NB):
        if max_bien is not None:
            A_ub.append(fila(-B[i], max_bien[i])); b_ub.append(0.0)
        else:
            A_ub.append(fila(-B[i])); b_ub.append(-yv[i])
        nombres.append("BAL_" + COD[i])
    for tec, g, s, _ in CUOTAS_TEC:
        v = np.zeros(NA)
        for k, a in enumerate(A_[:N_PROD]):
            if a["bien"] == g:
                v[k] = -s
        v[ID[tec]] += 1
        A_ub.append(fila(v)); b_ub.append(0.0); nombres.append("CUOTA_" + tec)
    if caps:
        for ri, r in enumerate(RECURSOS):
            if caps.get(r) is not None:
                A_ub.append(fila(R[ri])); b_ub.append(caps[r]); nombres.append(r)
    if modos and cuotas_modo:
        tot = np.zeros(NA); tot[PK] = 1
        car = np.zeros(NA); car[ACT_MODO["CICE"]] = 1; car[ACT_MODO["CBEV"]] = 1
        tr = np.zeros(NA); tr[ACT_MODO["TRAM"]] = 1
        bu = np.zeros(NA); bu[ACT_MODO["BUS"]] = 1
        for v, b, nm in [(car - CUOTA_CONDUCTORES * tot, 0, "CUOTA_COCHE_MAX"), (CUOTA_COCHE_MIN * tot - car, 0, "COCHE_MIN"),
                         (tr - CUOTA_TRAM_MAX * tot, 0, "CUOTA_TRAM"), (tr, VIA_MAX_KM * KAPPA_VIA, "VIA_MAX"),
                         (CUOTA_BUS_MIN * tot - bu, 0, "BUS_MIN")]:
            A_ub.append(fila(v)); b_ub.append(b); nombres.append(nm)
    if h_max is not None:
        A_ub.append(fila(H)); b_ub.append(h_max); nombres.append("HORAS")
    if co2_max is not None:
        A_ub.append(fila(C)); b_ub.append(co2_max); nombres.append("CO2")
    bounds = [(0, None)] * nv
    if not modos:
        for k in PK:
            bounds[k] = (0, 0)
    if fijar:
        for k, val in fijar.items():
            bounds[ACT_MODO[k]] = (val, val)
    if excluir:
        for tid in excluir:
            bounds[ID[tid]] = (0, 0)
    c = np.zeros(nv)
    if max_bien is not None:
        c[-1] = -1
    else:
        c[:NA] = obj
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
    if res.status != 0:
        return None
    du = -res.ineqlin.marginals
    z = res.x[:NA]
    return dict(z=z, t=res.x[-1] if max_bien is not None else None, fun=res.fun, dual=dict(zip(nombres, du)),
                precios=du[:NB], horas=float(H @ z), co2=float(C @ z))


# =============================================================================
# 5. DEMANDA DE LA CIUDAD
# =============================================================================
HAB, SUP = 735_000, 974
MU_CO2 = 3.0   # h de trabajo por t de CO2: valoración social (≈ 75 €/t con 25 €/h)
VIAJES_DIA, CUOTA_MOTOR, DIST_MEDIA = 2.6, 0.62, 6.8
D = HAB * VIAJES_DIA * CUOTA_MOTOR * DIST_MEDIA * 365 / 1000
CUOTA_CONDUCTORES, CUOTA_COCHE_MIN, CUOTA_TRAM_MAX, CUOTA_BUS_MIN = 0.58, 0.08, 0.45, 0.10
CAP_CIUDAD = {"RENOV": 380_000, "CELDAS": 260_000}
y_ciudad = np.zeros(NB); y_ciudad[IX["PKM"]] = D


def ind(sol):
    z = sol["z"]
    pkm = {k: z[ACT_MODO[k]] for k in MODOS}
    tot = sum(pkm.values())
    flota = {k: pkm[k] * MODOS[k]["vkm_kpkm"] / MODOS[k]["km_anio"] for k in MODOS}
    via = pkm["TRAM"] / KAPPA_VIA
    stock = dict(flota, VIA=via, PAR=via * PAR_POR_KM, MAR=pkm["BUS"] / KPKM_POR_MAR, CRG=flota["BUS"] * CRG_POR_BUS)
    prod = {g: sum(z[k] for k, a in enumerate(A_[:N_PROD]) if a["bien"] == g) for g in COD}
    grupos = {}
    for k, a in enumerate(A_):
        g = "Operación y mantenimiento" if a["bien"] == "PKM" else BIENES[IX[a["bien"]]][3]
        grupos[g] = grupos.get(g, 0.0) + H[k] * z[k]
    return dict(pkm=pkm, tot=tot, flota=flota, stock=stock, prod=prod, horas=float(H @ z), co2=float(C @ z),
                energia=float(ENERGIA_FINAL @ z), grupos=grupos,
                h_cond=sum(pkm[k] * MODOS[k]["h_conduccion"] for k in MODOS),
                h_inicial=sum(stock[g] * v0[IX[g]] for g in stock),
                tec={a["id"]: z[k] for k, a in enumerate(A_[:N_PROD])})


S = {}
S["h"] = lp(H, y_ciudad, caps=CAP_CIUDAD, modos=True)
S["c"] = lp(C + 1e-9 * H, y_ciudad, caps=CAP_CIUDAD, modos=True)
S["e"] = lp(ENERGIA_FINAL + 1e-9 * H, y_ciudad, caps=CAP_CIUDAD, modos=True)
S["ref"] = lp(H, y_ciudad, caps=CAP_CIUDAD, modos=True, excluir=[a["id"] for a in A_[:N_PROD] if BASE[a["bien"]] != ID[a["id"]]],
              fijar={"CICE": CUOTA_CONDUCTORES * D, "CBEV": 0, "TRAM": 0, "BUS": (1 - CUOTA_CONDUCTORES) * D})
S["bev"] = lp(H, y_ciudad, caps={"RENOV": None, "CELDAS": None}, modos=True,
              fijar={"CICE": 0, "CBEV": CUOTA_CONDUCTORES * D, "TRAM": 0, "BUS": (1 - CUOTA_CONDUCTORES) * D})
S["bus"] = lp(H, y_ciudad, caps=CAP_CIUDAD, modos=True,
              fijar={"CICE": 0, "CBEV": CUOTA_COCHE_MIN * D, "TRAM": 0, "BUS": (1 - CUOTA_COCHE_MIN) * D})
I = {k: ind(s) for k, s in S.items()}
IDEAL = (I["h"]["horas"], I["c"]["co2"], I["e"]["energia"])
NADIR = (I["ref"]["horas"], I["ref"]["co2"], I["ref"]["energia"])
S["comp"] = lp(H + MU_CO2 * C, y_ciudad, caps=CAP_CIUDAD, modos=True)
I["comp"] = ind(S["comp"])
u = np.zeros(NB); u[IX["PKM"]] = 1
S["max"] = lp(max_bien=u, caps=CAP_CIUDAD, modos=True, h_max=I["ref"]["horas"], co2_max=I["ref"]["co2"])
I["max"] = ind(S["max"])
ESCENARIOS = [("ref", "Coche-céntrico: combustión al máximo + autobús, técnicas base"),
              ("bev", "Coche eléctrico al máximo + autobús"),
              ("bus", "Autobús autónomo + coche eléctrico mínimo"),
              ("h", "Óptimo: mínimo trabajo"),
              ("c", "Óptimo: mínimo CO₂"),
              ("e", "Óptimo: mínima energía"),
              ("comp", "Óptimo de compromiso (recomendado)")]
PARETO = []
for fr in [0, 0.003, 0.01, 0.03, 0.1, 0.3, 0.6, 1.0]:
    eps = I["c"]["co2"] + fr * (I["h"]["co2"] - I["c"]["co2"])
    s = lp(H, y_ciudad, caps=CAP_CIUDAD, modos=True, co2_max=eps * 1.000001 + 1)
    if s:
        PARETO.append(dict(co2=s["co2"], horas=s["horas"], mu=s["dual"].get("CO2", 0), pkm=ind(s)["pkm"]))

PLAN = I["comp"]          # plan recomendado
Q_PLAN = {g: PLAN["prod"][g] for g in ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"]}

# Eficiencia por modo (técnica base)
for k, m in MODOS.items():
    a = A_[ACT_MODO[k]]
    veh = a["ins"][k]
    m["h_veh"], m["c_veh"] = veh * v0[IX[k]], veh * e0[IX[k]]
    inf = [g for g in a["ins"] if g in ("VIA", "PAR", "MAR", "CRG")]
    m["h_inf"] = sum(a["ins"][g] * v0[IX[g]] for g in inf)
    m["c_inf"] = sum(a["ins"][g] * e0[IX[g]] for g in inf)
    en = [g for g in a["ins"] if g in ("ELE", "GAS")]
    m["h_ene"] = sum(a["ins"][g] * v0[IX[g]] for g in en)
    m["c_ene"] = sum(a["ins"][g] * e0[IX[g]] for g in en) + a["co2"]
    m["h_tot"] = m["h_veh"] + m["h_inf"] + m["h_ene"] + m["h_oper"]
    m["c_tot"] = m["c_veh"] + m["c_inf"] + m["c_ene"]

# =============================================================================
# 6. FICHAS DE PRODUCCIÓN POR PRODUCTO (Leontief + Kantorovich + taller)
# =============================================================================
PRODUCTOS = ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"]
TEC_CLAVE = ["ACE", "ALU", "ELE", "HOR", "BAT", "BIW", "BUS", "TRAM", "VIA", "MAR"]
HORAS_ANIO = 2 * 7.5 * 230          # horas de planta por año (2 turnos)
HORAS_OPERARIO = 1650


def metodo_txt(z, bien_prod):
    """Describe la mezcla de técnicas activa en los bienes clave que usa el producto."""
    out = []
    for g in TEC_CLAVE:
        ks = [k for k, a in enumerate(A_[:N_PROD]) if a["bien"] == g]
        if len(ks) < 2:
            continue
        tot = z[ks].sum()
        if tot < 1e-9:
            continue
        partes = [(A_[k]["id"], z[k] / tot) for k in ks if z[k] / tot > 1e-4]
        out.append((g, partes))
    return out


Q_FICHA = dict(Q_PLAN, CICE=100_000, CBEV=100_000)   # los coches se fabrican en una planta de 100.000/año


def ficha(g):
    j = IX[g]
    q = Q_FICHA[g]
    y = np.zeros(NB); y[j] = q
    # métodos
    base_ids = [a["id"] for k, a in enumerate(A_[:N_PROD]) if BASE[a["bien"]] != k]
    m_base = lp(H, y, excluir=base_ids)
    m_h = lp(H, y)
    m_c = lp(C + 1e-7 * H, y)
    m_comp = lp(H + MU_CO2 * C, y)
    metodos = {}
    for key, nom, s in [("base", "Base (Leontief, una técnica por sector)", m_base), ("h", "Kantorovich: mínimo trabajo", m_h),
                        ("c", "Kantorovich: mínimo CO₂", m_c), ("comp", "Kantorovich: mínimo coste social (horas + μ·CO₂) — RECOMENDADO", m_comp)]:
        # máxima producción con las horas del método base (y con horas + CO2 del base)
        u = np.zeros(NB); u[j] = 1
        excl = base_ids if key == "base" else None
        mx_h = lp(max_bien=u, h_max=m_base["horas"], excluir=excl)
        mx_hc = lp(max_bien=u, h_max=m_base["horas"], co2_max=m_base["co2"], excluir=excl)
        if key in ("c", "comp"):
            # máxima producción con las horas del base sin superar el CO2 por unidad de este método
            mx_hc = lp(max_bien=u, h_max=m_base["horas"], co2_max=m_base["co2"] * s["co2"] / m_base["co2"] if m_base["co2"] > 0 else None)
        lm = leontief_mezcla(s["z"])
        metodos[key] = dict(nombre=nom, sol=s, h_ud=s["horas"] / q, c_ud=s["co2"] / q, ens=A_mix_l(s["z"], g),
                            qmax_h=mx_h["t"] if mx_h else None, qmax_hc=mx_hc["t"] if mx_hc else None,
                            mezcla=metodo_txt(s["z"], g), lm=lm,
                            cuotas={k[6:]: v for k, v in s["dual"].items() if k.startswith("CUOTA_")})
    # Leontief base: receta y requerimientos totales
    receta = []
    for k in [k for k, a in enumerate(A_[:N_PROD]) if a["bien"] == g]:
        receta.append((A_[k], [(gi, qq, qq * v0[IX[gi]], qq * e0[IX[gi]]) for gi, qq in A_[k]["ins"].items()]))
    req = L0[:, j]
    req_opt = metodos["comp"]["lm"]["L"][:, j]
    esc_h = {e: sum(l0[i] * req[i] for i in range(NB) if BIENES[i][3] == e) for e in ESCALONES}
    esc_c = {e: sum(d0[i] * req[i] for i in range(NB) if BIENES[i][3] == e) for e in ESCALONES}
    lmo = metodos["comp"]["lm"]
    esc_h_opt = {e: sum(lmo["l"][i] * req_opt[i] for i in range(NB) if BIENES[i][3] == e) for e in ESCALONES}
    esc_c_opt = {e: sum(lmo["d"][i] * req_opt[i] for i in range(NB) if BIENES[i][3] == e) for e in ESCALONES}
    # ε-restricción: frontera horas-CO2 del producto
    fr = []
    for f in [0, 0.15, 0.3, 0.5, 0.75, 1.0]:
        eps = m_c["co2"] + f * (m_h["co2"] - m_c["co2"])
        s = lp(H, y, co2_max=eps * 1.000001 + 1e-9)
        if s:
            fr.append(dict(c=s["co2"] / q, h=s["horas"] / q, mu=s["dual"].get("CO2", 0.0)))
    # taller
    l_ens = metodos["comp"]["ens"]
    takt_h = HORAS_ANIO / q
    if takt_h < 1:
        org = "Línea continua de montaje en cadena"
    elif takt_h < 60:
        org = "Línea por puestos con pulsos (el vehículo avanza un puesto cada takt)"
    else:
        org = "Puesto fijo / obra por proyecto (los equipos se desplazan al producto)"
    puestos = math.ceil(l_ens / takt_h) if takt_h < 60 else None
    return dict(g=g, q=q, metodos=metodos, receta=receta, req=req, req_opt=req_opt, esc_h=esc_h, esc_c=esc_c,
                esc_h_opt=esc_h_opt, esc_c_opt=esc_c_opt, frontera=fr, l_ens=l_ens, takt_h=takt_h, org=org,
                puestos=puestos, operarios=l_ens * q / HORAS_OPERARIO)


def A_mix_l(z, g):
    ks = [k for k, a in enumerate(A_[:N_PROD]) if a["bien"] == g]
    tot = z[ks].sum()
    return sum(z[k] * A_[k]["h"] for k in ks) / tot if tot > 0 else A_[BASE[g]]["h"]


FICHAS = {g: ficha(g) for g in PRODUCTOS}

# Fábrica de coches: escala de 100.000 coches/año para comparar con el plan del primer documento
Q_FAB = 100_000
H_FAB = float(v0[IX["CICE"]] * Q_FAB)
CAP_FAB = {"RENOV": 450_000, "CELDAS": 6_000_000}
VIDA_KM_COCHE = 180_000
CO2_USO = {"CICE": VIDA_KM_COCHE * 6.5 / 100 * GAS_DENS / 1000 * CO2_GAS, "CBEV": VIDA_KM_COCHE * 0.17 / 1000 * 0.20}


def max_coches(co2_max=None, tipos=("CICE", "CBEV"), vida=False, base=False):
    nv = NA + 1
    u = np.zeros(NB)
    # maximizar N = z_cice + z_cbev mediante variable t con fila t - z_cice - z_cbev <= 0
    c = np.zeros(nv); c[-1] = -1
    A_ub, b_ub = [], []
    for i in range(NB):
        r = np.zeros(nv); r[:NA] = -B[i]
        if COD[i] in ("CICE", "CBEV"):
            pass
        A_ub.append(r); b_ub.append(0.0)
    r = np.zeros(nv); r[-1] = 1
    for g in tipos:
        r[BASE[g]] = -1
    A_ub.append(r); b_ub.append(0.0)
    for tec, gg, s, _ in CUOTAS_TEC:
        r = np.zeros(nv)
        for k, a in enumerate(A_[:N_PROD]):
            if a["bien"] == gg:
                r[k] = -s
        r[ID[tec]] += 1
        A_ub.append(r); b_ub.append(0.0)
    for ri, rr in enumerate(RECURSOS):
        r = np.zeros(nv); r[:NA] = R[ri]; A_ub.append(r); b_ub.append(CAP_FAB[rr])
    r = np.zeros(nv); r[:NA] = H; A_ub.append(r); b_ub.append(H_FAB)
    if co2_max is not None:
        r = np.zeros(nv); r[:NA] = C
        if vida:
            for g in ("CICE", "CBEV"):
                r[BASE[g]] += CO2_USO[g]
        A_ub.append(r); b_ub.append(co2_max)
    bounds = [(0, None)] * nv
    for k in PK:
        bounds[k] = (0, 0)
    for gg in ("BUS", "TRAM", "VIA", "PAR", "MAR", "CRG", "CICE", "CBEV"):
        for k, a in enumerate(A_[:N_PROD]):
            if a["bien"] == gg and gg not in tipos:
                bounds[k] = (0, 0)
    if base:
        for k, a in enumerate(A_[:N_PROD]):
            if BASE[a["bien"]] != k:
                bounds[k] = (0, 0)
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
    if res.status != 0:
        return None
    z = res.x[:NA]
    n = {g: z[BASE[g]] for g in ("CICE", "CBEV")}
    co2 = float(C @ z)
    return dict(N=res.x[-1], n=n, co2=co2, co2_vida=co2 + sum(n[g] * CO2_USO[g] for g in n), z=z,
                tec={a["id"]: z[k] for k, a in enumerate(A_[:N_PROD])})


FAB = {"base": max_coches(tipos=("CICE",), base=True), "opt": max_coches(tipos=("CICE",)),
       "bev": max_coches(tipos=("CBEV",))}
FAB_SENS = [(f, max_coches(co2_max=f * FAB["base"]["co2"], tipos=("CICE",))) for f in [1, 0.7, 0.5, 0.35, 0.25, 0.2]]
FAB_VIDA = [(f, max_coches(co2_max=f * FAB["base"]["co2_vida"], vida=True)) for f in [1, 0.7, 0.5, 0.35, 0.25]]

# Camino crítico de la construcción de 1 km de vía (días)
CPM_VIA = [("A", "Replanteo y desvío de servicios afectados (agua, gas, telecom)", 30, []),
           ("B", "Excavación de caja y drenaje", 20, ["A"]),
           ("C", "Subestación de tracción (obra civil + equipos)", 90, ["A"]),
           ("D", "Losa de hormigón / plataforma", 25, ["B"]),
           ("E", "Montaje y soldadura aluminotérmica de carril", 15, ["D"]),
           ("F", "Postes y catenaria", 20, ["D"]),
           ("G", "Andenes de parada", 30, ["D"]),
           ("H", "Pavimentación, urbanización y césped", 20, ["E"]),
           ("I", "Señalización, comunicaciones y sistema autónomo", 15, ["E", "F"]),
           ("J", "Energización y pruebas dinámicas", 15, ["C", "H", "I", "G"])]
ES, EF = {}, {}
for a in CPM_VIA:
    ES[a[0]] = max([EF[p] for p in a[3]], default=0); EF[a[0]] = ES[a[0]] + a[2]
T_VIA = max(EF.values())
LS, LF = {}, {}
for a in reversed(CPM_VIA):
    suc = [b[0] for b in CPM_VIA if a[0] in b[3]]
    LF[a[0]] = min([LS[s] for s in suc], default=T_VIA); LS[a[0]] = LF[a[0]] - a[2]
HOLG = {k: LS[k] - ES[k] for k in ES}

if __name__ == "__main__":
    print(f"NB={NB} NA={NA} rho={RHO:.4f} D={D:,.0f}")
    for k, nom in ESCENARIOS:
        ii = I[k]
        print(f"{k:5s} h={ii['horas']:12,.0f} co2={ii['co2']:10,.0f} E={ii['energia']:10,.0f} "
              f"{ {m: round(100 * v / ii['tot'], 1) for m, v in ii['pkm'].items()} }")
    print("max mult", S["max"]["t"] / D)
    print("Q_PLAN", {g: round(v, 1) for g, v in Q_PLAN.items()})
    for g, fi in FICHAS.items():
        print(f"\n== {g} q={fi['q']:.1f} takt_h={fi['takt_h']:.2f} org={fi['org']} puestos={fi['puestos']} oper={fi['operarios']:.1f}")
        for key, m in fi["metodos"].items():
            mz = "; ".join(f"{gg}:" + ",".join(f"{t}={w:.2f}" for t, w in p) for gg, p in m["mezcla"])
            print(f"   {key:5s} h/ud={m['h_ud']:10.2f} ens={m['ens']:8.1f} co2/ud={m['c_ud']:9.3f} "
                  f"Qh={m['qmax_h'] / fi['q'] if m['qmax_h'] else 0:.4f} Qhc={m['qmax_hc'] / fi['q'] if m['qmax_hc'] else 0:.4f} | {mz}")
            if m["cuotas"]:
                print("        cuotas dual", {k: round(v, 3) for k, v in m["cuotas"].items() if abs(v) > 1e-6})
        print("   esc_h", {e: round(v, 2) for e, v in fi["esc_h"].items()}, "opt", {e: round(v, 2) for e, v in fi["esc_h_opt"].items()})
        print("   frontera", [(round(p['c'], 3), round(p['h'], 2), round(p['mu'], 3)) for p in fi["frontera"]])
    print("\nFAB", {k: (round(v["N"]), round(v["co2"])) for k, v in FAB.items()})
    print([(f, round(r["N"]) if r else None) for f, r in FAB_SENS])
    print([(f, {g: round(x) for g, x in r["n"].items()} if r else None) for f, r in FAB_VIDA])
    print("CPM via", T_VIA, HOLG)

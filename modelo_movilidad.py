"""
Modelo ampliado: producción de coches (combustión y eléctrico), autobuses autónomos eléctricos,
tranvías autónomos e infraestructura (vía, paradas, marquesinas, cargadores) para dar movilidad
a una ciudad de 735.000 habitantes en 974 km².

Marco: análisis de actividades de Kantorovich (Leontief generalizado con técnicas alternativas).
  - Leontief con la técnica base -> horas totales (v) y de ensamblaje final (l) de cada producto.
  - Comparación de técnicas (horas y CO2 incorporados por unidad con cada técnica).
  - LP-F (fábrica): máximo de coches producibles con unos recursos dados.
  - LP-M (ciudad): reparto modal + técnicas, multiobjetivo (trabajo, CO2, energía, movilidad).
"""
import numpy as np
from scipy.optimize import linprog

# ===========================================================================
# 0. BIENES (filas del balance)
# ===========================================================================
BIENES = [
    # código, nombre, unidad, escalón
    ("FE", "Mineral de hierro", "t", "Extracción"),
    ("BAU", "Bauxita", "t", "Extracción"),
    ("CUC", "Concentrado de cobre", "t", "Extracción"),
    ("CRU", "Petróleo crudo / gas", "t", "Extracción"),
    ("SIL", "Arena y áridos", "t", "Extracción"),
    ("CAR", "Carbón", "t", "Extracción"),
    ("LIT", "Minerales de batería (Li, Ni, grafito)", "t", "Extracción"),
    ("ELE", "Electricidad", "MWh", "Energía"),
    ("GAS", "Gasolina", "t", "Energía"),
    ("ACE", "Acero", "t", "Materiales"),
    ("ALU", "Aluminio", "t", "Materiales"),
    ("COB", "Cobre refinado", "t", "Materiales"),
    ("POL", "Polímeros y pinturas", "t", "Materiales"),
    ("CAU", "Caucho", "t", "Materiales"),
    ("VID", "Vidrio", "t", "Materiales"),
    ("HOR", "Hormigón", "t", "Materiales"),
    ("BIW", "Carrocería de coche", "ud", "Componentes"),
    ("MOT", "Motor de combustión", "ud", "Componentes"),
    ("TRA", "Transmisión", "ud", "Componentes"),
    ("CHA", "Chasis y suspensión", "ud", "Componentes"),
    ("RUE", "Ruedas y neumáticos", "jgo", "Componentes"),
    ("ELC", "Sistema eléctrico/electrónico (módulo)", "ud", "Componentes"),
    ("INT", "Interior de coche", "ud", "Componentes"),
    ("CRI", "Acristalamiento de coche", "jgo", "Componentes"),
    ("BAT", "Batería Li-ion", "kWh", "Componentes"),
    ("MEL", "Motor eléctrico + electrónica de potencia", "kW", "Componentes"),
    ("AUT", "Kit de conducción autónoma", "ud", "Componentes"),
    ("CICE", "Coche de combustión", "ud", "Vehículos"),
    ("CBEV", "Coche eléctrico", "ud", "Vehículos"),
    ("BUS", "Autobús autónomo eléctrico 12 m", "ud", "Vehículos"),
    ("TRAM", "Tranvía autónomo 32 m", "ud", "Vehículos"),
    ("VIA", "Línea de tranvía (vía doble + catenaria + subestaciones)", "km", "Infraestructura"),
    ("PAR", "Parada de tranvía", "ud", "Infraestructura"),
    ("MAR", "Marquesina de autobús", "ud", "Infraestructura"),
    ("CRG", "Cargador de depósito 150 kW", "ud", "Infraestructura"),
    ("PKM", "Movilidad urbana", "mil pkm", "Servicio"),
]
COD = [b[0] for b in BIENES]
IX = {c: i for i, c in enumerate(COD)}
NB = len(BIENES)

# ===========================================================================
# 1. ACTIVIDADES (técnicas). La primera de cada bien es la técnica base (Leontief).
#    (id, nombre, bien, insumos, horas directas, CO2 directo, recursos)
# ===========================================================================
A_ = []


def act(id_, nombre, bien, ins, h, co2, rec=None):
    A_.append(dict(id=id_, nombre=nombre, bien=bien, ins=ins, h=h, co2=co2, rec=rec or {}))


# --- extracción y energía
act("fe", "Minería de hierro", "FE", {"ELE": 0.02}, 0.15, 0.010)
act("bau", "Minería de bauxita", "BAU", {"ELE": 0.01}, 0.20, 0.008)
act("cuc", "Minería y concentración de cobre", "CUC", {"ELE": 0.80}, 2.00, 0.050)
act("cru", "Extracción de crudo y gas", "CRU", {"ELE": 0.05}, 0.10, 0.150)
act("sil", "Canteras de arena y áridos", "SIL", {"ELE": 0.01}, 0.10, 0.005)
act("car", "Minería de carbón", "CAR", {"ELE": 0.03}, 0.40, 0.060)
act("lit", "Minería y refino de minerales de batería", "LIT", {"ELE": 1.5, "CRU": 0.10}, 3.0, 0.50)
act("ele_t", "Electricidad térmica (carbón/gas)", "ELE", {"ELE": 0.06, "CAR": 0.08, "CRU": 0.04}, 0.20, 0.20)
act("ele_r", "Electricidad renovable (eólica + FV)", "ELE", {}, 0.35, 0.0, {"RENOV": 1.0})
act("gas", "Refino de gasolina", "GAS", {"CRU": 1.10, "ELE": 0.25}, 0.60, 0.35)
# --- materiales
act("ace_bof", "Acero BF-BOF (alto horno)", "ACE", {"FE": 1.60, "CAR": 0.75, "ELE": 0.45}, 2.50, 1.75)
act("ace_eaf", "Acero EAF (chatarra)", "ACE", {"ELE": 0.60}, 1.80, 0.08, {"CHA_FE": 1.10})
act("ace_h2", "Acero DRI-H₂ + EAF (hidrógeno verde)", "ACE", {"FE": 1.50, "ELE": 3.80}, 2.90, 0.10)
act("alu_p", "Aluminio primario", "ALU", {"BAU": 4.40, "ELE": 15.0, "CAR": 0.45}, 6.00, 1.60)
act("alu_s", "Aluminio secundario (reciclado)", "ALU", {"ELE": 0.80, "CRU": 0.05}, 3.00, 0.30, {"CHA_AL": 1.05})
act("cob", "Fundición y refino de cobre", "COB", {"CUC": 4.0, "ELE": 3.5}, 8.0, 0.40)
act("pol", "Petroquímica: polímeros y pinturas", "POL", {"CRU": 1.8, "ELE": 1.5}, 3.0, 0.90)
act("cau", "Caucho sintético", "CAU", {"CRU": 1.6, "ELE": 0.8}, 5.0, 0.70)
act("vid", "Vidrio flotado", "VID", {"SIL": 1.2, "ELE": 0.5, "CRU": 0.12}, 4.0, 0.45)
act("hor_c", "Hormigón con cemento Portland", "HOR", {"SIL": 0.85, "CAR": 0.02, "ELE": 0.03}, 0.30, 0.13)
act("hor_lc3", "Hormigón bajo en clínker (LC3)", "HOR", {"SIL": 0.88, "CAR": 0.01, "ELE": 0.035}, 0.33, 0.08)
# --- componentes de coche
act("biw_a", "Carrocería de acero", "BIW", {"ACE": 0.550, "ALU": 0.030, "ELE": 0.35}, 8.0, 0)
act("biw_m", "Carrocería multimaterial (acero + Al)", "BIW", {"ACE": 0.300, "ALU": 0.130, "ELE": 0.42}, 9.5, 0)
act("mot", "Motor de combustión", "MOT", {"ACE": 0.090, "ALU": 0.050, "COB": 0.004, "POL": 0.010, "ELE": 0.40}, 10.0, 0)
act("tra", "Transmisión", "TRA", {"ACE": 0.055, "ALU": 0.020, "ELE": 0.20}, 6.0, 0)
act("cha", "Chasis y suspensión", "CHA", {"ACE": 0.160, "ALU": 0.030, "CAU": 0.005, "ELE": 0.20}, 5.0, 0)
act("rue", "Ruedas y neumáticos", "RUE", {"ACE": 0.045, "ALU": 0.035, "CAU": 0.045, "ELE": 0.10}, 2.5, 0)
act("elc", "Sistema eléctrico/electrónico", "ELC", {"COB": 0.022, "POL": 0.020, "ELE": 0.15}, 9.0, 0)
act("int", "Interior", "INT", {"POL": 0.110, "ACE": 0.030, "ELE": 0.12}, 7.0, 0)
act("cri", "Acristalamiento", "CRI", {"VID": 0.045, "POL": 0.002, "ELE": 0.05}, 1.5, 0)
act("bat", "Celdas y pack de batería Li-ion", "BAT",
    {"LIT": 0.004, "ALU": 0.0012, "COB": 0.0009, "POL": 0.0006, "ACE": 0.0008, "ELE": 0.060}, 0.35, 0.02,
    {"CELDAS": 1.0})
act("mel", "Motor eléctrico + inversor", "MEL", {"COB": 0.0008, "ACE": 0.0015, "ALU": 0.0006, "POL": 0.0002, "ELE": 0.004}, 0.06, 0)
act("aut", "Kit autónomo (lidar, radar, cámaras, cómputo)", "AUT", {"COB": 0.003, "POL": 0.010, "ALU": 0.005, "ELE": 0.40}, 40.0, 0)
# --- vehículos (horas directas = ENSAMBLAJE FINAL)
act("cice", "Montaje final coche combustión", "CICE",
    {"BIW": 1, "MOT": 1, "TRA": 1, "CHA": 1, "RUE": 1, "ELC": 1, "INT": 1, "CRI": 1, "POL": 0.03, "ACE": 0.01, "ELE": 0.8}, 18.0, 0)
act("cbev", "Montaje final coche eléctrico", "CBEV",
    {"BIW": 1, "CHA": 1, "RUE": 1, "ELC": 1, "INT": 1, "CRI": 1, "BAT": 60, "MEL": 110, "POL": 0.03, "ACE": 0.01, "ELE": 0.8}, 16.0, 0)
act("bus", "Montaje final autobús autónomo", "BUS",
    {"ACE": 6.0, "ALU": 2.5, "COB": 0.15, "POL": 0.8, "CAU": 0.35, "VID": 0.4, "BAT": 420, "MEL": 300, "AUT": 1, "ELC": 6, "ELE": 15},
    1400.0, 0)
act("tram", "Montaje final tranvía autónomo", "TRAM",
    {"ACE": 22.0, "ALU": 6.0, "COB": 1.2, "POL": 2.5, "CAU": 0.3, "VID": 1.5, "BAT": 60, "MEL": 720, "AUT": 2, "ELC": 15, "ELE": 45},
    9000.0, 0)
# --- infraestructura
act("via", "Construcción de 1 km de línea de tranvía", "VIA",
    {"ACE": 260, "HOR": 9000, "COB": 12, "ALU": 2, "POL": 5, "CRU": 30, "ELE": 50, "ELC": 20}, 45000.0, 30.0)
act("par", "Construcción de parada de tranvía", "PAR",
    {"HOR": 120, "ACE": 6.0, "VID": 1.0, "ALU": 0.8, "POL": 0.5, "ELC": 2}, 1800.0, 0)
act("mar", "Fabricación e instalación de marquesina", "MAR",
    {"ACE": 0.6, "VID": 0.35, "ALU": 0.15, "HOR": 4.0, "POL": 0.05, "ELC": 0.5}, 70.0, 0)
act("crg", "Cargador de depósito 150 kW", "CRG",
    {"COB": 0.12, "ACE": 0.6, "ALU": 0.1, "POL": 0.05, "MEL": 150, "HOR": 3}, 120.0, 0)

N_PROD = len(A_)  # actividades de producción (sin servicio)

# ===========================================================================
# 2. MODOS DE TRANSPORTE (actividades de servicio: producen 1.000 pkm)
# ===========================================================================
KG_PERSONA = 100
MODOS = {
    #            plazas, ocupación media, masa vacío kg, eficiencia energética del tren motriz,
    #            energía final por vkm (kWh), km/año por vehículo, vida (años), velocidad comercial km/h
    "CICE": dict(nombre="Coche de combustión", plazas=5, ocup=1.0, masa=1350, eta_e=0.30, kwh_vkm=0.58,
                 litros_100=6.5, km_anio=7000, vida=15, vel=25, color="#a16207"),
    "CBEV": dict(nombre="Coche eléctrico", plazas=5, ocup=1.0, masa=1650, eta_e=0.85, kwh_vkm=0.17,
                 km_anio=7000, vida=15, vel=25, color="#b45309"),
    "BUS": dict(nombre="Autobús autónomo eléctrico", plazas=80, ocup=22.0, masa=13000, eta_e=0.85, kwh_vkm=1.30,
                km_anio=60000, vida=12, vel=18, color="#0e7490"),
    "TRAM": dict(nombre="Tranvía autónomo", plazas=220, ocup=66.0, masa=42000, eta_e=0.88, kwh_vkm=3.60,
                 km_anio=70000, vida=30, vel=20, color="#4338ca"),
}
for k, m in MODOS.items():
    m["eta_o"] = m["ocup"] / m["plazas"]
    m["eta_m"] = KG_PERSONA * m["ocup"] / (m["masa"] + KG_PERSONA * m["ocup"])
    m["eta_util"] = m["eta_e"] * m["eta_m"]
    m["eta_triple"] = m["eta_e"] * m["eta_o"] * m["eta_m"]
    m["vkm_kpkm"] = 1000 / m["ocup"]                # vehículos-km por mil pkm
    m["kwh_pkm"] = m["kwh_vkm"] / m["ocup"]
    m["kwh_util_pkm"] = m["kwh_pkm"] * m["eta_util"] / m["eta_m"] * m["eta_m"]  # placeholder (no usado)

# Infraestructura ligada a los modos
KAPPA_VIA = 10_000       # mil pkm/año que soporta 1 km de línea de tranvía (10 M pkm/km)
VIDA_VIA = 40
PAR_POR_KM = 1.8
KPKM_POR_MAR = 180       # 1 marquesina por cada 180 mil pkm/año de autobús
VIDA_MAR = 20
CRG_POR_BUS = 0.5
VIDA_CRG = 12
VIA_MAX_KM = 60          # corredores urbanos con densidad suficiente para tranvía

GAS_DENS = 0.745         # kg/L
CO2_GAS = 3.09           # t CO2 por t de gasolina quemada
MWH_T_GAS = 12.2         # MWh por t de gasolina (PCI)

ACT_MODO = {}


def servicio(k):
    m = MODOS[k]
    vkm = m["vkm_kpkm"]
    ins = {k: vkm / (m["km_anio"] * m["vida"])}   # vehículo amortizado
    co2 = 0.0
    h = 0.0
    if k == "CICE":
        t_gas = vkm * m["litros_100"] / 100 * GAS_DENS / 1000
        ins["GAS"] = t_gas
        co2 = t_gas * CO2_GAS
        h = vkm * 20 / m["km_anio"]               # 20 h/año de taller por coche
    elif k == "CBEV":
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        h = vkm * 14 / m["km_anio"]
    elif k == "BUS":
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        stock_bus = vkm / m["km_anio"]
        ins["CRG"] = stock_bus * CRG_POR_BUS / VIDA_CRG
        ins["MAR"] = 1 / KPKM_POR_MAR / VIDA_MAR
        h = vkm * 0.012 + 0.10 * vkm / m["vel"]     # mantenimiento (720 h/bus·año) + supervisión remota (1 por 10 vehículos)
    elif k == "TRAM":
        ins["ELE"] = vkm * m["kwh_vkm"] / 1000
        ins["VIA"] = 1 / KAPPA_VIA / VIDA_VIA
        ins["PAR"] = PAR_POR_KM / KAPPA_VIA / VIDA_VIA
        h = vkm * 0.04 + 0.10 * vkm / m["vel"] + 400 / KAPPA_VIA   # mant. vehículo (2.800 h/tram·año) + supervisión + mant. vía
    m["h_oper"] = h
    m["h_conduccion"] = vkm / m["vel"] if k in ("CICE", "CBEV") else 0.0
    m["h_conductor"] = vkm / m["vel"] if k in ("BUS", "TRAM") else 0.0   # lo que costaría con conductor
    act("pkm_" + k.lower(), "Servicio " + m["nombre"], "PKM", ins, h, co2)
    ACT_MODO[k] = len(A_) - 1


for k in MODOS:
    servicio(k)

NA = len(A_)
RECURSOS = ["CHA_FE", "CHA_AL", "RENOV", "CELDAS"]

# Matrices del análisis de actividades
B = np.zeros((NB, NA))
H = np.zeros(NA)
C = np.zeros(NA)
R = np.zeros((len(RECURSOS), NA))
for k, a in enumerate(A_):
    B[IX[a["bien"]], k] += 1
    for g, q in a["ins"].items():
        B[IX[g], k] -= q
    H[k] = a["h"]
    C[k] = a["co2"]
    for r, q in a["rec"].items():
        R[RECURSOS.index(r), k] = q

# ===========================================================================
# 3. LEONTIEF con técnica base: horas totales y de ensamblaje final
# ===========================================================================
def leontief(tecnica):
    """tecnica: dict bien -> índice de actividad. Devuelve A, v (horas), e (CO2)."""
    A = np.zeros((NB, NB))
    l = np.zeros(NB)
    d = np.zeros(NB)
    for g, k in tecnica.items():
        a = A_[k]
        j = IX[g]
        for gi, q in a["ins"].items():
            A[IX[gi], j] += q
        l[j] = a["h"]
        d[j] = a["co2"]
    Linv = np.linalg.inv(np.eye(NB) - A)
    return A, Linv, l @ Linv, d @ Linv, l, d


BASE = {}
for k, a in enumerate(A_):
    BASE.setdefault(a["bien"], k)
LIMPIA = dict(BASE)
LIMPIA.update({"ACE": [k for k, a in enumerate(A_) if a["id"] == "ace_h2"][0],
               "ALU": [k for k, a in enumerate(A_) if a["id"] == "alu_s"][0],
               "ELE": [k for k, a in enumerate(A_) if a["id"] == "ele_r"][0],
               "HOR": [k for k, a in enumerate(A_) if a["id"] == "hor_lc3"][0]})
A0, L0, v0, e0, l0, d0 = leontief(BASE)
A1, L1, v1, e1, l1, d1 = leontief(LIMPIA)

# Comparación de técnicas: para cada actividad alternativa, horas y CO2 incorporados por unidad
# evaluados con los precios-trabajo de la técnica base: h_k + v0·insumos
comp_tec = []
for k, a in enumerate(A_[:N_PROD]):
    alts = [kk for kk, aa in enumerate(A_[:N_PROD]) if aa["bien"] == a["bien"]]
    if len(alts) < 2:
        continue
    v_inc = a["h"] + sum(q * v0[IX[g]] for g, q in a["ins"].items())
    e_inc = a["co2"] + sum(q * e0[IX[g]] for g, q in a["ins"].items())
    elec = a["ins"].get("ELE", 0.0) + (1.0 if a["id"] == "ele_r" else 0.0) * 0
    comp_tec.append(dict(k=k, bien=a["bien"], nombre=a["nombre"], v=v_inc, e=e_inc,
                         rec=a["rec"], elec=a["ins"].get("ELE", 0.0)))

# ===========================================================================
# 4. DEMANDA DE MOVILIDAD de la ciudad
# ===========================================================================
HAB = 735_000
SUP = 974
VIAJES_DIA = 2.6
CUOTA_MOTOR = 0.62        # resto a pie o en bici
DIST_MEDIA = 6.8          # km por viaje motorizado
D = HAB * VIAJES_DIA * CUOTA_MOTOR * DIST_MEDIA * 365 / 1000   # mil pkm/año
CUOTA_CONDUCTORES = 0.58  # máximo de pkm que pueden hacer en coche personas con carné y coche
CUOTA_TRAM_MAX = 0.45     # sólo los corredores densos justifican tranvía
CUOTA_BUS_MIN = 0.10      # cobertura de barrios dispersos y pedanías (974 km²)
CUOTA_COCHE_MIN = 0.08    # viajes sin alternativa colectiva (pedanías, noche, movilidad reducida puerta a puerta)

CAP = {"CHA_FE": 9_000, "CHA_AL": 1_500, "RENOV": 380_000, "CELDAS": 260_000}

PK = [ACT_MODO[k] for k in MODOS]


def resolver(obj, y_pkm=D, co2_max=None, h_max=None, fijar=None, cap=None, maximizar_pkm=False,
             max_pkm_cap=None, extra_ub=None):
    """LP general. obj: vector de coste sobre actividades (minimiza).
    Si maximizar_pkm: añade variable t (pkm servidos) y maximiza t."""
    cap = cap or CAP
    nv = NA + (1 if maximizar_pkm else 0)
    A_ub, b_ub = [], []

    def fila(v_act, t_coef=0.0):
        r = np.zeros(nv)
        r[:NA] = v_act
        if maximizar_pkm:
            r[-1] = t_coef
        return r

    # balance: -B z <= -y   (para PKM: -B z + t <= 0 si maximizar)
    for i in range(NB):
        if COD[i] == "PKM":
            if maximizar_pkm:
                A_ub.append(fila(-B[i], 1.0)); b_ub.append(0.0)
            else:
                A_ub.append(fila(-B[i])); b_ub.append(-y_pkm)
        else:
            A_ub.append(fila(-B[i])); b_ub.append(0.0)
    # recursos
    for r_i, r in enumerate(RECURSOS):
        A_ub.append(fila(R[r_i])); b_ub.append(cap[r])
    # cuotas modales (relativas al total servido)
    tot = np.zeros(NA)
    for k in PK:
        tot[k] = 1
    car = np.zeros(NA); car[ACT_MODO["CICE"]] = 1; car[ACT_MODO["CBEV"]] = 1
    A_ub.append(fila(car - CUOTA_CONDUCTORES * tot)); b_ub.append(0.0)
    A_ub.append(fila(CUOTA_COCHE_MIN * tot - car)); b_ub.append(0.0)
    tr = np.zeros(NA); tr[ACT_MODO["TRAM"]] = 1
    A_ub.append(fila(tr - CUOTA_TRAM_MAX * tot)); b_ub.append(0.0)
    A_ub.append(fila(tr)); b_ub.append(VIA_MAX_KM * KAPPA_VIA)
    bu = np.zeros(NA); bu[ACT_MODO["BUS"]] = 1
    A_ub.append(fila(CUOTA_BUS_MIN * tot - bu)); b_ub.append(0.0)
    nombres_extra = ["CUOTA_COCHE", "COCHE_MIN", "CUOTA_TRAM", "VIA_MAX", "BUS_MIN"]
    if co2_max is not None:
        A_ub.append(fila(C)); b_ub.append(co2_max); nombres_extra.append("CO2")
    if h_max is not None:
        A_ub.append(fila(H)); b_ub.append(h_max); nombres_extra.append("HORAS")
    if extra_ub:
        for vec, lim, nom in extra_ub:
            A_ub.append(fila(vec)); b_ub.append(lim); nombres_extra.append(nom)
    bounds = [(0, None)] * nv
    if fijar:
        for k, val in fijar.items():
            bounds[ACT_MODO[k]] = (val, val)
    c = np.zeros(nv)
    if maximizar_pkm:
        c[-1] = -1.0
    else:
        c[:NA] = obj
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
    if res.status != 0:
        return None
    du = -res.ineqlin.marginals
    out = dict(z=res.x[:NA], fun=res.fun, precios=du[:NB],
               rec_dual=dict(zip(RECURSOS, du[NB:NB + len(RECURSOS)])),
               extra_dual=dict(zip(nombres_extra, du[NB + len(RECURSOS):])),
               t=res.x[-1] if maximizar_pkm else None, rc=res.lower.marginals[:NA])
    return out


ENERGIA_FINAL = np.zeros(NA)  # MWh de energía final consumida en la operación (para objetivo de energía)
for k in MODOS:
    a = A_[ACT_MODO[k]]
    ENERGIA_FINAL[ACT_MODO[k]] = a["ins"].get("ELE", 0) + a["ins"].get("GAS", 0) * MWH_T_GAS


def indicadores(sol, pkm_total=None):
    z = sol["z"]
    pkm = {k: z[ACT_MODO[k]] for k in MODOS}
    tot = sum(pkm.values())
    flota = {}
    for k, m in MODOS.items():
        vkm = pkm[k] * m["vkm_kpkm"]
        flota[k] = vkm / m["km_anio"]
    via_km = pkm["TRAM"] / KAPPA_VIA
    infra = dict(VIA=via_km, PAR=via_km * PAR_POR_KM, MAR=pkm["BUS"] / KPKM_POR_MAR,
                 CRG=flota["BUS"] * CRG_POR_BUS)
    prod_anual = {g: z[[k for k, a in enumerate(A_) if a["bien"] == g]].sum()
                  for g in ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"]}
    horas = float(H @ z)
    co2 = float(C @ z)
    energia = float(ENERGIA_FINAL @ z)
    h_ens = {g: prod_anual[g] * A_[BASE[g]]["h"] for g in prod_anual}
    h_cond = sum(pkm[k] * MODOS[k]["h_conduccion"] for k in MODOS)
    elec_ren = z[[k for k, a in enumerate(A_) if a["id"] == "ele_r"][0]]
    elec_tot = z[[k for k, a in enumerate(A_) if a["bien"] == "ELE"]].sum()
    tec = {a["id"]: z[k] for k, a in enumerate(A_[:N_PROD])}
    stock = dict(flota, **infra)
    grupos = {}
    for k, a in enumerate(A_):
        g = "Operación y mantenimiento" if a["bien"] == "PKM" else \
            {"Extracción": "Extracción", "Energía": "Energía", "Materiales": "Materiales",
             "Componentes": "Componentes", "Vehículos": "Ensamblaje final de vehículos",
             "Infraestructura": "Construcción de infraestructura"}[BIENES[IX[a["bien"]]][3]]
        grupos[g] = grupos.get(g, 0.0) + H[k] * z[k]
    h_inicial = sum(stock[g] * v0[IX[g]] for g in stock)   # construir el sistema desde cero
    co2_inicial = sum(stock[g] * e0[IX[g]] for g in stock)
    return dict(pkm=pkm, tot=tot, flota=flota, infra=infra, prod=prod_anual, horas=horas, co2=co2,
                energia=energia, h_ens=h_ens, h_cond=h_cond, elec_ren=elec_ren, elec_tot=elec_tot,
                tec=tec, stock=stock, grupos=grupos, h_inicial=h_inicial, co2_inicial=co2_inicial)


# ---------------------------------------------------------------------------
# 4a. Objetivos individuales
# ---------------------------------------------------------------------------
sol_h = resolver(H)                       # mínimo trabajo social
sol_c = resolver(C + 1e-9 * H)            # mínimo CO2 (desempate por horas)
sol_e = resolver(ENERGIA_FINAL + 1e-9 * H)  # mínima energía final
# Escenario de referencia "coche-céntrico": todo el que puede va en coche de combustión, resto en bus
ref_fix = {"CICE": CUOTA_CONDUCTORES * D, "CBEV": 0, "TRAM": 0, "BUS": (1 - CUOTA_CONDUCTORES) * D}
sol_ref = resolver(H, fijar=ref_fix)
# Coche eléctrico masivo (celdas sin límite para verlo)
bev_fix = {"CICE": 0, "CBEV": CUOTA_CONDUCTORES * D, "TRAM": 0, "BUS": (1 - CUOTA_CONDUCTORES) * D}
sol_bev = resolver(H, fijar=bev_fix, cap=dict(CAP, CELDAS=1e9, RENOV=1e9))
# Sólo transporte público con autobús
bus_fix = {"CICE": CUOTA_COCHE_MIN * D, "CBEV": 0, "TRAM": 0, "BUS": (1 - CUOTA_COCHE_MIN) * D}
sol_bus = resolver(H, fijar=bus_fix)
# Máxima movilidad con el mismo trabajo y CO2 que el escenario coche-céntrico
ind_ref = indicadores(sol_ref)
sol_max = resolver(None, maximizar_pkm=True, h_max=ind_ref["horas"], co2_max=ind_ref["co2"])

# Compromiso: minimizar suma de objetivos normalizados por su ideal
f_h = indicadores(sol_h)["horas"]
f_c = indicadores(sol_c)["co2"]
f_e = indicadores(sol_e)["energia"]
# normalización por rango: (f - ideal) / (nadir - ideal), con nadir = escenario coche-céntrico
n_h, n_c, n_e = ind_ref["horas"], ind_ref["co2"], ind_ref["energia"]
sol_comp = resolver(H / (n_h - f_h) + C / (n_c - f_c) + ENERGIA_FINAL / (n_e - f_e))
PAYOFF = dict(ideal=(f_h, f_c, f_e), nadir=(n_h, n_c, n_e))

ESCENARIOS = [
    ("ref", "Coche-céntrico (combustión al máximo + autobús)", sol_ref),
    ("bev", "Coche eléctrico al máximo + autobús (sin límite de celdas)", sol_bev),
    ("bus", "Autobús autónomo (92 %) + coche mínimo", sol_bus),
    ("h", "Óptimo Kantorovich: mínimo trabajo", sol_h),
    ("c", "Óptimo Kantorovich: mínimo CO₂", sol_c),
    ("e", "Óptimo Kantorovich: mínima energía final", sol_e),
    ("comp", "Óptimo de compromiso (horas + CO₂ + energía normalizados)", sol_comp),
]
IND = {k: indicadores(s) for k, _, s in ESCENARIOS}
IND_MAX = indicadores(sol_max)

# ---------------------------------------------------------------------------
# 4b. Frontera de Pareto trabajo–CO2 (método ε-restricción)
# ---------------------------------------------------------------------------
pareto = []
c_hi = IND["h"]["co2"]
c_lo = IND["c"]["co2"]
for f in [0, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0]:
    eps = c_lo + f * (c_hi - c_lo)
    s = resolver(H, co2_max=eps * 1.000001)
    if s:
        ii = indicadores(s)
        pareto.append(dict(eps=eps, horas=ii["horas"], co2=ii["co2"], pkm=ii["pkm"],
                           mu=s["extra_dual"].get("CO2", 0.0)))

# ---------------------------------------------------------------------------
# 4c. Eficiencia por modo: horas, CO2 y energía por pkm (ciclo de vida, técnica base)
# ---------------------------------------------------------------------------
for k, m in MODOS.items():
    a = A_[ACT_MODO[k]]
    # horas y CO2 por mil pkm desglosados: fabricación vehículo, infraestructura, energía, operación
    veh = a["ins"][k]
    m["h_veh"] = veh * v0[IX[k]]
    m["c_veh"] = veh * e0[IX[k]]
    infra_keys = [g for g in a["ins"] if g in ("VIA", "PAR", "MAR", "CRG")]
    m["h_inf"] = sum(a["ins"][g] * v0[IX[g]] for g in infra_keys)
    m["c_inf"] = sum(a["ins"][g] * e0[IX[g]] for g in infra_keys)
    en_keys = [g for g in a["ins"] if g in ("ELE", "GAS")]
    m["h_ene"] = sum(a["ins"][g] * v0[IX[g]] for g in en_keys)
    m["c_ene"] = sum(a["ins"][g] * e0[IX[g]] for g in en_keys) + a["co2"]
    m["c_ene_ren"] = a["co2"] + sum(a["ins"][g] * e1[IX[g]] for g in en_keys)  # con electricidad renovable
    m["h_tot"] = m["h_veh"] + m["h_inf"] + m["h_ene"] + m["h_oper"]
    m["c_tot"] = m["c_veh"] + m["c_inf"] + m["c_ene"]
    m["mwh_final"] = ENERGIA_FINAL[ACT_MODO[k]]

# ===========================================================================
# 5. LP-F: MÁXIMO DE COCHES QUE PUEDE PRODUCIR LA FÁBRICA
# ===========================================================================
H_FAB = 7_390_000            # horas disponibles en toda la cadena (las del plan anterior)
CAP_FAB = {"CHA_FE": 45_000, "CHA_AL": 7_000, "RENOV": 450_000, "CELDAS": 6_000_000}
VIDA_KM_COCHE = 180_000
CO2_USO = {"CICE": VIDA_KM_COCHE * 6.5 / 100 * GAS_DENS / 1000 * CO2_GAS,
           "CBEV": VIDA_KM_COCHE * 0.17 / 1000 * 0.20}   # red con 0,2 t/MWh


def max_coches(co2_max=None, tipos=("CICE", "CBEV"), ciclo_vida=False, cap=None, techs=None):
    """max N_CICE + N_CBEV  s.a. balance, horas <= H_FAB, recursos, CO2 <= co2_max.
    Las actividades de servicio (PKM) y la producción de bus/tram/infra se anulan."""
    cap = cap or CAP_FAB
    nv = NA
    c = np.zeros(nv)
    finales = {g: BASE[g] for g in ("CICE", "CBEV")}
    for g, k in finales.items():
        c[k] = -1.0 if g in tipos else 0.0
    A_ub, b_ub = [], []
    for i in range(NB):
        A_ub.append(-B[i]); b_ub.append(0.0)
    for r_i, r in enumerate(RECURSOS):
        A_ub.append(R[r_i]); b_ub.append(cap[r])
    A_ub.append(H.copy()); b_ub.append(H_FAB)
    nombres = ["HORAS"]
    if co2_max is not None:
        fila_c = C.copy()
        if ciclo_vida:
            for g, k in finales.items():
                fila_c[k] += CO2_USO[g]
        A_ub.append(fila_c); b_ub.append(co2_max); nombres.append("CO2")
    bounds = [(0, None)] * nv
    for k in PK:
        bounds[k] = (0, 0)
    for g in ("BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"):
        for k, a in enumerate(A_):
            if a["bien"] == g:
                bounds[k] = (0, 0)
    for g, k in finales.items():
        if g not in tipos:
            bounds[k] = (0, 0)
    if techs is not None:   # restringir técnicas permitidas (ids)
        for k, a in enumerate(A_[:N_PROD]):
            alts = [aa for aa in A_[:N_PROD] if aa["bien"] == a["bien"]]
            if len(alts) > 1 and a["id"] not in techs:
                bounds[k] = (0, 0)
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
    if res.status != 0:
        return None
    du = -res.ineqlin.marginals
    z = res.x
    co2_p = float(C @ z)
    n = {g: z[k] for g, k in finales.items()}
    return dict(z=z, n=n, N=sum(n.values()), co2=co2_p,
                co2_vida=co2_p + sum(n[g] * CO2_USO[g] for g in n),
                horas=float(H @ z), dual=dict(zip(RECURSOS + nombres, du[NB:])),
                tec={a["id"]: z[k] for k, a in enumerate(A_[:N_PROD])})


BASE_IDS = {A_[k]["id"] for k in BASE.values()}
fab = {}
fab["base_ice"] = max_coches(tipos=("CICE",), techs=BASE_IDS)            # Leontief puro
fab["opt_ice"] = max_coches(tipos=("CICE",))                             # con técnicas alternativas
fab["opt_bev"] = max_coches(tipos=("CBEV",))
fab["opt_mix"] = max_coches()
# Máximo de coches con techo de CO2 de producción decreciente
CO2_REF_FAB = fab["base_ice"]["co2"]
fab_sens = []
for f in [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25]:
    r = max_coches(co2_max=f * CO2_REF_FAB, tipos=("CICE",))
    fab_sens.append((f, f * CO2_REF_FAB, r))
# Con CO2 de ciclo de vida (fabricación + 180.000 km de uso)
CO2_VIDA_REF = fab["base_ice"]["co2_vida"]
fab_vida = []
for f in [1.0, 0.7, 0.5, 0.35, 0.25]:
    r = max_coches(co2_max=f * CO2_VIDA_REF, ciclo_vida=True)
    fab_vida.append((f, f * CO2_VIDA_REF, r))

if __name__ == "__main__":
    np.set_printoptions(suppress=True, linewidth=180)
    print(f"D = {D:,.0f} mil pkm/año  ({D / HAB:,.0f} mil pkm/hab)")
    print("\nHORAS: ensamblaje final l, total v (base), total v (limpia); CO2 e base, e limpia")
    for g in ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG", "BAT", "MEL", "AUT", "ACE", "ALU", "ELE", "HOR"]:
        i = IX[g]
        print(f"  {g:5s} l={l0[i]:10.2f} v0={v0[i]:12.2f} v1={v1[i]:12.2f} e0={e0[i]:10.3f} e1={e1[i]:10.3f}")
    print("\nMODOS")
    for k, m in MODOS.items():
        print(f"  {k:5s} eta_e={m['eta_e']:.2f} eta_o={m['eta_o']:.3f} eta_m={m['eta_m']:.4f} util={m['eta_util']:.4f} "
              f"triple={m['eta_triple']:.5f} kWh/pkm={m['kwh_pkm']:.3f} h/kpkm={m['h_tot']:.2f} "
              f"(veh {m['h_veh']:.2f} inf {m['h_inf']:.2f} ene {m['h_ene']:.2f} op {m['h_oper']:.2f}) "
              f"CO2 kg/pkm={m['c_tot']:.4f} (veh {m['c_veh']:.4f} inf {m['c_inf']:.4f} ene {m['c_ene']:.4f})")
    print("\nTECNICAS")
    for t in comp_tec:
        print(f"  {t['bien']:4s} {t['nombre']:45s} v={t['v']:10.3f} e={t['e']:10.4f}")
    print("\nESCENARIOS")
    for k, nom, s in ESCENARIOS:
        ii = IND[k]
        sh = {m: round(100 * ii["pkm"][m] / ii["tot"], 1) for m in MODOS}
        print(f"  {k:5s} h={ii['horas']:14,.0f} co2={ii['co2']:12,.0f} E={ii['energia']:12,.0f} share={sh} "
              f"flota={ {m: round(v) for m, v in ii['flota'].items()} } via={ii['infra']['VIA']:.1f} mar={ii['infra']['MAR']:.0f}")
        print(f"        duales rec={ {r: round(v, 3) for r, v in s['rec_dual'].items()} } extra={ {r: round(v, 3) for r, v in s['extra_dual'].items()} }")
        print(f"        tec act: {[t for t, v in ii['tec'].items() if v > 1e-6 and t in ('ace_bof','ace_eaf','ace_h2','alu_p','alu_s','ele_t','ele_r','hor_c','hor_lc3','biw_a','biw_m')]}  h_inicial={ii['h_inicial']:,.0f}")
    print("\nMAX pkm con recursos de ref:", sol_max["t"] / D, IND_MAX["pkm"])
    print("\nPARETO")
    for p in pareto:
        print(f"  co2={p['co2']:12,.0f} h={p['horas']:14,.0f} mu={p['mu']:.3f} pkm={ {m: round(v / D * 100, 1) for m, v in p['pkm'].items()} }")
    print("\nFABRICA")
    for k, r in fab.items():
        print(f"  {k:9s} N={r['N']:10,.0f} n={ {g: round(v) for g, v in r['n'].items()} } co2={r['co2']:12,.0f} vida={r['co2_vida']:14,.0f} dual={ {a: round(b, 3) for a, b in r['dual'].items()} }")
    for f, cmax, r in fab_sens:
        print(f"  sens prod {f:.2f} {cmax:12,.0f} -> {r['N'] if r else None}")
    for f, cmax, r in fab_vida:
        print(f"  sens vida {f:.2f} {cmax:14,.0f} -> {(r['N'], {g: round(v) for g, v in r['n'].items()}) if r else None}")
    print("CO2_USO", CO2_USO)

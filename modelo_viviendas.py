"""
Planificación de 1.000.000 de viviendas en España:
  Caso A: viviendas de 70 m² útiles con cocina.
  Caso B: viviendas de 62 m² útiles sin cocina + comedores comunales para toda la población residente.
Leontief (materiales y horas), Kantorovich (métodos constructivos, máxima producción, ubicación de fábricas,
transporte), algoritmos de localización de comedores (MILP, voraz, k-medias) y método del taller.
Datos ilustrativos con órdenes de magnitud del sector.
"""
import math
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from scipy import sparse

# =============================================================================
# 0. BIENES
# =============================================================================
BIENES = [
    ("FE", "Mineral de hierro", "t", "Extracción"), ("BAU", "Bauxita", "t", "Extracción"),
    ("CUC", "Concentrado de cobre", "t", "Extracción"), ("CRU", "Petróleo y gas", "t", "Extracción"),
    ("SIL", "Arena y áridos", "t", "Extracción"), ("CAR", "Carbón y coque de petróleo", "t", "Extracción"),
    ("CAL", "Caliza y arcilla", "t", "Extracción"), ("YES", "Yeso natural", "t", "Extracción"),
    ("MDR", "Madera en rollo (bosque gestionado)", "m³", "Extracción"),
    ("ELE", "Electricidad", "MWh", "Energía"), ("DIE", "Gasóleo", "t", "Energía"),
    ("CEM", "Cemento", "t", "Materiales"), ("HOR", "Hormigón", "t", "Materiales"),
    ("ACE", "Acero (corrugado, perfiles, chapa)", "t", "Materiales"), ("ALU", "Aluminio", "t", "Materiales"),
    ("COB", "Cobre", "t", "Materiales"), ("POL", "Plásticos (PVC, PE, pinturas)", "t", "Materiales"),
    ("VID", "Vidrio", "t", "Materiales"), ("CER", "Cerámica (ladrillo, teja, azulejo, sanitarios)", "t", "Materiales"),
    ("YSO", "Yeso y placa de yeso", "t", "Materiales"), ("AIS", "Aislamiento (lana mineral)", "t", "Materiales"),
    ("MAD", "Madera técnica (CLT, tablero)", "m³", "Materiales"),
    ("INS", "Instalaciones de vivienda (electricidad, agua, saneamiento, aerotermia)", "ud", "Componentes"),
    ("CRP", "Carpinterías exteriores (aluminio RPT + doble vidrio)", "ud", "Componentes"),
    ("BAN", "Baño completo", "ud", "Componentes"),
    ("COC", "Cocina equipada (muebles + electrodomésticos)", "ud", "Componentes"),
    ("ACB", "Acabados (suelos, puertas, pintura)", "ud", "Componentes"),
    ("ASC", "Ascensor", "ud", "Componentes"),
    ("URB", "Urbanización y redes (por vivienda)", "ud", "Componentes"),
    ("EQC", "Equipamiento de comedor (cocina industrial + mobiliario, por plaza)", "plaza", "Componentes"),
    ("VIVA", "Vivienda A: 70 m² útiles con cocina", "ud", "Productos"),
    ("VIVB", "Vivienda B: 62 m² útiles sin cocina", "ud", "Productos"),
    ("PLZ", "Plaza de comedor comunal", "plaza", "Productos"),
]
COD = [b[0] for b in BIENES]; IX = {c: i for i, c in enumerate(COD)}; NB = len(BIENES)
NOMBRE = {b[0]: b[1] for b in BIENES}; UNIDAD = {b[0]: b[2] for b in BIENES}; ESC = {b[0]: b[3] for b in BIENES}
ESCALONES = ["Extracción", "Energía", "Materiales", "Componentes", "Productos"]

A_ = []


def act(id_, nombre, bien, ins, h, co2, rec=None, nota=""):
    A_.append(dict(id=id_, nombre=nombre, bien=bien, ins=ins, h=h, co2=co2, rec=rec or {}, nota=nota))


# --- extracción y energía
act("fe", "Minería de hierro", "FE", {"ELE": 0.02}, 0.15, 0.010)
act("bau", "Minería de bauxita", "BAU", {"ELE": 0.01}, 0.20, 0.008)
act("cuc", "Minería de cobre", "CUC", {"ELE": 0.80}, 2.00, 0.050)
act("cru", "Petróleo y gas", "CRU", {"ELE": 0.05}, 0.10, 0.150)
act("sil", "Canteras de áridos", "SIL", {"ELE": 0.004, "DIE": 0.0008}, 0.04, 0.002)
act("car", "Carbón y coque", "CAR", {"ELE": 0.03}, 0.40, 0.060)
act("cal", "Canteras de caliza y arcilla", "CAL", {"ELE": 0.004, "DIE": 0.0008}, 0.04, 0.002)
act("yes", "Canteras de yeso", "YES", {"ELE": 0.004, "DIE": 0.0008}, 0.06, 0.002)
act("mdr", "Aprovechamiento forestal sostenible", "MDR", {"DIE": 0.003}, 0.60, 0.0, {"BOSQUE": 1.0},
    "limitado por la corta sostenible disponible para el programa")
act("ele_t", "Electricidad térmica", "ELE", {"ELE": 0.06, "CAR": 0.08, "CRU": 0.04}, 0.20, 0.20)
act("ele_r", "Electricidad renovable", "ELE", {}, 0.35, 0.0)
act("die", "Refino de gasóleo", "DIE", {"CRU": 1.10, "ELE": 0.25}, 0.60, 0.35)
# --- materiales
act("cem_p", "Cemento Portland (clínker 90 %)", "CEM", {"CAL": 1.55, "CAR": 0.10, "ELE": 0.11}, 0.40, 0.75, {"CEMENTO": 1.0})
act("cem_b", "Cemento bajo en clínker (LC3: 50 % clínker + arcilla calcinada)", "CEM", {"CAL": 1.30, "CAR": 0.07, "ELE": 0.12}, 0.45, 0.45, {"CEMENTO": 1.0})
act("hor_n", "Hormigón con árido natural (300 kg cemento/m³)", "HOR", {"CEM": 0.13, "SIL": 0.82, "ELE": 0.005, "DIE": 0.001}, 0.25, 0.002)
act("hor_r", "Hormigón con árido reciclado de demolición", "HOR", {"CEM": 0.135, "SIL": 0.40, "ELE": 0.008, "DIE": 0.0015}, 0.27, 0.002, {},
    "máx. 30 % del hormigón (disponibilidad de residuo de demolición)")
act("ace_bof", "Acero integral (alto horno)", "ACE", {"FE": 1.60, "CAR": 0.75, "ELE": 0.45}, 2.50, 1.75)
act("ace_eaf", "Acero de horno eléctrico con chatarra", "ACE", {"ELE": 0.60}, 1.80, 0.08, {}, "máx. 70 % del acero (el corrugado ya es casi todo EAF)")
act("alu_p", "Aluminio primario", "ALU", {"BAU": 4.40, "ELE": 15.0, "CAR": 0.45}, 6.00, 1.60)
act("alu_s", "Aluminio reciclado", "ALU", {"ELE": 0.80, "CRU": 0.05}, 3.00, 0.30, {}, "máx. 55 %")
act("cob", "Cobre", "COB", {"CUC": 4.0, "ELE": 3.5}, 8.0, 0.40)
act("pol", "Plásticos", "POL", {"CRU": 1.8, "ELE": 1.5}, 3.0, 0.90)
act("vid", "Vidrio", "VID", {"SIL": 1.2, "ELE": 0.5, "CRU": 0.12}, 4.0, 0.45)
act("cer", "Cerámica cocida", "CER", {"CAL": 1.15, "ELE": 0.06, "CRU": 0.05}, 1.5, 0.18)
act("yso", "Yeso y placa de yeso", "YSO", {"YES": 1.0, "ELE": 0.05, "CRU": 0.02}, 0.8, 0.06)
act("ais", "Lana mineral", "AIS", {"SIL": 1.1, "ELE": 1.2, "CRU": 0.10}, 4.0, 0.60)
act("mad", "Madera contralaminada y tablero", "MAD", {"MDR": 2.0, "ELE": 0.15, "POL": 0.01}, 3.0, 0.03)
# --- componentes (horas = fabricación industrial; la instalación en obra va en la vivienda)
act("ins", "Instalaciones: electricidad, fontanería, saneamiento, ventilación, aerotermia", "INS",
    {"COB": 0.06, "POL": 0.08, "ACE": 0.05, "ALU": 0.01, "ELE": 0.2}, 55.0, 0)
act("crp", "Ventanas y balconeras de aluminio con rotura de puente térmico", "CRP", {"ALU": 0.12, "VID": 0.25, "POL": 0.01, "ELE": 0.05}, 40.0, 0)
act("ban", "Baño: sanitarios, grifería, alicatado, plato de ducha", "BAN", {"CER": 0.25, "COB": 0.005, "POL": 0.02, "ACE": 0.01, "ELE": 0.05}, 18.0, 0)
act("coc", "Cocina: muebles, encimera, placa, horno, frigorífico, lavavajillas, campana", "COC",
    {"MAD": 0.35, "ACE": 0.12, "ALU": 0.01, "COB": 0.012, "POL": 0.04, "VID": 0.02, "CER": 0.10, "ELE": 1.2}, 55.0, 0)
act("acb", "Acabados: pavimento cerámico, puertas, pintura, falsos techos", "ACB", {"CER": 1.75, "MAD": 0.25, "POL": 0.08, "YSO": 0.20, "ELE": 0.1}, 30.0, 0)
act("asc", "Ascensor (6 paradas)", "ASC", {"ACE": 4.0, "COB": 0.3, "ALU": 0.2, "POL": 0.2, "ELE": 2.0}, 900.0, 0)
act("urb", "Urbanización, viales y redes (parte por vivienda)", "URB", {"HOR": 6.0, "ACE": 0.1, "POL": 0.15, "COB": 0.02, "SIL": 10.0, "DIE": 0.15}, 120.0, 0.47)
act("eqc", "Cocina industrial de inox, cámaras, lavavajillas de túnel, mesas y sillas (por plaza)", "EQC",
    {"ACE": 0.08, "COB": 0.01, "POL": 0.02, "MAD": 0.03, "ELE": 0.3}, 25.0, 0)
N_COMP = len(A_)

# --- métodos constructivos: intensidades por m² construido
M2C = {"VIVA": 84.0, "VIVB": 74.0}           # m² construidos (útiles + muros + zonas comunes)
INST_H = {"VIVA": 420.0, "VIVB": 360.0}      # horas de instalación y acabado en obra (método tradicional)
COMUNES = {"VIVA": {"INS": 1, "CRP": 1, "BAN": 1.2, "COC": 1, "ACB": 1, "ASC": 1 / 20, "URB": 1},
           "VIVB": {"INS": 0.85, "CRP": 1, "BAN": 1.2, "ACB": 0.9, "ASC": 1 / 20, "URB": 1}}
METODOS = {
    #        materiales por m²,                                             obra h/m², fábrica h/m², factor instalación, parte en obra, impresora h/m², CO2 obra t/m²
    "trad": ("Tradicional: estructura de hormigón armado in situ + fábrica de ladrillo",
             {"HOR": 0.84, "ACE": 0.035, "CER": 0.25, "YSO": 0.03, "AIS": 0.004, "DIE": 0.0012}, 9.0, 0.0, 1.00, 1.00, 0.0, 0.004),
    "pref": ("Prefabricado 2D: paneles portantes de hormigón fabricados en taller",
             {"HOR": 0.80, "ACE": 0.032, "CER": 0.05, "YSO": 0.02, "AIS": 0.005, "DIE": 0.0009}, 3.8, 2.6, 0.90, 0.90, 0.0, 0.003),
    "mod": ("Modular 3D: módulos volumétricos de acero terminados en fábrica",
            {"HOR": 0.45, "ACE": 0.055, "YSO": 0.035, "AIS": 0.006, "MAD": 0.01, "DIE": 0.0005}, 1.2, 4.0, 0.75, 0.30, 0.0, 0.002),
    "lsf": ("Entramado ligero de acero (LSF) en paneles",
            {"HOR": 0.35, "ACE": 0.045, "YSO": 0.05, "AIS": 0.008, "MAD": 0.005, "DIE": 0.0007}, 3.0, 2.0, 0.85, 0.80, 0.0, 0.002),
    "clt": ("Madera contralaminada (CLT) sobre zócalo de hormigón",
            {"HOR": 0.30, "ACE": 0.015, "YSO": 0.05, "AIS": 0.007, "MAD": 0.35, "DIE": 0.0007}, 2.6, 2.2, 0.85, 0.80, 0.0, 0.002),
    "imp": ("Impresión 3D de muros de hormigón in situ",
            {"HOR": 0.95, "ACE": 0.025, "YSO": 0.02, "AIS": 0.005, "DIE": 0.0012}, 6.0, 0.0, 1.00, 1.00, 0.15, 0.004),
}
ACT_VIV = {}
for tipo in ("VIVA", "VIVB"):
    m2 = M2C[tipo]
    for mid, (nom, mat, h_ob, h_fab, f_inst, share_obra, imp, co2m2) in METODOS.items():
        ins = {g: q * m2 for g, q in mat.items()}
        for g, q in COMUNES[tipo].items():
            ins[g] = ins.get(g, 0) + q
        inst = INST_H[tipo] * f_inst
        h_obra = h_ob * m2 + inst * share_obra
        h_fab_t = h_fab * m2 + inst * (1 - share_obra)
        act(f"{tipo.lower()}_{mid}", nom, tipo, ins, h_obra + h_fab_t, co2m2 * m2,
            {"HOBRA": h_obra, "HFAB": h_fab_t, "IMPR": imp * m2})
        ACT_VIV[(tipo, mid)] = len(A_) - 1
# --- plaza de comedor: 2,2 m² construidos por plaza (sala, cocina, cámaras, almacén)
M2_PLAZA = 2.2
for mid in ("trad", "mod"):
    nom, mat, h_ob, h_fab, _, _, _, co2m2 = METODOS[mid]
    ins = {g: q * M2_PLAZA for g, q in mat.items()}
    ins["EQC"] = 1
    act(f"plz_{mid}", f"Plaza de comedor, edificio {('tradicional' if mid == 'trad' else 'modular')}", "PLZ", ins,
        (h_ob + h_fab) * M2_PLAZA + 6, co2m2 * M2_PLAZA, {"HOBRA": h_ob * M2_PLAZA + 6, "HFAB": h_fab * M2_PLAZA})
NA = len(A_)
ID = {a["id"]: k for k, a in enumerate(A_)}
CUOTAS = [("ace_eaf", "ACE", 0.70), ("alu_s", "ALU", 0.55), ("hor_r", "HOR", 0.30)]
RECURSOS = ["HOBRA", "HFAB", "IMPR", "CEMENTO", "BOSQUE"]

B = np.zeros((NB, NA)); H = np.zeros(NA); C = np.zeros(NA); R = np.zeros((len(RECURSOS), NA))
for k, a in enumerate(A_):
    B[IX[a["bien"]], k] += 1
    for g, q in a["ins"].items():
        B[IX[g], k] -= q
    H[k] = a["h"]; C[k] = a["co2"]
    for r, q in a["rec"].items():
        R[RECURSOS.index(r), k] = q
# CO2 del gasóleo quemado en obra (3,17 t/t) ya imputado en co2m2; el del refino va en DIE.
BASE = {}
for k, a in enumerate(A_):
    BASE.setdefault(a["bien"], k)


def leontief(z=None, forzar=None):
    """Leontief con la mezcla de técnicas de z, o forzando una actividad concreta para ciertos bienes."""
    A = np.zeros((NB, NB)); l = np.zeros(NB); d = np.zeros(NB); rr = np.zeros((len(RECURSOS), NB))
    for g in set(a["bien"] for a in A_):
        ks = [k for k, a in enumerate(A_) if a["bien"] == g]
        if forzar and g in forzar:
            pesos = {forzar[g]: 1.0}
        elif z is None or z[ks].sum() < 1e-12:
            pesos = {BASE[g]: 1.0}
        else:
            t = z[ks].sum(); pesos = {k: z[k] / t for k in ks if z[k] > 1e-14}
        j = IX[g]
        for k, w in pesos.items():
            for gi, q in A_[k]["ins"].items():
                A[IX[gi], j] += w * q
            l[j] += w * H[k]; d[j] += w * C[k]; rr[:, j] += w * R[:, k]
    L = np.linalg.inv(np.eye(NB) - A)
    return dict(A=A, L=L, l=l, d=d, v=l @ L, e=d @ L, rec=rr @ L)


LB = leontief()
RHO = max(abs(np.linalg.eigvals(LB["A"])))
MU = 3.0


def lp(obj=None, y=None, maxdir=None, caps=None, h_max=None, co2_max=None, excluir=None, solo=None):
    nv = NA + (1 if maxdir is not None else 0)

    def fila(v, t=0.0):
        r = np.zeros(nv); r[:NA] = v
        if maxdir is not None:
            r[-1] = t
        return r
    Au, bu, nom = [], [], []
    yv = np.zeros(NB) if y is None else y
    for i in range(NB):
        if maxdir is not None:
            Au.append(fila(-B[i], maxdir[i])); bu.append(0.0)
        else:
            Au.append(fila(-B[i])); bu.append(-yv[i])
        nom.append("BAL_" + COD[i])
    for tec, g, s in CUOTAS:
        v = np.zeros(NA)
        for k, a in enumerate(A_):
            if a["bien"] == g:
                v[k] = -s
        v[ID[tec]] += 1
        Au.append(fila(v)); bu.append(0.0); nom.append("CUOTA_" + tec)
    if caps:
        for ri, r in enumerate(RECURSOS):
            if caps.get(r) is not None:
                Au.append(fila(R[ri])); bu.append(caps[r]); nom.append(r)
    if h_max is not None:
        Au.append(fila(H)); bu.append(h_max); nom.append("HORAS")
    if co2_max is not None:
        Au.append(fila(C)); bu.append(co2_max); nom.append("CO2")
    bounds = [(0, None)] * nv
    for t in (excluir or []):
        bounds[ID[t]] = (0, 0)
    if solo:   # forzar un único método constructivo de vivienda
        for (tipo, mid), k in ACT_VIV.items():
            if mid != solo:
                bounds[k] = (0, 0)
    c = np.zeros(nv)
    if maxdir is not None:
        c[-1] = -1
    else:
        c[:NA] = obj
    r = linprog(c, A_ub=np.array(Au), b_ub=np.array(bu), bounds=bounds, method="highs")
    if r.status != 0:
        return None
    du = -r.ineqlin.marginals
    z = r.x[:NA]
    return dict(z=z, t=r.x[-1] if maxdir is not None else None, dual=dict(zip(nom, du)), horas=float(H @ z), co2=float(C @ z),
                rec={RECURSOS[i]: float(R[i] @ z) for i in range(len(RECURSOS))})


# =============================================================================
# 1. COMPARACIÓN DE MÉTODOS POR VIVIENDA (Leontief con cada método)
# =============================================================================
COMP_MET = {}
for tipo in ("VIVA", "VIVB"):
    for mid in METODOS:
        lm = leontief(forzar={tipo: ACT_VIV[(tipo, mid)]})
        j = IX[tipo]
        COMP_MET[(tipo, mid)] = dict(v=lm["v"][j], e=lm["e"][j], obra=lm["rec"][0, j], fab=lm["rec"][1, j], impr=lm["rec"][2, j],
                                     cem=lm["L"][IX["CEM"], j], mdr=lm["L"][IX["MDR"], j], lm=lm,
                                     mat={g: lm["L"][IX[g], j] for g in ["HOR", "CEM", "ACE", "CER", "MAD", "YSO", "AIS", "ALU", "COB", "VID", "POL", "SIL", "ELE"]})

# =============================================================================
# 2. KANTOROVICH NACIONAL: máxima producción anual
# =============================================================================
N_VIV = 1_000_000
ANIOS = 5
CAP = {"HOBRA": 330e6,      # 200.000 trabajadores de obra × 1.650 h
       "HFAB": 70e6,        # ≈42.000 empleos en fábricas de construcción industrializada
       "IMPR": 1.0e6,       # 290 impresoras 3D × 3.450 h
       "CEMENTO": 9.0e6,    # t de cemento al año disponibles para el programa
       "BOSQUE": 2.0e6}     # m³ de madera en rollo al año para el programa
PLZ_POR_VIV = 2.5 * 1.05 / 3    # 2,5 personas, 5 % de margen, 3 turnos por servicio
yA = np.zeros(NB); yA[IX["VIVA"]] = 1
yB = np.zeros(NB); yB[IX["VIVB"]] = 1; yB[IX["PLZ"]] = PLZ_POR_VIV
MAXP = {"A": lp(maxdir=yA, caps=CAP), "B": lp(maxdir=yB, caps=CAP)}
MAXP_SOLO = {(c, mid): lp(maxdir=(yA if c == "A" else yB), caps=CAP, solo=mid) for c in ("A", "B") for mid in METODOS}
# segunda etapa: con la producción máxima fija, mínimo CO2 (lexicográfico)
MAXP_CO2 = {c: lp(C + 1e-7 * H, (yA if c == "A" else yB) * MAXP[c]["t"] * 0.9999, caps=CAP) for c in ("A", "B")}

# plan anual de 200.000 viviendas: métodos según objetivo
Q_ANUAL = N_VIV / ANIOS
PLAN = {}
for c, y in (("A", yA), ("B", yB)):
    yy = y * Q_ANUAL
    PLAN[c] = {"h": lp(H, yy, caps=CAP), "c": lp(C + 1e-7 * H, yy, caps=CAP), "comp": lp(H + MU * C, yy, caps=CAP)}
    PLAN[c]["base"] = lp(H, yy, caps={**CAP, "HOBRA": None}, excluir=[a["id"] for k, a in enumerate(A_) if BASE[a["bien"]] != k])

PARETO = {}
for c, y in (("A", yA), ("B", yB)):
    yy = y * Q_ANUAL
    lo, hi = PLAN[c]["c"]["co2"], PLAN[c]["h"]["co2"]
    PARETO[c] = []
    for fr in [0, 0.05, 0.15, 0.3, 0.5, 0.75, 1.0]:
        s = lp(H, yy, caps=CAP, co2_max=lo + fr * (hi - lo) + 1)
        if s:
            PARETO[c].append(dict(co2=s["co2"], horas=s["horas"], mu=s["dual"].get("CO2", 0),
                                  mix={mid: s["z"][ACT_VIV[("VIV" + c, mid)]] for mid in METODOS}))


def mezcla_viv(z, tipo):
    tot = sum(z[ACT_VIV[(tipo, m)]] for m in METODOS)
    return {m: z[ACT_VIV[(tipo, m)]] / tot for m in METODOS if z[ACT_VIV[(tipo, m)]] / tot > 1e-4}


# =============================================================================
# 3. PROVINCIAS: reparto de viviendas y ubicación de fábricas (problema de transporte)
# =============================================================================
PROV = [  # nombre, población (miles, aprox. 2024), superficie km², lat, lon, isla/territorio aparte
    ("Madrid", 7000, 8028, 40.42, -3.70, ""), ("Barcelona", 5840, 7726, 41.39, 2.17, ""), ("Valencia", 2710, 10806, 39.47, -0.38, ""),
    ("Alicante", 1960, 5817, 38.35, -0.48, ""), ("Sevilla", 1960, 14036, 37.39, -5.98, ""), ("Málaga", 1750, 7308, 36.72, -4.42, ""),
    ("Murcia", 1570, 11313, 37.99, -1.13, ""), ("Cádiz", 1250, 7436, 36.53, -6.29, ""), ("Illes Balears", 1230, 4992, 39.57, 2.65, "BAL"),
    ("Las Palmas", 1160, 4066, 28.12, -15.43, "CAN"), ("Bizkaia", 1160, 2217, 43.26, -2.93, ""), ("S.C. Tenerife", 1080, 3381, 28.47, -16.25, "CAN"),
    ("A Coruña", 1130, 7950, 43.36, -8.41, ""), ("Asturias", 1010, 10604, 43.36, -5.85, ""), ("Zaragoza", 990, 17274, 41.65, -0.89, ""),
    ("Pontevedra", 950, 4495, 42.43, -8.65, ""), ("Granada", 930, 12647, 37.18, -3.60, ""), ("Tarragona", 850, 6303, 41.12, 1.25, ""),
    ("Córdoba", 770, 13771, 37.89, -4.78, ""), ("Girona", 800, 5910, 41.98, 2.82, ""), ("Gipuzkoa", 730, 1980, 43.32, -1.98, ""),
    ("Toledo", 720, 15370, 39.86, -4.02, ""), ("Almería", 760, 8775, 36.84, -2.46, ""), ("Badajoz", 670, 21766, 38.88, -6.97, ""),
    ("Navarra", 680, 10391, 42.81, -1.64, ""), ("Jaén", 620, 13496, 37.78, -3.79, ""), ("Cantabria", 590, 5321, 43.46, -3.80, ""),
    ("Castellón", 600, 6632, 39.99, -0.05, ""), ("Huelva", 530, 10128, 37.26, -6.95, ""), ("Valladolid", 520, 8110, 41.65, -4.72, ""),
    ("Ciudad Real", 490, 19813, 38.99, -3.93, ""), ("León", 450, 15581, 42.60, -5.57, ""), ("Lleida", 450, 12172, 41.62, 0.62, ""),
    ("Cáceres", 390, 19868, 39.48, -6.37, ""), ("Albacete", 390, 14926, 38.99, -1.86, ""), ("Burgos", 360, 14292, 42.34, -3.70, ""),
    ("Salamanca", 330, 12350, 40.97, -5.66, ""), ("Lugo", 325, 9856, 43.01, -7.56, ""), ("Ourense", 305, 7273, 42.34, -7.86, ""),
    ("La Rioja", 325, 5045, 42.47, -2.45, ""), ("Araba/Álava", 335, 3037, 42.85, -2.67, ""), ("Guadalajara", 275, 12214, 40.63, -3.17, ""),
    ("Huesca", 225, 15636, 42.14, -0.41, ""), ("Cuenca", 200, 17141, 40.07, -2.13, ""), ("Zamora", 165, 10561, 41.50, -5.75, ""),
    ("Ávila", 160, 8050, 40.66, -4.70, ""), ("Palencia", 158, 8052, 42.01, -4.53, ""), ("Segovia", 155, 6923, 40.95, -4.12, ""),
    ("Teruel", 135, 14810, 40.34, -1.11, ""), ("Soria", 90, 10306, 41.76, -2.47, ""), ("Ceuta", 83, 19, 35.89, -5.32, "CEU"),
    ("Melilla", 85, 12, 35.29, -2.94, "MEL"),
]
NP = len(PROV)
POB = np.array([p[1] for p in PROV], float) * 1000
SUPP = np.array([p[2] for p in PROV], float)
VIV_PROV = N_VIV * POB / POB.sum()
DENS = POB / SUPP
SUP_TOTAL = SUPP.sum()


def dist_km(i, j):
    la1, lo1, la2, lo2 = map(math.radians, (PROV[i][3], PROV[i][4], PROV[j][3], PROV[j][4]))
    a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    d = 2 * 6371 * math.asin(math.sqrt(a)) * 1.25
    zi, zj = PROV[i][5], PROV[j][5]
    if zi != zj:          # cruce marítimo: penalización en km equivalentes de camión
        pen = {"BAL": 250, "CAN": 1400, "CEU": 150, "MEL": 250}
        d += pen.get(zi, 0) + pen.get(zj, 0)
    elif zi == "CAN" and i != j:
        d += 100
    return d


DIST = np.array([[dist_km(i, j) for j in range(NP)] for i in range(NP)])

# =============================================================================
# 4. LOCALIZACIÓN DE COMEDORES (MILP de localización con capacidad)
# =============================================================================
VEL_PIE = 4500.0           # m/h
PERS_VIV = 2.5
COMIDAS = 3
W_PASEO = 0.5              # peso del tiempo de paseo respecto a una hora de trabajo
H_PASEO_M = PERS_VIV * COMIDAS * 365 * 2 / VEL_PIE     # horas de paseo al año por vivienda y metro de distancia
FIJO_COM = 3 * 12 * 365.0  # h/año: equipo mínimo de 3 personas durante los servicios (12 h × 365)
MOD_PLZ = 50               # plazas por módulo de comedor
H_MOD = None               # se calcula con Leontief (edificio + equipo amortizados)
H_RACION = 0.06            # h de personal variable por ración (cocina, sala, friegue), además del equipo mínimo
REPARTO_H = 210.0          # h/año por vivienda servida a domicilio (rural disperso)
TIPOLOGIAS = {
    "denso": dict(nombre="Urbano denso", lado=1600, paso=100, ocup=0.62, viv=(50, 110), dmax=300, seed=1),
    "medio": dict(nombre="Urbano medio / ensanche", lado=3000, paso=150, ocup=0.45, viv=(24, 64), dmax=450, seed=2),
    "rural": dict(nombre="Rural (pueblos y diseminado)", lado=10000, paso=250, ocup=None, viv=(4, 24), dmax=1500, seed=3),
}


def generar(tip):
    rng = np.random.default_rng(tip["seed"])
    if tip["ocup"] is not None:
        n = tip["lado"] // tip["paso"]
        pts, viv = [], []
        c = tip["lado"] / 2
        for ix in range(n):
            for iy in range(n):
                x, y = (ix + 0.5) * tip["paso"], (iy + 0.5) * tip["paso"]
                dc = math.hypot(x - c, y - c) / c
                if rng.random() < tip["ocup"] * (1.25 - 0.5 * dc):
                    pts.append((x, y)); viv.append(int(rng.integers(*tip["viv"])))
        return np.array(pts), np.array(viv)
    # rural: 9 pueblos con calles en retícula + diseminado
    pts, viv = [], []
    centros = rng.uniform(800, tip["lado"] - 800, (9, 2))
    tam = rng.integers(6, 26, 9)
    for (cx, cy), t in zip(centros, tam):
        for _ in range(t):
            pts.append((cx + rng.normal(0, 180), cy + rng.normal(0, 180))); viv.append(int(rng.integers(*tip["viv"])))
    for _ in range(18):
        pts.append(tuple(rng.uniform(0, tip["lado"], 2))); viv.append(int(rng.integers(1, 4)))
    return np.array(pts), np.array(viv)


def coste_modulo():
    """horas/año de un módulo de 50 plazas: edificio y equipo amortizados (Leontief)."""
    lm = leontief(forzar={"PLZ": ID["plz_trad"]})
    j = IX["PLZ"]
    # edificio 50 años, equipo 15 años: separamos la parte de equipo
    v_eq = LB["v"][IX["EQC"]]
    return MOD_PLZ * ((lm["v"][j] - v_eq) / 50 + v_eq / 15)


H_MOD = coste_modulo()


def localizar(pts, viv, dmax, rural=False):
    """MILP: abrir comedores y asignar bloques. Variables: y_j (abre), m_j (módulos), x_ij (fracción), r_i (reparto)."""
    n = len(pts)
    D = np.abs(pts[:, None, 0] - pts[None, :, 0]) + np.abs(pts[:, None, 1] - pts[None, :, 1])   # distancia por calles (Manhattan)
    pares = [(i, j) for i in range(n) for j in range(n) if D[i, j] <= dmax]
    npar = len(pares)
    # índices: y (n), m (n), x (npar), r (n si rural)
    ny, nm, nx = n, n, npar
    nr = n if rural else 0
    nv = ny + nm + nx + nr
    c = np.zeros(nv)
    c[:ny] = FIJO_COM
    c[ny:ny + nm] = H_MOD
    for p, (i, j) in enumerate(pares):
        c[ny + nm + p] = W_PASEO * H_PASEO_M * D[i, j] * viv[i]
    if rural:
        c[ny + nm + nx:] = REPARTO_H * viv
    rows, cols, vals, lo, hi = [], [], [], [], []
    r = 0
    # asignación: sum_j x_ij + r_i = 1
    for p, (i, j) in enumerate(pares):
        rows.append(i); cols.append(ny + nm + p); vals.append(1)
    if rural:
        for i in range(n):
            rows.append(i); cols.append(ny + nm + nx + i); vals.append(1)
    lo += [1] * n; hi += [1] * n; r = n
    # capacidad: sum_i plz_i x_ij - 50 m_j <= 0
    for p, (i, j) in enumerate(pares):
        rows.append(r + j); cols.append(ny + nm + p); vals.append(viv[i] * PLZ_POR_VIV)
    for j in range(n):
        rows.append(r + j); cols.append(ny + j); vals.append(-MOD_PLZ)
    lo += [-np.inf] * n; hi += [0] * n; r += n
    # m_j <= 12 y_j
    for j in range(n):
        rows += [r + j, r + j]; cols += [ny + j, j]; vals += [1, -12]
    lo += [-np.inf] * n; hi += [0] * n; r += n
    # x_ij <= y_j  (enlace fuerte)
    for p, (i, j) in enumerate(pares):
        rows += [r + p, r + p]; cols += [ny + nm + p, j]; vals += [1, -1]
    lo += [-np.inf] * npar; hi += [0] * npar; r += npar
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(r, nv))
    integr = np.zeros(nv); integr[:ny + nm] = 1
    ub = np.full(nv, np.inf); ub[:ny] = 1; ub[ny:ny + nm] = 12
    if rural:   # reparto a domicilio sólo para el diseminado (bloques de 1 a 3 viviendas)
        for i in range(n):
            if viv[i] > 3:
                ub[ny + nm + nx + i] = 0
    res = milp(c, constraints=LinearConstraint(A, lo, hi), integrality=integr, bounds=Bounds(np.zeros(nv), ub),
               options={"time_limit": 120, "mip_rel_gap": 0.005})
    x = res.x
    abiertos = [j for j in range(n) if x[j] > 0.5]
    asign = {}
    for p, (i, j) in enumerate(pares):
        if x[ny + nm + p] > 0.5:
            asign[i] = j
    reparto = [i for i in range(n) if rural and x[ny + nm + nx + i] > 0.5]
    return dict(abiertos=abiertos, modulos={j: int(round(x[ny + j])) for j in abiertos}, asign=asign, reparto=reparto,
                obj=res.fun, D=D, gap=getattr(res, "mip_gap", None), estado=res.message)


def evaluar(pts, viv, abiertos, asign, D, reparto=()):
    """Horas/año de una solución: fijo + módulos + paseo; distancias."""
    carga = {j: 0.0 for j in abiertos}
    dist = []
    paseo = 0.0
    for i, j in asign.items():
        carga[j] += viv[i] * PLZ_POR_VIV
        dist += [D[i, j]] * int(viv[i])
        paseo += H_PASEO_M * D[i, j] * viv[i]
    mods = {j: math.ceil(carga[j] / MOD_PLZ - 1e-9) for j in abiertos}
    h_inst = FIJO_COM * len(abiertos) + H_MOD * sum(mods.values())
    h_rep = REPARTO_H * sum(viv[i] for i in reparto)
    return dict(n=len(abiertos), plazas=sum(mods.values()) * MOD_PLZ, h_inst=h_inst, paseo=paseo, h_rep=h_rep,
                obj=h_inst + W_PASEO * paseo + h_rep, dmed=float(np.mean(dist)) if dist else 0, dmax=float(max(dist)) if dist else 0,
                viv=int(viv.sum()))


def voraz(pts, viv, dmax):
    """Heurística voraz: abrir el comedor que más bloques sin cubrir alcanza, hasta cubrirlos todos;
    después asignar cada bloque al comedor abierto más cercano."""
    n = len(pts)
    D = np.abs(pts[:, None, 0] - pts[None, :, 0]) + np.abs(pts[:, None, 1] - pts[None, :, 1])
    sin = set(range(n)); abiertos = []
    while sin:
        mejor = max(range(n), key=lambda j: sum(viv[i] for i in sin if D[i, j] <= dmax))
        abiertos.append(mejor)
        sin -= {i for i in sin if D[i, mejor] <= dmax}
    asign = {i: min(abiertos, key=lambda j: D[i, j]) for i in range(n)}
    return abiertos, asign, D


def kmedias(pts, viv, k, iters=60, seed=0):
    """k-medias ponderado por viviendas; cada centro se lleva al bloque más cercano (planta baja disponible)."""
    rng = np.random.default_rng(seed)
    cen = pts[rng.choice(len(pts), k, replace=False, p=viv / viv.sum())].astype(float)
    for _ in range(iters):
        lab = np.argmin(np.abs(pts[:, None, :] - cen[None, :, :]).sum(-1), axis=1)
        for c in range(k):
            m = lab == c
            if m.any():
                cen[c] = np.average(pts[m], axis=0, weights=viv[m])
    D = np.abs(pts[:, None, 0] - pts[None, :, 0]) + np.abs(pts[:, None, 1] - pts[None, :, 1])
    abiertos = sorted({int(np.argmin(np.abs(pts - c).sum(1))) for c in cen})
    asign = {i: min(abiertos, key=lambda j: D[i, j]) for i in range(len(pts))}
    return abiertos, asign, D


LOC = {}
for key, tip in TIPOLOGIAS.items():
    pts, viv = generar(tip)
    rural = key == "rural"
    sol = localizar(pts, viv, tip["dmax"], rural=rural)
    ev_milp = evaluar(pts, viv, sol["abiertos"], sol["asign"], sol["D"], sol["reparto"])
    ab_v, as_v, Dv = voraz(pts, viv, tip["dmax"])
    ev_vor = evaluar(pts, viv, ab_v, as_v, Dv)
    ab_k, as_k, Dk = kmedias(pts, viv, max(1, len(sol["abiertos"])))
    ev_km = evaluar(pts, viv, ab_k, as_k, Dk)
    # solución ingenua: un único gran comedor central (sin límite de distancia)
    cen = int(np.argmin(np.abs(pts - np.average(pts, axis=0, weights=viv)).sum(1)))
    D1 = np.abs(pts[:, None, 0] - pts[None, :, 0]) + np.abs(pts[:, None, 1] - pts[None, :, 1])
    ev_1 = evaluar(pts, viv, [cen], {i: cen for i in range(len(pts))}, D1)
    LOC[key] = dict(tip=tip, pts=pts, viv=viv, sol=sol, milp=ev_milp, voraz=ev_vor, kmedias=ev_km, uno=ev_1,
                    voraz_sol=(ab_v, as_v), km_sol=(ab_k, as_k))

# reparto nacional de tipologías según densidad provincial (hab/km²)
SH = np.zeros((NP, 3))
for i, d in enumerate(DENS):
    den = np.clip((d - 100) / 900, 0, 0.85)
    rur = np.clip((150 - d) / 150, 0.05, 0.60)
    if d > 3000:       # ciudades autónomas
        den, rur = 0.9, 0.0
    SH[i] = [den, 1 - den - rur, rur]
TASA = {k: dict(com_por_mil=1000 * LOC[k]["milp"]["n"] / LOC[k]["milp"]["viv"],
                plz_por_viv=LOC[k]["milp"]["plazas"] / LOC[k]["milp"]["viv"],
                dmed=LOC[k]["milp"]["dmed"],
                rep=sum(LOC[k]["viv"][i] for i in LOC[k]["sol"]["reparto"]) / LOC[k]["milp"]["viv"]) for k in TIPOLOGIAS}
TIPS = list(TIPOLOGIAS)
COM_PROV = np.array([sum(VIV_PROV[i] * SH[i, t] * TASA[k]["com_por_mil"] / 1000 for t, k in enumerate(TIPS)) for i in range(NP)])
PLZ_PROV = np.array([sum(VIV_PROV[i] * SH[i, t] * TASA[k]["plz_por_viv"] * (1 - TASA[k]["rep"]) for t, k in enumerate(TIPS)) for i in range(NP)])
REP_PROV = np.array([sum(VIV_PROV[i] * SH[i, t] * TASA[k]["rep"] for t, k in enumerate(TIPS)) for i in range(NP)])

# =============================================================================
# 5. UBICACIÓN DE FÁBRICAS (MILP de localización + transporte de Kantorovich)
# =============================================================================
MEZ_A = mezcla_viv(PLAN["A"]["comp"]["z"], "VIVA")
CUOTA_IND = sum(w for m, w in MEZ_A.items() if m in ("pref", "mod", "lsf", "clt"))
VIAJES = {"pref": 1.8, "mod": 4.2, "lsf": 1.2, "clt": 1.3}
VIAJES_MED = sum(MEZ_A.get(m, 0) * VIAJES[m] for m in VIAJES) / max(CUOTA_IND, 1e-9)
H_KM = 1 / 65 + 0.00030 * LB["v"][IX["DIE"]] + MU * 0.00095     # h por camión·km (conductor + gasóleo + μ·CO2)
CAP_FAB = 2500          # viviendas/año por fábrica
FIJO_FAB = 300_000 / 25 + 20_000                  # h/año: construcción amortizada + estructura fija
DEM_FAB = Q_ANUAL * CUOTA_IND * POB / POB.sum()   # viviendas industrializadas al año por provincia


def ubicar_fabricas():
    n = NP
    nv = n + n * n          # y_j, x_ij (viviendas de i servidas desde j)
    c = np.zeros(nv); c[:n] = FIJO_FAB
    for i in range(n):
        for j in range(n):
            c[n + i * n + j] = VIAJES_MED * DIST[i, j] * H_KM
    rows, cols, vals, lo, hi = [], [], [], [], []
    for i in range(n):   # demanda
        for j in range(n):
            rows.append(i); cols.append(n + i * n + j); vals.append(1)
    lo += list(DEM_FAB); hi += list(DEM_FAB)
    for j in range(n):   # capacidad
        for i in range(n):
            rows.append(n + j); cols.append(n + i * n + j); vals.append(1)
        rows.append(n + j); cols.append(j); vals.append(-CAP_FAB)       # y_j = número de fábricas en el emplazamiento j
    lo += [-np.inf] * n; hi += [0] * n
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(2 * n, nv))
    integr = np.zeros(nv); integr[:n] = 1
    ub = np.full(nv, np.inf); ub[:n] = 20
    res = milp(c, constraints=LinearConstraint(A, lo, hi), integrality=integr, bounds=Bounds(np.zeros(nv), ub),
               options={"time_limit": 120, "mip_rel_gap": 0.002})
    x = res.x
    y = np.round(x[:n]).astype(int)
    flujo = x[n:].reshape(n, n)
    tkm = float((flujo * DIST).sum() * VIAJES_MED)
    return dict(y=y, flujo=flujo, obj=res.fun, camion_km=tkm)


FAB = ubicar_fabricas()
FAB_TODAS = dict(y=np.ceil(DEM_FAB / CAP_FAB).astype(int))      # una o más fábricas en cada provincia
FAB_TODAS["obj"] = FAB_TODAS["y"].sum() * FIJO_FAB
FAB_UNA = None

# =============================================================================
# 6. OPERACIÓN: cocina doméstica frente a comedor comunal (por vivienda y año)
# =============================================================================
RACIONES = PERS_VIV * COMIDAS * 365
RAC_DIA_PLZ = RACIONES / PLZ_POR_VIV      # raciones al año por plaza
N_COM_NAC = float(COM_PROV.sum())
H_RAC_EF = (FIJO_COM * N_COM_NAC + H_RACION * RACIONES * (N_VIV - REP_PROV.sum())) / (RACIONES * (N_VIV - REP_PROV.sum()))
OPER = {
    "A": dict(h_trabajo=1.4 * 365, kwh=900, desperdicio=0.12, nota="1 h 25 min al día de compra, cocina y limpieza (encuestas de empleo del tiempo)"),
    "B": dict(h_trabajo=H_RAC_EF * RACIONES, kwh=0.22 * RACIONES, desperdicio=0.06, nota="equipo mínimo de 3 personas por comedor + 0,06 h por ración; 0,22 kWh por ración"),
}
DMED_NAC = float(sum((VIV_PROV * SH[:, t]).sum() * TASA[k]["dmed"] for t, k in enumerate(TIPS)) / N_VIV)
OPER["B"]["paseo"] = H_PASEO_M * DMED_NAC
OPER["A"]["paseo"] = 0.0

# =============================================================================
# 7. TALLER: fábrica modular y camino crítico de un bloque de 40 viviendas
# =============================================================================
H_ANIO = 3450
MOD_POR_VIV = 4.2
TAKT_MOD_MIN = H_ANIO * 60 / (CAP_FAB * MOD_POR_VIV)
H_FAB_VIV = COMP_MET[("VIVA", "mod")]["fab"]
OBRA_CPM = {
    "trad": [("A", "Licencia, replanteo y movimiento de tierras", 45, []), ("B", "Cimentación", 40, ["A"]),
             ("C", "Estructura de hormigón (6 plantas, 1 planta cada 15 días)", 95, ["B"]), ("D", "Cubierta", 25, ["C"]),
             ("E", "Fachada de ladrillo y carpinterías", 110, ["C"]), ("F", "Tabiquería", 70, ["C"]),
             ("G", "Instalaciones", 90, ["F"]), ("H", "Acabados", 100, ["G", "E"]), ("I", "Ascensor", 30, ["D", "G"]),
             ("J", "Urbanización y acometidas", 40, ["B"]), ("K", "Pruebas, limpieza y entrega", 20, ["H", "I", "J"])],
    "mod": [("A", "Licencia, replanteo y movimiento de tierras", 45, []), ("B", "Cimentación y zócalo", 40, ["A"]),
            ("M", "Fabricación de 168 módulos en fábrica (en paralelo)", 60, ["A"]), ("C", "Montaje de módulos con grúa (12 al día)", 15, ["B", "M"]),
            ("D", "Cubierta y juntas", 15, ["C"]), ("E", "Fachada ventilada", 30, ["C"]), ("G", "Conexión de instalaciones entre módulos", 20, ["C"]),
            ("I", "Ascensor", 25, ["D", "G"]), ("J", "Urbanización y acometidas", 40, ["B"]), ("K", "Pruebas, remates y entrega", 15, ["E", "I", "J"])],
}


def cpm(acts):
    ES, EF = {}, {}
    for a in acts:
        ES[a[0]] = max([EF[p] for p in a[3]], default=0); EF[a[0]] = ES[a[0]] + a[2]
    T = max(EF.values())
    LS, LF = {}, {}
    for a in reversed(acts):
        suc = [b[0] for b in acts if a[0] in b[3]]
        LF[a[0]] = min([LS[s] for s in suc], default=T); LS[a[0]] = LF[a[0]] - a[2]
    return dict(ES=ES, EF=EF, T=T, H={k: LS[k] - ES[k] for k in ES})


CPM = {k: cpm(v) for k, v in OBRA_CPM.items()}

if __name__ == "__main__":
    print("NB", NB, "NA", NA, "rho", round(RHO, 4))
    for (t, m), d in COMP_MET.items():
        print(f"{t} {m:5s} v={d['v']:8.0f} obra={d['obra']:7.0f} fab={d['fab']:6.0f} co2={d['e']:6.1f} cem={d['cem']:5.1f} mdr={d['mdr']:5.1f}")
    for c in ("A", "B"):
        s = MAXP[c]
        print(f"\nMAX {c}: {s['t']:,.0f}/año mezcla={ {m: round(w, 3) for m, w in mezcla_viv(s['z'], 'VIV' + c).items()} } "
              f"duales={ {k: round(v, 5) for k, v in s['dual'].items() if not k.startswith('BAL') and v > 1e-9} } rec={ {k: round(v / 1e6, 2) for k, v in s['rec'].items()} }")
        print("   solo:", {m: round(MAXP_SOLO[(c, m)]['t']) if MAXP_SOLO[(c, m)] else None for m in METODOS})
        print("   max+minCO2:", round(MAXP_CO2[c]["co2"] / MAXP[c]["t"], 2), mezcla_viv(MAXP_CO2[c]["z"], "VIV" + c), "vs co2", round(MAXP[c]["co2"] / MAXP[c]["t"], 2))
        for k, s in PLAN[c].items():
            print(f"   plan {k:5s} h/viv={s['horas'] / Q_ANUAL:7.0f} co2/viv={s['co2'] / Q_ANUAL:6.1f} {mezcla_viv(s['z'], 'VIV' + c)}")
    print("H_MOD", H_MOD, "H_PASEO_M", H_PASEO_M)
    for k, L in LOC.items():
        print(f"\nLOC {k}: viv={L['milp']['viv']} bloques={len(L['viv'])} estado={L['sol']['estado'][:40]}")
        for nom in ("milp", "voraz", "kmedias", "uno"):
            e = L[nom]
            print(f"   {nom:8s} n={e['n']:4d} plazas={e['plazas']:6d} inst={e['h_inst']:10,.0f} paseo={e['paseo']:12,.0f} rep={e['h_rep']:9,.0f} obj={e['obj']:12,.0f} dmed={e['dmed']:6.0f} dmax={e['dmax']:6.0f}")
    print("TASA", TASA)
    print("comedores nacionales", COM_PROV.sum(), "plazas", PLZ_PROV.sum(), "reparto viv", REP_PROV.sum())
    print("CUOTA_IND", CUOTA_IND, "VIAJES", VIAJES_MED, "fabricas", FAB["y"].sum(), [PROV[j][0] + f"x{FAB['y'][j]}" for j in range(NP) if FAB['y'][j]],
          "camion-km", FAB["camion_km"], "obj", FAB["obj"], "todas", FAB_TODAS["y"].sum(), FAB_TODAS["obj"])
    print("OPER", OPER, "DMED", DMED_NAC, "h_racion_efectiva", H_RAC_EF)
    print("TAKT mod", TAKT_MOD_MIN, "H_FAB_VIV", H_FAB_VIV, {k: v["T"] for k, v in CPM.items()})

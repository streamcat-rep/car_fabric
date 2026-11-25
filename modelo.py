"""
Modelo de planificación de un turismo medio (segmento C) desde la mina hasta la línea final.
Tres niveles:
  1. Leontief  (balance input-output, cantidades brutas, trabajo y CO2 incorporados)
  2. Kantorovich (programación lineal: elección de técnicas y valoraciones duales)
  3. Taller (problema de los juegos completos de Kantorovich 1939, balanceo de línea,
     regla de Johnson y camino crítico de la cadena)
Genera los resultados en un diccionario que usa build_html.py.
"""
import math
import numpy as np
from scipy.optimize import linprog

N_COCHES = 100_000  # demanda final anual (plan)

# ---------------------------------------------------------------------------
# 1. LEONTIEF
# ---------------------------------------------------------------------------
# (código, nombre, unidad, nivel, horas trabajo directas por unidad, CO2 directo t/unidad)
SECTORES = [
    ("FE",   "Mineral de hierro",              "t",   "Extracción", 0.15, 0.010),
    ("BAU",  "Bauxita",                        "t",   "Extracción", 0.20, 0.008),
    ("CUC",  "Concentrado de cobre (25 % Cu)", "t",   "Extracción", 2.00, 0.050),
    ("CRU",  "Petróleo crudo / gas",           "t",   "Extracción", 0.10, 0.150),
    ("SIL",  "Arena de sílice",                "t",   "Extracción", 0.10, 0.005),
    ("CAR",  "Carbón (térmico y coquizable)",  "t",   "Extracción", 0.40, 0.060),
    ("ELE",  "Electricidad",                   "MWh", "Energía",    0.20, 0.000),
    ("ACE",  "Acero (laminado plano y largo)", "t",   "Materiales", 2.50, 0.000),
    ("ALU",  "Aluminio primario",              "t",   "Materiales", 6.00, 1.600),
    ("COB",  "Cobre refinado",                 "t",   "Materiales", 8.00, 0.400),
    ("POL",  "Polímeros y pinturas",           "t",   "Materiales", 3.00, 0.900),
    ("CAU",  "Caucho sintético",               "t",   "Materiales", 5.00, 0.700),
    ("VID",  "Vidrio plano",                   "t",   "Materiales", 4.00, 0.450),
    ("BIW",  "Carrocería en blanco",           "ud",  "Componentes", 8.0, 0.000),
    ("MOT",  "Motor",                          "ud",  "Componentes", 10.0, 0.000),
    ("TRA",  "Transmisión",                    "ud",  "Componentes", 6.0, 0.000),
    ("CHA",  "Chasis y suspensión",            "ud",  "Componentes", 5.0, 0.000),
    ("RUE",  "Ruedas y neumáticos (juego)",    "jgo", "Componentes", 2.5, 0.000),
    ("ELC",  "Sistema eléctrico y electrónico","ud",  "Componentes", 9.0, 0.000),
    ("INT",  "Interior (asientos, salpicadero)","ud", "Componentes", 7.0, 0.000),
    ("CRI",  "Acristalamiento (juego)",        "jgo", "Componentes", 1.5, 0.000),
    ("TUR",  "Turismo (pintura + montaje final)","ud","Producto final", 18.0, 0.000),
]
COD = [s[0] for s in SECTORES]
IDX = {c: i for i, c in enumerate(COD)}
n = len(SECTORES)

# Carbón: emisiones de su combustión se imputan a quien lo quema (electricidad / acería)
# -> lo añadimos como CO2 directo de ELE y ACE (ver abajo).
CO2_EXTRA = {"ELE": 0.20, "ACE": 1.75}

# Coeficientes técnicos a_ij = cantidad del bien i necesaria por unidad de j (incluye mermas)
INSUMOS = {
    "FE":  {"ELE": 0.02},
    "BAU": {"ELE": 0.01},
    "CUC": {"ELE": 0.80},
    "CRU": {"ELE": 0.05},
    "SIL": {"ELE": 0.01},
    "CAR": {"ELE": 0.03},
    "ELE": {"ELE": 0.06, "CAR": 0.08, "CRU": 0.04},
    "ACE": {"FE": 1.60, "CAR": 0.75, "ELE": 0.45},
    "ALU": {"BAU": 4.40, "ELE": 15.0, "CAR": 0.45},  # carbón -> ánodos de coque
    "COB": {"CUC": 4.00, "ELE": 3.50},
    "POL": {"CRU": 1.80, "ELE": 1.50},
    "CAU": {"CRU": 1.60, "ELE": 0.80},
    "VID": {"SIL": 1.20, "ELE": 0.50, "CRU": 0.12},
    "BIW": {"ACE": 0.550, "ALU": 0.030, "ELE": 0.35},
    "MOT": {"ACE": 0.090, "ALU": 0.050, "COB": 0.004, "POL": 0.010, "ELE": 0.40},
    "TRA": {"ACE": 0.055, "ALU": 0.020, "ELE": 0.20},
    "CHA": {"ACE": 0.160, "ALU": 0.030, "CAU": 0.005, "ELE": 0.20},
    "RUE": {"ACE": 0.045, "ALU": 0.035, "CAU": 0.045, "ELE": 0.10},
    "ELC": {"COB": 0.022, "POL": 0.020, "ELE": 0.15},
    "INT": {"POL": 0.110, "ACE": 0.030, "ELE": 0.12},
    "CRI": {"VID": 0.045, "POL": 0.002, "ELE": 0.05},
    "TUR": {"BIW": 1, "MOT": 1, "TRA": 1, "CHA": 1, "RUE": 1, "ELC": 1, "INT": 1,
            "CRI": 1, "POL": 0.030, "ACE": 0.010, "ELE": 0.80},
}

A = np.zeros((n, n))
for j, ins in INSUMOS.items():
    for i, v in ins.items():
        A[IDX[i], IDX[j]] = v

l = np.array([s[4] for s in SECTORES])
d = np.array([s[5] + CO2_EXTRA.get(s[0], 0.0) for s in SECTORES])

y = np.zeros(n)
y[IDX["TUR"]] = N_COCHES

I = np.eye(n)
L = np.linalg.inv(I - A)          # inversa de Leontief
x = L @ y                          # producción bruta necesaria
v = l @ L                          # trabajo total incorporado por unidad (valores-trabajo)
e = d @ L                          # CO2 total incorporado por unidad
rho = max(abs(np.linalg.eigvals(A)))  # radio espectral

# Hawkins-Simon: menores principales de (I-A) positivos
HS = all(np.linalg.det((I - A)[:k, :k]) > 0 for k in range(1, n + 1))

leontief = dict(A=A, L=L, x=x, v=v, e=e, rho=rho, HS=HS,
                trabajo_total=float(l @ x), co2_total=float(d @ x))

# ---------------------------------------------------------------------------
# 2. KANTOROVICH: análisis de actividades con técnicas alternativas
# ---------------------------------------------------------------------------
# Cada actividad produce 1 unidad de un bien con un vector de insumos, trabajo y CO2.
# Recursos escasos no producidos: chatarra de acero, chatarra de aluminio,
# capacidad renovable y techo de emisiones.
ACT = []  # (nombre, bien producido, insumos dict, horas, co2, recursos dict)
for c, nom, *_ in SECTORES:
    j = IDX[c]
    base_nombre = {
        "ACE": "Acero BF-BOF (alto horno + convertidor)",
        "ALU": "Aluminio primario (Bayer + Hall-Héroult)",
        "ELE": "Electricidad térmica (carbón/gas)",
        "BIW": "Carrocería de acero (estampado + soldadura)",
    }.get(c, nom)
    ACT.append((base_nombre, c, INSUMOS.get(c, {}), l[j], d[j], {}))

ACT += [
    ("Acero de horno eléctrico (EAF, chatarra)", "ACE", {"ELE": 0.60}, 1.80, 0.08, {"CHA_ACE": 1.10}),
    ("Aluminio secundario (refundición)", "ALU", {"ELE": 0.80, "CRU": 0.05}, 3.00, 0.30, {"CHA_ALU": 1.05}),
    ("Electricidad renovable (eólica + FV)", "ELE", {}, 0.35, 0.00, {"RENOV": 1.0}),
    ("Carrocería multimaterial (acero + aluminio)", "BIW", {"ACE": 0.300, "ALU": 0.130, "ELE": 0.42}, 9.50, 0.00, {}),
]

RECURSOS = {
    "CHA_ACE": ("Chatarra de acero disponible", "t", 45_000),
    "CHA_ALU": ("Chatarra de aluminio disponible", "t", 7_000),
    "RENOV":   ("Capacidad renovable", "MWh", 250_000),
    "CO2":     ("Techo de emisiones del plan", "t CO2", None),  # se calibra abajo
}

m_act = len(ACT)
# Matriz neta B (n x m): producción - insumos
B = np.zeros((n, m_act))
for k, (_, prod, ins, *_r) in enumerate(ACT):
    B[IDX[prod], k] += 1.0
    for i, val in ins.items():
        B[IDX[i], k] -= val
h = np.array([a[3] for a in ACT])
co2 = np.array([a[4] for a in ACT])


def resolver_kantorovich(techo_co2):
    """min h·z  s.a.  B z >= y ; R z <= r ; co2·z <= techo ; z >= 0"""
    filas_rec = []
    lim = []
    nombres = []
    for key, (nom, _u, cap) in RECURSOS.items():
        if key == "CO2":
            continue
        filas_rec.append([a[5].get(key, 0.0) for a in ACT])
        lim.append(cap)
        nombres.append(key)
    filas_rec.append(list(co2))
    lim.append(techo_co2)
    nombres.append("CO2")
    A_ub = np.vstack([-B, np.array(filas_rec)])
    b_ub = np.concatenate([-y, np.array(lim)])
    res = linprog(h, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)] * m_act, method="highs")
    assert res.status == 0, res.message
    duales = -res.ineqlin.marginals  # >=0
    precios = duales[:n]             # valoraciones de los bienes (horas/unidad)
    rec_duales = dict(zip(nombres, duales[n:]))
    rec_uso = dict(zip(nombres, np.array(filas_rec) @ res.x))
    return res, precios, rec_duales, rec_uso


# Plan sin techo de CO2 -> emisiones "libres" ; luego techo = 75 % de las emisiones Leontief base
res_libre, _, _, uso_libre = resolver_kantorovich(1e12)
TECHO = round(0.62 * leontief["co2_total"], -3)
RECURSOS["CO2"] = ("Techo de emisiones del plan", "t CO2", TECHO)
res_k, precios_k, duales_rec, uso_rec = resolver_kantorovich(TECHO)

# costes reducidos (criterio de Kantorovich): h_k - p·B_k + sum_r u_r R_rk + u_co2 co2_k
coste_red = []
for k, a in enumerate(ACT):
    cr = h[k] - precios_k @ B[:, k] + sum(duales_rec[r] * q for r, q in a[5].items()) \
        + duales_rec["CO2"] * co2[k]
    coste_red.append(cr)
kantorovich = dict(coste_red=np.array(coste_red), ACT=ACT, B=B, z=res_k.x, obj=res_k.fun, precios=precios_k,
                   duales=duales_rec, uso=uso_rec, z_libre=res_libre.x,
                   obj_libre=res_libre.fun, co2_libre=uso_libre["CO2"], techo=TECHO)

# Sensibilidad: coste en horas del plan para distintos techos de CO2
sens = []
for f in [1.00, 0.80, 0.72, 0.66, 0.62, 0.58, 0.55, 0.50]:
    t = f * leontief["co2_total"]
    try:
        r, _, du, _ = resolver_kantorovich(t)
        sens.append((f, t, r.fun, du["CO2"]))
    except AssertionError:
        sens.append((f, t, None, None))

# ---------------------------------------------------------------------------
# 3. TALLER
# ---------------------------------------------------------------------------
# 3a. Problema de los juegos completos (Kantorovich 1939) en el taller de mecanizado del motor
PIEZAS = [("Bloque motor", 1), ("Culata", 1), ("Cigüeñal", 1), ("Árbol de levas", 2), ("Biela", 4)]
# grupos de máquinas: (nombre, número de máquinas, horas disponibles por máquina y año)
MAQ = [("Centros de mecanizado CNC 5 ejes", 8, 3_500),
       ("Líneas transfer", 2, 3_500),
       ("Tornos-rectificadoras CNC", 10, 3_500)]
# productividad a_ik (piezas por hora y máquina); 0 = no puede hacerla
PROD = np.array([
    # bloque culata cigüeñal levas biela
    [3.0,   4.0,   2.5,   6.0,  20.0],   # CNC 5 ejes (flexible)
    [24.0,  30.0,  0.0,   0.0,  0.0],     # transfer (sólo bloque y culata, muy rápida)
    [0.0,   0.0,   8.0,   14.0, 40.0],    # tornos-rectificadoras
])
mI, kP = PROD.shape
need = np.array([p[1] for p in PIEZAS], dtype=float)
cap_h = np.array([m[1] * m[2] for m in MAQ], dtype=float)

# variables: t_ik (horas del grupo i dedicadas a pieza k), lambda (juegos completos)
nv = mI * kP + 1
c = np.zeros(nv); c[-1] = -1.0
A_ub, b_ub = [], []
for k in range(kP):          # need_k * lambda - sum_i a_ik t_ik <= 0
    row = np.zeros(nv)
    for i in range(mI):
        row[i * kP + k] = -PROD[i, k]
    row[-1] = need[k]
    A_ub.append(row); b_ub.append(0.0)
for i in range(mI):          # sum_k t_ik <= T_i
    row = np.zeros(nv)
    row[i * kP:(i + 1) * kP] = 1.0
    A_ub.append(row); b_ub.append(cap_h[i])
bounds = []
for i in range(mI):
    for k in range(kP):
        bounds.append((0, 0) if PROD[i, k] == 0 else (0, None))
bounds.append((0, None))
r_taller = linprog(c, A_ub=np.array(A_ub), b_ub=b_ub, bounds=bounds, method="highs")
assert r_taller.status == 0
T_opt = r_taller.x[:-1].reshape(mI, kP)
lam = r_taller.x[-1]
du_t = -r_taller.ineqlin.marginals
mult_piezas = du_t[:kP]        # valor de 1 pieza extra en juegos
mult_maq = du_t[kP:]           # valor de 1 hora extra de máquina en juegos

# Plan "ingenuo": cada grupo reparte su tiempo a partes iguales entre las piezas que sabe hacer
T_naive = np.zeros_like(PROD)
for i in range(mI):
    k_ok = PROD[i] > 0
    T_naive[i, k_ok] = cap_h[i] / k_ok.sum()
piezas_naive = (PROD * T_naive).sum(axis=0)
lam_naive = float(min(piezas_naive / need))
piezas_opt = (PROD * T_opt).sum(axis=0)
taller = dict(PIEZAS=PIEZAS, MAQ=MAQ, PROD=PROD, T=T_opt, lam=lam,
              mult_piezas=mult_piezas, mult_maq=mult_maq, cap_h=cap_h,
              T_naive=T_naive, lam_naive=lam_naive, piezas_naive=piezas_naive,
              piezas_opt=piezas_opt)

# 3b. Balanceo de línea (tramo "Trim 1" del montaje final) por el método de pesos posicionales
HORAS_ANIO = 2 * 7.5 * 230 * 60   # minutos disponibles: 2 turnos x 7,5 h x 230 días
TAKT = HORAS_ANIO / N_COCHES       # minutos por coche
TAREAS = [  # (id, descripción, tiempo min, precedentes)
    ("T1", "Desmontar puertas (van a línea propia)", 0.9, []),
    ("T2", "Mazo de cables principal", 1.8, ["T1"]),
    ("T3", "Insonorizantes de suelo", 1.1, ["T1"]),
    ("T4", "Mazo de cables de techo", 0.8, ["T2"]),
    ("T5", "Tuberías de freno y combustible", 1.4, ["T1"]),
    ("T6", "Revestimiento de techo", 1.2, ["T4"]),
    ("T7", "Salpicadero (módulo completo)", 1.6, ["T2", "T3"]),
    ("T8", "Columna de dirección", 0.7, ["T7"]),
    ("T9", "Alfombra y moqueta", 1.0, ["T3", "T5"]),
    ("T10", "Parabrisas y luneta (robot + pegado)", 1.3, ["T6", "T7"]),
    ("T11", "Consola central", 0.6, ["T8", "T9"]),
    ("T12", "Pilares y guarnecidos laterales", 0.9, ["T10"]),
    ("T13", "Cinturones de seguridad", 0.5, ["T12"]),
    ("T14", "Pedalier y conexión servofreno", 0.6, ["T8"]),
]
tid = {t[0]: t for t in TAREAS}
sucesores = {t[0]: [] for t in TAREAS}
for t in TAREAS:
    for p in t[3]:
        sucesores[p].append(t[0])


def todos_suc(tk, acc=None):
    acc = set() if acc is None else acc
    for s in sucesores[tk]:
        if s not in acc:
            acc.add(s)
            todos_suc(s, acc)
    return acc


PW = {t[0]: t[2] + sum(tid[s][2] for s in todos_suc(t[0])) for t in TAREAS}
orden = sorted(TAREAS, key=lambda t: -PW[t[0]])
asignadas, estaciones = set(), []
while len(asignadas) < len(TAREAS):
    carga, est = 0.0, []
    while True:
        cand = [t for t in orden if t[0] not in asignadas
                and all(p in asignadas for p in t[3]) and carga + t[2] <= TAKT + 1e-9]
        if not cand:
            break
        t = cand[0]
        est.append(t[0]); asignadas.add(t[0]); carga += t[2]
    estaciones.append((est, carga))
sum_t = sum(t[2] for t in TAREAS)
N_min = math.ceil(sum_t / TAKT)
eficiencia = sum_t / (len(estaciones) * TAKT)
balanceo = dict(TAKT=TAKT, TAREAS=TAREAS, PW=PW, estaciones=estaciones, sum_t=sum_t,
                N_min=N_min, eficiencia=eficiencia, min_anio=HORAS_ANIO)

# 3c. Regla de Johnson: estampación -> soldadura de 6 lotes de piezas
LOTES = [("L5 Suelo", 6.0, 3.0), ("L3 Capó", 3.0, 1.5), ("L1 Laterales", 4.0, 6.0),
         ("L4 Puertas", 5.0, 7.0), ("L2 Techo", 2.0, 2.5), ("L6 Portón", 1.5, 2.0)]
g1 = sorted([j for j in LOTES if j[1] <= j[2]], key=lambda j: j[1])
g2 = sorted([j for j in LOTES if j[1] > j[2]], key=lambda j: -j[2])
seq = g1 + g2


def makespan(s):
    f1 = f2 = 0.0
    gantt = []
    for nom, p1, p2 in s:
        s1 = f1; f1 += p1
        s2 = max(f1, f2); f2 = s2 + p2
        gantt.append((nom, s1, f1, s2, f2))
    return f2, gantt


Cmax_j, gantt_j = makespan(seq)
Cmax_orig, _ = makespan(LOTES)
johnson = dict(LOTES=LOTES, seq=seq, Cmax=Cmax_j, Cmax_orig=Cmax_orig, gantt=gantt_j)

# 3d. Camino crítico de la cadena (días) de la mina al coche terminado
ACTIV = [  # (id, nombre, duración días, precedentes)
    ("A", "Extracción de mineral de hierro y carbón", 12, []),
    ("B", "Transporte marítimo mineral → acería", 25, ["A"]),
    ("C", "Extracción de bauxita", 10, []),
    ("D", "Refinado Bayer + electrólisis (aluminio)", 18, ["C"]),
    ("E", "Extracción y concentración de cobre", 15, []),
    ("F", "Fundición y refino electrolítico de cobre", 14, ["E"]),
    ("G", "Extracción y refino de crudo → polímeros", 20, []),
    ("H", "Acería y laminación (bobinas)", 9, ["B"]),
    ("I", "Fundición de bloques y culatas", 6, ["D", "H"]),
    ("J", "Estampación de paneles", 4, ["H"]),
    ("K", "Soldadura carrocería en blanco", 3, ["J", "D"]),
    ("L", "Mecanizado y montaje de motor y caja", 8, ["I"]),
    ("M", "Mazos de cables y electrónica", 12, ["F", "G"]),
    ("N", "Interior, neumáticos y vidrio", 10, ["G"]),
    ("O", "Pintura de carrocería", 1, ["K"]),
    ("P", "Montaje final, matrimonio y pruebas", 2, ["O", "L", "M", "N"]),
]
aid = {a[0]: a for a in ACTIV}
ES, EF = {}, {}
for a in ACTIV:  # ya en orden topológico
    ES[a[0]] = max([EF[p] for p in a[3]], default=0)
    EF[a[0]] = ES[a[0]] + a[2]
T_fin = max(EF.values())
LF, LS = {}, {}
for a in reversed(ACTIV):
    suc = [b[0] for b in ACTIV if a[0] in b[3]]
    LF[a[0]] = min([LS[s] for s in suc], default=T_fin)
    LS[a[0]] = LF[a[0]] - a[2]
holg = {k: LS[k] - ES[k] for k in ES}
cpm = dict(ACTIV=ACTIV, ES=ES, EF=EF, LS=LS, LF=LF, holg=holg, T=T_fin)

if __name__ == "__main__":
    np.set_printoptions(suppress=True, linewidth=160)
    print("rho(A) =", rho, "HS", HS)
    for i, s in enumerate(SECTORES):
        print(f"{s[0]:4s} x={x[i]:14,.1f} {s[2]:4s}  L[:,TUR]={L[i, IDX['TUR']]:9.4f}  v={v[i]:9.3f} h  e={e[i]:8.4f} t")
    print("Trabajo total (h):", leontief["trabajo_total"], "por coche:", v[IDX['TUR']])
    print("CO2 total:", leontief["co2_total"], "por coche:", e[IDX['TUR']])
    print("\nKANTOROVICH libre obj", res_libre.fun, "co2", uso_libre["CO2"])
    print("Techo", TECHO, "obj", res_k.fun)
    for k, a in enumerate(ACT):
        if res_k.x[k] > 1e-6 or res_libre.x[k] > 1e-6:
            print(f"  {a[0]:45s} z={res_k.x[k]:14,.1f}   libre={res_libre.x[k]:14,.1f}")
    print("duales recursos", duales_rec)
    print("uso", uso_rec)
    print("precios", dict(zip(COD, np.round(precios_k, 3))))
    print("sens", sens)
    print("\nTALLER lambda", lam)
    print(T_opt)
    print("mult piezas", mult_piezas, "maq", mult_maq)
    print("\nTAKT", TAKT, "sum", sum_t, "Nmin", N_min, "est", estaciones, "ef", eficiencia)
    print("\nJohnson", [s[0] for s in seq], Cmax_j, Cmax_orig)
    print("\nCPM", T_fin, holg)

"""
Planificación de la producción de ordenadores (oficina, gaming), servidores y un centro de datos de 50 MW
con su operación 24/7/365 (energía hora a hora: red, fotovoltaica, eólica, baterías, turbinas de gas,
grupos diésel de respaldo). Leontief + Kantorovich + método del taller.  Datos ilustrativos.
"""
import math
import numpy as np
from scipy.optimize import linprog
from scipy import sparse

# =============================================================================
# 0. BIENES
# =============================================================================
BIENES = [
    ("FE", "Mineral de hierro", "t", "Extracción"),
    ("BAU", "Bauxita", "t", "Extracción"),
    ("CUC", "Concentrado de cobre", "t", "Extracción"),
    ("CRU", "Petróleo y gas natural", "t", "Extracción"),
    ("SIL", "Arena y áridos", "t", "Extracción"),
    ("CAR", "Carbón", "t", "Extracción"),
    ("QZ", "Cuarzo de alta pureza", "t", "Extracción"),
    ("PM", "Estaño, plata, oro y paladio", "kg", "Extracción"),
    ("LIT", "Minerales de batería", "t", "Extracción"),
    ("AGU", "Agua", "m³", "Extracción"),
    ("ELE", "Electricidad", "MWh", "Energía"),
    ("DIE", "Gasóleo", "t", "Energía"),
    ("ACE", "Acero", "t", "Materiales"),
    ("ALU", "Aluminio", "t", "Materiales"),
    ("COB", "Cobre", "t", "Materiales"),
    ("POL", "Polímeros", "t", "Materiales"),
    ("VID", "Vidrio", "t", "Materiales"),
    ("HOR", "Hormigón", "t", "Materiales"),
    ("SIM", "Silicio metalúrgico", "t", "Materiales"),
    ("PSI", "Polisilicio", "kg", "Materiales"),
    ("QUI", "Gases y química de fabricación de chips", "t", "Materiales"),
    ("FR4", "Laminado de circuito impreso (8 capas eq.)", "m²", "Materiales"),
    ("OBL", "Oblea de silicio virgen 300 mm", "ud", "Obleas"),
    ("OBA", "Oblea procesada, lógica avanzada (3–5 nm)", "ud", "Obleas"),
    ("OBM", "Oblea procesada, memoria (DRAM/NAND)", "ud", "Obleas"),
    ("OBV", "Oblea procesada, nodo maduro (28–65 nm)", "ud", "Obleas"),
    ("CPD", "CPU de sobremesa", "ud", "Componentes"),
    ("CPS", "CPU de servidor (96 núcleos)", "ud", "Componentes"),
    ("GPC", "Chip GPU de consumo", "ud", "Componentes"),
    ("GPD", "Acelerador GPU de centro de datos con HBM", "ud", "Componentes"),
    ("DRAM", "Memoria DRAM", "GB", "Componentes"),
    ("NAND", "Almacenamiento SSD (NAND)", "TB", "Componentes"),
    ("PLB", "Placa base de PC montada", "ud", "Componentes"),
    ("PLS", "Placa base de servidor montada", "ud", "Componentes"),
    ("TGF", "Tarjeta gráfica de consumo", "ud", "Componentes"),
    ("PSU", "Fuente de alimentación", "kW", "Componentes"),
    ("CAJ", "Caja / chasis metálico", "kg", "Componentes"),
    ("VEN", "Ventiladores y disipadores", "kg", "Componentes"),
    ("AIO", "Refrigeración líquida AIO", "ud", "Componentes"),
    ("NIC", "Tarjeta de red 400G", "ud", "Componentes"),
    ("BAT", "Batería LFP", "kWh", "Componentes"),
    ("PCO", "PC de oficina", "ud", "Productos"),
    ("PCG", "PC gaming", "ud", "Productos"),
    ("SRV", "Servidor CPU (2 sockets)", "ud", "Productos"),
    ("SGP", "Servidor GPU (8 aceleradores)", "ud", "Productos"),
    ("RCK", "Rack equipado (armario, PDU, switch)", "ud", "Productos"),
    ("EDI", "Edificio de CPD", "MW TI", "Infraestructura CPD"),
    ("REF", "Sistema de refrigeración del CPD", "MW TI", "Infraestructura CPD"),
    ("TRF", "Transformador MT/BT", "MVA", "Infraestructura CPD"),
    ("UPS", "SAI (UPS) con baterías 10 min", "MW", "Infraestructura CPD"),
    ("GEN", "Grupo electrógeno diésel 3 MW", "ud", "Infraestructura CPD"),
    ("TGS", "Turbina de gas aeroderivada 10 MW", "ud", "Infraestructura CPD"),
    ("FV", "Planta fotovoltaica", "MW", "Infraestructura CPD"),
    ("EOL", "Parque eólico", "MW", "Infraestructura CPD"),
    ("BES", "Batería estacionaria", "MWh", "Infraestructura CPD"),
    ("CPDS", "Servicio de CPD (1 MW TI durante 1 año)", "MW·año", "Servicio"),
]
COD = [b[0] for b in BIENES]
IX = {c: i for i, c in enumerate(COD)}
NB = len(BIENES)
NOMBRE = {b[0]: b[1] for b in BIENES}
UNIDAD = {b[0]: b[2] for b in BIENES}
ESC = {b[0]: b[3] for b in BIENES}
ESCALONES = ["Extracción", "Energía", "Materiales", "Obleas", "Componentes", "Productos", "Infraestructura CPD"]

# =============================================================================
# 1. ACTIVIDADES (la primera de cada bien es la técnica base)
# =============================================================================
A_ = []


def act(id_, nombre, bien, ins, h, co2, nota=""):
    A_.append(dict(id=id_, nombre=nombre, bien=bien, ins=ins, h=h, co2=co2, nota=nota))


# extracción
act("fe", "Minería de hierro", "FE", {"ELE": 0.02}, 0.15, 0.010)
act("bau", "Minería de bauxita", "BAU", {"ELE": 0.01}, 0.20, 0.008)
act("cuc", "Minería y concentración de cobre", "CUC", {"ELE": 0.80}, 2.00, 0.050)
act("cru", "Extracción de petróleo y gas", "CRU", {"ELE": 0.05}, 0.10, 0.150)
act("sil", "Canteras de áridos", "SIL", {"ELE": 0.01, "CRU": 0.002}, 0.10, 0.005)
act("car", "Minería de carbón", "CAR", {"ELE": 0.03}, 0.40, 0.060)
act("qz", "Minería y lavado de cuarzo de alta pureza", "QZ", {"ELE": 0.05}, 1.00, 0.010)
act("pm", "Minería y refino de estaño, plata, oro y paladio (mezcla de soldadura y contactos)", "PM", {"ELE": 0.05}, 0.80, 0.020)
act("lit", "Minería y refino de minerales de batería", "LIT", {"ELE": 1.5, "CRU": 0.10}, 3.0, 0.50)
act("agu", "Captación y tratamiento de agua", "AGU", {"ELE": 0.0008}, 0.002, 0.0)
# energía
act("ele_t", "Electricidad de red térmica (carbón y gas)", "ELE", {"ELE": 0.06, "CAR": 0.08, "CRU": 0.04}, 0.20, 0.20)
act("ele_r", "Electricidad renovable (eólica + fotovoltaica)", "ELE", {}, 0.35, 0.0, "más horas de construcción por MWh, sin combustible")
act("die", "Refino de gasóleo", "DIE", {"CRU": 1.10, "ELE": 0.25}, 0.60, 0.35)
# materiales
act("ace_bof", "Acero integral (alto horno)", "ACE", {"FE": 1.60, "CAR": 0.75, "ELE": 0.45}, 2.50, 1.75)
act("ace_eaf", "Acero de horno eléctrico con chatarra", "ACE", {"ELE": 0.60}, 1.80, 0.08, "máx. 40 % del acero")
act("alu_p", "Aluminio primario", "ALU", {"BAU": 4.40, "ELE": 15.0, "CAR": 0.45}, 6.00, 1.60)
act("alu_s", "Aluminio reciclado", "ALU", {"ELE": 0.80, "CRU": 0.05}, 3.00, 0.30, "máx. 55 % del aluminio")
act("cob_p", "Cobre primario", "COB", {"CUC": 4.0, "ELE": 3.5}, 8.0, 0.40)
act("cob_s", "Cobre reciclado (cables y chatarra electrónica)", "COB", {"ELE": 1.2}, 4.0, 0.10, "máx. 35 % del cobre")
act("pol", "Petroquímica: polímeros", "POL", {"CRU": 1.8, "ELE": 1.5}, 3.0, 0.90)
act("vid", "Vidrio", "VID", {"SIL": 1.2, "ELE": 0.5, "CRU": 0.12}, 4.0, 0.45)
act("hor", "Hormigón", "HOR", {"SIL": 0.85, "CAR": 0.02, "ELE": 0.03}, 0.30, 0.13)
act("sim", "Silicio metalúrgico (horno de arco: cuarzo + carbón)", "SIM", {"QZ": 2.8, "CAR": 1.4, "ELE": 11.5}, 4.0, 1.50)
act("psi_s", "Polisilicio por proceso Siemens (grado electrónico)", "PSI", {"SIM": 0.0013, "ELE": 0.110}, 0.05, 0.002)
act("psi_f", "Polisilicio en lecho fluidizado (FBR)", "PSI", {"SIM": 0.0013, "ELE": 0.040}, 0.06, 0.002,
    "un tercio de la energía; sólo grado solar: máx. 60 % del polisilicio")
act("qui", "Gases ultrapuros y química de fabricación", "QUI", {"CRU": 0.5, "ELE": 2.0}, 6.0, 0.80)
act("fr4", "Laminado de circuito impreso FR-4 (8 capas eq.)", "FR4", {"VID": 0.004, "POL": 0.004, "COB": 0.0025, "ELE": 0.08, "QUI": 0.002}, 1.5, 0.01)
# obleas
act("obl", "Lingote Czochralski y corte de oblea 300 mm", "OBL", {"PSI": 1.0, "ELE": 0.15, "QUI": 0.002}, 0.8, 0.005)
act("oba", "Fabricación de chips lógicos 3–5 nm (≈80 capas de máscara, litografía EUV)", "OBA",
    {"OBL": 1, "ELE": 1.5, "AGU": 9.0, "QUI": 0.015}, 16.0, 0.80, "CO₂ directo: gases fluorados de grabado y limpieza")
act("obm", "Fabricación de memoria DRAM / NAND 3D", "OBM", {"OBL": 1, "ELE": 0.9, "AGU": 7.0, "QUI": 0.012}, 11.0, 0.50)
act("obv", "Fabricación de chips de nodo maduro 28–65 nm", "OBV", {"OBL": 1, "ELE": 0.45, "AGU": 5.0, "QUI": 0.007}, 6.0, 0.25)
# componentes
act("cpd_m", "CPU de sobremesa monolítica (dado de 200 mm², 250 buenos por oblea)", "CPD",
    {"OBA": 0.0040, "FR4": 0.0016, "PM": 0.002, "ELE": 0.004}, 0.25, 0)
act("cpd_c", "CPU de sobremesa con chiplets (2 dados de 75 mm² en 3 nm + E/S en 6 nm)", "CPD",
    {"OBA": 0.0019, "OBV": 0.0017, "FR4": 0.0020, "PM": 0.003, "ELE": 0.005}, 0.35, 0,
    "los dados pequeños salen con más rendimiento: menos oblea avanzada por CPU buena")
act("cps", "CPU de servidor de 96 núcleos (12 chiplets + dado de E/S)", "CPS",
    {"OBA": 0.0170, "OBV": 0.0083, "FR4": 0.006, "PM": 0.010, "ELE": 0.02}, 1.2, 0)
act("gpc_m", "Chip GPU de consumo monolítico (380 mm², 105 buenos por oblea)", "GPC",
    {"OBA": 0.0095, "FR4": 0.002, "PM": 0.003, "ELE": 0.005}, 0.30, 0)
act("gpc_c", "Chip GPU de consumo con chiplets (dado gráfico + 6 dados de caché)", "GPC",
    {"OBA": 0.0060, "OBV": 0.0040, "FR4": 0.0025, "PM": 0.004, "ELE": 0.006}, 0.45, 0)
act("gpd", "Acelerador GPU con 80 GB de HBM en encapsulado 2,5D (CoWoS)", "GPD",
    {"OBA": 0.029, "DRAM": 104, "OBV": 0.05, "FR4": 0.01, "PM": 0.02, "ELE": 0.10}, 6.0, 0,
    "dado de 800 mm² (35 buenos por oblea) + interposer de silicio + 5 pilas HBM")
act("dram", "Módulo DRAM DDR5 (por GB)", "DRAM", {"OBM": 0.0005, "FR4": 0.00006, "PM": 0.00002, "ELE": 0.0001}, 0.004, 0)
act("nand", "SSD NVMe (por TB)", "NAND", {"OBM": 0.0089, "OBV": 0.0005, "FR4": 0.0015, "PM": 0.0005, "ELE": 0.0005}, 0.05, 0)
act("plb", "Placa base de PC: montaje superficial (SMT) + soldadura por refusión + prueba", "PLB",
    {"FR4": 0.05, "OBV": 0.004, "PM": 0.02, "COB": 0.0003, "POL": 0.0002, "ELE": 0.02}, 0.6, 0)
act("pls", "Placa base de servidor (SMT, 16 capas)", "PLS",
    {"FR4": 0.25, "OBV": 0.012, "PM": 0.06, "COB": 0.001, "POL": 0.0005, "ELE": 0.06}, 2.0, 0)
act("tgf", "Tarjeta gráfica: placa + 16 GB GDDR + disipador", "TGF",
    {"GPC": 1, "DRAM": 16, "FR4": 0.04, "ALU": 0.0012, "COB": 0.0004, "PM": 0.01, "POL": 0.0003, "ELE": 0.02}, 1.0, 0)
act("psu", "Fuente de alimentación de silicio (92 % de eficiencia)", "PSU",
    {"COB": 0.0012, "ALU": 0.0004, "ACE": 0.0008, "FR4": 0.02, "OBV": 0.002, "POL": 0.0002, "PM": 0.004, "ELE": 0.01}, 0.8, 0)
act("psu_g", "Fuente de alimentación de nitruro de galio (GaN, 96 %)", "PSU",
    {"COB": 0.0008, "ALU": 0.0003, "ACE": 0.0006, "FR4": 0.015, "OBV": 0.003, "POL": 0.0002, "PM": 0.003, "ELE": 0.01}, 0.7, 0,
    "transistores GaN: menos cobre magnético y menos pérdidas")
act("caj_a", "Caja de chapa de acero estampada", "CAJ", {"ACE": 0.00085, "POL": 0.0001, "ELE": 0.0015}, 0.05, 0)
act("caj_l", "Caja de aluminio extruido y mecanizado", "CAJ", {"ALU": 0.0006, "POL": 0.0001, "ELE": 0.002}, 0.07, 0)
act("ven", "Ventiladores y disipadores", "VEN", {"ALU": 0.0006, "COB": 0.0003, "POL": 0.0002, "ELE": 0.002}, 0.08, 0)
act("aio", "Refrigeración líquida AIO (bomba, radiador, tubos)", "AIO", {"COB": 0.0006, "ALU": 0.0004, "POL": 0.0006, "ELE": 0.005}, 0.6, 0)
act("nic", "Tarjeta de red 400G", "NIC", {"OBA": 0.004, "FR4": 0.02, "PM": 0.005, "ELE": 0.01}, 0.5, 0)
act("bat", "Batería LFP", "BAT", {"LIT": 0.0026, "ALU": 0.0014, "COB": 0.0011, "POL": 0.0006, "ACE": 0.0012, "ELE": 0.050}, 0.33, 0.015)
# productos (horas directas = ENSAMBLAJE FINAL)
act("pco", "Montaje final del PC de oficina (montaje, prueba, embalaje)", "PCO",
    {"PLB": 1, "CPD": 1, "DRAM": 16, "NAND": 0.5, "PSU": 0.3, "CAJ": 5, "VEN": 0.6, "POL": 0.001, "ELE": 0.01}, 0.35, 0)
act("pcg", "Montaje final del PC gaming (montaje bajo pedido, prueba de estrés)", "PCG",
    {"PLB": 1, "CPD": 1, "TGF": 1, "DRAM": 32, "NAND": 2, "PSU": 0.85, "CAJ": 8, "VID": 0.004, "VEN": 1.2, "AIO": 1, "POL": 0.002, "ELE": 0.015}, 0.9, 0)
act("srv", "Integración del servidor CPU (montaje + 24 h de quemado)", "SRV",
    {"PLS": 1, "CPS": 2, "DRAM": 512, "NAND": 15.36, "PSU": 3.2, "CAJ": 15, "VEN": 1.5, "NIC": 1, "POL": 0.001, "ELE": 0.05}, 2.5, 0)
act("sgp", "Integración del servidor GPU (montaje + 72 h de quemado)", "SGP",
    {"PLS": 2, "CPS": 2, "GPD": 8, "DRAM": 2048, "NAND": 30, "PSU": 18, "CAJ": 60, "VEN": 6, "NIC": 8, "COB": 0.02, "POL": 0.005, "ELE": 0.3}, 14.0, 0)
act("rck", "Rack equipado: armario, PDU, switch de 51,2 Tb/s, cableado", "RCK",
    {"ACE": 0.18, "COB": 0.04, "POL": 0.02, "OBA": 0.02, "FR4": 0.2, "PSU": 1.0, "ELE": 0.2}, 18.0, 0)
# infraestructura del CPD
act("edi", "Edificio de CPD (por MW TI): estructura, envolvente, salas", "EDI",
    {"HOR": 1200, "ACE": 90, "ALU": 3, "COB": 6, "POL": 8, "VID": 2, "ELE": 40, "CRU": 10}, 9000.0, 8.0)
act("ref_ch", "Refrigeración por enfriadoras + climatizadores de sala (aire)", "REF",
    {"ACE": 25, "COB": 6, "ALU": 4, "POL": 1.5, "ELE": 20}, 1800.0, 2.0, "PUE 1,45; torres de refrigeración: 1,8 L/kWh TI")
act("ref_ad", "Refrigeración por aire exterior con enfriamiento adiabático", "REF",
    {"ACE": 18, "COB": 3, "ALU": 5, "POL": 2, "ELE": 15}, 1500.0, 0.5, "PUE 1,22; 1,5 L/kWh TI de agua evaporada")
act("ref_lq", "Refrigeración líquida directa al chip + aerorrefrigeradores secos", "REF",
    {"ACE": 14, "COB": 8, "ALU": 6, "POL": 3, "ELE": 18}, 2100.0, 0.5, "PUE 1,10; casi sin agua")
act("trf", "Transformador MT/BT (por MVA)", "TRF", {"ACE": 2.2, "COB": 0.9, "ALU": 0.1, "CRU": 0.5, "POL": 0.05, "ELE": 3}, 80.0, 0)
act("ups", "SAI con baterías LFP de 10 minutos (por MW)", "UPS",
    {"BAT": 170, "OBV": 0.05, "COB": 1.0, "ACE": 1.5, "ALU": 0.3, "FR4": 2, "PM": 0.4, "ELE": 2}, 300.0, 0)
act("gen", "Grupo electrógeno diésel de 3 MW", "GEN", {"ACE": 28, "ALU": 2, "COB": 4, "POL": 0.5, "ELE": 30}, 2600.0, 0)
act("tgs", "Turbina de gas aeroderivada de 10 MW", "TGS", {"ACE": 60, "ALU": 5, "COB": 8, "ELE": 150}, 18000.0, 0)
act("fv", "Planta fotovoltaica (por MW: 1.820 módulos de 550 W, estructura, inversores)", "FV",
    {"PSI": 2500, "VID": 50, "ALU": 13, "ACE": 45, "COB": 4, "POL": 6, "HOR": 60, "OBV": 0.3, "ELE": 80}, 3000.0, 0)
act("eol", "Parque eólico (por MW: 1/5 de aerogenerador de 5 MW)", "EOL",
    {"ACE": 130, "HOR": 500, "COB": 3, "ALU": 2, "POL": 12, "VID": 6, "ELE": 100}, 4500.0, 0)
act("bes", "Batería estacionaria (por MWh)", "BES", {"BAT": 1000, "ACE": 6, "COB": 0.5, "ALU": 0.5, "HOR": 3, "FR4": 1, "OBV": 0.02, "ELE": 5}, 120.0, 0)
N_PROD = len(A_)

CUOTAS_TEC = [("ace_eaf", "ACE", 0.40), ("alu_s", "ALU", 0.55), ("cob_s", "COB", 0.35), ("psi_f", "PSI", 0.60)]

# --- servicio de CPD: 1 MW TI durante un año, con cada sistema de refrigeración
UTIL_TI = 0.80                 # consumo medio de TI respecto a la potencia nominal
PUE = {"ref_ch": 1.45, "ref_ad": 1.22, "ref_lq": 1.10}
AGUA_L_KWH = {"ref_ch": 1.8, "ref_ad": 1.5, "ref_lq": 0.1}
VIDA_INF = {"EDI": 30, "REF": 15, "TRF": 25, "UPS": 12, "GEN": 25, "RCK": 10}
HORAS_OPER_MW = 2100           # 24/7: operación, seguridad, mantenimiento (≈1,3 FTE por MW)
GEN_MW = 3
CPU_MW, GPU_MW = 30, 20        # mezcla del CPD de 50 MW
SRV_POR_MW, SGP_POR_MW = 1000, 100      # servidores por MW nominal de TI
VIDA_SRV, VIDA_SGP = 5, 4
RCK_POR_MW = 0.6 * 34 + 0.4 * 25        # 34 racks/MW CPU (30 servidores), 25 racks/MW GPU (4 servidores)
ACT_CPD = {}
for ref_id, pue in PUE.items():
    e_mwh = 8760 * UTIL_TI * pue
    ins = {"ELE": e_mwh, "AGU": 8760 * UTIL_TI * AGUA_L_KWH[ref_id],
           "SRV": CPU_MW / (CPU_MW + GPU_MW) * SRV_POR_MW / VIDA_SRV,
           "SGP": GPU_MW / (CPU_MW + GPU_MW) * SGP_POR_MW / VIDA_SGP,
           "RCK": RCK_POR_MW / VIDA_INF["RCK"],
           "EDI": 1 / VIDA_INF["EDI"], "REF": 1 / VIDA_INF["REF"], "TRF": 1.25 * pue / VIDA_INF["TRF"],
           "UPS": 2.0 / VIDA_INF["UPS"],           # 2N
           "GEN": (math.ceil(pue / GEN_MW * 50) + 2) / 50 / VIDA_INF["GEN"],   # N+2 para la carga total
           "DIE": 0.01 * 8760 * pue * 0.25 / 50 * 50 / 50}   # pruebas mensuales ≈ 1 % de horas
    act("cpd_" + ref_id[4:], f"Servicio de CPD 24/7 con {dict(ref_ch='enfriadoras (aire)', ref_ad='aire exterior adiabático', ref_lq='refrigeración líquida')[ref_id]}",
        "CPDS", ins, HORAS_OPER_MW, 0.0, f"PUE {pue}")
    ACT_CPD[ref_id] = len(A_) - 1
NA = len(A_)
ID = {a["id"]: k for k, a in enumerate(A_)}

B = np.zeros((NB, NA)); H = np.zeros(NA); C = np.zeros(NA)
for k, a in enumerate(A_):
    B[IX[a["bien"]], k] += 1
    for g, q in a["ins"].items():
        B[IX[g], k] -= q
    H[k] = a["h"]; C[k] = a["co2"]
# el CO2 del gasóleo quemado en pruebas de grupos: 3,17 t CO2/t
for ref_id, k in ACT_CPD.items():
    C[k] += A_[k]["ins"]["DIE"] * 3.17
    A_[k]["co2"] = C[k]

BASE = {}
for k, a in enumerate(A_):
    BASE.setdefault(a["bien"], k)


def leontief_mezcla(z=None):
    A = np.zeros((NB, NB)); l = np.zeros(NB); d = np.zeros(NB)
    for g in set(a["bien"] for a in A_):
        ks = [k for k, a in enumerate(A_) if a["bien"] == g]
        if z is None or z[ks].sum() < 1e-12:
            pesos = {BASE[g]: 1.0}
        else:
            t = z[ks].sum(); pesos = {k: z[k] / t for k in ks if z[k] > 1e-14}
        j = IX[g]
        for k, w in pesos.items():
            for gi, q in A_[k]["ins"].items():
                A[IX[gi], j] += w * q
            l[j] += w * A_[k]["h"]; d[j] += w * C[k]
    L = np.linalg.inv(np.eye(NB) - A)
    return dict(A=A, L=L, l=l, d=d, v=l @ L, e=d @ L)


LB = leontief_mezcla()
A0, L0, l0, d0, v0, e0 = LB["A"], LB["L"], LB["l"], LB["d"], LB["v"], LB["e"]
RHO = max(abs(np.linalg.eigvals(A0)))
MU_CO2 = 3.0


def lp(obj=None, y=None, max_bien=None, h_max=None, co2_max=None, excluir=None):
    nv = NA + (1 if max_bien is not None else 0)

    def fila(v, t=0.0):
        r = np.zeros(nv); r[:NA] = v
        if max_bien is not None:
            r[-1] = t
        return r
    Au, bu, nom = [], [], []
    yv = np.zeros(NB) if y is None else y
    for i in range(NB):
        if max_bien is not None:
            Au.append(fila(-B[i], max_bien[i])); bu.append(0.0)
        else:
            Au.append(fila(-B[i])); bu.append(-yv[i])
        nom.append("BAL_" + COD[i])
    for tec, g, s in CUOTAS_TEC:
        v = np.zeros(NA)
        for k, a in enumerate(A_):
            if a["bien"] == g:
                v[k] = -s
        v[ID[tec]] += 1
        Au.append(fila(v)); bu.append(0.0); nom.append("CUOTA_" + tec)
    if h_max is not None:
        Au.append(fila(H)); bu.append(h_max); nom.append("HORAS")
    if co2_max is not None:
        Au.append(fila(C)); bu.append(co2_max); nom.append("CO2")
    bounds = [(0, None)] * nv
    if excluir:
        for t in excluir:
            bounds[ID[t]] = (0, 0)
    c = np.zeros(nv)
    if max_bien is not None:
        c[-1] = -1
    else:
        c[:NA] = obj
    r = linprog(c, A_ub=np.array(Au), b_ub=np.array(bu), bounds=bounds, method="highs")
    if r.status != 0:
        return None
    du = -r.ineqlin.marginals
    z = r.x[:NA]
    return dict(z=z, t=r.x[-1] if max_bien is not None else None, dual=dict(zip(nom, du)), horas=float(H @ z), co2=float(C @ z))


NO_BASE = [a["id"] for k, a in enumerate(A_) if BASE[a["bien"]] != k]

# =============================================================================
# 2. FICHAS POR PRODUCTO
# =============================================================================
Q = {"PCO": 1_000_000, "PCG": 250_000, "SRV": CPU_MW * SRV_POR_MW, "SGP": GPU_MW * SGP_POR_MW}
PRODUCTOS = ["PCO", "PCG", "SRV", "SGP"]
TEC_CLAVE = ["ACE", "ALU", "COB", "ELE", "PSI", "CPD", "GPC", "PSU", "CAJ", "REF"]
H_ANIO, H_OPER = 3450, 1650


def mezcla(z):
    out = []
    for g in TEC_CLAVE:
        ks = [k for k, a in enumerate(A_) if a["bien"] == g]
        t = z[ks].sum()
        if len(ks) > 1 and t > 1e-9:
            out.append((g, [(A_[k]["id"], z[k] / t) for k in ks if z[k] / t > 1e-4]))
    return out


def ensamblaje(z, g):
    ks = [k for k, a in enumerate(A_) if a["bien"] == g]
    t = z[ks].sum()
    return sum(z[k] * A_[k]["h"] for k in ks) / t


def ficha(g, q):
    j = IX[g]
    y = np.zeros(NB); y[j] = q
    met = {}
    for key, nom, sol in [("base", "Base (Leontief, una técnica por sector)", lp(H, y, excluir=NO_BASE)),
                          ("h", "Kantorovich: máxima producción (mínimo trabajo)", lp(H, y)),
                          ("c", "Kantorovich: mínimo CO₂", lp(C + 1e-7 * H, y)),
                          ("comp", "Kantorovich: mínimo coste social (h + 3·CO₂) — RECOMENDADO", lp(H + MU_CO2 * C, y))]:
        lm = leontief_mezcla(sol["z"])
        met[key] = dict(nombre=nom, sol=sol, h_ud=sol["horas"] / q, c_ud=sol["co2"] / q, ens=ensamblaje(sol["z"], g),
                        mezcla=mezcla(sol["z"]), lm=lm, e_ud=lm["L"][IX["ELE"], j], agua_ud=lm["L"][IX["AGU"], j],
                        cuotas={k[6:]: v for k, v in sol["dual"].items() if k.startswith("CUOTA_") and v > 1e-6})
    takt = H_ANIO / q
    l_ens = met["comp"]["ens"]
    return dict(g=g, q=q, met=met, takt_s=takt * 3600, puestos=math.ceil(l_ens / takt), operarios=l_ens * q / H_OPER)


FICHAS = {g: ficha(g, Q[g]) for g in PRODUCTOS}


def arbol(g, qty, nivel=0, max_nivel=4, out=None, lm=None):
    """Descomposición en piezas (receta base) hasta materiales/obleas."""
    lm = lm or LB
    out = [] if out is None else out
    j = IX[g]
    out.append(dict(g=g, nivel=nivel, q=qty, h=qty * lm["v"][j], c=qty * lm["e"][j],
                    ele=qty * lm["L"][IX["ELE"], j], agu=qty * lm["L"][IX["AGU"], j], ens=qty * lm["l"][j]))
    if nivel < max_nivel and ESC[g] not in ("Extracción", "Energía", "Materiales"):
        a = A_[BASE[g]]
        for gi, qq in sorted(a["ins"].items(), key=lambda kv: -kv[1] * lm["v"][IX[kv[0]]]):
            if gi in ("ELE",):
                continue
            arbol(gi, qty * qq, nivel + 1, max_nivel, out, lm)
    return out


# =============================================================================
# 3. CENTRO DE DATOS: Kantorovich sobre refrigeración + plan de 50 MW
# =============================================================================
MW_TI = CPU_MW + GPU_MW
y_cpd = np.zeros(NB); y_cpd[IX["CPDS"]] = MW_TI
CPD = {}
for key, obj in [("base", None), ("h", H), ("c", C + 1e-7 * H), ("comp", H + MU_CO2 * C)]:
    if key == "base":
        CPD[key] = lp(H, y_cpd, excluir=NO_BASE)
    else:
        CPD[key] = lp(obj, y_cpd)
# cada refrigeración por separado (método de producción del servicio)
CPD_REF = {}
for rid in PUE:
    otros = [r for r in PUE if r != rid]
    CPD_REF[rid] = lp(H + MU_CO2 * C, y_cpd, excluir=["cpd_" + r[4:] for r in otros])

# =============================================================================
# 4. OPERACIÓN 24/7/365: despacho horario de energía (8.760 h)
# =============================================================================
T = 8760
rng = np.random.default_rng(7)
dia = np.arange(T) // 24
hora = np.arange(T) % 24
# temperatura exterior y PUE horario (la refrigeración trabaja más en verano por la tarde)
temp = 15 + 9 * np.sin(2 * np.pi * (dia - 110) / 365) + 6 * np.sin(2 * np.pi * (hora - 9) / 24)
# fotovoltaica: duración del día, altura solar y nubosidad diaria
dur = 12 + 2.8 * np.sin(2 * np.pi * (dia - 80) / 365)
amanecer = 12.5 - dur / 2
x = (hora + 0.5 - amanecer) / dur
nubes_d = np.clip(rng.beta(5, 1.6, 365), 0.15, 1.0)
cf_fv = np.where((x > 0) & (x < 1), np.sin(np.pi * np.clip(x, 0, 1)) ** 1.3, 0) * (0.82 + 0.10 * np.sin(2 * np.pi * (dia - 80) / 365)) * nubes_d[dia]
# eólica: proceso autorregresivo + estacionalidad (más en invierno)
ruido = np.zeros(T)
e_ = rng.normal(0, 1, T)
for t in range(1, T):
    ruido[t] = 0.97 * ruido[t - 1] + 0.243 * e_[t]
cf_eol = np.clip(0.30 + 0.08 * np.cos(2 * np.pi * (dia - 15) / 365) + 0.16 * ruido + 0.03 * np.sin(2 * np.pi * (hora - 15) / 24), 0, 0.95)
# intensidad de CO2 de la red: menor al mediodía (solar en la red) y en días de viento
co2_red = np.clip(0.24 - 0.10 * cf_fv - 0.08 * (cf_eol - 0.3), 0.06, 0.32)

VIDA_E = {"FV": 30, "EOL": 25, "BES": 15, "TGS": 25}
OM_H = {"FV": 25, "EOL": 60, "BES": 4, "TGS": 300}           # h de mantenimiento por MW (o MWh) y año
H_MWH_RED = v0[IX["ELE"]]                                    # horas incorporadas por MWh de red
GAS_T_MWH = 0.19                                             # t de gas por MWh en turbina (rendimiento ≈ 39 %)
CO2_GAS_MWH = 0.52
H_GAS_MWH = GAS_T_MWH * v0[IX["CRU"]] + 0.05


def despacho(pue_base, red=True, co2_max=None, red_max=None, mu=MU_CO2, solo_red=False):
    """LP horario de capacidad y despacho. Devuelve capacidades, energías y costes."""
    carga = MW_TI * UTIL_TI * (pue_base + (pue_base - 1) * 0.35 * np.clip((temp - 18) / 12, -0.6, 1.2))
    nv_cap = 5                              # S (FV MW), W (EOL MW), E (BES MWh), G (TGS MW), R (red MW)
    blocks = ["s", "w", "g", "q", "c", "d", "soc"]
    off = {b: nv_cap + i * T for i, b in enumerate(blocks)}
    nv = nv_cap + len(blocks) * T
    cost = np.zeros(nv)
    # costes anualizados de capacidad (horas + μ·CO2 incorporado / vida) + mantenimiento
    def cap_cost(g):
        return (v0[IX[g]] + mu * e0[IX[g]]) / VIDA_E[g] + OM_H[g]
    cost[0] = cap_cost("FV"); cost[1] = cap_cost("EOL"); cost[2] = cap_cost("BES")
    cost[3] = (v0[IX["TGS"]] + mu * e0[IX["TGS"]]) / 10 / VIDA_E["TGS"] + OM_H["TGS"]
    cost[4] = 50.0                          # reserva de capacidad de acceso a red (h/MW·año)
    cost[off["g"]:off["g"] + T] = H_MWH_RED + mu * co2_red
    cost[off["q"]:off["q"] + T] = H_GAS_MWH + mu * CO2_GAS_MWH
    cost[off["c"]:off["c"] + T] = 0.001
    rows, cols, vals, b_ub = [], [], [], []
    r = 0
    I = np.arange(T)

    def add(rr, cc, vv):
        rows.extend(rr); cols.extend(cc); vals.extend(vv)
    # balance: -(s+w+g+q+d-c) <= -carga
    for b_, sg in [("s", -1), ("w", -1), ("g", -1), ("q", -1), ("d", -1), ("c", 1)]:
        add(r + I, off[b_] + I, np.full(T, sg))
    b_ub += list(-carga); r += T
    # s <= S*cf_fv ; w <= W*cf_eol ; g <= R ; q <= G ; c <= E/4 ; d <= E/4 ; soc <= E
    for b_, capi, coef in [("s", 0, cf_fv), ("w", 1, cf_eol), ("g", 4, np.ones(T)), ("q", 3, np.ones(T)),
                           ("c", 2, np.full(T, 0.25)), ("d", 2, np.full(T, 0.25)), ("soc", 2, np.ones(T))]:
        add(r + I, off[b_] + I, np.ones(T)); add(r + I, np.full(T, capi), -coef)
        b_ub += [0.0] * T; r += T
    if co2_max is not None:
        add(np.full(T, r), off["g"] + I, co2_red); add(np.full(T, r), off["q"] + I, np.full(T, CO2_GAS_MWH))
        b_ub.append(co2_max); r += 1
    A_ub = sparse.csr_matrix((vals, (rows, cols)), shape=(r, nv))
    # dinámica de la batería: soc[t+1] = soc[t] + 0.92 c[t] - d[t]/0.92  (cíclica)
    rows, cols, vals = [], [], []
    nxt = (I + 1) % T
    add(I, off["soc"] + nxt, np.ones(T)); add(I, off["soc"] + I, -np.ones(T))
    add(I, off["c"] + I, np.full(T, -0.92)); add(I, off["d"] + I, np.full(T, 1 / 0.92))
    A_eq = sparse.csr_matrix((vals, (rows, cols)), shape=(T, nv))
    bounds = [(0, None)] * nv
    if solo_red:
        for i in range(4):
            bounds[i] = (0, 0)
    if not red:
        bounds[4] = (0, 0)
    elif red_max is not None:
        bounds[4] = (0, red_max)
    res = linprog(cost, A_ub=A_ub, b_ub=np.array(b_ub), A_eq=A_eq, b_eq=np.zeros(T), bounds=bounds, method="highs")
    assert res.status == 0, res.message
    xx = res.x
    S, W, E, G, R = xx[:5]
    ser = {b_: xx[off[b_]:off[b_] + T] for b_ in blocks}
    co2 = float(co2_red @ ser["g"] + CO2_GAS_MWH * ser["q"].sum())
    h_cap = sum((v0[IX[g_]]) / VIDA_E[g_] * cap + OM_H[g_] * cap for g_, cap in [("FV", S), ("EOL", W), ("BES", E)]) \
        + (v0[IX["TGS"]] / 10 / VIDA_E["TGS"] + OM_H["TGS"]) * G
    h_ener = float(H_MWH_RED * ser["g"].sum() + H_GAS_MWH * ser["q"].sum())
    return dict(S=S, W=W, E=E, G=G, R=R, ser=ser, carga=carga, co2=co2, horas=h_cap + h_ener,
                e_tot=float(carga.sum()), red=float(ser["g"].sum()), fv=float(ser["s"].sum()), eol=float(ser["w"].sum()),
                gas=float(ser["q"].sum()), bat=float(ser["d"].sum()),
                vert=float((S * cf_fv - ser["s"]).sum() + (W * cf_eol - ser["w"]).sum()))


REF_OPT = max(PUE, key=lambda r: CPD["comp"]["z"][ACT_CPD[r]])
PUE_OPT = PUE[REF_OPT]
DESP = {}
DESP["red"] = despacho(PUE_OPT, solo_red=True)                         # todo de la red
DESP["gas"] = despacho(PUE_OPT, mu=0.0)                                # mínimo trabajo sin valorar el CO2
DESP["opt"] = despacho(PUE_OPT)                                        # coste social con μ = 3 (recomendado)
DESP["isla"] = despacho(PUE_OPT, red=False)                           # sin conexión a red, μ = 3
DESP["isla0"] = despacho(PUE_OPT, red=False, co2_max=0.0)             # sin red y sin gas: 100 % renovable + baterías
ESC_DESP = [("red", "Todo de la red eléctrica"), ("gas", "Mínimo trabajo sin valorar el CO₂"),
            ("opt", "Recomendado: coste social mínimo (μ = 3)"), ("isla", "Isla sin red (μ = 3)"),
            ("isla0", "Isla 100 % renovable, sin gas")]
# grupos diésel de respaldo (N+2) y depósito para 48 h
CARGA_PICO = max(DESP["opt"]["carga"])
N_GEN = math.ceil(CARGA_PICO / GEN_MW) + 2
DIESEL_48H = CARGA_PICO * 48 * 0.25          # t de gasóleo (0,25 t/MWh)

# =============================================================================
# 5. PROCESOS DE FABRICACIÓN (juegos completos de Kantorovich, 1939)
# =============================================================================
PLANTAS = {
    "PCO": dict(nombre="PC de oficina — planta de 1.000.000/año",
                piezas=[("PLB", "Placa base", 1), ("CAJ", "Caja", 1), ("MON", "Montaje y prueba", 1)],
                recursos={"OPER": ("Horas de operario", "h", 520_000), "SMT1": ("Horas de línea SMT de alta velocidad (1 línea)", "h", H_ANIO),
                          "SMT2": ("Horas de línea SMT flexible (2 líneas)", "h", 2 * H_ANIO), "PRE": ("Horas de prensa de chapa (1)", "h", H_ANIO),
                          "INY": ("Horas de inyectora de plástico (2)", "h", 2 * H_ANIO), "CAD": ("Horas de línea de montaje en cadena (1)", "h", H_ANIO),
                          "CEL": ("Horas de célula de montaje (12)", "h", 12 * H_ANIO)},
                procesos=[("PLB", "SMT de alta velocidad: 6 montadoras en serie, 250 placas/h", {"OPER": 0.08, "SMT1": 0.004}, "≈1.200 componentes por placa"),
                          ("PLB", "SMT flexible: 2 montadoras, 145 placas/h", {"OPER": 0.12, "SMT2": 0.0069}, "cambios de modelo en 10 min"),
                          ("CAJ", "Caja de chapa de acero estampada en prensa progresiva", {"OPER": 0.05, "PRE": 0.0008}, "1 caja cada 3 s; 5 kg de acero"),
                          ("CAJ", "Caja de plástico inyectado con bastidor de chapa ligera", {"OPER": 0.04, "INY": 0.006}, "1 caja cada 22 s por inyectora"),
                          ("MON", "Línea en cadena con takt de 12 s (40 puestos)", {"OPER": 0.30, "CAD": 0.0035}, "prueba automática de 4 min"),
                          ("MON", "Células de 3 personas que montan el PC completo", {"OPER": 0.38, "CEL": 0.02}, "más flexible, menos especializado")]),
    "PCG": dict(nombre="PC gaming — planta de 250.000/año (montaje bajo pedido)",
                piezas=[("TGF", "Tarjeta gráfica", 1), ("MON", "Montaje", 1), ("TEST", "Prueba de estrés", 1)],
                recursos={"OPER": ("Horas de operario", "h", 330_000), "SMT": ("Horas de línea SMT de tarjetas (1)", "h", H_ANIO),
                          "ROB": ("Horas de célula robotizada de disipadores (1)", "h", H_ANIO), "CAD": ("Horas de línea en cadena (1)", "h", H_ANIO),
                          "CEL": ("Horas de célula de montaje (20)", "h", 20 * H_ANIO), "QUE": ("Horas-puesto de quemado (600 puestos)", "h", 600 * H_ANIO)},
                procesos=[("TGF", "Tarjeta: SMT + disipador atornillado a mano", {"OPER": 0.35, "SMT": 0.012}, "pasta térmica manual"),
                          ("TGF", "Tarjeta: SMT + disipador colocado por robot", {"OPER": 0.12, "SMT": 0.012, "ROB": 0.016}, "pasta térmica dispensada"),
                          ("MON", "Línea en cadena por configuraciones estándar", {"OPER": 0.70, "CAD": 0.012}, "sólo 30 configuraciones"),
                          ("MON", "Célula de un montador por PC (bajo pedido)", {"OPER": 0.95, "CEL": 0.25}, "cualquier configuración, gestión de cables cuidada"),
                          ("TEST", "Quemado de 4 h en estantería", {"OPER": 0.05, "QUE": 4.0}, "detecta el 99 % de fallos tempranos"),
                          ("TEST", "Prueba automática de 25 min + quemado por muestreo (10 %)", {"OPER": 0.08, "QUE": 0.82}, "detecta el 96 %")]),
    "SRV": dict(nombre="Servidores para el CPD — planta de integración",
                piezas=[("PLS", "Placa de servidor", 1), ("L10", "Integración del servidor", 1), ("L11", "Integración en rack", 1), ("QUE", "Quemado", 1)],
                recursos={"OPER": ("Horas de operario", "h", 120_000), "SMT": ("Horas de línea SMT de servidor (1)", "h", H_ANIO),
                          "CEL": ("Horas de célula L10 (8)", "h", 8 * H_ANIO), "RACK": ("Horas de bahía de integración de racks (6)", "h", 6 * H_ANIO),
                          "QUE": ("Horas-ranura de quemado (300)", "h", 300 * H_ANIO), "OBRA": ("Horas de técnico en el CPD", "h", 30_000)},
                procesos=[("PLS", "SMT de placa de 16 capas con inspección por rayos X", {"OPER": 0.6, "SMT": 0.09}, "BGA de CPU verificados por rayos X"),
                          ("L10", "Montaje del servidor en célula", {"OPER": 1.2, "CEL": 0.6}, "CPU, 16 DIMM, SSD, fuentes"),
                          ("L11", "Rack completo integrado y cableado en fábrica (30 servidores)", {"OPER": 0.5, "RACK": 0.25}, "se envía el rack entero"),
                          ("L11", "Servidores sueltos instalados en el CPD", {"OPER": 0.2, "OBRA": 0.9}, "cableado en sitio"),
                          ("QUE", "Quemado de 24 h en fábrica", {"OPER": 0.1, "QUE": 24}, "fallos tempranos detectados antes de enviar"),
                          ("QUE", "Quemado de 8 h + supervisión en producción", {"OPER": 0.1, "QUE": 8, "OBRA": 0.15}, "algunos fallos llegan al CPD")]),
    "OBRA": dict(nombre="Construcción del CPD de 50 MW (por MW TI)",
                 piezas=[("EDI", "Edificio y salas", 1), ("ELEC", "Instalación eléctrica y de refrigeración", 1)],
                 recursos={"OPER": ("Horas de cuadrilla", "h", 420_000), "GRUA": ("Horas de grúa (4 grúas)", "h", 4 * H_ANIO),
                           "PREF": ("Horas de planta de módulos prefabricados", "h", 2 * H_ANIO), "SKID": ("Horas de taller de módulos eléctricos (skids)", "h", H_ANIO)},
                 procesos=[("EDI", "Edificio de hormigón construido in situ", {"OPER": 9000, "GRUA": 250}, "≈26 meses de obra"),
                           ("EDI", "Edificio de módulos prefabricados", {"OPER": 5200, "GRUA": 140, "PREF": 160}, "≈14 meses de obra"),
                           ("ELEC", "Cuadros, SAI y tuberías montados en obra", {"OPER": 3800, "GRUA": 30}, "pieza a pieza"),
                           ("ELEC", "Salas eléctricas y de refrigeración en patines (skids) prefabricados", {"OPER": 2100, "GRUA": 20, "SKID": 90}, "probados en fábrica")]),
}


def juegos(pl, solo=None):
    P = pl["procesos"]; piezas = pl["piezas"]; recs = list(pl["recursos"])
    nv = len(P) + 1
    c = np.zeros(nv); c[-1] = -1
    Au, bu = [], []
    for k, _, n in piezas:
        r = np.zeros(nv)
        for p, pr in enumerate(P):
            if pr[0] == k:
                r[p] = -1
        r[-1] = n; Au.append(r); bu.append(0)
    for rr in recs:
        r = np.zeros(nv)
        for p, pr in enumerate(P):
            r[p] = pr[2].get(rr, 0)
        Au.append(r); bu.append(pl["recursos"][rr][2])
    bounds = [(0, None)] * nv
    if solo is not None:
        for p in range(len(P)):
            if p not in solo:
                bounds[p] = (0, 0)
    res = linprog(c, A_ub=np.array(Au), b_ub=np.array(bu), bounds=bounds, method="highs")
    du = -res.ineqlin.marginals
    xx = res.x[:-1]
    return dict(lam=res.x[-1], x=xx, dual=dict(zip(recs, du[len(piezas):])),
                uso={rr: sum(P[p][2].get(rr, 0) * xx[p] for p in range(len(P))) for rr in recs})


JUEGOS = {}
for key, pl in PLANTAS.items():
    P = pl["procesos"]
    trad = [next(p for p, pr in enumerate(P) if pr[0] == k) for k, _, _ in pl["piezas"]]
    nuevo = [max(p for p, pr in enumerate(P) if pr[0] == k) for k, _, _ in pl["piezas"]]
    JUEGOS[key] = dict(opt=juegos(pl), trad=juegos(pl, trad), nuevo=juegos(pl, nuevo))

# =============================================================================
# 6. CAMINO CRÍTICO DE LA CONSTRUCCIÓN DEL CPD (días)
# =============================================================================
CPM = [("A", "Permisos, conexión a red y diseño", 120, []),
       ("B", "Movimiento de tierras y cimentación", 60, ["A"]),
       ("C", "Pedido y fabricación de transformadores de potencia", 330, ["A"]),
       ("D", "Pedido y fabricación de grupos electrógenos", 300, ["A"]),
       ("E", "Estructura y envolvente del edificio", 150, ["B"]),
       ("F", "Subestación y salas eléctricas", 90, ["C", "E"]),
       ("G", "Instalación de refrigeración", 100, ["E"]),
       ("H", "Instalación de grupos y depósitos de gasóleo", 45, ["D", "E"]),
       ("I", "Planta fotovoltaica, eólica y baterías", 240, ["A"]),
       ("J", "Racks, cableado de red e integración de servidores", 60, ["F", "G"]),
       ("K", "Puesta en marcha integrada (niveles 1 a 5) y prueba de carga 24/7", 45, ["J", "H", "I"])]
ES_, EF_ = {}, {}
for a in CPM:
    ES_[a[0]] = max([EF_[p] for p in a[3]], default=0); EF_[a[0]] = ES_[a[0]] + a[2]
T_CPD = max(EF_.values())
LS_, LF_ = {}, {}
for a in reversed(CPM):
    suc = [b[0] for b in CPM if a[0] in b[3]]
    LF_[a[0]] = min([LS_[s] for s in suc], default=T_CPD); LS_[a[0]] = LF_[a[0]] - a[2]
HOLG = {k: LS_[k] - ES_[k] for k in ES_}

# máxima producción de PCs con las horas del método base
FAB = {}
for g in ["PCO", "PCG"]:
    u = np.zeros(NB); u[IX[g]] = 1
    mb = FICHAS[g]["met"]["base"]
    FAB[g] = dict(base=Q[g], max_h=lp(max_bien=u, h_max=mb["sol"]["horas"])["t"],
                  max_hc=lp(max_bien=u, h_max=mb["sol"]["horas"], co2_max=mb["sol"]["co2"])["t"])

if __name__ == "__main__":
    print("NB", NB, "NA", NA, "rho", round(RHO, 4))
    for g in PRODUCTOS:
        fi = FICHAS[g]
        print(f"\n{g} q={fi['q']:,} takt={fi['takt_s']:.1f}s puestos={fi['puestos']} oper={fi['operarios']:.0f}")
        for k, m in fi["met"].items():
            print(f"  {k:5s} h={m['h_ud']:9.2f} ens={m['ens']:6.2f} co2={m['c_ud']:8.4f} MWh={m['e_ud']:7.3f} agua={m['agua_ud']:7.3f}",
                  "; ".join(f"{gg}:" + ",".join(f"{t}={w:.2f}" for t, w in p) for gg, p in m["mezcla"]))
    print("\nCPD por MW·año:", {k: (round(v["horas"] / MW_TI), round(v["co2"] / MW_TI, 1)) for k, v in CPD.items()})
    for r, s in CPD_REF.items():
        print("  ", r, round(s["horas"] / MW_TI), round(s["co2"] / MW_TI, 1))
    print("REF_OPT", REF_OPT, PUE_OPT)
    for k, d in DESP.items():
        print(f"DESP {k:5s} FV={d['S']:6.1f} EOL={d['W']:6.1f} BES={d['E']:7.1f} TGS={d['G']:5.1f} RED={d['R']:5.1f} "
              f"E={d['e_tot']:,.0f} red={d['red']:,.0f} fv={d['fv']:,.0f} eol={d['eol']:,.0f} gas={d['gas']:,.0f} co2={d['co2']:,.0f} h={d['horas']:,.0f} vert={d['vert']:,.0f}")
    print("CF fv", cf_fv.mean(), "eol", cf_eol.mean(), "pico", CARGA_PICO, "NGEN", N_GEN, "diesel48", DIESEL_48H)
    for k, r in JUEGOS.items():
        print(k, round(r["trad"]["lam"]), round(r["nuevo"]["lam"]), round(r["opt"]["lam"]), [round(v) for v in r["opt"]["x"]],
              {a: round(b, 4) for a, b in r["opt"]["dual"].items() if b > 1e-9})
    print("CPM", T_CPD, HOLG)
    print("FAB", FAB)

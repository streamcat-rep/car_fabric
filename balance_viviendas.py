"""
Balance entre lo que necesita el programa de 1.000.000 de viviendas (plan de máxima producción de Kantorovich,
con el mínimo CO2 en segunda etapa) y la producción industrial nacional de 2025 (INE, Encuesta Industrial Anual
de Productos, vía streamcat-rep.github.io/Produccion_Industrial_Nacional). No modifica modelo_viviendas.py.
"""
import json
import numpy as np
import modelo_viviendas as M

INE = json.load(open("datos/ine_2025_construccion.json", encoding="utf-8"))
IX = M.IX
PLZ_VIV = float(M.PLZ_PROV.sum() / M.N_VIV)     # plazas de comedor por vivienda del plan nacional (caso B)

# parámetros físicos por método (t por m² construido) para separar tipos de producto
REDONDO = {"trad": 0.035, "pref": 0.032, "imp": 0.025, "clt": 0.010, "mod": 0.015, "lsf": 0.012}   # armadura de hormigón
CHAPA_GALV = {"trad": 0.0, "pref": 0.0, "imp": 0.0, "clt": 0.005, "mod": 0.025, "lsf": 0.033}     # perfil conformado de chapa galvanizada
PERFIL_LAM = {"trad": 0.0, "pref": 0.0, "imp": 0.0, "clt": 0.0, "mod": 0.015, "lsf": 0.0}          # perfiles laminados (bastidor de módulo)
PLACA_YESO = {"lsf", "mod", "clt"}               # métodos que usan placa de yeso (el resto, yeso en pasta)


def caso(c):
    tipo = "VIV" + c
    s = M.MAXP_CO2[c]                       # máxima producción + mínimo CO2
    tasa = float(M.MAXP[c]["t"])            # viviendas al año
    z = s["z"]
    mix = M.mezcla_viv(z, tipo)
    lm = M.leontief(z)
    j = IX[tipo]
    m2 = M.M2C[tipo]
    col = lm["L"][:, j].copy()
    plz_mix = {}
    if c == "B":
        col = col + PLZ_VIV * lm["L"][:, IX["PLZ"]]
        tot = z[M.ID["plz_trad"]] + z[M.ID["plz_mod"]]
        plz_mix = {"trad": z[M.ID["plz_trad"]] / tot, "mod": z[M.ID["plz_mod"]] / tot}
    m2_plz = M.M2_PLAZA * PLZ_VIV if c == "B" else 0.0

    def por_metodo(tabla):
        v = sum(w * m2 * tabla[m] for m, w in mix.items())
        v += sum(w * m2_plz * tabla[m] for m, w in plz_mix.items())
        return v

    yso_m2 = {m: M.METODOS[m][1].get("YSO", 0) for m in M.METODOS}
    cer_m2 = {m: M.METODOS[m][1].get("CER", 0) for m in M.METODOS}
    clt_m2 = {m: (M.METODOS[m][1].get("MAD", 0) if m == "clt" else 0) for m in M.METODOS}
    A = c == "A"
    # (id, nombre, unidad, necesidad por vivienda, códigos INE, factor INE→unidad, cómo se calcula)
    items = [
        ("cem", "Cemento", "t", col[IX["CEM"]], ["2351121028", "2351121019", "2351129003"], 1,
         "Leontief: todo el cemento del hormigón, morteros, prefabricados y urbanización"),
        ("hor", "Hormigón preparado y prefabricado de hormigón", "t", col[IX["HOR"]], ["2363100009", "2361120001"], 1,
         "Leontief: hormigón in situ + elementos prefabricados"),
        ("red", "Acero: redondo y alambrón para hormigón armado", "t", por_metodo(REDONDO) + 0.1, ["2410621003", "2410613000"], 1,
         "armadura por m² según método + 0,1 t de urbanización"),
        ("gal", "Acero: chapa galvanizada (perfiles conformados en frío)", "t", por_metodo(CHAPA_GALV), ["2410513007"], 1,
         "estructura de acero ligero y módulos"),
        ("lam", "Acero: perfiles laminados en caliente (U, I, H y otros)", "t", por_metodo(PERFIL_LAM), ["2410711000", "2410712008", "2410713006", "2410714004"], 1,
         "bastidores de módulos 3D"),
        ("alu", "Perfiles de aluminio (extrusión)", "t", col[IX["ALU"]], ["2442225000", "2442223005"], 1,
         "Leontief: carpinterías, módulos, electrodomésticos, ascensor"),
        ("ven", "Ventanas y balconeras", "ud", 7.0, ["2512105003", "2223145002", "1623111003"], 1,
         "7 huecos por vivienda (aluminio, PVC o madera)"),
        ("vid", "Vidrio aislante de doble hoja", "m²", 14.0 if A else 13.0, ["2312133007"], 1, "superficie acristalada por vivienda"),
        ("cob", "Cobre refinado", "t", col[IX["COB"]], ["2444133005"], 1, "Leontief: cables, instalaciones, motores"),
        ("cab", "Cable eléctrico de baja tensión", "kg", (90.0 if A else 80.0) + (8.0 * PLZ_VIV if not A else 0), ["2732138001"], 1,
         "instalación de vivienda (y de comedor en B)"),
        ("tub", "Tubos de plástico (PVC, PE, PP)", "t", 0.19 + (0.01 * PLZ_VIV if not A else 0), ["2221215709", "2221215302", "2221215500"], 1,
         "fontanería, saneamiento y redes de urbanización"),
        ("lad", "Ladrillo cerámico", "m³", por_metodo(cer_m2) / 1.0, ["2332111001"], 1000,
         "cerámica de fachada y tabiquería según método (1 t ≈ 1 m³ aparente)"),
        ("baldosa", "Azulejos y baldosas cerámicas", "m²", (100.0 if A else 88.0) + (2.5 * PLZ_VIV if not A else 0), ["2331100006"], 1000,
         "pavimento + alicatado de baños y cocina"),
        ("san", "Aparatos sanitarios (inodoros, lavabos…)", "ud", 2.4 + (0.05 * PLZ_VIV if not A else 0), ["2342103007", "2342105002"], 1000,
         "1,2 baños × 2 piezas de porcelana"),
        ("placa", "Placa de yeso laminado", "m²", sum(w * m2 * yso_m2[m] * 100 for m, w in mix.items() if m in PLACA_YESO) + 10.0,
         ["2362105000", "2362109002"], 1000, "tabiques y trasdosados de métodos en seco + 10 m² de falso techo"),
        ("yeso", "Yeso y escayola", "t", sum(w * m2 * yso_m2[m] for m, w in mix.items() if m not in PLACA_YESO) + 0.1, ["2352200007"], 1,
         "guarnecidos en métodos húmedos"),
        ("lana", "Lana mineral (roca y vidrio)", "kg", col[IX["AIS"]] * 1000, ["2399191002", "2314129802"], 1, "Leontief: aislamiento"),
        ("pino", "Madera aserrada de pino (para CLT)", "m³", por_metodo(clt_m2) * 1.4, ["1610114004"], 1,
         "1,4 m³ de aserrado por m³ de CLT"),
        ("tab", "Tableros de partículas", "m³", 0.60 if A else 0.25, ["1621120008", "1621141908"], 1, "muebles de cocina, puertas y armarios"),
        ("pue", "Puertas de madera (con marco)", "ud", 7.0 if A else 6.0, ["1623115004"], 1, "puertas interiores + entrada"),
        ("mco", "Muebles de cocina (módulos)", "ud", 12.0 if A else 0.0, ["3102100004"], 1, "12 módulos por cocina"),
        ("pla", "Placas de cocción", "ud", 1.0 if A else 0.0, ["2751283002"], 1, ""),
        ("hor2", "Hornos de empotrar", "ud", 1.0 if A else 0.0, ["2751287003"], 1, ""),
        ("fri", "Frigoríficos", "ud", 1.0 if A else 0.0, ["2751111105", "2751113302"], 1, "en B no hay cocina (la nevera está en el comedor)"),
        ("lav", "Lavavajillas domésticos", "ud", 1.0 if A else 0.0, ["2751120009"], 1, ""),
        ("cam", "Campanas extractoras", "ud", 1.0 if A else 0.0, ["2751158106"], 1, ""),
        ("bdc", "Bombas de calor (aerotermia)", "ud", 1.0, ["2825138001"], 1, "climatización y agua caliente"),
        ("cua", "Cuadros eléctricos ≤ 1.000 V", "ud", 1.0 + (0.002 * PLZ_VIV if not A else 0), ["2712317008"], 1, "cuadro de vivienda"),
        ("asc", "Ascensores", "ud", 1 / 20, ["2822163006", "2822165001"], 1, "1 por cada 20 viviendas"),
        ("pin", "Pinturas al agua", "t", 0.06 if A else 0.055, ["2030115008", "2030117004"], 1, ""),
    ]
    filas = []
    for iid, nom, u, nec, cods, fac, como in items:
        qs = [INE["productos"][k]["q2025"] for k in cods]
        conocidos = [q for q in qs if q is not None]
        prod = sum(conocidos) * fac if conocidos else None
        parcial = len(conocidos) < len(qs)
        nec_anual = nec * tasa
        filas.append(dict(id=iid, nombre=nom, u=u, nec_viv=nec, nec_anual=nec_anual, nec_200k=nec * 200_000, nec_total=nec * M.N_VIV,
                          prod=prod, parcial=parcial, balance=(prod - nec_anual) if prod is not None else None,
                          cuota=(nec_anual / prod) if prod else None, codigos=cods, como=como))
    return dict(c=c, tasa=tasa, mix=mix, plz_mix=plz_mix, filas=filas, anios=M.N_VIV / tasa)


CASOS = {c: caso(c) for c in ("A", "B")}

if __name__ == "__main__":
    for c, r in CASOS.items():
        print(f"\n=== Caso {c}: {r['tasa']:,.0f} viv/año, mezcla {r['mix']} comedor {r['plz_mix']}")
        for fl in r["filas"]:
            prod = "sin dato" if fl["prod"] is None else f"{fl['prod']:,.0f}"
            bal = "" if fl["balance"] is None else f"{fl['balance']:,.0f}"
            cuo = "" if fl["cuota"] is None else f"{100 * fl['cuota']:.1f}%"
            print(f"  {fl['nombre'][:45]:45s} {fl['u']:3s} viv={fl['nec_viv']:10.3f} anual={fl['nec_anual']:14,.0f} prod={prod:>16} bal={bal:>16} cuota={cuo}")

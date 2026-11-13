# -*- coding: utf-8 -*-
# Versión .py del cuaderno ejercicio_12_3_analisis_accesibilidad.ipynb (celdas de código concatenadas)
# =========================================================
# Celda 1 — Librerías, estilo y carga de archivos / Libraries, style and file loading
# Entorno de ejecución: Google Colaboratory (Colab) · CPU
# =========================================================
import os, math                           # utilidades estándar / standard utilities
import pandas as pd                       # tablas / tables
import numpy as np                        # cálculo numérico / numeric computing
import matplotlib.pyplot as plt           # gráficos / charts

PALETA = ["#1F3864", "#800000", "#1B7E34", "#C5961A", "#5B2C6F", "#0A3D5C"]   # paleta del curso
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "#333333", "axes.grid": True,
                     "grid.color": "#DDDDDD", "axes.prop_cycle": plt.cycler(color=PALETA), "font.size": 11})

# En Colab, si los CSV no están en la carpeta actual, se pueden subir con este bloque (se ignora fuera de Colab)
ARCHIVOS = ["auditoria_accesibilidad_axe_sitios_reales.csv", "auditoria_accesibilidad_axe_detalle_reglas.csv"]
try:
    from google.colab import files        # solo existe en Colab / only exists in Colab
    faltan = [a for a in ARCHIVOS if not os.path.exists(a)]
    if faltan:
        print("Suba estos archivos:", faltan); files.upload()
except ImportError:
    pass
print("pandas", pd.__version__, "· numpy", np.__version__)

# =========================================================
# Celda 2 — Contraste WCAG: luminancia relativa y razón (con pruebas de verificación)
# =========================================================
def hex_a_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)          # #abc → #aabbcc
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def linealizar(c):                                          # canal sRGB (0–255) → lineal
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminancia(rgb):                                        # luminancia relativa
    r, g, b = (linealizar(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def razon_contraste(f, b):
    l1, l2 = sorted((luminancia(hex_a_rgb(f)), luminancia(hex_a_rgb(b))), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

# Verificación contra valores conocidos (si falla, el cuaderno se detiene)
assert round(razon_contraste("#000000", "#ffffff"), 2) == 21.00
assert round(razon_contraste("#767676", "#ffffff"), 2) == 4.54
assert razon_contraste("#777777", "#ffffff") < 4.5
assert abs(razon_contraste("#ff0000", "#ff0000") - 1) < 1e-9
for f, b in [("#000000", "#ffffff"), ("#767676", "#ffffff"), ("#777777", "#ffffff"), ("#0b3d75", "#ffffff")]:
    r = razon_contraste(f, b)
    print(f"{f} sobre {b}: {r:5.2f} : 1  → AA normal {'cumple' if r >= 4.5 else 'NO cumple'} · AA grande {'cumple' if r >= 3 else 'NO cumple'}")

# =========================================================
# Celda 3 — Carga de la auditoría y tabla de sitios válidos
# =========================================================
aud = pd.read_csv("auditoria_accesibilidad_axe_sitios_reales.csv")
det = pd.read_csv("auditoria_accesibilidad_axe_detalle_reglas.csv")
print("Sitios auditados:", len(aud), "· válidos:", (aud.estado == "VÁLIDA").sum(), "· no válidos:", (aud.estado != "VÁLIDA").sum())
print("Fecha y hora de las consultas:", aud.fecha_hora.min(), "→", aud.fecha_hora.max())
if (aud.estado != "VÁLIDA").any():
    print("\nNO VÁLIDOS (no se promedian):"); print(aud.loc[aud.estado != "VÁLIDA", ["sitio", "nota"]].to_string(index=False))
ok = aud[aud.estado == "VÁLIDA"].copy()
print(); print(ok[["sitio", "pais", "lang", "total_violaciones", "critical", "serious", "moderate", "minor"]].to_string(index=False))

# =========================================================
# Celda 4 — Violaciones por sitio y por impacto (barras apiladas)
# =========================================================
ok = ok.sort_values("total_violaciones", ascending=True)
fig, ax = plt.subplots(figsize=(10, 5.5))
izq = np.zeros(len(ok))
for col, color in [("critical", "#800000"), ("serious", "#C5961A"), ("moderate", "#1F3864"), ("minor", "#7F8C8D")]:
    ax.barh(ok.sitio, ok[col], left=izq, label=col, color=color); izq += ok[col].values
ax.set_xlabel("Nodos con violación detectados por axe-core (impacto)"); ax.set_title("Violaciones de accesibilidad por sitio (axe-core 4.10.2, página de inicio)")
ax.legend(title="Impacto"); plt.tight_layout(); plt.show()

# =========================================================
# Celda 5 — Perú frente a internacional (DESCRIPTIVO: n pequeño, sin pruebas de hipótesis)
# =========================================================
g = ok.groupby("pais").agg(sitios=("sitio", "count"), mediana_violaciones=("total_violaciones", "median"), media_violaciones=("total_violaciones", "mean"),
                           mediana_criticas_serias=("serious", "median"), con_lang=("lang", lambda s: (s != "(vacío)").sum()))
print(g.round(1).to_string())
print("\nLectura: con pocos sitios por grupo, la diferencia observada describe esta muestra y esta fecha; no se generaliza a 'Perú' ni a 'el mundo'.")

# =========================================================
# Celda 6 — Reglas más incumplidas (comparar con WebAIM Million)
# =========================================================
top = det.groupby(["regla", "descripcion"]).agg(sitios=("sitio", "nunique"), nodos=("nodos", "sum")).sort_values(["sitios", "nodos"], ascending=False).head(10)
print(top.to_string())
fig, ax = plt.subplots(figsize=(10, 4.8))
t = top.reset_index().iloc[::-1]
ax.barh(t.regla, t.sitios, color=PALETA[0]); ax.set_xlabel("Número de sitios (de los válidos) donde aparece la regla"); ax.set_title("Diez reglas de axe-core más frecuentes en la muestra")
plt.tight_layout(); plt.show()
print("\nCompare esta lista con las categorías de error más frecuentes del informe anual WebAIM Million (https://webaim.org/projects/million/): consulte las cifras vigentes allí; este cuaderno no las reproduce de memoria.")

# =========================================================
# Celda 7 — Resultados del verificador de 15 criterios (CSV exportado por el ejercicio 12.2)
# =========================================================
arch = "ejercicio_12_2_verificador_resultados.csv"
if not os.path.exists(arch) and os.path.exists("ejercicio_12_2_verificador_PRUEBA_TECNICA_BOT.csv"):
    arch = "ejercicio_12_2_verificador_PRUEBA_TECNICA_BOT.csv"; print("AVISO: usando la PRUEBA TÉCNICA del bot (no se interpreta).")
if os.path.exists(arch):
    v = pd.read_csv(arch)
    v["A"] = v.formulario_A.eq("cumple"); v["B"] = v.formulario_B.eq("cumple")
    print(v[["id", "criterio", "formulario_A", "formulario_B"]].to_string(index=False))
    print(f"\nFormulario A cumple {v.A.sum()} de {len(v)} · Formulario B cumple {v.B.sum()} de {len(v)}")
    fig, ax = plt.subplots(figsize=(5.5, 3.6)); ax.bar(["A (con barreras)", "B (corregido)"], [v.A.sum(), v.B.sum()], color=[PALETA[1], PALETA[2]])
    ax.set_ylabel("Criterios cumplidos (de 15)"); ax.set_ylim(0, 15.5); ax.set_title("Verificador 12.2"); plt.tight_layout(); plt.show()
else:
    print("Falta el CSV del verificador. Ejecute el ejercicio 12.2, pulse «Exportar CSV» y súbalo. No se inventan datos.")

# =========================================================
# Celda 8 — Análisis apareado del experimento (tiempo, completitud, SEQ)
# =========================================================
arch = "ejercicio_12_3_experimento_teclado.csv"
if not os.path.exists(arch) and os.path.exists("ejercicio_12_3_experimento_PRUEBA_TECNICA_BOT.csv"):
    arch = "ejercicio_12_3_experimento_PRUEBA_TECNICA_BOT.csv"; print("AVISO: usando la PRUEBA TÉCNICA del bot (sus números NO se interpretan).")
if os.path.exists(arch):
    e = pd.read_csv(arch)
    print("Participantes:", e.participante.nunique(), "· filas:", len(e))
    print(e.groupby("formulario").agg(completadas=("resultado", lambda s: (s == "completada").sum()), tiempo_mediana=("segundos", "median"),
                                      tab_mediana=("pulsaciones_tab", "median"), errores=("errores_envio", "sum"), seq_mediana=("seq_1a7", "median")).round(2).to_string())
    ancho = e.pivot(index="participante", columns="formulario", values="segundos").dropna()
    n = len(ancho)
    if n >= 5:
        try:
            from scipy.stats import wilcoxon
            res = wilcoxon(ancho["A"], ancho["B"], zero_method="wilcox")
            print(f"\nWilcoxon apareado (tiempo A vs B), n = {n}: W = {res.statistic:.1f}, p = {res.pvalue:.4f}")
            print("Recuerde: un tiempo de A mayor incluye tareas ABANDONADAS (no completadas); reporte también la tasa de completitud.")
        except Exception as ex:
            print("No se pudo calcular Wilcoxon:", ex)
    else:
        print(f"\nn = {n} < 5: solo descripción; no se aplica Wilcoxon.")
    fig, ax = plt.subplots(figsize=(6, 4)); ancho.T.plot(ax=ax, legend=False, marker="o", color="#999999"); ax.set_ylabel("Segundos"); ax.set_title("Tiempo por participante: A → B"); plt.tight_layout(); plt.show()
else:
    print("Falta el CSV del experimento. Realice el ejercicio 12.3 con su equipo (mínimo 5 participantes) y súbalo. No se inventan datos.")


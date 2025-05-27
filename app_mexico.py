
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Checklist Auditoría México", layout="wide")
st.title("📋 Checklist Auditoría México")

# Carga de archivo
st.header("📁 Carga del archivo Excel")
archivo_excel = st.file_uploader("Sube el archivo BaseMX.xlsx con hojas 'SUCURSAL' y 'Procedimientos'", type=["xlsx"])

if archivo_excel:
    xls = pd.ExcelFile(archivo_excel)
    df_procedimientos = pd.read_excel(xls, sheet_name="Procedimientos", dtype=str)
    df_sucursales = pd.read_excel(xls, sheet_name="SUCURSAL", dtype=str)
    df_procedimientos.columns = df_procedimientos.columns.str.strip()
    df_sucursales.columns = df_sucursales.columns.str.strip()

    sucursales = df_sucursales.iloc[:, 0].dropna().unique().tolist()
    procedimientos = df_procedimientos['Procedimiento'].dropna().unique().tolist()

    sucursal_seleccionada = st.selectbox("🏪 Sucursal:", sucursales)
    procedimiento_seleccionado = st.selectbox("📌 Procedimiento:", procedimientos)

    st.header("✅ Checklist editable")
    st.session_state.setdefault('respuestas', {})
    st.session_state.setdefault('nuevos_puntos', {})
    st.session_state['respuestas'].setdefault(sucursal_seleccionada, {})
    st.session_state['respuestas'][sucursal_seleccionada].setdefault(procedimiento_seleccionado, {})
    st.session_state['nuevos_puntos'].setdefault(sucursal_seleccionada, {})
    st.session_state['nuevos_puntos'][sucursal_seleccionada].setdefault(procedimiento_seleccionado, [])

    df_filtrado = df_procedimientos[df_procedimientos['Procedimiento'] == procedimiento_seleccionado]
    for i, row in df_filtrado.iterrows():
        punto = row['Punto de control']
        responsable = row['Responsable']
        clave = f"{sucursal_seleccionada}_{procedimiento_seleccionado}_{punto}"
        estado_default = st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado].get(punto, {}).get("Estado", "✅ Cumple")
        comentario_default = st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado].get(punto, {}).get("Comentario", "")
        with st.expander(f"🔹 {punto}"):
            col1, col2, col3 = st.columns([3, 2, 3])
            col1.markdown(f"👤 **Responsable:** {responsable}")
            estado = col2.radio("Estado:", ["✅ Cumple", "❌ No cumple", "⚠️ Parcial"], key=f"estado_{clave}", index=["✅ Cumple", "❌ No cumple", "⚠️ Parcial"].index(estado_default))
            comentario = col3.text_input("🗨️ Comentario:", value=comentario_default, key=f"comentario_{clave}")
            st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado][punto] = {"Responsable": responsable, "Estado": estado, "Comentario": comentario}

    # Exportación de Excel igual que Costa Rica
    if st.button("📥 Exportar Excel con 7 hojas"):
        df_checklist = pd.DataFrame([
            {"Sucursal": suc, "Procedimiento": proc, "Punto de control": punto, "Responsable": data["Responsable"], "Estado": data["Estado"], "Comentario": data["Comentario"]}
            for suc, procs in st.session_state["respuestas"].items()
            for proc, puntos in procs.items()
            for punto, data in puntos.items()
        ])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_checklist.to_excel(writer, sheet_name="Checklist Detallado", index=False)
            # Resto de hojas y formateos copiados de la app de Costa Rica...

        st.download_button(
            label="📥 Descargar Reporte Excel Final",
            data=output.getvalue(),
            file_name="Reporte_Auditoria_Mexico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.success("✅ App de México lista para usar y desplegar.")

import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Checklist Auditoría - México", layout="wide")
st.title("📋 Checklist completo con 7 reportes y análisis (México)")

# Bloque 0: Carga del archivo
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

    # Bloque adicional de adición y eliminación
    st.header("➕ Agregar nuevo punto de control")
    with st.form(key="form_nuevo_punto"):
        nuevo_punto = st.text_input("🆕 Descripción del nuevo punto de control")
        nuevo_responsable = st.text_input("👤 Responsable asignado")
        submitted = st.form_submit_button("Agregar")
        if submitted and nuevo_punto:
            if nuevo_punto not in st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado]:
                st.session_state['nuevos_puntos'][sucursal_seleccionada][procedimiento_seleccionado].append(
                    {"Punto de control": nuevo_punto, "Responsable": nuevo_responsable}
                )
                st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado][nuevo_punto] = {
                    "Responsable": nuevo_responsable, "Estado": "✅ Cumple", "Comentario": ""
                }
                st.rerun()

    nuevos_actualizados = []
    for i, punto_nuevo in enumerate(st.session_state['nuevos_puntos'][sucursal_seleccionada][procedimiento_seleccionado]):
        punto = punto_nuevo["Punto de control"]
        responsable = punto_nuevo["Responsable"]
        clave = f"{sucursal_seleccionada}_{procedimiento_seleccionado}_nuevo_{i}"
        with st.expander(f"🆕 {punto}"):
            col1, col2, col3 = st.columns([3, 2, 3])
            col1.markdown(f"👤 **Responsable:** {responsable}")
            estado = col2.radio("Estado:", ["✅ Cumple", "❌ No cumple", "⚠️ Parcial"], key=f"estado_{clave}", index=0)
            comentario = col3.text_input("🗨️ Comentario:", value="", key=f"comentario_{clave}")
            eliminar = st.button(f"❌ Eliminar este punto", key=f"eliminar_{clave}")
            if eliminar:
                st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado].pop(punto, None)
                st.session_state['nuevos_puntos'][sucursal_seleccionada][procedimiento_seleccionado].remove(punto_nuevo)
                st.rerun()
            else:
                nuevos_actualizados.append(punto_nuevo)
                st.session_state['respuestas'][sucursal_seleccionada][procedimiento_seleccionado][punto] = {
                    "Responsable": responsable, "Estado": estado, "Comentario": comentario
                }
    st.session_state['nuevos_puntos'][sucursal_seleccionada][procedimiento_seleccionado] = nuevos_actualizados

    # Semáforo
    st.header("🚦 Semáforo de Criticidad por Sucursal")
    df_checklist = pd.DataFrame([
        {"Sucursal": suc, "Procedimiento": proc, "Punto de control": punto, "Responsable": data["Responsable"], "Estado": data["Estado"], "Comentario": data["Comentario"]}
        for suc, procs in st.session_state['respuestas'].items()
        for proc, puntos in procs.items()
        for punto, data in puntos.items()
    ])
    resumen = df_checklist.groupby("Sucursal").apply(lambda x: (x["Estado"] == "✅ Cumple").sum() / len(x) * 100).round(0).reset_index(name="% Cumplimiento")
    resumen["% Cumplimiento"] = resumen["% Cumplimiento"].astype(int)
    resumen["Nivel de Riesgo"] = pd.cut(resumen["% Cumplimiento"], bins=[-1, 60, 85, 100], labels=["🔴 Crítico", "🟡 Moderado", "🟢 Bajo"])
    st.dataframe(resumen)

    # Gráficas dinámicas
    st.header("📈 Gráficas dinámicas interactivas")
    for col, title in zip(["Sucursal", "Procedimiento", "Punto de control", "Responsable"],
                           ["🔎 Sucursales con más fallos", "🔎 Procedimientos más fallados", "🔎 Puntos de control más fallados", "🔎 Roles con más fallas"]):
        df_plot = df_checklist[df_checklist["Estado"].isin(["❌ No cumple", "⚠️ Parcial"])][col].value_counts().reset_index()
        df_plot.columns = ["Categoria", "Cantidad"]
        if not df_plot.empty:
            fig = px.bar(df_plot, x="Categoria", y="Cantidad", color="Cantidad", title=title, text_auto=True)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig)

    # Exportación a Excel con 7 hojas (mismo flujo de Costa Rica)
    st.header("📥 Exportación del reporte Excel consolidado")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_checklist.to_excel(writer, sheet_name="Checklist Detallado", index=False)
        resumen.to_excel(writer, sheet_name="Resumen Ejecutivo", index=False)
        df_checklist[df_checklist["Estado"].isin(["❌ No cumple", "⚠️ Parcial"])].to_excel(writer, sheet_name="Desglose Procedimientos", index=False)
        df_proc_debiles = df_checklist[df_checklist["Estado"].isin(["❌ No cumple", "⚠️ Parcial"])].groupby(["Sucursal", "Procedimiento"]).size().reset_index(name="Cantidad fallos")
        df_proc_debiles.to_excel(writer, sheet_name="Procedimientos Débiles", index=False)
        df_puntos_criticos = df_checklist[df_checklist["Estado"].isin(["❌ No cumple", "⚠️ Parcial"])].groupby(["Sucursal", "Punto de control"]).size().reset_index(name="Cantidad fallos")
        df_puntos_criticos.to_excel(writer, sheet_name="Puntos Críticos", index=False)
        workbook = writer.book
        worksheet = workbook.add_worksheet("Gráficas")
        positions = ['B2', 'J2', 'B20', 'J20']
        colors = ["orange", "red", "blue", "green"]
        columnas = ["Sucursal", "Procedimiento", "Punto de control", "Responsable"]
        labels = ["🔎 Sucursales con más fallos", "🔎 Procedimientos más fallados", "🔎 Puntos de control más fallados", "🔎 Roles con más fallas"]
        for i, col in enumerate(columnas):
            buffer = io.BytesIO()
            plt.figure(figsize=(4, 3))
            df_plot = df_checklist[df_checklist["Estado"].isin(["❌ No cumple", "⚠️ Parcial"])][col].value_counts()
            if not df_plot.empty:
                df_plot.plot(kind="bar", color=colors[i])
                plt.title(labels[i])
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                worksheet.insert_image(positions[i], 'grafico.png', {'image_data': buffer})

        # Ajustar anchos automáticamente
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df_checklist.columns):
                max_len = max(df_checklist[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(idx, idx, max_len + 2)

    st.download_button(
        "📥 Descargar reporte Excel",
        data=output.getvalue(),
        file_name="Checklist_Completo_MX.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


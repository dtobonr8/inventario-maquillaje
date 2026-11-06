import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Ventas y Abonos - Maquillaje",
    page_icon="💄",
    layout="wide"
)

DATA_FILE = "maquillaje_data.json"

# Cargar y Guardar Datos
def cargar_datos():
    estructura_base = {
        "clientes": [],
        "ventas_credito": [],
        "abonos": []
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                datos = json.load(f)
                for key in estructura_base:
                    if key not in datos:
                        datos[key] = estructura_base[key]
                return datos
        except:
            return estructura_base
    return estructura_base

def guardar_datos(datos):
    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=4)

datos = cargar_datos()

st.title("💄 Sistema de Control de Maquillaje: Ventas y Abonos")
st.caption("Administra clientes, cuentas por cobrar, abonos parciales y saldos pendientes.")

# Navegación
opcion = st.sidebar.radio(
    "Navegación",
    [
        "👥 Clientes", 
        "🛍️ Registrar Venta / Crédito", 
        "💵 Registrar Abono", 
        "📊 Estado de Cuentas (Sábana)"
    ]
)

# ----------------------------------------------------
# 1. MÓDULO DE CLIENTES
# ----------------------------------------------------
if opcion == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    
    with st.form("form_cliente", clear_on_submit=True):
        nombre = st.text_input("Nombre de la Clienta / Cliente")
        telefono = st.text_input("Teléfono / WhatsApp")
        
        btn = st.form_submit_button("Guardar Cliente")
        if btn:
            if not nombre.strip():
                st.warning("⚠️ Ingresa el nombre del cliente.")
            else:
                nuevo = {
                    "id": len(datos["clientes"]) + 1,
                    "nombre": nombre.strip(),
                    "telefono": telefono.strip()
                }
                datos["clientes"].append(nuevo)
                guardar_datos(datos)
                st.success(f"✅ Cliente '{nombre}' registrado con éxito.")

    st.subheader("📋 Listado de Clientes")
    if datos["clientes"]:
        st.dataframe(pd.DataFrame(datos["clientes"]), use_container_width=True)
    else:
        st.info("No hay clientes registrados aún.")

# ----------------------------------------------------
# 2. MÓDULO DE REGISTRAR VENTA / CRÉDITO
# ----------------------------------------------------
elif opcion == "🛍️ Registrar Venta / Crédito":
    st.header("🛍️ Registrar Venta o Cuenta por Cobrar")
    st.caption("Registra los productos entregados y el valor total que el cliente queda debiendo.")

    if not datos["clientes"]:
        st.warning("⚠️ Primero registra clientes en la sección anterior.")
    else:
        clientes_dict = {f"{c['id']} - {c['nombre']}": c for c in datos["clientes"]}
        
        with st.form("form_venta", clear_on_submit=True):
            cli_sel = st.selectbox("Seleccionar Cliente", list(clientes_dict.keys()))
            cliente_info = clientes_dict[cli_sel]
            
            col1, col2 = st.columns(2)
            with col1:
                detalles_productos = st.text_area("Detalle de Productos (Ej. 5 labiales, 1 polvo)")
                monto_total = st.number_input("Valor Total del Credito / Deuda ($)", min_value=1000, step=1000)
            with col2:
                fecha_venta = st.date_input("Fecha de la Venta", value=date.today())
                
            btn_v = st.form_submit_button("Registrar Venta a Crédito")
            if btn_v:
                venta_rec = {
                    "id": len(datos["ventas_credito"]) + 1,
                    "cliente_id": cliente_info["id"],
                    "nombre_cliente": cliente_info["nombre"],
                    "detalles": detalles_productos.strip(),
                    "monto_total": monto_total,
                    "fecha": str(fecha_venta)
                }
                datos["ventas_credito"].append(venta_rec)
                guardar_datos(datos)
                st.success(f"✅ Venta registrada por ${monto_total:,.0f} para {cliente_info['nombre']}.")

    st.subheader("📋 Historial de Ventas y Créditos Activos")
    if datos["ventas_credito"]:
        st.dataframe(pd.DataFrame(datos["ventas_credito"]), use_container_width=True)
    else:
        st.info("No hay ventas registradas.")

# ----------------------------------------------------
# 3. MÓDULO DE REGISTRAR ABONO
# ----------------------------------------------------
elif opcion == "💵 Registrar Abono":
    st.header("💵 Registrar Abono Parcial")
    st.caption("Ingresa los abonos que hacen los clientes (ej. si debe $50.000 y abona $27.000).")

    if not datos["ventas_credito"]:
        st.warning("⚠️ No hay créditos o ventas registradas para abonar.")
    else:
        opciones_ventas = {}
        for v in datos["ventas_credito"]:
            abonos_previos = sum([a.get("monto_abono", 0) for a in datos["abonos"] if a.get("venta_id") == v["id"]])
            saldo_pendiente = v["monto_total"] - abonos_previos
            
            if saldo_pendiente > 0:
                label = f"Venta #{v['id']} - {v['nombre_cliente']} | Total: ${v['monto_total']:,.0f} | Debe Actual: ${saldo_pendiente:,.0f}"
                opciones_ventas[label] = {"venta": v, "saldo": saldo_pendiente}

        if not opciones_ventas:
            st.success("🎉 ¡Todas las ventas registradas se encuentran totalmente pagadas!")
        else:
            with st.form("form_abono", clear_on_submit=True):
                venta_sel_str = st.selectbox("Seleccionar Deuda / Venta del Cliente", list(opciones_ventas.keys()))
                info_sel = opciones_ventas[venta_sel_str]
                v_info = info_sel["venta"]
                saldo_actual = info_sel["saldo"]
                
                col1, col2 = st.columns(2)
                with col1:
                    monto_abono = st.number_input("Valor del Abono de Hoy ($)", min_value=1000, max_value=float(saldo_actual), step=1000)
                with col2:
                    fecha_abono = st.date_input("Fecha del Abono", value=date.today())
                    
                nota_abono = st.text_input("Observación (Opcional)", placeholder="Ej. Abono parcial en efectivo")
                
                btn_ab = st.form_submit_button("Guardar Abono")
                if btn_ab:
                    reg_abono = {
                        "venta_id": v_info["id"],
                        "cliente_id": v_info["cliente_id"],
                        "nombre_cliente": v_info["nombre_cliente"],
                        "monto_abono": monto_abono,
                        "fecha": str(fecha_abono),
                        "observacion": nota_abono.strip() if nota_abono else "Abono registrado"
                    }
                    datos["abonos"].append(reg_abono)
                    guardar_datos(datos)
                    
                    nuevo_saldo = saldo_actual - monto_abono
                    st.success(f"✅ ¡Abono de ${monto_abono:,.0f} registrado con éxito! El nuevo saldo pendiente es de ${nuevo_saldo:,.0f}.")

    st.subheader("📋 Historial de Abonos Realizados")
    if datos["abonos"]:
        st.dataframe(pd.DataFrame(datos["abonos"]), use_container_width=True)
    else:
        st.info("Aún no hay abonos registrados.")

# ----------------------------------------------------
# 4. ESTADO DE CUENTAS / SÁBANA
# ----------------------------------------------------
elif opcion == "📊 Estado de Cuentas (Sábana)":
    st.header("📊 Sábana de Control de Deudores y Saldos")
    st.caption("Resumen detallado de cuánto compró cada cliente, cuánto ha abonado y cuánto debe exactamente en tiempo real.")

    if not datos["clientes"]:
        st.warning("⚠️ No hay clientes registrados.")
    else:
        resumen_list = []
        for c in datos["clientes"]:
            ventas_cli = [v for v in datos["ventas_credito"] if v["cliente_id"] == c["id"]]
            total_comprado = sum([v["monto_total"] for v in ventas_cli])
            
            abonos_cli = [a for a in datos["abonos"] if a["cliente_id"] == c["id"]]
            total_abonado = sum([a["monto_abono"] for a in abonos_cli])
            
            saldo_pendiente = total_comprado - total_abonado
            
            resumen_list.append({
                "ID": c["id"],
                "Cliente": c["nombre"],
                "Teléfono": c["telefono"],
                "Total Deuda Inicial ($)": total_comprado,
                "Total Abonado ($)": total_abonado,
                "Saldo Pendiente ($)": saldo_pendiente
            })
            
        df_resumen = pd.DataFrame(resumen_list)
        
        st.dataframe(df_resumen.style.format({
            "Total Deuda Inicial ($)": "${:,.0f}",
            "Total Abonado ($)": "${:,.0f}",
            "Saldo Pendiente ($)": "${:,.0f}"
        }), use_container_width=True)

        st.divider()
        csv_data = df_resumen.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Estado de Cuentas (CSV)",
            data=csv_data,
            file_name="estado_cuentas_maquillaje.csv",
            mime="text/csv"
        )
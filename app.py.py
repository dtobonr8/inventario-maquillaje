import streamlit as st
import pandas as pd
import os
import io

DB_FILE = 'inventario_maquillaje.xlsx'

def normalizar_nombre(nombre):
    """Transforma cualquier texto escrito en mayúsculas/minúsculas a un formato unificado (Title Case)."""
    if not nombre or pd.isna(nombre):
        return ""
    return " ".join(nombre.strip().split()).title()

def cargar_datos():
    if not os.path.exists(DB_FILE):
        # Si no existe el archivo, crear la estructura base limpia
        df_prod = pd.DataFrame(columns=['ID', 'MARCA', 'PRODUCTO', 'COSTO', 'PRECIO', 'STOCK'])
        df_vent = pd.DataFrame(columns=['ID_VENTA', 'FECHA', 'CLIENTE', 'PRODUCTO', 'CANTIDAD', 'VALOR_UNITARIO', 'TOTAL', 'ESTADO'])
        df_comp = pd.DataFrame(columns=['ID_COMPRA', 'FECHA', 'PRODUCTO', 'CANTIDAD', 'COSTO_TOTAL'])
        with pd.ExcelWriter(DB_FILE) as writer:
            df_prod.to_excel(writer, sheet_name='PRODUCTOS', index=False)
            df_vent.to_excel(writer, sheet_name='VENTAS', index=False)
            df_comp.to_excel(writer, sheet_name='COMPRAS', index=False)

    productos = pd.read_excel(DB_FILE, sheet_name='PRODUCTOS')
    ventas = pd.read_excel(DB_FILE, sheet_name='VENTAS')
    compras = pd.read_excel(DB_FILE, sheet_name='COMPRAS')
    
    # Asegurar que los nombres existentes en ventas estén unificados
    if 'CLIENTE' in ventas.columns and not ventas.empty:
        ventas['CLIENTE'] = ventas['CLIENTE'].apply(normalizar_nombre)
        
    return productos, ventas, compras

def guardar_datos(productos, ventas, compras):
    with pd.ExcelWriter(DB_FILE) as writer:
        productos.to_excel(writer, sheet_name='PRODUCTOS', index=False)
        ventas.to_excel(writer, sheet_name='VENTAS', index=False)
        compras.to_excel(writer, sheet_name='COMPRAS', index=False)

def generar_excel_respaldo(productos, ventas, compras):
    """Genera un archivo Excel binario en memoria con las 3 pestañas para descargar de inmediato."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        productos.to_excel(writer, sheet_name='PRODUCTOS', index=False)
        ventas.to_excel(writer, sheet_name='VENTAS', index=False)
        compras.to_excel(writer, sheet_name='COMPRAS', index=False)
    return output.getvalue()

st.set_page_config(page_title="Stock Maquillaje", page_icon="💄", layout="wide")

# Control de Clave de Acceso
PASSWORD_CORRECTA = "maquillaje2026"
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema de Maquillaje")
    clave = st.text_input("Ingresa la clave de acceso:", type="password")
    if st.button("Entrar"):
        if clave == PASSWORD_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

productos, ventas, compras = cargar_datos()

# Menú lateral
opcion = st.sidebar.radio("📌 MENÚ", [
    "📊 Estado General", 
    "🛍️ Registrar Venta", 
    "📦 Registrar Compra / Stock", 
    "💳 Cuentas por Cobrar", 
    "📄 Reportes de Ventas"
])

# --- SECCIÓN DE RESPALDO EN BARRA LATERAL ---
st.sidebar.divider()
st.sidebar.subheader("💾 Respaldo de Base de Datos")
st.sidebar.caption("Descarga una copia actualizada de tu Excel con todos los cambios para respaldar tu información.")

excel_bytes = generar_excel_respaldo(productos, ventas, compras)
st.sidebar.download_button(
    label="📥 Descargar Excel Actualizado",
    data=excel_bytes,
    file_name="inventario_maquillaje.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# --- MODULO 1: ESTADO GENERAL ---
if opcion == "📊 Estado General":
    st.title("💄 Resumen de Inventario y Ventas")
    
    pendientes = ventas[ventas['ESTADO'] == 'PENDIENTE']['TOTAL'].sum() if not ventas.empty else 0
    pagado = ventas[ventas['ESTADO'] == 'PAGADO']['TOTAL'].sum() if not ventas.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Unidades en Stock", int(productos['STOCK'].sum()) if not productos.empty else 0)
    col2.metric("Por Cobrar (Deudas)", f"${pendientes:,.0f}")
    col3.metric("Ventas Cobradas", f"${pagado:,.0f}")
    
    st.subheader("📦 Stock de Productos")
    marcas_unicas = list(productos['MARCA'].dropna().unique()) if not productos.empty else []
    filtro_marca = st.selectbox("Filtrar por Marca (Opcional)", ["TODAS"] + marcas_unicas)
    df_ver = productos if filtro_marca == "TODAS" else productos[productos['MARCA'] == filtro_marca]
    st.dataframe(df_ver[['MARCA', 'PRODUCTO', 'COSTO', 'PRECIO', 'STOCK']], use_container_width=True)

# --- MODULO 2: REGISTRAR VENTA ---
elif opcion == "🛍️ Registrar Venta":
    st.title("🛍️ Registrar Venta (Disminuye Stock)")
    
    if productos.empty:
        st.warning("⚠️ No hay productos cargados en el inventario.")
    else:
        # Limpiar posibles valores nulos (NaN) en MARCA o PRODUCTO para prevenir fallos
        productos['MARCA'] = productos['MARCA'].fillna("SIN MARCA").astype(str)
        productos['PRODUCTO'] = productos['PRODUCTO'].fillna("SIN NOMBRE").astype(str)
        
        prod_lista = productos['MARCA'] + " - " + productos['PRODUCTO']
        prod_sel = st.selectbox("Selecciona Producto", prod_lista)
        
        # Búsqueda segura del índice para evitar IndexError
        resultados_idx = prod_lista[prod_lista == prod_sel].index
        if len(resultados_idx) == 0:
            st.error("⚠️ El producto seleccionado no es válido o está incompleto.")
            st.stop()
            
        idx = resultados_idx[0]
        stock_actual = int(productos.loc[idx, 'STOCK'])
        precio_sugerido = float(productos.loc[idx, 'PRECIO'])
        
        st.info(f" Stock disponible: **{stock_actual}** | Precio Base: **${precio_sugerido:,.0f}**")
        
        cliente_input = st.text_input("Nombre del Cliente")
        cliente = normalizar_nombre(cliente_input)
        
        cantidad = st.number_input("Cantidad Vendida", min_value=1, value=1)
        precio_venta = st.number_input("Precio Venta Unitario ($)", value=precio_sugerido)
        estado = st.selectbox("Estado del Pago", ["PAGADO", "PENDIENTE"])
        
        if st.button("🚀 Confirmar Venta"):
            if stock_actual < cantidad:
                st.error("⚠️ No hay suficiente stock para esta venta.")
            elif not cliente:
                st.error("⚠️ Por favor escribe el nombre del cliente.")
            else:
                total = cantidad * precio_venta
                # Actualizar stock
                productos.loc[idx, 'STOCK'] -= cantidad
                
                # Registrar venta
                nueva_venta = {
                    'ID_VENTA': len(ventas) + 1,
                    'FECHA': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                    'CLIENTE': cliente,
                    'PRODUCTO': prod_sel,
                    'CANTIDAD': cantidad,
                    'VALOR_UNITARIO': precio_venta,
                    'TOTAL': total,
                    'ESTADO': estado
                }
                ventas = pd.concat([ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
                guardar_datos(productos, ventas, compras)
                st.success(f"✅ Venta registrada a **{cliente}** por ${total:,.0f}. Stock actualizado.")

# --- MODULO 3: REGISTRAR COMPRA / PRODUCTO NUEVO ---
elif opcion == "📦 Registrar Compra / Stock":
    st.title("📦 Entradas de Mercancía (Aumenta Stock)")
    
    tipo = st.radio("¿Qué deseas ingresar?", ["Aumentar Stock de Producto Existente", "Crear Producto Nuevo"])
    
    if tipo == "Aumentar Stock de Producto Existente":
        if productos.empty:
            st.warning("⚠️ No hay productos para reabastecer.")
        else:
            productos['MARCA'] = productos['MARCA'].fillna("SIN MARCA").astype(str)
            productos['PRODUCTO'] = productos['PRODUCTO'].fillna("SIN NOMBRE").astype(str)
            
            prod_lista = productos['MARCA'] + " - " + productos['PRODUCTO']
            prod_sel = st.selectbox("Selecciona Producto a Reabastecer", prod_lista)
            idx = prod_lista[prod_lista == prod_sel].index[0]
            
            cant_compra = st.number_input("Cantidad Comprada", min_value=1, value=1)
            costo_unitario = st.number_input("Costo Unitario ($)", value=float(productos.loc[idx, 'COSTO']))
            
            if st.button("➕ Sumar al Stock"):
                productos.loc[idx, 'STOCK'] += cant_compra
                productos.loc[idx, 'COSTO'] = costo_unitario
                
                nueva_compra = {
                    'ID_COMPRA': len(compras) + 1,
                    'FECHA': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                    'PRODUCTO': prod_sel,
                    'CANTIDAD': cant_compra,
                    'COSTO_TOTAL': cant_compra * costo_unitario
                }
                compras = pd.concat([compras, pd.DataFrame([nueva_compra])], ignore_index=True)
                guardar_datos(productos, ventas, compras)
                st.success(f"✅ Se agregaron {cant_compra} unidades al stock de {prod_sel}.")

    else:
        nueva_marca = st.text_input("Marca").strip().upper()
        nuevo_prod = st.text_input("Nombre del Producto").strip().upper()
        nuevo_costo = st.number_input("Costo Unitario ($)", min_value=0.0, value=10000.0)
        nuevo_precio = st.number_input("Precio Venta ($)", min_value=0.0, value=15000.0)
        nuevo_stock = st.number_input("Stock Inicial", min_value=1, value=1)
        
        if st.button("✨ Guardar Nuevo Producto"):
            if not nueva_marca or not nuevo_prod:
                st.error("Escribe la marca y el nombre del producto.")
            else:
                nuevo_reg = {
                    'ID': len(productos) + 1,
                    'MARCA': nueva_marca,
                    'PRODUCTO': nuevo_prod,
                    'COSTO': nuevo_costo,
                    'PRECIO': nuevo_precio,
                    'STOCK': nuevo_stock
                }
                productos = pd.concat([productos, pd.DataFrame([nuevo_reg])], ignore_index=True)
                guardar_datos(productos, ventas, compras)
                st.success(f"✅ Producto '{nueva_marca} - {nuevo_prod}' creado con éxito.")

# --- MODULO 4: CUENTAS POR COBRAR ---
elif opcion == "💳 Cuentas por Cobrar":
    st.title("💳 Control de Deudores, Cobros y Abonos")
    
    pendientes_df = ventas[ventas['ESTADO'] == 'PENDIENTE']
    
    if pendientes_df.empty:
        st.balloons()
        st.success("🎉 ¡No hay deudas pendientes por cobrar!")
    else:
        clientes_deudores = sorted(pendientes_df['CLIENTE'].dropna().unique())
        cliente_sel = st.selectbox("Selecciona un Cliente para ver su deuda", clientes_deudores)
        
        compras_cliente = pendientes_df[pendientes_df['CLIENTE'] == cliente_sel]
        total_deuda = compras_cliente['TOTAL'].sum()
        
        st.warning(f"📌 Deuda Total de **{cliente_sel}**: **${total_deuda:,.0f}**")
        st.dataframe(compras_cliente[['ID_VENTA', 'FECHA', 'PRODUCTO', 'CANTIDAD', 'VALOR_UNITARIO', 'TOTAL']], use_container_width=True)
        
        tab1, tab2 = st.tabs(["💵 Registrar Abono Extraordinario", "✅ Saldar Deuda Completa"])
        
        with tab1:
            st.subheader("Registrar Abono")
            monto_abono = st.number_input("Monto abonado ($)", min_value=1.0, max_value=float(total_deuda), value=min(10000.0, float(total_deuda)), step=1000.0)
            
            if st.button(f"💵 Aplicar Abono de ${monto_abono:,.0f} a {cliente_sel}"):
                saldo_restante = monto_abono
                
                indices_compras = compras_cliente.index
                for idx in indices_compras:
                    if saldo_restante <= 0:
                        break
                    monto_pendiente_compra = ventas.loc[idx, 'TOTAL']
                    
                    if saldo_restante >= monto_pendiente_compra:
                        saldo_restante -= monto_pendiente_compra
                        ventas.loc[idx, 'TOTAL'] = 0
                        ventas.loc[idx, 'ESTADO'] = 'PAGADO'
                    else:
                        ventas.loc[idx, 'TOTAL'] -= saldo_restante
                        saldo_restante = 0
                
                guardar_datos(productos, ventas, compras)
                st.success(f"✅ Se registraron ${monto_abono:,.0f} de abono a {cliente_sel}.")
                st.rerun()

        with tab2:
            st.subheader("Saldar Totalidad")
            if st.button(f"✅ Marcar TODAS las compras de {cliente_sel} como PAGADAS"):
                ventas.loc[ventas['CLIENTE'] == cliente_sel, 'ESTADO'] = 'PAGADO'
                guardar_datos(productos, ventas, compras)
                st.success(f"🎉 ¡Toda la deuda de {cliente_sel} ha sido saldada!")
                st.rerun()

# --- MODULO 5: REPORTES DE VENTAS ---
elif opcion == "📄 Reportes de Ventas":
    st.title("📄 Reporte y Exportación de Ventas")
    
    if ventas.empty:
        st.info("Aún no existen ventas registradas.")
    else:
        st.subheader("🔍 Filtros de Búsqueda")
        col1, col2 = st.columns(2)
        
        with col1:
            todos_clientes = ["TODOS"] + sorted(list(ventas['CLIENTE'].dropna().unique()))
            cliente_filtro = st.selectbox("Filtrar por Cliente", todos_clientes)
        
        with col2:
            estado_filtro = st.selectbox("Filtrar por Estado", ["TODOS", "PAGADO", "PENDIENTE"])
            
        df_reporte = ventas.copy()
        
        if cliente_filtro != "TODOS":
            df_reporte = df_reporte[df_reporte['CLIENTE'] == cliente_filtro]
            
        if estado_filtro != "TODOS":
            df_reporte = df_reporte[df_reporte['ESTADO'] == estado_filtro]
            
        columnas_mostrar = ['FECHA', 'CLIENTE', 'PRODUCTO', 'VALOR_UNITARIO', 'CANTIDAD', 'TOTAL', 'ESTADO']
        
        st.subheader("📋 Lista de Ventas")
        st.dataframe(df_reporte[columnas_mostrar].rename(columns={'VALOR_UNITARIO': 'PRECIO'}), use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export = df_reporte[columnas_mostrar].rename(columns={'VALOR_UNITARIO': 'PRECIO'})
            df_export.to_excel(writer, sheet_name='REPORTE_VENTAS', index=False)
            
        st.download_button(
            label="📥 Descargar Reporte de Ventas en Excel",
            data=buffer.getvalue(),
            file_name=f"reporte_ventas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
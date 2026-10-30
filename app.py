import streamlit as st
import pandas as pd
import os

DB_FILE = 'inventario_maquillaje.xlsx'

def cargar_datos():
    if not os.path.exists(DB_FILE):
        st.error("No se encontró 'inventario_maquillaje.xlsx'. Ejecuta primero 'migrar_datos.py'.")
        st.stop()
    productos = pd.read_excel(DB_FILE, sheet_name='PRODUCTOS')
    ventas = pd.read_excel(DB_FILE, sheet_name='VENTAS')
    compras = pd.read_excel(DB_FILE, sheet_name='COMPRAS')
    return productos, ventas, compras

def guardar_datos(productos, ventas, compras):
    with pd.ExcelWriter(DB_FILE) as writer:
        productos.to_excel(writer, sheet_name='PRODUCTOS', index=False)
        ventas.to_excel(writer, sheet_name='VENTAS', index=False)
        compras.to_excel(writer, sheet_name='COMPRAS', index=False)

st.set_page_config(page_title="Stock Maquillaje", page_icon="💄", layout="wide")

# Control de Clave de Acceso Sencilla
PASSWORD_CORRECTA = "maquillaje2026" # Puedes cambiar esta clave
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

# Menú superior adaptable a Celular
opcion = st.sidebar.radio("📌 MENÚ", ["📊 Estado General", "🛍️ Registrar Venta", "📦 Registrar Compra / Stock", "💳 Cuentas por Cobrar"])

# --- MODULO 1: ESTADO GENERAL ---
if opcion == "📊 Estado General":
    st.title("💄 Resumen de Inventario y Ventas")
    
    pendientes = ventas[ventas['ESTADO'] == 'PENDIENTE']['TOTAL'].sum() if not ventas.empty else 0
    pagado = ventas[ventas['ESTADO'] == 'PAGADO']['TOTAL'].sum() if not ventas.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Unidades en Stock", int(productos['STOCK'].sum()))
    col2.metric("Por Cobrar (Deudas)", f"${pendientes:,.0f}")
    col3.metric("Ventas Cobradas", f"${pagado:,.0f}")
    
    st.subheader("📦 Stock de Productos")
    filtro_marca = st.selectbox("Filtrar por Marca (Opcional)", ["TODAS"] + list(productos['MARCA'].unique()))
    df_ver = productos if filtro_marca == "TODAS" else productos[productos['MARCA'] == filtro_marca]
    st.dataframe(df_ver[['MARCA', 'PRODUCTO', 'COSTO', 'PRECIO', 'STOCK']], use_container_width=True)

# --- MODULO 2: REGISTRAR VENTA ---
elif opcion == "🛍️ Registrar Venta":
    st.title("🛍️ Registrar Venta (Disminuye Stock)")
    
    prod_lista = productos['MARCA'] + " - " + productos['PRODUCTO']
    prod_sel = st.selectbox("Selecciona Producto", prod_lista)
    
    idx = prod_lista[prod_lista == prod_sel].index[0]
    stock_actual = int(productos.loc[idx, 'STOCK'])
    precio_sugerido = float(productos.loc[idx, 'PRECIO'])
    
    st.info(f" Stock disponible: **{stock_actual}** | Precio Base: **${precio_sugerido:,.0f}**")
    
    cliente = st.text_input("Nombre del Cliente").strip().upper()
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
            st.success(f"✅ Venta registrada a {cliente} por ${total:,.0f}. Stock actualizado.")

# --- MODULO 3: REGISTRAR COMPRA / PRODUCTO NUEVO ---
elif opcion == "📦 Registrar Compra / Stock":
    st.title("📦 Entradas de Mercancía (Aumenta Stock)")
    
    tipo = st.radio("¿Qué deseas ingresar?", ["Aumentar Stock de Producto Existente", "Crear Producto Nuevo"])
    
    if tipo == "Aumentar Stock de Producto Existente":
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
    st.title("💳 Control de Deudores y Cobros")
    
    pendientes_df = ventas[ventas['ESTADO'] == 'PENDIENTE']
    
    if pendientes_df.empty:
        st.balloons()
        st.success("🎉 ¡No hay deudas pendientes por cobrar!")
    else:
        clientes_deudores = pendientes_df['CLIENTE'].unique()
        cliente_sel = st.selectbox("Selecciona un Cliente para ver su deuda", clientes_deudores)
        
        compras_cliente = pendientes_df[pendientes_df['CLIENTE'] == cliente_sel]
        total_deuda = compras_cliente['TOTAL'].sum()
        
        st.warning(f"📌 Deuda Total de **{cliente_sel}**: **${total_deuda:,.0f}**")
        st.dataframe(compras_cliente[['FECHA', 'PRODUCTO', 'CANTIDAD', 'TOTAL']], use_container_width=True)
        
        if st.button(f"✅ Marcar TODAS las compras de {cliente_sel} como PAGADAS"):
            ventas.loc[ventas['CLIENTE'] == cliente_sel, 'ESTADO'] = 'PAGADO'
            guardar_datos(productos, ventas, compras)
            st.success(f"🎉 ¡Toda la deuda de {cliente_sel} ha sido saldada!")
            st.rerun()
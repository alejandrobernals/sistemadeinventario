from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Conexión DB
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Crear tabla
def crear_tabla():
    conn = get_db()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        cantidad INTEGER,
        fecha_vencimiento TEXT
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        cantidad INTEGER,
        fecha TEXT
    )
''')
    conn.close()
    


# 🏠 DASHBOARD
@app.route('/')
def dashboard():
    conn = get_db()
    
    # ⏳ Productos por vencer (en 7 días)
    por_vencer = conn.execute('''
    SELECT * FROM productos
    WHERE fecha_vencimiento IS NOT NULL
    AND DATE(fecha_vencimiento) BETWEEN DATE('now') AND DATE('now', '+7 days')
''').fetchall()

    # 🔥 Ventas del día (últimas 5)
    ventas_hoy = conn.execute('''
        SELECT ventas.*, productos.nombre
        FROM ventas
        JOIN productos ON ventas.producto_id = productos.id
        WHERE DATE(ventas.fecha) = DATE('now')
        ORDER BY ventas.id DESC
        LIMIT 5
    ''').fetchall()
    
# 🏆 Productos más vendidos (top 5)
    mas_vendidos = conn.execute('''
    SELECT productos.nombre, SUM(ventas.cantidad) as total
    FROM ventas
    INNER JOIN productos ON ventas.producto_id = productos.id
    GROUP BY productos.id
    ORDER BY total DESC
    LIMIT 5
''').fetchall()
    
    # ⚠️ Productos con bajo stock (< 10)
    alertas_stock = conn.execute('''
    SELECT * FROM productos WHERE cantidad < 10
''').fetchall()

    # ❌ Sin stock
    productos_sin_stock = conn.execute(
        "SELECT * FROM productos WHERE cantidad <= 0"
    ).fetchall()

    conn.close()

    return render_template(
    'dashboard.html',
    ventas_hoy=ventas_hoy,
    productos_sin_stock=productos_sin_stock,
    mas_vendidos=mas_vendidos,
    alertas_stock=alertas_stock
)
    
    
# 📦 PRODUCTOS
@app.route('/productos')
def productos():
    conn = get_db()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template('index.html', productos=productos)

# ➕ AGREGAR
@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        fecha = request.form['fecha_vencimiento']

        conn = get_db()
        conn.execute(
    "INSERT INTO productos (nombre, cantidad, fecha_vencimiento) VALUES (?, ?, ?)",
    (nombre, cantidad, fecha)
)
        conn.commit()
        conn.close()

        return redirect('/productos')

    return render_template('agregar.html')

# ✏️ EDITAR
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db()
    producto = conn.execute(
        "SELECT * FROM productos WHERE id = ?", (id,)
    ).fetchone()

    if producto is None:
        return "Producto no encontrado"

    if request.method == 'POST':
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        fecha = request.form['fecha_vencimiento']

        conn.execute(
    "UPDATE productos SET nombre=?, cantidad=?, fecha_vencimiento=? WHERE id=?",
    (nombre, cantidad, fecha, id)
)
        conn.commit()
        conn.close()

        return redirect('/productos')

    conn.close()
    return render_template('editar.html', producto=producto)

# ❌ ELIMINAR
@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/productos')

@app.route('/ventas')
def ventas():
    conn = get_db()

    ventas = conn.execute('''
        SELECT ventas.*, productos.nombre 
        FROM ventas 
        JOIN productos ON ventas.producto_id = productos.id
        ORDER BY ventas.id DESC
    ''').fetchall()

    conn.close()
    return render_template('ventas.html', ventas=ventas)

@app.route('/nueva_venta', methods=['GET', 'POST'])
def nueva_venta():
    conn = get_db()

    productos = conn.execute("SELECT * FROM productos").fetchall()

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])

        # Obtener stock actual
        producto = conn.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()

        if producto["cantidad"] < cantidad:
            return "Stock insuficiente"

        # Guardar venta
        conn.execute(
            "INSERT INTO ventas (producto_id, cantidad, fecha) VALUES (?, ?, datetime('now'))",
            (producto_id, cantidad)
        )

        # Descontar stock
        conn.execute(
            "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
            (cantidad, producto_id)
        )

        conn.commit()
        conn.close()

        return redirect('/ventas')

    conn.close()
    return render_template('nueva_venta.html', productos=productos)

if __name__ == '__main__':
    crear_tabla()
    app.run(debug=True)
    

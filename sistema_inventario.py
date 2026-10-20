import math
import sqlite3

DB = 'inventario_tienda.db'


def crear_bd():
    conexion = sqlite3.connect(DB)
    try:
        conexion.execute('PRAGMA foreign_keys = ON;')
        conexion.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL CHECK (precio >= 0),
                cantidad_disponible INTEGER NOT NULL CHECK (cantidad_disponible >= 0)
            )
        ''')
        conexion.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                cantidad_vendida INTEGER NOT NULL CHECK (cantidad_vendida > 0),
                total_venta REAL NOT NULL CHECK (total_venta >= 0),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        ''')
        conexion.commit()
    finally:
        conexion.close()


def leer_numero(mensaje, tipo=float, permite_cero=False):
    try:
        valor = tipo(input(mensaje))
    except ValueError:
        print('Error: ingrese un numero valido.')
        return None
    if not math.isfinite(valor) or valor < 0 or (not permite_cero and valor == 0):
        print('Error: el valor debe ser ' + ('mayor o igual a cero' if permite_cero else 'estrictamente mayor a cero'))
        return None
    return valor


def leer_id(mensaje):
    try:
        identificador = int(input(mensaje))
        if identificador <= 0:
            raise ValueError
        return identificador
    except ValueError:
        print('Error: el ID debe ser un entero positivo.')
        return None


def registrar_producto():
    nombre = input('Nombre del componente electrónico: ').strip()
    if not nombre:
        print('Error: el nombre no puede estar vacio.')
        return
    precio = leer_numero('Precio unitario: ', tipo=float, permite_cero=False)
    if precio is None:
        return
    cantidad = leer_numero('Cantidad disponible en stock: ', tipo=int, permite_cero=True)
    if cantidad is None:
        return
    
    conexion = sqlite3.connect(DB)
    try:
        cursor = conexion.execute(
            'INSERT INTO productos (nombre, precio, cantidad_disponible) VALUES (?, ?, ?)',
            (nombre, precio, int(cantidad))
        )
        conexion.commit()
        print(f'Producto registrado exitosamente. ID asignado: {cursor.lastrowid}')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al registrar producto:', error)
    finally:
        conexion.close()


def mostrar_productos():
    conexion = sqlite3.connect(DB)
    try:
        productos = conexion.execute('SELECT id, nombre, precio, cantidad_disponible FROM productos ORDER BY id').fetchall()
        if not productos:
            print('No hay productos registrados en el inventario.')
            return
        print('\n--- CATÁLOGO DE PRODUCTOS ---')
        for identificador, nombre, precio, cantidad in productos:
            print(f'ID: {identificador} | Producto: {nombre} | Precio: ${precio:.2f} | Stock: {cantidad} unidades')
    except sqlite3.Error as error:
        print('Error al consultar productos:', error)
    finally:
        conexion.close()


def actualizar_producto():
    identificador = leer_id('ID del producto a actualizar: ')
    if identificador is None:
        return
    
    print('1. Actualizar precio')
    print('2. Actualizar cantidad disponible')
    opcion = input('Seleccione qué desea modificar: ').strip()
    
    conexion = sqlite3.connect(DB)
    try:
        if opcion == '1':
            nuevo_precio = leer_numero('Nuevo precio: ', tipo=float, permite_cero=False)
            if nuevo_precio is None:
                return
            cursor = conexion.execute('UPDATE productos SET precio = ? WHERE id = ?', (nuevo_precio, identificador))
        elif opcion == '2':
            nueva_cantidad = leer_numero('Nueva cantidad en stock: ', tipo=int, permite_cero=True)
            if nueva_cantidad is None:
                return
            cursor = conexion.execute('UPDATE productos SET cantidad_disponible = ? WHERE id = ?', (int(nueva_cantidad), identificador))
        else:
            print('Opción no válida.')
            return

        if cursor.rowcount == 0:
            conexion.rollback()
            print('El producto especificado no existe.')
        else:
            conexion.commit()
            print('Producto actualizado correctamente.')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al actualizar:', error)
    finally:
        conexion.close()


def eliminar_producto():
    identificador = leer_id('ID del producto a eliminar: ')
    if identificador is None:
        return
    
    conexion = sqlite3.connect(DB)
    conexion.execute('PRAGMA foreign_keys = ON;')
    try:
        producto = conexion.execute('SELECT nombre, cantidad_disponible FROM productos WHERE id = ?', (identificador,)).fetchone()
        if producto is None:
            print('El producto no existe.')
            return
        
        if producto[1] > 0:
            print(f'Advertencia: El producto "{producto[0]}" aún tiene {producto[1]} unidades en stock.')
            confirmacion = input('¿Desea forzar la eliminación de todas formas? (s/n): ').strip().lower()
            if confirmacion != 's':
                print('Eliminación cancelada.')
                return

        cursor = conexion.execute('DELETE FROM productos WHERE id = ?', (identificador,))
        conexion.commit()
        print('Producto eliminado exitosamente del inventario.')
    except sqlite3.IntegrityError:
        conexion.rollback()
        print('Error: No se puede eliminar el producto porque tiene ventas asociadas en el historial (clave foránea).')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al eliminar:', error)
    finally:
        conexion.close()


def registrar_venta(simular_error=False):
    print('\n--- REGISTRAR VENTA ---')
    identificador = leer_id('ID del producto a vender: ')
    if identificador is None:
        return
    cantidad_a_vender = leer_numero('Cantidad a vender: ', tipo=int, permite_cero=False)
    if cantidad_a_vender is None:
        return
    cantidad_a_vender = int(cantidad_a_vender)

    conexion = sqlite3.connect(DB)
    try:
        conexion.execute('BEGIN IMMEDIATE')
        
        producto = conexion.execute('SELECT nombre, precio, cantidad_disponible FROM productos WHERE id = ?', (identificador,)).fetchone()
        if producto is None:
            raise ValueError('El producto especificado no existe.')
        
        nombre, precio, stock_actual = producto[0], producto[1], producto[2]
        
        if stock_actual < cantidad_a_vender:
            raise ValueError(f'Stock insuficiente. Stock actual: {stock_actual}, unidades solicitadas: {cantidad_a_vender}.')
        
        total_venta = precio * cantidad_a_vender
        
        conexion.execute(
            'INSERT INTO ventas (producto_id, cantidad_vendida, total_venta) VALUES (?, ?, ?)',
            (identificador, cantidad_a_vender, total_venta)
        )
        
        conexion.execute(
            'UPDATE productos SET cantidad_disponible = cantidad_disponible - ? WHERE id = ?',
            (cantidad_a_vender, identificador)
        )
        
        if simular_error:
            raise RuntimeError('¡Error simulado intencionalmente para probar el ROLLBACK!')
        
        conexion.commit()
        print(f'¡Venta registrada con éxito! Total a pagar: ${total_venta:.2f} por {cantidad_a_vender} unidad(es) de "{nombre}".')
        
    except (ValueError, RuntimeError, sqlite3.Error) as error:
        conexion.rollback()
        print('TRANSACCIÓN CANCELADA (Rollback ejecutado con éxito):', error)
    finally:
        conexion.close()


def mostrar_historial_ventas():
    conexion = sqlite3.connect(DB)
    try:
        query = '''
            SELECT v.id, p.nombre, v.cantidad_vendida, v.total_venta 
            FROM ventas v
            JOIN productos p ON v.producto_id = p.id
            ORDER BY v.id
        '''
        ventas = conexion.execute(query).fetchall()
        if not ventas:
            print('No hay ventas registradas en el historial.')
            return
        print('\n--- HISTORIAL DE VENTAS (Con JOIN) ---')
        for id_venta, nombre_prod, cant, total in ventas:
            print(f'Venta ID: {id_venta} | Producto: {nombre_prod} | Cantidad: {cant} | Total Recaudado: ${total:.2f}')
    except sqlite3.Error as error:
        print('Error al consultar el historial de ventas:', error)
    finally:
        conexion.close()


def menu():
    while True:
        print('\n===== SISTEMA DE INVENTARIO Y VENTAS =====')
        print('1. Registrar nuevo producto')
        print('2. Consultar todos los productos')
        print('3. Actualizar precio o cantidad de un producto')
        print('4. Eliminar producto')
        print('5. Registrar una venta')
        print('6. Mostrar historial de ventas (con JOIN)')
        print('7. Simular error en venta (Probar ROLLBACK)')
        print('8. Salir')
        
        opcion = input('Seleccione una opción: ').strip()
        if opcion == '1':
            registrar_producto()
        elif opcion == '2':
            mostrar_productos()
        elif opcion == '3':
            actualizar_producto()
        elif opcion == '4':
            eliminar_producto()
        elif opcion == '5':
            registrar_venta(simular_error=False)
        elif opcion == '6':
            mostrar_historial_ventas()
        elif opcion == '7':
            registrar_venta(simular_error=True)
        elif opcion == '8':
            print('Saliendo del sistema de inventario...')
            break
        else:
            print('Opción no válida. Intente de nuevo.')


if __name__ == '__main__':
    crear_bd()
    menu()
# Parcial Práctico – Sistema de Inventario y Ventas

Aplicación de consola desarrollada en Python y SQLite diseñada para administrar los productos, controlar el stock y registrar las ventas de una tienda de componentes electrónicos de forma íntegra y segura.

## 1. Análisis y Modelo de Datos
### Entidades y Atributos
`productos`: Almacena el catálogo general del inventario.
`id` (INTEGER, Primary Key, Auto-increment)
`nombre` (TEXT, Not Null)
`precio` (REAL, Not Null, Check $\ge 0$)
`cantidad_disponible` (INTEGER, Not Null, Check $\ge 0$)

`ventas`: Registra cada transacción comercial realizada.
  * `id` (INTEGER, Primary Key, Auto-increment)
  * `producto_id` (INTEGER, Foreign Key referenciando a `productos(id)`, Not Null)
  * `cantidad_vendida` (INTEGER, Not Null, Check $> 0$)
  * `total_venta` (REAL, Not Null)

### Relación de la Base de Datos
La base de datos maneja una relación de Uno a Muchos (1:N): un producto puede estar asociado a múltiples registros en el historial de ventas, garantizando la integridad referencial mediante claves foráneas (`FOREIGN KEY`).


## 2. Diagrama de Arquitectura e Interacción
El esquema muestra cómo interactúan el usuario, la aplicación en Python y el motor de base de datos SQLite:

```text
+----------+      Entradas por consola       +------------------+      Consultas SQL / Transacciones      +-----------------+
|  Usuario | ------------------------------> | Aplicación Python| --------------------------------------> |  Base de datos  |
|          | <------------------------------ |    (Consola)     | <-------------------------------------- |  (SQLite)       |
+----------+        Menú / Resultados        +------------------+                                         +-----------------+
```

## 3. Análisis de Construcción del Software
El software está construido de forma modular utilizando funciones especializadas:
* Manejo de Errores y Validaciones: Funciones auxiliares (`leer_numero`, `leer_id`) que previenen fallos por entradas vacías, tipos de datos incorrectos o valores negativos.
* CRUD Completo: Permite registrar, consultar, actualizar y eliminar productos aplicando restricciones para no dejar inconsistencias en el stock.
* Consultas Avanzadas (`JOIN`): El historial de ventas vincula la tabla `ventas` con `productos` mediante un `JOIN` explícito para mostrar los nombres reales de los componentes en lugar de IDs numéricos.

## 4. Explicación de la Transacción
Al procesar una venta, la aplicación ejecuta un bloque transaccional controlado (`BEGIN IMMEDIATE`) que realiza las siguientes operaciones en orden estricto:
1. Verificación de existencia: Comprueba que el ID del producto exista en la base de datos.
2. Validación de stock: Comprueba que las unidades solicitadas sean menores o iguales a las disponibles.
3. Registro: Inserta la venta en la tabla correspondiente.
4. Descuento de inventario: Actualiza restando las unidades vendidas del stock actual.
5. Confirmación (`commit`): Si todo es correcto, sella los cambios permanentemente.

Control de Fallos (`rollback`): Si ocurre un error de ejecución o si se activa la simulación de fallo (Opción 7 del menú), el sistema captura la excepción y ejecuta inmediatamente un `rollback()`. Esto cancela toda la operación y garantiza que los datos del inventario permanezcan totalmente intactos.

## 5. Instrucciones para Ejecutar el Proyecto
1. Asegúrate de tener Python instalado en tu equipo.
2. Descarga o clona este repositorio que contiene el archivo `inventario.py`.
3. Abre tu editor o terminal en la carpeta del proyecto y ejecuta el script:
   ```bash
   python inventario.py
   ```
4. El programa creará automáticamente la base de datos local (`inventario_tienda.db`) y mostrará el menú interactivo en la consola.

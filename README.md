# Prueba tecnica WH

Este proyecto se hizo en Django para cubrir el flujo completo de reserva de una propiedad en WynwoodHouse, intentando respetar el diseño ya maquetado del frontend y enfocandome más en la parte funcional, validaciones, modelos y conexión de datos reales.

La idea general del proyecto es que un usuario pueda:

- entrar al home,
- buscar por ciudad, fechas y huespedes,
- ver resultados segun filtros,
- entrar al detalle de una propiedad,
- iniciar una reserva,
- registrarse o logearse,
- completar checkout,
- confirmar la reserva,
- y recibir un correo de confirmación.

Tambien se dejó soporte para español e inglés en la landing y en el flujo principal.

## Stack que utilizé

- Python 3.11+
- Django 5.2
- SQLite por defecto
- PostgreSQL como opcion
- HTML, CSS, JavaScript
- Bootstrap
- DTL de Django

## Cosas que cubre la prueba

Del lado backend:

- proyecto en Django ya configurado
- conexión a base de datos por SQLite o PostgreSQL
- vistas basadas en clases
- modelos para ciudades, propiedades, imagenes, reservas, servicios adicionales, amenidades, paises y configuración del sitio
- datos administrables desde base de datos, para evitar hardcodes innecesarios
- validaciones de reservas
- comando de carga de datos de prueba
- envio de correo de confirmación
- optimización automatica de imagenes a WebP con maximo 1200px

Del lado frontend:

- home con barra de busqueda
- resultados de busqueda
- detalle de propiedad
- login y registro manual
- checkout de nuevo usuario
- confirmación de reserva

## Instalación local

crear y activar un entorno virtual.

python -m venv .venv
.venv\Scripts\activate

instalar dependencias:
pip install -r requirements.txt

correr migraciones:
python manage.py migrate

cargar datos de prueba:
python manage.py seed_demo

Finalmente levantar el servidor:
python manage.py runserver

Abrir en el navegador:
http://127.0.0.1:8000/

## Base de datos

### SQLite

opción por defecto, asi que no toco nada extra para correrlo localmente.

## Correo de confirmación

Por defecto el proyecto usa backend de consola, o sea que cuando se completa una reserva el correo se imprime en terminal. Eso lo dejé asi para que sea facil de probar rapido.

Configuración por defecto:

```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Si se quiere probar SMTP local, se puede usar algo asi:

```bash
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=localhost
set EMAIL_PORT=1025
```

Con eso ya puedes levantar algun servidor SMTP de pruebas, por ejemplo MailHog, smtp4dev o algo parecido.

## Datos iniciales

insertar data:
python manage.py seed_demo

Crea, entre otras cosas:

- usuario admin: `admin@example.com`
- contraseña: `AdminPass123!`
- ciudades de ejemplo
- propiedades destacadas
- imagenes de prueba
- amenidades
- servicios adicionales
- paises para checkout y facturación
- navegación y footer desde base de datos
- configuración base del sitio

## Flujo para probar rapido

1. Entrar al home.
2. Buscar una ciudad con fechas futuras y cantidad de huespedes.
3. Revisar los resultados filtrados.
4. Entrar al detalle de una propiedad.
5. Intentar fechas invalidas para ver validaciones.
6. Hacer una reserva con fechas validas.
7. Completar el checkout como usuario nuevo.
8. Confirmar el pago.
9. Revisar la vista de confirmación.
10. Revisar el correo.

## Validaciones implementadas

Algunas validaciones importantes que sí quedaron cubiertas:

- email unico en el registro
- validación basica y segura de contraseña usando validadores de Django
- check-in no puede estar en el pasado
- check-out tiene que ser posterior al check-in
- no se permite solapamiento de reservas en la misma propiedad
- cantidad de huespedes no puede exceder la capacidad de la propiedad
- validación de telefono y fecha de nacimiento en checkout
- validación basica de datos de pago y facturación

## Optimización automatica de imagenes

Cuando se guardan imagenes de propiedades:

- se convierten a formato WebP
- se redimensionan con maximo 1200px de ancho o alto

## Estructura general

La app principal es `bookings`, ahi está practicamente todo:

- modelos
- vistas
- formularios
- templates
- admin
- tests
- comando custom `seed_demo`

## Verificación

Para comprobar que todo esté bien en local:
python manage.py check
python manage.py test

## Notas finales

Se trató de replicar con la mayor fidelidad el prototipo y diseño que se brindó en figma

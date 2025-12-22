# Hotel Website Reservation

Este módulo extiende el sistema de gestión hotelera para permitir a los clientes realizar reservas directamente desde el sitio web con capacidades de pago en línea.

## Características

### Funcionalidades Web
- **Catálogo de habitaciones online**: Muestra habitaciones disponibles con imágenes, descripciones y amenidades
- **Verificador de disponibilidad**: Permite a los clientes verificar disponibilidad en tiempo real
- **Formulario de reserva**: Interfaz fácil de usar para realizar reservas
- **Integración con pagos**: Utiliza website_sale para procesar pagos online
- **Diseño responsive**: Optimizado para dispositivos móviles

### Gestión de Reservas
- **Portal del cliente**: Los clientes pueden ver y gestionar sus reservas
- **Confirmaciones por email**: Envío automático de emails de confirmación
- **Estados de pago**: Seguimiento del estado de pagos (pendiente, parcial, pagado)
- **Configuración flexible**: Porcentaje de anticipo configurable por habitación

### Funcionalidades Administrativas
- **Gestión de imágenes**: Subida y gestión de múltiples imágenes por habitación
- **Configuración web**: Control de qué habitaciones se publican en el sitio web
- **Informes**: Seguimiento de reservas web separado de las reservas internas
- **Integración completa**: Funciona seamlessly con los módulos hotel existentes

## Instalación

### Dependencias
Este módulo requiere los siguientes módulos:
- `hotel_reservation`
- `website_sale` 
- `website`
- `portal`

### Pasos de instalación
1. Asegúrate de que todas las dependencias están instaladas
2. Copia el módulo `hotel_website_reservation` al directorio de addons
3. Actualiza la lista de aplicaciones
4. Instala el módulo desde Apps

## Configuración

### Configuración inicial
1. **Configurar habitaciones para web**:
   - Ve a Hotel > Configuration > Rooms
   - Edita cada habitación que quieras mostrar en el web
   - En la pestaña "Website":
     - Marca "Published on Website"
     - Añade descripción web
     - Configura imágenes
     - Establece configuración de reservas

2. **Configurar productos**:
   - Cada habitación necesita un producto asociado
   - Los productos se crean automáticamente si no existen
   - Asegúrate de que están marcados como "Is Hotel Room"

3. **Configurar pagos**:
   - Configura métodos de pago en website_sale
   - Los pagos se procesan a través del checkout estándar de Odoo

### Configuración de habitaciones
Para cada habitación puedes configurar:
- **Porcentaje de anticipo**: Cantidad requerida como pago inicial
- **Estancia mínima**: Número mínimo de noches
- **Estancia máxima**: Número máximo de noches
- **Descripción web**: Descripción rich text para el sitio web
- **Amenidades**: Amenidades a destacar en el web
- **Imágenes**: Múltiples imágenes con imagen principal

## Uso

### Para clientes
1. **Buscar habitaciones**: Los clientes van a `/hotel` o `/hotel/rooms`
2. **Filtrar por disponibilidad**: Usar el formulario de búsqueda con fechas
3. **Ver detalles**: Click en "View Details" para ver información completa
4. **Realizar reserva**: Llenar el formulario de reserva
5. **Procesar pago**: Redirigido al checkout para pago online
6. **Confirmación**: Recibir email de confirmación y acceso al portal

### Para administradores
1. **Gestionar reservas web**: Hotel > Reservations > Website Bookings
2. **Configurar habitaciones**: Hotel > Configuration > Rooms
3. **Gestionar imágenes**: Hotel > Configuration > Room Images
4. **Ver informes**: Usar filtros para separar reservas web de internas

## Portal del cliente

Los clientes registrados pueden:
- Ver todas sus reservas en `/my/hotel_reservations`
- Ver detalles de cada reserva
- Cancelar reservas (si está permitido)
- Acceder a información de contacto

## Integración con website_sale

El módulo se integra completamente con website_sale:
- **Productos automáticos**: Cada habitación se convierte en un producto
- **Proceso de checkout**: Utiliza el checkout estándar de Odoo
- **Gestión de órdenes**: Las reservas se vinculan con órdenes de venta
- **Facturación**: Integración completa con el sistema de facturación

## Estructura técnica

### Modelos principales
- `hotel.room`: Extendido con campos web
- `hotel.reservation`: Extendido con campos de reserva web
- `hotel.room.image`: Nuevo modelo para imágenes
- `product.template`: Extendido para habitaciones
- `sale.order`: Extendido para reservas de hotel

### Controladores
- `HotelWebsiteController`: Maneja páginas web y reservas
- `HotelPortalController`: Maneja portal del cliente
- `HotelWebsiteSale`: Extiende website_sale para hoteles

### Plantillas principales
- Catálogo de habitaciones
- Detalle de habitación con formulario de reserva
- Portal del cliente
- Emails de confirmación

## Personalización

### CSS personalizado
Los estilos están en `static/src/css/hotel_frontend.css` y se pueden personalizar para match el branding del hotel.

### JavaScript personalizado
La funcionalidad frontend está en `static/src/js/hotel_reservation.js` incluyendo:
- Validación de formularios
- Verificación de disponibilidad AJAX
- Cálculo de precios dinámico

### Templates
Todas las plantillas web se pueden personalizar heredando las vistas correspondientes.

## Soporte

Para issues y contribuciones, por favor usa el repositorio GitHub del proyecto vertical-hotel.

## Licencia

AGPL-3.0 - Ver archivo LICENSE para detalles.
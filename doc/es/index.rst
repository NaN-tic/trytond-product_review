==================
Producto. Revisión
==================

- Productos/Configuración/Revisiones:
  - Tipos de revisiones
- Productos/Producto (plantilla):
  Un producto le podemos activar la opción "revisión"
  - Revisión
  - Tipos de revisiones
  - Notas
- Productos/Revisiones:
  - Listado de revisiones pendientes a procesar
- Notificación de revisiones de productos
  - Se dispone de una acción planificada (cron) para el envío de las revisiones pendientes.
  - Se envia a todos los usuarios del grupo "Revisión productos" y que dispongan correo.
  - Los usuarios deberán disponer de un correo electrónico válido. En caso que se detecte
    un correo no válido, no se enviará el correo.
  - Las revisiones que se envian son en estado borrador, que no se hayan modificado
    y la creación sea superior al último envío de correo.
  - Para el envío deberá activar un servidor SMTP por defecto o que el modelo sea "Producto Revisión".

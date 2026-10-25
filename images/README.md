# Imágenes remotas

Organiza cada historia en su propia carpeta y usa nombres versionados:

```text
images/david-and-goliath/01-cover-v2.webp
images/david-and-goliath/02-challenge-v2.webp
```

En el JSON usa la ruta relativa, por ejemplo:

```json
"image": "images/david-and-goliath/02-challenge-v2.webp"
```

La aplicación agrega automáticamente el dominio configurado. Al reemplazar una imagen, cambia también el sufijo de versión para evitar una copia anterior en la caché de Coil.

Convierte los originales PNG/JPG con `python scripts/optimize_images.py <carpeta-origen> images/<id-historia>` (WebP calidad 80, máximo 1200 × 1800). Para íconos de elementos con fondo transparente añade `--max-size 384x384`.

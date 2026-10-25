# Contenido de Pasitos de Fe

Repositorio estático para publicar historias bíblicas mediante GitHub Pages. No contiene backend, cuentas, anuncios ni servicios con facturación.

## Activación

1. Conserva esta estructura en la raíz del repositorio.
2. En **Settings → Pages → Source** selecciona **GitHub Actions**.
3. Haz push a `main`.
4. Comprueba la URL que muestra el job `Deploy GitHub Pages`.

El workflow valida todas las historias antes de desplegar. En pull requests solamente valida; al hacer merge en `main`, publica una unidad consistente de catálogo, historias e imágenes.

## Comprobar localmente

```bash
python scripts/validate_content.py
```

No requiere instalar paquetes.

## Estructura pública

```text
catalog.json
stories/
  david-and-goliath.json
  panes-y-peces.json
images/
  nombre-de-historia/
    cover-v1.webp
```

Usa rutas relativas en `coverImage`, `image` e `interaction.itemImage`. Ejemplo:

```json
"image": "images/david-and-goliath/02-challenge-v2.webp"
```

Las historias usan `schemaVersion: 2`; el formato completo está en `docs/CONTENT_GUIDE.md` del proyecto Android.

Incrementa la versión del catálogo y de la historia en cada actualización. Si una historia usa una mecánica que solo existe a partir de cierta versión de la app, indica ese `versionCode` en `minAppVersion` de su entrada del catálogo: las apps anteriores la omiten en lugar de fallar. Consulta la guía incluida en el proyecto Android para las reglas editoriales y de licencias.

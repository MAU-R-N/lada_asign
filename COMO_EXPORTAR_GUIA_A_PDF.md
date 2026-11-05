# 📄 Cómo Exportar la Guía de Auditoría a PDF

Hay varias formas de convertir `GUIA_AUDITORIA_FACTURACION.md` a PDF profesional.

## Opción 1: Visual Studio Code (Recomendado)

### Extensión: Markdown PDF

1. Abrir Visual Studio Code
2. Instalar extensión **"Markdown PDF"** por yzane:
   - View → Extensions (Ctrl+Shift+X)
   - Buscar "Markdown PDF"
   - Click "Install"

3. Abrir `GUIA_AUDITORIA_FACTURACION.md`

4. Generar PDF:
   - Click derecho en el archivo
   - Seleccionar **"Markdown PDF: Export (pdf)"**
   - O usar comando: `Ctrl+Shift+P` → "Markdown PDF: Export (pdf)"

5. El PDF se guardará en el mismo directorio

**Ventajas:**
- Formato profesional
- Tabla de contenido con enlaces
- Sintaxis de código bien formateada
- Emojis renderizados

## Opción 2: Pandoc (Línea de Comandos)

### Instalar Pandoc

**Ubuntu/Debian:**
```bash
sudo apt install pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

**macOS:**
```bash
brew install pandoc
brew install --cask basictex
```

**Windows:**
- Descargar de https://pandoc.org/installing.html

### Convertir a PDF

```bash
cd /home/party/Documentos/NAUPHILUS_DEV/DEVS/LADA

pandoc GUIA_AUDITORIA_FACTURACION.md \
  -o GUIA_AUDITORIA_FACTURACION.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V linkcolor:blue \
  -V fontsize=11pt \
  --toc \
  --toc-depth=2
```

**Opciones:**
- `--toc`: Genera tabla de contenido
- `--toc-depth=2`: Incluye hasta nivel 2 de headers
- `-V geometry:margin=1in`: Márgenes de 1 pulgada
- `-V fontsize=11pt`: Tamaño de fuente 11pt

## Opción 3: Markdown to PDF (Online)

### Sin instalación de software

1. Ir a https://www.markdowntopdf.com/
2. Copiar y pegar el contenido de `GUIA_AUDITORIA_FACTURACION.md`
3. Click "Convert to PDF"
4. Descargar el PDF generado

**Ventajas:**
- No requiere instalación
- Rápido para uso ocasional

**Desventajas:**
- Menos control sobre formato
- Requiere internet

## Opción 4: GitHub (con Acceso a Repo)

Si el archivo está en GitHub:

1. Ver archivo en GitHub
2. Click en el botón "..." (más opciones)
3. Seleccionar "Download"
4. Abrir en Google Chrome
5. Ctrl+P → Guardar como PDF

## Opción 5: Typora (Editor Markdown)

### Software recomendado para edición

1. Descargar Typora: https://typora.io/
2. Abrir `GUIA_AUDITORIA_FACTURACION.md`
3. File → Export → PDF
4. Configurar opciones de exportación
5. Guardar PDF

**Ventajas:**
- Vista previa en tiempo real
- Exportación con temas personalizables
- Soporte completo de Markdown

## Personalización del PDF

### Agregar Logo/Header

Si usas Pandoc, crea un archivo `header.tex`:

```latex
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead[L]{Farmacias del Ahorro}
\fancyhead[R]{\includegraphics[width=2cm]{logo.png}}
\fancyfoot[C]{\thepage}
```

Luego:
```bash
pandoc GUIA_AUDITORIA_FACTURACION.md \
  -o GUIA_AUDITORIA_FACTURACION.pdf \
  --pdf-engine=xelatex \
  -H header.tex \
  --toc
```

### Cambiar Colores/Estilo

Con Markdown PDF en VS Code, crea `.vscode/markdown-pdf.css`:

```css
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.6;
}

h1, h2, h3 {
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.3em;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

th {
  background-color: #3498db;
  color: white;
  padding: 10px;
}

td {
  border: 1px solid #ddd;
  padding: 8px;
}

code {
  background-color: #f4f4f4;
  padding: 2px 4px;
  border-radius: 3px;
}
```

## Resultado Esperado

El PDF debería incluir:

- ✅ Portada con título y fecha
- ✅ Tabla de contenido interactiva (links)
- ✅ 7 secciones principales
- ✅ Tablas bien formateadas
- ✅ Bloques de código con sintaxis
- ✅ Emojis (📊, ✅, ⚠️, etc.)
- ✅ Checklist con cajas
- ✅ Enlaces internos funcionales
- ✅ ~40 páginas aproximadamente

## Verificación del PDF

Después de generar el PDF, verifica:

1. **Tabla de contenido**: Links funcionan al hacer click
2. **Tablas**: Todas las columnas son legibles
3. **Código**: Bloques de código no se cortan
4. **Imágenes/Emojis**: Se renderizan correctamente
5. **Páginas**: No hay saltos de página extraños en secciones

## Compartir el PDF

### Por Email

```
Para: [persona_facturacion@farmacias.com]
Asunto: Guía de Auditoría - Sistema de Facturación Automática

Adjunto:
- GUIA_AUDITORIA_FACTURACION.pdf (guía completa de uso)
- facturacion_procesada_YYYYMMDD_HHMMSS.xlsx (Excel del mes)

Esta guía explica cómo:
1. Auditar las asignaciones automáticas
2. Revisar y corregir casos manuales
3. Validar la facturación antes de cerrar el mes
4. Exportar reportes para gerencia

Ver especialmente:
- Sección 5: Validación de facturación
- Sección 7: Checklist final

Cualquier duda, consultar la guía o contactar a TI.
```

### En SharePoint/Drive

Subir a carpeta compartida con nombre descriptivo:
```
Facturacion_2026/
  └── Documentacion/
      ├── GUIA_AUDITORIA_FACTURACION.pdf
      ├── README_SISTEMA.pdf
      └── EJEMPLOS_CASOS_USO.pdf
```

---

**Archivo generado:** `GUIA_AUDITORIA_FACTURACION.md`  
**PDF esperado:** `GUIA_AUDITORIA_FACTURACION.pdf` (~40 páginas)  
**Formato:** Markdown → PDF  
**Versión:** 1.0
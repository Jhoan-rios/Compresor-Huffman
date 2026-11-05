# Compresor de texto con codificación de Huffman

Proyecto de Estructuras de Datos - Universidad de Medellín.

## Ejecutar
Requiere Python 3.10 o superior. No requiere paquetes externos.

1. Extrae el ZIP.
2. Abre una terminal dentro de `Compresor_Huffman_Terminal`.
3. Ejecuta `python main.py` (en Windows también puedes usar `py main.py`).

## Menú
1. **Comprimir:** ingresa la ruta del TXT. Si presionas Enter en la ruta de salida, se guarda en `comprimidos/`.
2. **Descomprimir:** ingresa la ruta del HUF. Si presionas Enter en la ruta de salida, se guarda en `descomprimidos/`.
3. **Reporte:** ingresa el TXT original y su HUF correspondiente. El reporte aparece en la terminal y se guarda en `reportes/`.
4. **Salir.**

Puedes ingresar rutas relativas o absolutas. Si contienen espacios, puedes pegarlas entre comillas.

## Organización
- `main.py`: programa y menú de terminal.
- `comprimidos/`: archivos `.huf`.
- `descomprimidos/`: archivos `.txt` recuperados.
- `reportes/`: reportes `.txt`.
- `ejemplos/`: archivos para probar.
- `README.md`: instrucciones y formato.

## Formato del archivo HUF
| Bytes | Contenido |
|---|---|
| 1 | Bits de relleno (0 a 7) |
| 4 | Cantidad de símbolos distintos |
| 4 por símbolo | Código Unicode del carácter |
| 4 por símbolo | Frecuencia |
| Restantes | Carga útil binaria de Huffman |

Los enteros de cabecera usan big-endian. La carga útil contiene bytes reales, no los caracteres `0` y `1`. El árbol se reconstruye usando las frecuencias guardadas.

## Regla de prioridad
Se compara primero por frecuencia menor y, en caso de empate, por el menor carácter Unicode del subárbol. El primero extraído queda a la izquierda (`0`) y el segundo a la derecha (`1`). La cola de prioridad es propia; no se usa `heapq` ni `PriorityQueue`.

Contempla archivos vacíos, un carácter, caracteres repetidos, tildes, ñ, Unicode, espacios, tabulaciones y saltos de línea.

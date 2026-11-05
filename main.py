from __future__ import annotations
import math
from collections import Counter
from pathlib import Path
from typing import TypeAlias


Frecuencias: TypeAlias = dict[str, int]
Codigos: TypeAlias = dict[str, str]


class Nodo:
    """Representa una hoja o un nodo interno del árbol de Huffman."""

    def __init__(self, caracter: str | None, frecuencia: int, izquierdo: Nodo | None = None, derecho: Nodo | None = None, caracter_minimo: str | None = None) -> None:
        self.caracter: str | None = caracter
        self.frecuencia: int = frecuencia
        self.izquierdo: Nodo | None = izquierdo
        self.derecho: Nodo | None = derecho
        self.caracter_minimo: str = (
            caracter if caracter_minimo is None and caracter is not None
            else caracter_minimo if caracter_minimo is not None
            else ""
        )

    def __repr__(self) -> str:
        return f"caracter:{self.caracter}, frecuencia:{self.frecuencia}"


class ColaPrioridad:
    """Cola de prioridad propia, ordenada por frecuencia y carácter mínimo."""

    def __init__(self) -> None:
        self.cola: list[Nodo] = []

    def insertar_nodo(self, nodo: Nodo) -> None:
        self.cola.append(nodo)

    def extraer_min(self) -> Nodo:
        if not self.cola:
            raise IndexError("La cola de prioridad está vacía.")

        menor: Nodo = self.cola[0]
        for nodo in self.cola[1:]:
            if (nodo.frecuencia, ord(nodo.caracter_minimo)) < (menor.frecuencia, ord(menor.caracter_minimo)):
                menor = nodo

        self.cola.remove(menor)
        return menor

    def __len__(self) -> int:
        return len(self.cola)


def contar_frecuencias(texto: str) -> Frecuencias:
    """Cuenta cuántas veces aparece cada carácter."""
    return dict(Counter(texto))


def construir_arbol(frecuencias: Frecuencias) -> Nodo | None:
    """Construye el árbol de Huffman respetando la regla de desempate."""
    cola: ColaPrioridad = ColaPrioridad()

    for caracter, frecuencia in frecuencias.items():
        cola.insertar_nodo(Nodo(caracter, frecuencia))

    while len(cola) > 1:
        izquierdo: Nodo = cola.extraer_min()
        derecho: Nodo = cola.extraer_min()
        minimo: str = min(izquierdo.caracter_minimo, derecho.caracter_minimo)
        padre: Nodo = Nodo(
            None,
            izquierdo.frecuencia + derecho.frecuencia,
            izquierdo,
            derecho,
            minimo,
        )
        cola.insertar_nodo(padre)

    return cola.extraer_min() if len(cola) else None


def generar_codigos(raiz: Nodo | None) -> Codigos:
    """Genera el código binario de cada carácter a partir del árbol."""
    codigos: Codigos = {}
    if raiz is None:
        return codigos

    if raiz.caracter is not None:
        return {raiz.caracter: "0"}

    def recorrer(nodo: Nodo, codigo: str) -> None:
        if nodo.caracter is not None:
            codigos[nodo.caracter] = codigo
            return

        if nodo.izquierdo is None or nodo.derecho is None:
            raise ValueError("El árbol de Huffman está incompleto.")

        recorrer(nodo.izquierdo, codigo + "0")
        recorrer(nodo.derecho, codigo + "1")

    recorrer(raiz, "")
    return codigos


def codificar(texto: str, codigos: Codigos) -> tuple[bytes, int]:
    """Convierte el texto en bytes usando los códigos de Huffman."""
    if not texto:
        return b"", 0

    bits: str = "".join(codigos[caracter] for caracter in texto)
    relleno: int = (8 - len(bits) % 8) % 8
    bits += "0" * relleno

    carga: bytearray = bytearray()
    for posicion in range(0, len(bits), 8):
        grupo: str = bits[posicion:posicion + 8]
        carga.append(int(grupo, 2))

    return bytes(carga), relleno


def escribir_comprimido(ruta_salida: str | Path, frecuencias: Frecuencias, carga: bytes,relleno: int) -> None:
    """
    Escribe la cabecera y la carga útil del archivo comprimido.

    Cabecera:
    - 1 byte: cantidad de bits de relleno.
    - 4 bytes: cantidad de símbolos distintos.
    - 8 bytes por símbolo: código Unicode y frecuencia.
    """
    with open(ruta_salida, "wb") as archivo:
        archivo.write(bytes([relleno]))
        archivo.write(len(frecuencias).to_bytes(4, "big"))

        for caracter, frecuencia in sorted(
            frecuencias.items(), key=lambda elemento: ord(elemento[0])
        ):
            archivo.write(ord(caracter).to_bytes(4, "big"))
            archivo.write(frecuencia.to_bytes(4, "big"))

        archivo.write(carga)


def leer_comprimido(
    ruta: str | Path,
) -> tuple[Frecuencias, int, bytes]:
    """Lee la cabecera y la carga útil de un archivo .huf."""
    datos: bytes = Path(ruta).read_bytes()
    if len(datos) < 5:
        raise ValueError("El archivo comprimido está incompleto o no tiene una cabecera válida.")

    relleno: int = datos[0]
    if relleno > 7:
        raise ValueError("La cabecera contiene un valor de relleno inválido.")

    cantidad_simbolos: int = int.from_bytes(datos[1:5], "big")
    fin_cabecera: int = 5 + cantidad_simbolos * 8
    if len(datos) < fin_cabecera:
        raise ValueError("La cabecera está incompleta.")

    frecuencias: Frecuencias = {}
    posicion: int = 5

    for _ in range(cantidad_simbolos):
        codigo_unicode: int = int.from_bytes(datos[posicion:posicion + 4], "big")
        frecuencia: int = int.from_bytes(datos[posicion + 4:posicion + 8], "big")
        posicion += 8

        try:
            caracter: str = chr(codigo_unicode)
        except ValueError as error:
            raise ValueError("La cabecera contiene un carácter Unicode inválido.") from error

        if frecuencia <= 0 or caracter in frecuencias:
            raise ValueError("La tabla de frecuencias del comprimido no es válida.")

        frecuencias[caracter] = frecuencia

    carga: bytes = datos[fin_cabecera:]
    if cantidad_simbolos == 0 and (carga or relleno):
        raise ValueError("El archivo vacío tiene datos adicionales no válidos.")
    if cantidad_simbolos > 0 and not carga:
        raise ValueError("El archivo comprimido no contiene carga útil.")

    return frecuencias, relleno, carga


def decodificar(raiz: Nodo | None, carga: bytes, relleno: int) -> str:
    """Reconstruye el texto original recorriendo el árbol de Huffman."""
    if raiz is None:
        return ""

    bits: str = "".join(format(byte, "08b") for byte in carga)
    if relleno:
        if not bits or relleno > len(bits):
            raise ValueError("El relleno del archivo comprimido no es válido.")
        bits = bits[:-relleno]

    if raiz.caracter is not None:
        if any(bit != "0" for bit in bits):
            raise ValueError("La carga útil no corresponde al árbol de Huffman.")
        return raiz.caracter * len(bits)

    resultado: list[str] = []
    nodo: Nodo = raiz

    for bit in bits:
        if bit == "0":
            nodo = nodo.izquierdo  # type: ignore[assignment]
        else:
            nodo = nodo.derecho  # type: ignore[assignment]

        if nodo is None:
            raise ValueError("La carga útil contiene una secuencia de bits inválida.")

        if nodo.caracter is not None:
            resultado.append(nodo.caracter)
            nodo = raiz

    if nodo is not raiz:
        raise ValueError("La carga útil terminó a mitad de un código.")

    return "".join(resultado)


def comprimir(
    ruta_entrada: str | Path,
    ruta_salida: str | Path,
) -> tuple[int, int]:
    """Comprime un archivo TXT y devuelve caracteres y símbolos distintos."""
    with open(ruta_entrada, "r", encoding="utf-8", newline="") as archivo:
        texto: str = archivo.read()

    frecuencias: Frecuencias = contar_frecuencias(texto)
    raiz: Nodo | None = construir_arbol(frecuencias)
    codigos: Codigos = generar_codigos(raiz)
    carga, relleno = codificar(texto, codigos)

    escribir_comprimido(ruta_salida, frecuencias, carga, relleno)
    return len(texto), len(frecuencias)


def descomprimir(
    ruta_comprimido: str | Path,
    ruta_salida: str | Path,
) -> int:
    """Descomprime un archivo .huf y devuelve la cantidad de caracteres."""
    frecuencias, relleno, carga = leer_comprimido(ruta_comprimido)
    raiz: Nodo | None = construir_arbol(frecuencias)
    texto: str = decodificar(raiz, carga, relleno)

    with open(ruta_salida, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(texto)

    return len(texto)


def nombre_legible(caracter: str) -> str:
    """Devuelve una representación visible de espacios y caracteres especiales."""
    especiales: dict[str, str] = {
        " ": "␣",
        "\n": r"\n",
        "\r": r"\r",
        "\t": r"\t",
    }
    if caracter in especiales:
        return especiales[caracter]
    if not caracter.isprintable():
        return f"U+{ord(caracter):04X}"
    return caracter


def generar_reporte(
    ruta_original: str | Path,
    ruta_comprimido: str | Path,
) -> tuple[str, bool]:
    """Genera las estadísticas y verifica la recuperación byte a byte."""
    ruta_original = Path(ruta_original)
    ruta_comprimido = Path(ruta_comprimido)

    with open(ruta_original, "r", encoding="utf-8", newline="") as archivo:
        texto: str = archivo.read()

    frecuencias: Frecuencias = contar_frecuencias(texto)
    raiz: Nodo | None = construir_arbol(frecuencias)
    codigos: Codigos = generar_codigos(raiz)

    frecuencias_guardadas, relleno, carga = leer_comprimido(ruta_comprimido)
    if frecuencias_guardadas != frecuencias:
        raise ValueError("El comprimido no corresponde al archivo original seleccionado.")

    raiz_guardada: Nodo | None = construir_arbol(frecuencias_guardadas)
    recuperado: str = decodificar(raiz_guardada, carga, relleno)
    identicos: bool = recuperado.encode("utf-8") == ruta_original.read_bytes()

    cantidad_caracteres: int = len(texto)
    distintos: int = len(frecuencias)
    tamano_original: int = ruta_original.stat().st_size
    tamano_total: int = ruta_comprimido.stat().st_size
    tamano_cabecera: int = 5 + 8 * distintos
    tamano_carga: int = len(carga)

    entropia: float = 0.0
    longitud_media: float = 0.0

    if cantidad_caracteres:
        for caracter, frecuencia in frecuencias.items():
            probabilidad: float = frecuencia / cantidad_caracteres
            entropia -= probabilidad * math.log2(probabilidad)
            longitud_media += probabilidad * len(codigos[caracter])

    lineas: list[str] = [
        "=" * 58,
        "REPORTE DE COMPRESIÓN - ALGORITMO DE HUFFMAN",
        "=" * 58,
        f"Archivo original:        {ruta_original.name}",
        f"Archivo comprimido:      {ruta_comprimido.name}",
        f"Caracteres:              {cantidad_caracteres}",
        f"Símbolos distintos:      {distintos}",
        f"Tamaño original:         {tamano_original} bytes",
        f"Tamaño de cabecera:      {tamano_cabecera} bytes",
        f"Tamaño de carga útil:    {tamano_carga} bytes",
        f"Tamaño comprimido total: {tamano_total} bytes",
    ]

    if tamano_original:
        lineas.append(f"Tasa de compresión:      {tamano_total / tamano_original:.4f}")
    else:
        lineas.append("Tasa de compresión:      No aplica (archivo vacío)")

    lineas.extend([
        f"Entropía H:              {entropia:.4f} bits/carácter",
        f"Longitud media L:        {longitud_media:.4f} bits/carácter",
        f"Verificación:            {'IDÉNTICO' if identicos else 'DIFERENTE'}",
        "",
        "TABLA DE CÓDIGOS",
        f"{'Carácter':<14}{'Frecuencia':>12}   Código",
        "-" * 42,
    ])

    for caracter, frecuencia in sorted(
        frecuencias.items(), key=lambda elemento: (-elemento[1], elemento[0])
    ):
        lineas.append(
            f"{nombre_legible(caracter):<14}{frecuencia:>12}   {codigos[caracter]}"
        )

    return "\n".join(lineas), identicos


def pedir_ruta(mensaje: str) -> Path:
    """Solicita una ruta al usuario desde la terminal."""
    ruta: str = input(mensaje).strip().strip('"').strip("'")
    if not ruta:
        raise ValueError("No ingresaste una ruta.")
    return Path(ruta).expanduser()


def menu() -> None:
    """Muestra las opciones disponibles."""
    print("\n" + "=" * 48)
    print("       COMPRESOR DE TEXTO - HUFFMAN")
    print("=" * 48)
    print("1. Comprimir archivo TXT")
    print("2. Descomprimir archivo HUF")
    print("3. Generar reporte de comparación")
    print("4. Salir")
    print("=" * 48)


def main() -> None:
    """Controla el menú principal del programa."""
    carpeta_proyecto: Path = Path(__file__).resolve().parent
    carpeta_comprimidos: Path = carpeta_proyecto / "comprimidos"
    carpeta_descomprimidos: Path = carpeta_proyecto / "descomprimidos"
    carpeta_reportes: Path = carpeta_proyecto / "reportes"

    for carpeta in (carpeta_comprimidos, carpeta_descomprimidos, carpeta_reportes):
        carpeta.mkdir(exist_ok=True)

    while True:
        menu()
        opcion: str = input("Selecciona una opción (1-4): ").strip()

        try:
            if opcion == "1":
                entrada: Path = pedir_ruta("Ruta del archivo TXT: ")
                if not entrada.is_file():
                    raise FileNotFoundError(f"No existe el archivo: {entrada}")

                sugerido: Path = carpeta_comprimidos / (entrada.stem + ".huf")
                respuesta: str = input(
                    f"Ruta de salida [Enter para {sugerido}]: "
                ).strip().strip('"').strip("'")
                salida: Path = Path(respuesta).expanduser() if respuesta else sugerido
                salida.parent.mkdir(parents=True, exist_ok=True)

                caracteres, simbolos = comprimir(entrada, salida)
                print("\n¡COMPRESIÓN EXITOSA!")
                print(f"Caracteres procesados: {caracteres}")
                print(f"Símbolos distintos: {simbolos}")
                print(f"Archivo generado: {salida.resolve()}")

            elif opcion == "2":
                entrada = pedir_ruta("Ruta del archivo HUF: ")
                if not entrada.is_file():
                    raise FileNotFoundError(f"No existe el archivo: {entrada}")

                sugerido = carpeta_descomprimidos / (entrada.stem + "_recuperado.txt")
                respuesta = input(
                    f"Ruta de salida [Enter para {sugerido}]: "
                ).strip().strip('"').strip("'")
                salida = Path(respuesta).expanduser() if respuesta else sugerido
                salida.parent.mkdir(parents=True, exist_ok=True)

                caracteres = descomprimir(entrada, salida)
                print("\n¡DESCOMPRESIÓN EXITOSA!")
                print(f"Caracteres recuperados: {caracteres}")
                print(f"Archivo generado: {salida.resolve()}")

            elif opcion == "3":
                original: Path = pedir_ruta("Ruta del TXT original: ")
                comprimido: Path = pedir_ruta("Ruta del HUF correspondiente: ")
                if not original.is_file():
                    raise FileNotFoundError(f"No existe el archivo: {original}")
                if not comprimido.is_file():
                    raise FileNotFoundError(f"No existe el archivo: {comprimido}")

                reporte, identicos = generar_reporte(original, comprimido)
                destino: Path = carpeta_reportes / (original.stem + "_reporte.txt")
                with open(destino, "w", encoding="utf-8", newline="") as archivo:
                    archivo.write(reporte)

                print("\n" + reporte)
                print(f"\nReporte guardado en: {destino.resolve()}")
                print(
                    "Verificación byte a byte: "
                    + ("CORRECTA" if identicos else "FALLÓ")
                )

            elif opcion == "4":
                print("Programa finalizado.")
                break

            else:
                print("Opción no válida. Selecciona 1, 2, 3 o 4.")

        except (OSError, ValueError, KeyError) as error:
            print(f"\nERROR: {error}")
        except Exception as error:
            print(f"\nOcurrió un error inesperado: {error}")

        input("\nPresiona Enter para volver al menú...")


if __name__ == "__main__":
    main()
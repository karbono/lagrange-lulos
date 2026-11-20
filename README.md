# lagrange-lulos

Compilación automática en GitHub Actions de [Lagrange Reader](https://github.com/van-geaux/lagrange-reader) para Android, preconfigurada con el servidor BookOrbit (`https://book.karbono.es`).

Al abrir la app por primera vez, se salta la configuración de servidor y va directa a la pantalla de usuario y contraseña.

## Funcionamiento

- Comprueba cada 6 horas si hay una nueva versión estable en `van-geaux/lagrange-reader`.
- Si cambia la versión: clona el tag upstream, aplica `scripts/patch_server.py`, compila y firma con keystore fijo, verifica el bytecode con `scripts/verify_apk.py` y actualiza el release `custom` con nombres fijos:
  - `lagrange-lulos.apk` (universal)
  - `lagrange-lulos-arm64.apk` (arm64-v8a)
  - `lagrange-lulos-VERSION.txt`
  - `lagrange-lulos-SHA256SUMS.txt`

## Descarga

- Página web: `https://dl.karbono.es/libros`
- Enlace directo APK universal: `https://dl.karbono.es/libros/apk`

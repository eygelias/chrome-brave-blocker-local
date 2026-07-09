# Chrome Brave-like Blocker Local

Extensión local para Chrome Manifest V3 inspirada en Brave Shields/uBlock filters.

## Qué incluye

- Reglas DNR generadas desde EasyList/EasyPrivacy/uBlock.
- Limpieza experimental de respuestas de YouTube basada en reglas Brave/uBO (`adPlacements`, `playerAds`, `adSlots`).
- Sin interfaz. Funciona cargada como extensión desempaquetada.

## Instalar en Chrome

1. Abrir `chrome://extensions/`.
2. Activar **Modo de desarrollador**.
3. Pulsar **Cargar extensión sin empaquetar**.
4. Seleccionar carpeta:

```txt
C:\Users\ELY\AppData\Local\chrome-brave-blocker-local\extension
```

## Limitación

Chrome MV3 no permite copiar 100% Brave Shields porque Brave bloquea desde dentro del navegador con su motor nativo. Esta extensión usa lo máximo posible desde una extensión de Chrome.

## Rebuild

```bash
npm install
npm run build
```

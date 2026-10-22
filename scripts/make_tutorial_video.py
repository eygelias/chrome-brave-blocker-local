import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# Resolution and framerate
WIDTH = 1280
HEIGHT = 720
FPS = 30

OUTPUT_DIR = Path(r"C:\Users\ELY\.gemini\antigravity\scratch\chrome-brave-blocker-local\docs\videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load fonts
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
FONT_SUB = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
FONT_HEAVY = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 34)
FONT_BODY = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
FONT_BODY_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
FONT_SMALL = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_MONO = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)

def ease_in_out(t):
    return 3 * t**2 - 2 * t**3

def lerp(a, b, t):
    return a + (b - a) * t

def draw_cursor(img, x, y, clicking=False, click_progress=0.0):
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    
    if clicking and click_progress < 1.0:
        radius = int(8 + 26 * click_progress)
        alpha = int(220 * (1.0 - click_progress))
        odraw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            outline=(26, 115, 232, alpha),
            width=3
        )
        odraw.ellipse(
            [x - radius // 2, y - radius // 2, x + radius // 2, y + radius // 2],
            fill=(66, 133, 244, int(alpha * 0.4))
        )
    
    # Cursor coordinates
    coords = [
        (x, y),
        (x, y + 22),
        (x + 6, y + 17),
        (x + 11, y + 26),
        (x + 15, y + 24),
        (x + 10, y + 15),
        (x + 17, y + 15)
    ]
    shadow_coords = [(cx + 2, cy + 3) for cx, cy in coords]
    odraw.polygon(shadow_coords, fill=(0, 0, 0, 110))
    odraw.polygon(coords, outline=(0, 0, 0, 255), fill=(255, 255, 255, 255), width=2)
    
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))

def draw_browser_chrome(draw, title="Google Chrome", url="chrome://newtab"):
    # Window background
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(241, 243, 244))
    
    # Top Tab Bar
    draw.rectangle([0, 0, WIDTH, 42], fill=(222, 225, 230))
    
    # Window controls (macOS/Chrome style pill buttons)
    colors = [(237, 106, 94), (245, 191, 79), (98, 197, 84)]
    for i, col in enumerate(colors):
        draw.ellipse([16 + i * 20, 14, 28 + i * 20, 26], fill=col)
    
    # Tab
    tab_x, tab_w = 85, 230
    draw.rounded_rectangle([tab_x, 8, tab_x + tab_w, 42], radius=8, fill=(255, 255, 255))
    draw.ellipse([tab_x + 14, 18, tab_x + 26, 30], fill=(66, 133, 244))
    draw.text((tab_x + 36, 15), title[:22], font=FONT_BODY_BOLD, fill=(60, 64, 67))
    
    # Address bar row
    draw.rectangle([0, 42, WIDTH, 86], fill=(255, 255, 255))
    draw.line([(0, 86), (WIDTH, 86)], fill=(218, 220, 224), width=1)
    
    # Navigation buttons: Back, Forward, Refresh
    btn_color = (95, 99, 104)
    # Left arrow
    draw.polygon([(26, 64), (34, 58), (34, 70)], fill=btn_color)
    # Right arrow
    draw.polygon([(56, 64), (48, 58), (48, 70)], fill=(189, 193, 198))
    # Refresh circle
    draw.ellipse([70, 56, 84, 70], outline=btn_color, width=2)
    
    # Omnibox / Address bar
    box_x = 100
    box_w = WIDTH - 220
    draw.rounded_rectangle([box_x, 48, box_x + box_w, 80], radius=16, fill=(241, 243, 244))
    # Lock / Info icon
    draw.rectangle([box_x + 14, 60, box_x + 22, 68], fill=(95, 99, 104))
    draw.arc([box_x + 14, 55, box_x + 22, 63], 180, 0, fill=(95, 99, 104), width=2)
    # URL text
    draw.text((box_x + 34, 54), url, font=FONT_BODY, fill=(32, 33, 36))
    
    # Right icons: Extensions puzzle icon & Avatar
    # Puzzle icon
    p_x = WIDTH - 100
    draw.rounded_rectangle([p_x, 52, p_x + 24, 76], radius=4, fill=(95, 99, 104))
    # Avatar
    draw.ellipse([WIDTH - 55, 50, WIDTH - 27, 78], fill=(26, 115, 232))
    draw.text((WIDTH - 46, 54), "E", font=FONT_BODY_BOLD, fill=(255, 255, 255))

def draw_step_banner(draw, step_num, step_title, subtext=""):
    # Header Step Banner overlay
    banner_w = WIDTH - 80
    draw.rounded_rectangle([40, 96, 40 + banner_w, 154], radius=10, fill=(24, 28, 38))
    
    # Accent color badge
    draw.rounded_rectangle([52, 106, 142, 144], radius=6, fill=(26, 115, 232))
    draw.text((62, 114), f"PASO {step_num}", font=FONT_BODY_BOLD, fill=(255, 255, 255))
    
    # Title & subtext
    draw.text((158, 108), step_title, font=FONT_TITLE, fill=(255, 255, 255))
    if subtext:
        draw.text((160, 134), subtext, font=FONT_SMALL, fill=(180, 192, 212))

def draw_progress(draw, current_frame, total_frames):
    progress = min(1.0, current_frame / max(1, total_frames))
    bar_w = int(WIDTH * progress)
    draw.rectangle([0, HEIGHT - 5, WIDTH, HEIGHT], fill=(220, 225, 232))
    draw.rectangle([0, HEIGHT - 5, bar_w, HEIGHT], fill=(26, 115, 232))

# ==========================================================
# SCENE 1: Descargar Release de GitHub
# ==========================================================
def render_scene_1(out_writer):
    frames = 180  # 6 seconds
    for f in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Chrome UI
        draw_browser_chrome(draw, title="Releases · eygelias/chrome-brave-blocker-local", url="https://github.com/eygelias/chrome-brave-blocker-local/releases")
        draw_step_banner(draw, 1, "Descarga el ZIP desde GitHub Releases", "Accede a Releases y descarga chrome-brave-blocker-local-v3.1.0.zip")
        
        # GitHub Release Page content
        content_y = 168
        # Header repo
        draw.text((60, content_y), "eygelias / chrome-brave-blocker-local", font=FONT_SUB, fill=(9, 105, 218))
        draw.rounded_rectangle([WIDTH - 210, content_y - 2, WIDTH - 60, content_y + 30], radius=6, fill=(246, 248, 250), outline=(208, 215, 222))
        draw.text((WIDTH - 190, content_y + 4), "★ Public Repo", font=FONT_BODY, fill=(31, 35, 40))
        
        # Release Card Box
        card_y = content_y + 36
        draw.rounded_rectangle([60, card_y, WIDTH - 60, card_y + 420], radius=12, fill=(255, 255, 255), outline=(208, 215, 222), width=1)
        
        # Tag & Title
        draw.rounded_rectangle([80, card_y + 18, 160, card_y + 44], radius=12, fill=(234, 254, 238), outline=(63, 185, 80))
        draw.text((96, card_y + 22), "v3.1.0", font=FONT_BODY_BOLD, fill=(26, 127, 55))
        draw.text((176, card_y + 20), "v3.1.0 — Brave Upstream Sync & Shields Suite", font=FONT_TITLE, fill=(31, 35, 40))
        
        # Description
        draw.text((80, card_y + 60), "Última versión compilada con 147.906 reglas DNR, Clean URLs, Suite YouTube Shields y Twitch VAFT.", font=FONT_BODY, fill=(101, 109, 118))
        
        # Assets Header Box
        assets_y = card_y + 100
        draw.rounded_rectangle([80, assets_y, WIDTH - 80, assets_y + 280], radius=8, fill=(246, 248, 250), outline=(208, 215, 222))
        draw.text((100, assets_y + 14), "Assets (Archivos descargables)", font=FONT_BODY_BOLD, fill=(31, 35, 40))
        
        # Asset 1: Chrome ZIP (Target)
        a1_y = assets_y + 48
        is_hovered = 35 <= f <= 75
        btn_bg = (235, 245, 255) if is_hovered else (255, 255, 255)
        border_col = (26, 115, 232) if is_hovered else (208, 215, 222)
        
        draw.rounded_rectangle([100, a1_y, WIDTH - 100, a1_y + 54], radius=6, fill=btn_bg, outline=border_col, width=2 if is_hovered else 1)
        draw.text((120, a1_y + 16), "📦 chrome-brave-blocker-local-v3.1.0.zip", font=FONT_BODY_BOLD, fill=(9, 105, 218))
        draw.text((WIDTH - 240, a1_y + 16), "3.13 MB · Descargar", font=FONT_BODY_BOLD, fill=(26, 127, 55))
        
        # Asset 2: Firefox ZIP
        a2_y = a1_y + 64
        draw.rounded_rectangle([100, a2_y, WIDTH - 100, a2_y + 50], radius=6, fill=(255, 255, 255), outline=(208, 215, 222))
        draw.text((120, a2_y + 15), "📦 firefox-brave-blocker-local-v3.1.0.zip", font=FONT_BODY, fill=(31, 35, 40))
        draw.text((WIDTH - 220, a2_y + 15), "1.18 MB", font=FONT_BODY, fill=(101, 109, 118))
        
        # Asset 3: Source Code
        a3_y = a2_y + 58
        draw.rounded_rectangle([100, a3_y, WIDTH - 100, a3_y + 50], radius=6, fill=(255, 255, 255), outline=(208, 215, 222))
        draw.text((120, a3_y + 15), "📁 Source code (zip)", font=FONT_BODY, fill=(101, 109, 118))
        
        # Download animation popup (after click at frame 50)
        if f >= 55:
            # Download notification at top-right
            d_t = min(1.0, (f - 55) / 15.0)
            d_y = int(lerp(40, 94, ease_in_out(d_t)))
            draw.rounded_rectangle([WIDTH - 380, d_y, WIDTH - 50, d_y + 64], radius=8, fill=(255, 255, 255), outline=(26, 115, 232), width=2)
            draw.text((WIDTH - 360, d_y + 12), "✓ Descarga completada", font=FONT_BODY_BOLD, fill=(26, 127, 55))
            draw.text((WIDTH - 360, d_y + 36), "chrome-brave-blocker-local-v3.1.0.zip", font=FONT_SMALL, fill=(60, 64, 67))
        
        # File extraction card overlay (after frame 100)
        if f >= 105:
            e_t = min(1.0, (f - 105) / 20.0)
            modal_alpha = ease_in_out(e_t)
            # Extracted Explorer window mockup
            ex_x, ex_y = 200, 260
            ex_w, ex_h = 880, 310
            draw.rounded_rectangle([ex_x, ex_y, ex_x + ex_w, ex_y + ex_h], radius=12, fill=(255, 255, 255), outline=(26, 115, 232), width=3)
            # Explorer titlebar
            draw.rounded_rectangle([ex_x, ex_y, ex_x + ex_w, ex_y + 40], radius=12, fill=(240, 243, 248))
            draw.text((ex_x + 20, ex_y + 10), "Explorador de Archivos — Extraer Carpeta", font=FONT_BODY_BOLD, fill=(30, 35, 45))
            
            # Explorer content
            draw.text((ex_x + 30, ex_y + 55), "1. Haz clic derecho sobre el ZIP descargado y pulsa 'Extraer todo...'", font=FONT_BODY, fill=(30, 30, 30))
            draw.text((ex_x + 30, ex_y + 85), "2. Extrae en una carpeta permanente (ej. C:\\Program Files\\Blocker o Documentos)", font=FONT_BODY, fill=(30, 30, 30))
            
            # Folder card highlight
            draw.rounded_rectangle([ex_x + 30, ex_y + 125, ex_x + ex_w - 30, ex_y + 230], radius=8, fill=(235, 245, 255), outline=(66, 133, 244), width=2)
            draw.text((ex_x + 50, ex_y + 145), "📁  extension/", font=FONT_HEAVY, fill=(26, 115, 232))
            draw.text((ex_x + 50, ex_y + 190), "Esta carpeta contiene el bloqueador listo (manifest.json, rulesets, etc.). ¡No la borres!", font=FONT_BODY_BOLD, fill=(32, 33, 36))
            
            # Tip badge
            draw.rounded_rectangle([ex_x + 30, ex_y + 245, ex_x + ex_w - 30, ex_y + 285], radius=6, fill=(254, 243, 199), outline=(245, 158, 11))
            draw.text((ex_x + 45, ex_y + 256), "💡 Consejo: Mantén la carpeta extraída en una ubicación fija para que Chrome la conserve.", font=FONT_SMALL, fill=(146, 64, 14))

        # Cursor animation
        if f < 90:
            c_t = min(1.0, f / 48.0)
            cx = lerp(WIDTH // 2, 450, ease_in_out(c_t))
            cy = lerp(400, a1_y + 27, ease_in_out(c_t))
            is_click = 48 <= f <= 60
            click_p = (f - 48) / 12.0 if is_click else 0.0
            draw_cursor(img, int(cx), int(cy), clicking=is_click, click_progress=click_p)
            
        draw_progress(draw, f, frames)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out_writer.write(frame_cv)

# ==========================================================
# SCENE 2: Abrir chrome://extensions/ en Google Chrome
# ==========================================================
def render_scene_2(out_writer):
    frames = 180  # 6 seconds
    full_url = "chrome://extensions/"
    
    for f in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Typing progress
        if f < 30:
            typed_url = ""
        elif f < 110:
            type_t = (f - 30) / 80.0
            chars = int(len(full_url) * type_t)
            typed_url = full_url[:chars]
            if (f // 8) % 2 == 0:
                typed_url += "|"
        else:
            typed_url = full_url
            
        draw_browser_chrome(draw, title="Nueva pestaña" if f < 130 else "Extensiones", url=typed_url)
        draw_step_banner(draw, 2, "Abre la página de extensiones en Chrome", "Escribe chrome://extensions/ en la barra de direcciones y pulsa Enter")
        
        content_y = 170
        if f < 130:
            # Google New Tab mockup
            draw.text((WIDTH // 2 - 130, 290), "Google", font=FONT_HEAVY, fill=(95, 99, 104))
            draw.rounded_rectangle([WIDTH // 2 - 280, 360, WIDTH // 2 + 280, 410], radius=24, fill=(255, 255, 255), outline=(218, 220, 224), width=1)
            draw.text((WIDTH // 2 - 240, 375), "Buscar en Google o escribir una URL...", font=FONT_BODY, fill=(150, 150, 150))
            
            # Instruction card center
            draw.rounded_rectangle([WIDTH // 2 - 320, 460, WIDTH // 2 + 320, 560], radius=10, fill=(246, 248, 250), outline=(26, 115, 232), width=2)
            draw.text((WIDTH // 2 - 280, 480), "💡 También puedes entrar desde el menú:", font=FONT_BODY_BOLD, fill=(26, 115, 232))
            draw.text((WIDTH // 2 - 280, 512), "Menú ⋮ arriba a la derecha  →  Extensiones  →  Gestionar extensiones", font=FONT_BODY, fill=(32, 33, 36))
        else:
            # Transition to Extensions UI mockup
            draw.rectangle([0, 86, WIDTH, HEIGHT], fill=(248, 249, 250))
            draw_browser_chrome(draw, title="Extensiones", url="chrome://extensions/")
            draw_step_banner(draw, 2, "¡Página de extensiones cargada!", "Ahora activaremos el Modo de desarrollador")
            
            draw.rounded_rectangle([80, 200, WIDTH - 80, 500], radius=12, fill=(255, 255, 255), outline=(218, 220, 224))
            draw.text((110, 230), "Extensiones de Google Chrome", font=FONT_TITLE, fill=(32, 33, 36))
            draw.text((110, 270), "Administra tus complementos y extensiones locales instaladas.", font=FONT_BODY, fill=(95, 99, 104))
            draw.rounded_rectangle([110, 320, 480, 420], radius=8, fill=(241, 243, 244))
            draw.text((140, 360), "Sin extensiones de desarrollador aún.", font=FONT_BODY, fill=(120, 120, 120))
            
        # Cursor typing in address bar
        if f < 125:
            if f < 35:
                c_t = min(1.0, f / 30.0)
                cx = lerp(WIDTH // 2, 240, ease_in_out(c_t))
                cy = lerp(350, 64, ease_in_out(c_t))
                is_click = 25 <= f <= 35
                click_p = (f - 25) / 10.0 if is_click else 0.0
            else:
                cx, cy = 280, 64
                is_click = False
                click_p = 0.0
            draw_cursor(img, int(cx), int(cy), clicking=is_click, click_progress=click_p)
            
        draw_progress(draw, f, frames)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out_writer.write(frame_cv)

# ==========================================================
# SCENE 3: Activar Modo de desarrollador
# ==========================================================
def render_scene_3(out_writer):
    frames = 180  # 6 seconds
    for f in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (248, 249, 250))
        draw = ImageDraw.Draw(img)
        
        draw_browser_chrome(draw, title="Extensiones", url="chrome://extensions/")
        draw_step_banner(draw, 3, "Activa 'Modo de desarrollador' arriba a la derecha", "Haz clic en el interruptor para desbloquear las opciones de carga local")
        
        # Extensions Header inside page
        page_header_y = 160
        draw.rectangle([0, page_header_y, WIDTH, page_header_y + 60], fill=(255, 255, 255))
        draw.line([(0, page_header_y + 60), (WIDTH, page_header_y + 60)], fill=(218, 220, 224), width=1)
        
        draw.text((60, page_header_y + 16), "Extensiones", font=FONT_TITLE, fill=(32, 33, 36))
        
        # Toggle switch at top right
        toggle_x = WIDTH - 260
        toggle_y = page_header_y + 18
        
        is_toggled = f >= 90
        # Callout highlight pulse
        pulse = math.sin(f * 0.15) * 4
        hl_box = [toggle_x - 14 - pulse, toggle_y - 8 - pulse, WIDTH - 40 + pulse, toggle_y + 36 + pulse]
        if f < 90:
            draw.rounded_rectangle(hl_box, radius=8, outline=(234, 67, 53), width=3)
            draw.text((toggle_x - 300, toggle_y + 4), "👈  ¡HAZ CLIC AQUÍ!", font=FONT_BODY_BOLD, fill=(234, 67, 53))
        
        draw.text((toggle_x, toggle_y + 4), "Modo de desarrollador", font=FONT_BODY_BOLD, fill=(32, 33, 36))
        
        # The Switch element
        sw_x = WIDTH - 80
        sw_y = toggle_y + 2
        sw_w, sw_h = 38, 20
        
        if is_toggled:
            # Blue switch ON
            draw.rounded_rectangle([sw_x, sw_y, sw_x + sw_w, sw_y + sw_h], radius=10, fill=(26, 115, 232))
            draw.ellipse([sw_x + sw_w - 18, sw_y + 2, sw_x + sw_w - 2, sw_y + sw_h - 2], fill=(255, 255, 255))
        else:
            # Grey switch OFF
            draw.rounded_rectangle([sw_x, sw_y, sw_x + sw_w, sw_y + sw_h], radius=10, fill=(189, 193, 198))
            draw.ellipse([sw_x + 2, sw_y + 2, sw_x + 18, sw_y + sw_h - 2], fill=(255, 255, 255))
            
        # Action Bar that appears when toggle is turned ON
        if is_toggled:
            bar_t = min(1.0, (f - 90) / 18.0)
            bar_y = int(lerp(page_header_y + 60, page_header_y + 61, ease_in_out(bar_t)))
            bar_h = 56
            draw.rectangle([0, bar_y, WIDTH, bar_y + bar_h], fill=(255, 255, 255))
            draw.line([(0, bar_y + bar_h), (WIDTH, bar_y + bar_h)], fill=(218, 220, 224), width=1)
            
            # Button 1: Cargar extensión sin empaquetar (Load unpacked)
            btn1_w = 260
            b1_x = 60
            draw.rounded_rectangle([b1_x, bar_y + 10, b1_x + btn1_w, bar_y + 46], radius=18, fill=(235, 245, 255), outline=(26, 115, 232), width=2)
            draw.text((b1_x + 20, bar_y + 18), "Cargar extensión sin empaquetar", font=FONT_BODY_BOLD, fill=(26, 115, 232))
            
            # Button 2: Empaquetar extensión
            b2_x = b1_x + btn1_w + 16
            draw.rounded_rectangle([b2_x, bar_y + 10, b2_x + 180, bar_y + 46], radius=18, fill=(255, 255, 255), outline=(218, 220, 224))
            draw.text((b2_x + 20, bar_y + 18), "Empaquetar extensión", font=FONT_BODY, fill=(60, 64, 67))
            
            # Button 3: Actualizar
            b3_x = b2_x + 196
            draw.rounded_rectangle([b3_x, bar_y + 10, b3_x + 120, bar_y + 46], radius=18, fill=(255, 255, 255), outline=(218, 220, 224))
            draw.text((b3_x + 24, bar_y + 18), "Actualizar ↻", font=FONT_BODY, fill=(60, 64, 67))
            
            # Pointer to Button 1
            if f >= 115:
                draw.text((b1_x + 30, bar_y + 70), "⬆️ ¡Apareció este botón! En el siguiente paso lo pulsaremos.", font=FONT_BODY_BOLD, fill=(26, 115, 232))

        # Main empty body
        body_y = 350
        draw.rounded_rectangle([60, body_y, WIDTH - 60, body_y + 240], radius=12, fill=(255, 255, 255), outline=(218, 220, 224))
        draw.text((90, body_y + 30), "Todas las extensiones", font=FONT_TITLE, fill=(32, 33, 36))
        draw.text((90, body_y + 70), "Activa el modo de desarrollador para cargar extensiones locales descargadas desde GitHub.", font=FONT_BODY, fill=(100, 100, 100))
        
        # Cursor moves to toggle
        if f < 90:
            c_t = min(1.0, f / 75.0)
            cx = lerp(WIDTH // 2, sw_x + 12, ease_in_out(c_t))
            cy = lerp(400, sw_y + 10, ease_in_out(c_t))
            is_click = 75 <= f <= 90
            click_p = (f - 75) / 15.0 if is_click else 0.0
        else:
            # Cursor moves towards "Cargar descomprimida"
            c_t = min(1.0, (f - 90) / 60.0)
            cx = lerp(sw_x + 12, 190, ease_in_out(c_t))
            cy = lerp(sw_y + 10, page_header_y + 88, ease_in_out(c_t))
            is_click = False
            click_p = 0.0
            
        draw_cursor(img, int(cx), int(cy), clicking=is_click, click_progress=click_p)
        
        draw_progress(draw, f, frames)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out_writer.write(frame_cv)

# ==========================================================
# SCENE 4: Cargar Extensión y Verificación
# ==========================================================
def render_scene_4(out_writer):
    frames = 240  # 8 seconds
    for f in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (248, 249, 250))
        draw = ImageDraw.Draw(img)
        
        draw_browser_chrome(draw, title="Extensiones", url="chrome://extensions/")
        draw_step_banner(draw, 4, "Pulsa 'Cargar extensión sin empaquetar' y elige 'extension'", "Selecciona la carpeta extraída para instalarla instantáneamente")
        
        # Extensions Header
        page_header_y = 160
        draw.rectangle([0, page_header_y, WIDTH, page_header_y + 60], fill=(255, 255, 255))
        draw.text((60, page_header_y + 16), "Extensiones", font=FONT_TITLE, fill=(32, 33, 36))
        
        # Toggle switch ON
        toggle_x = WIDTH - 260
        toggle_y = page_header_y + 18
        draw.text((toggle_x, toggle_y + 4), "Modo de desarrollador", font=FONT_BODY_BOLD, fill=(32, 33, 36))
        sw_x = WIDTH - 80
        draw.rounded_rectangle([sw_x, toggle_y + 2, sw_x + 38, toggle_y + 22], radius=10, fill=(26, 115, 232))
        draw.ellipse([sw_x + 20, toggle_y + 4, sw_x + 36, toggle_y + 20], fill=(255, 255, 255))
        
        # Action Bar
        bar_y = page_header_y + 60
        draw.rectangle([0, bar_y, WIDTH, bar_y + 56], fill=(255, 255, 255))
        draw.line([(0, bar_y + 56), (WIDTH, bar_y + 56)], fill=(218, 220, 224), width=1)
        
        # Button 1: Load unpacked
        btn1_hover = f < 60
        draw.rounded_rectangle([60, bar_y + 10, 320, bar_y + 46], radius=18, fill=(235, 245, 255) if btn1_hover else (255, 255, 255), outline=(26, 115, 232), width=2)
        draw.text((80, bar_y + 18), "Cargar extensión sin empaquetar", font=FONT_BODY_BOLD, fill=(26, 115, 232))
        
        # Folder dialog popup (Frames 55 to 140)
        show_dialog = 55 <= f <= 145
        if show_dialog:
            d_x, d_y = 240, 260
            d_w, d_h = 800, 350
            # Dim background
            draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(0, 0, 0, 70))
            
            # Dialog window
            draw.rounded_rectangle([d_x, d_y, d_x + d_w, d_y + d_h], radius=12, fill=(255, 255, 255), outline=(26, 115, 232), width=3)
            # Dialog header
            draw.rounded_rectangle([d_x, d_y, d_x + d_w, d_y + 45], radius=12, fill=(240, 243, 248))
            draw.text((d_x + 20, d_y + 12), "Seleccionar carpeta de extensión", font=FONT_BODY_BOLD, fill=(32, 33, 36))
            
            # File list
            draw.text((d_x + 30, d_y + 65), "Buscar en:  chrome-brave-blocker-local-v3.1.0", font=FONT_BODY, fill=(100, 100, 100))
            
            # Folder item 1: extension (HIGHLIGHTED)
            f1_y = d_y + 100
            draw.rounded_rectangle([d_x + 30, f1_y, d_x + d_w - 30, f1_y + 54], radius=6, fill=(204, 229, 255), outline=(26, 115, 232), width=2)
            draw.text((d_x + 50, f1_y + 14), "📁  extension", font=FONT_HEAVY, fill=(26, 115, 232))
            draw.text((d_x + 260, f1_y + 18), "←  ¡Selecciona esta carpeta!", font=FONT_BODY_BOLD, fill=(26, 127, 55))
            
            # Folder item 2: firefox
            f2_y = f1_y + 64
            draw.rounded_rectangle([d_x + 30, f2_y, d_x + d_w - 30, f2_y + 44], radius=6, fill=(248, 249, 250), outline=(218, 220, 224))
            draw.text((d_x + 50, f2_y + 12), "📁  firefox", font=FONT_BODY, fill=(100, 100, 100))
            
            # Bottom action: "Seleccionar carpeta" button
            btn_sel_x = d_x + d_w - 220
            btn_sel_y = d_y + d_h - 60
            btn_sel_hover = f >= 115
            draw.rounded_rectangle([btn_sel_x, btn_sel_y, btn_sel_x + 190, btn_sel_y + 42], radius=6, fill=(26, 115, 232) if btn_sel_hover else (11, 87, 208))
            draw.text((btn_sel_x + 24, btn_sel_y + 12), "Seleccionar carpeta", font=FONT_BODY_BOLD, fill=(255, 255, 255))
            
        # Installed Extension Card (Appears after frame 145)
        if f > 145:
            card_x, card_y = 60, 300
            card_w, card_h = 560, 260
            
            # Glow / animation entrance
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=12, fill=(255, 255, 255), outline=(26, 115, 232), width=2)
            
            # Extension Icon (Shield)
            ic_x, ic_y = card_x + 24, card_y + 24
            draw.rounded_rectangle([ic_x, ic_y, ic_x + 48, ic_y + 48], radius=12, fill=(251, 84, 43))
            draw.polygon([(ic_x + 24, ic_y + 10), (ic_x + 38, ic_y + 18), (ic_x + 38, ic_y + 36), (ic_x + 24, ic_y + 42), (ic_x + 10, ic_y + 36), (ic_x + 10, ic_y + 18)], fill=(255, 255, 255))
            
            # Extension Info
            draw.text((card_x + 86, card_y + 22), "Brave-like Blocker Local (Chrome)", font=FONT_TITLE, fill=(32, 33, 36))
            draw.text((card_x + 86, card_y + 54), "3.1.0", font=FONT_SMALL, fill=(95, 99, 104))
            
            # Description
            draw.text((card_x + 24, card_y + 86), "Bloqueador local inspirado en Brave | Local ad/tracker blocker.", font=FONT_BODY, fill=(60, 64, 67))
            
            # Badges
            draw.rounded_rectangle([card_x + 24, card_y + 120, card_x + 240, card_y + 148], radius=6, fill=(234, 254, 238), outline=(63, 185, 80))
            draw.text((card_x + 34, card_y + 125), "✓ 147.906 reglas DNR activas", font=FONT_SMALL, fill=(26, 127, 55))
            
            draw.rounded_rectangle([card_x + 252, card_y + 120, card_x + 460, card_y + 148], radius=6, fill=(235, 245, 255), outline=(66, 133, 244))
            draw.text((card_x + 262, card_y + 125), "🛡️ Clean URLs & YouTube/Twitch", font=FONT_SMALL, fill=(26, 115, 232))
            
            # Bottom row inside card
            draw.line([(card_x, card_y + 165), (card_x + card_w, card_y + 165)], fill=(241, 243, 244), width=1)
            draw.text((card_x + 24, card_y + 185), "Detalles", font=FONT_BODY_BOLD, fill=(26, 115, 232))
            draw.text((card_x + 110, card_y + 185), "Quitar", font=FONT_BODY, fill=(95, 99, 104))
            
            # Active switch ON
            sw_c_x = card_x + card_w - 60
            sw_c_y = card_y + 180
            draw.rounded_rectangle([sw_c_x, sw_c_y, sw_c_x + 38, sw_c_y + 20], radius=10, fill=(26, 115, 232))
            draw.ellipse([sw_c_x + 20, sw_c_y + 2, sw_c_x + 36, sw_c_y + 18], fill=(255, 255, 255))
            
            # Success Announcement Banner Right
            s_x = card_x + card_w + 30
            s_w = WIDTH - s_x - 60
            draw.rounded_rectangle([s_x, card_y + 20, s_x + s_w, card_y + 220], radius=12, fill=(234, 254, 238), outline=(63, 185, 80), width=2)
            draw.text((s_x + 24, card_y + 45), "🎉  ¡INSTALACIÓN EXITOSA!", font=FONT_HEAVY, fill=(26, 127, 55))
            draw.text((s_x + 24, card_y + 95), "La extensión ya está funcionando silenciosamente.", font=FONT_BODY_BOLD, fill=(32, 33, 36))
            draw.text((s_x + 24, card_y + 125), "• Bloquea anuncios de red nativamente con DNR.", font=FONT_BODY, fill=(60, 64, 67))
            draw.text((s_x + 24, card_y + 150), "• Limpia parámetros de rastreo (Clean URLs).", font=FONT_BODY, fill=(60, 64, 67))
            draw.text((s_x + 24, card_y + 175), "• YouTube sin anuncios ni retrasos SABR en móviles.", font=FONT_BODY, fill=(60, 64, 67))

        # Cursor animations
        if f < 60:
            c_t = min(1.0, f / 45.0)
            cx = lerp(200, 180, ease_in_out(c_t))
            cy = lerp(350, bar_y + 28, ease_in_out(c_t))
            is_click = 45 <= f <= 58
            click_p = (f - 45) / 13.0 if is_click else 0.0
            draw_cursor(img, int(cx), int(cy), clicking=is_click, click_progress=click_p)
        elif show_dialog:
            c_t = min(1.0, (f - 60) / 60.0)
            cx = lerp(d_x + 200, btn_sel_x + 90, ease_in_out(c_t))
            cy = lerp(f1_y + 25, btn_sel_y + 20, ease_in_out(c_t))
            is_click = 120 <= f <= 135
            click_p = (f - 120) / 15.0 if is_click else 0.0
            draw_cursor(img, int(cx), int(cy), clicking=is_click, click_progress=click_p)
            
        draw_progress(draw, f, frames)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out_writer.write(frame_cv)

# ==========================================================
# SCENE 5: Resumen y Conclusión
# ==========================================================
def render_scene_5(out_writer):
    frames = 90  # 3 seconds
    for f in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (24, 28, 38))
        draw = ImageDraw.Draw(img)
        
        # Center card
        box_w, box_h = 920, 520
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2
        
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=16, fill=(32, 38, 52), outline=(26, 115, 232), width=3)
        
        # Title
        draw.text((box_x + 50, box_y + 40), "Resumen: Cómo instalar en Chrome", font=FONT_HEAVY, fill=(255, 255, 255))
        draw.text((box_x + 50, box_y + 85), "Brave-like Blocker Local v3.1.0 — Guía Rápida", font=FONT_SUB, fill=(66, 133, 244))
        
        steps = [
            ("1", "Descarga el ZIP", "Baja chrome-brave-blocker-local-v3.1.0.zip desde GitHub Releases."),
            ("2", "Extrae la carpeta", "Extrae el archivo y conserva la carpeta 'extension' en una ruta fija."),
            ("3", "Abre chrome://extensions/", "Escribe la dirección en la barra de Chrome o accede desde Menú → Extensiones."),
            ("4", "Modo desarrollador", "Activa el interruptor 'Modo de desarrollador' arriba a la derecha."),
            ("5", "Carga la extensión", "Pulsa 'Cargar extensión sin empaquetar' y selecciona la carpeta 'extension'.")
        ]
        
        for idx, (num, title, desc) in enumerate(steps):
            sy = box_y + 130 + idx * 64
            draw.ellipse([box_x + 50, sy, box_x + 86, sy + 36], fill=(26, 115, 232))
            draw.text((box_x + 63, sy + 6), num, font=FONT_BODY_BOLD, fill=(255, 255, 255))
            draw.text((box_x + 104, sy + 3), title, font=FONT_BODY_BOLD, fill=(255, 255, 255))
            draw.text((box_x + 104, sy + 25), desc, font=FONT_SMALL, fill=(180, 192, 212))
            
        # Bottom repo link
        draw.text((box_x + 50, box_y + 470), "Repositorio: github.com/eygelias/chrome-brave-blocker-local", font=FONT_BODY_BOLD, fill=(26, 115, 232))
        
        draw_progress(draw, f, frames)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out_writer.write(frame_cv)

def main():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # 1. Escena 1
    p1 = str(OUTPUT_DIR / "escena_1_descarga.mp4")
    print("Renderizando Escena 1:", p1)
    w1 = cv2.VideoWriter(p1, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_1(w1)
    w1.release()
    
    # 2. Escena 2
    p2 = str(OUTPUT_DIR / "escena_2_abrir_chrome.mp4")
    print("Renderizando Escena 2:", p2)
    w2 = cv2.VideoWriter(p2, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_2(w2)
    w2.release()
    
    # 3. Escena 3
    p3 = str(OUTPUT_DIR / "escena_3_modo_desarrollador.mp4")
    print("Renderizando Escena 3:", p3)
    w3 = cv2.VideoWriter(p3, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_3(w3)
    w3.release()
    
    # 4. Escena 4
    p4 = str(OUTPUT_DIR / "escena_4_cargar_extension.mp4")
    print("Renderizando Escena 4:", p4)
    w4 = cv2.VideoWriter(p4, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_4(w4)
    w4.release()
    
    # 5. Escena 5
    p5 = str(OUTPUT_DIR / "escena_5_resumen.mp4")
    print("Renderizando Escena 5:", p5)
    w5 = cv2.VideoWriter(p5, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_5(w5)
    w5.release()
    
    # Video Completo
    p_full = str(OUTPUT_DIR / "tutorial_instalacion_chrome_completo.mp4")
    print("Generando Video Completo:", p_full)
    w_full = cv2.VideoWriter(p_full, fourcc, FPS, (WIDTH, HEIGHT))
    render_scene_1(w_full)
    render_scene_2(w_full)
    render_scene_3(w_full)
    render_scene_4(w_full)
    render_scene_5(w_full)
    w_full.release()
    
    print("\n¡Todos los videos se han generado con éxito en:", str(OUTPUT_DIR))

if __name__ == "__main__":
    main()

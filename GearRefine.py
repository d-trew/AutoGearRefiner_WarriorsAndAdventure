"""
Gear Refine Automation Bot for BlueStacks
==========================================
Requirements:
    pip install pyautogui pillow pytesseract keyboard

Also install Tesseract OCR:
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
    Set TESSERACT_PATH below to your install path.

SETUP INSTRUCTIONS:
1. Run the script once with CALIBRATION_MODE = True to capture screen coordinates.
2. Fill in the coordinate constants below.
3. Set your DESIRED_STATS and MAX_STONES_PER_GEAR.
4. Run normally.

Press F9 at any time to emergency stop.
"""
import os

import pyautogui
import pytesseract
import time
import keyboard
import sys
from PIL import Image, ImageGrab

# ─────────────────────────────────────────────
# CONFIGURATION — Edit these values
# ─────────────────────────────────────────────

# Path to Tesseract executable
TESSERACT_PATH = r"C:\Users\Daniel's laptop\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

CALIBRATION_MODE = False
VISUALISATION_MODE = False

TEST_OCR_MODE = False
TEST_OCR_IMAGE = "debug\multimon_test0.png"
# TEST_OCR_IMAGE =  "debug/all_skills_read_test.png"

# for naming debug images
capture_count = 0

# areas of screen coords do not match and cannot be used for clicks on the screen 
# and in the same way points from calibration mode cannot be used to map regions of the screen
#  ------------------------- EXPLANATION ------------`-----------------------
# CAPTURE COORDINATES — used by ImageGrab.grab(), these are physical pixels
# relative to the top-left corner of the secondary monitor itself.
# These are different because ImageGrab uses the raw framebuffer coordinate
# system which doesn't match the logical/scaled coords that mouse clicks use.

# From Calibration mode
# CLICK COORDINATES — used by pyautogui.click(), these are logical pixels
# relative to your primary monitor. Negative X = left monitor.
REFINE_BUTTON  = (-1753, 693)
SAVE_BUTTON  = (-1627, 694)
CANCEL_BUTTON = (-1765, 610) # reject the popup to refine the stat
CONFIRM_BUTTON  = (-1665, 610) # confirm the refining of the new stat

# Region of the popup text box: (left, top, right, bottom)
# Capture the area that shows the new rolled stat text

# refine button coords worked when using calibration but this was trial and error
POPUP_TEXT_REGION = (-1785, 690, -1470, 750)
POPUP_PIXEL_POS = (-1700, 562)        # position of pixel to watch
POPUP_PIXEL_COLOUR = (17, 15, 13)  # colour when popup IS visible
POPUP_COLOUR_TOLERANCE = 15           # how close the colour needs to be (handles antialiasing)

# TRIAL AND ERROR
# The 4 stat rows — each is the region containing the stat text for that row
# (left, top, right, bottom)
CURRENT_STAT_ROW_REGIONS = [
    (-1712, 666, -1600, 685),  # row 1
    (-1712, 695, -1600, 715),  # row 2
    (-1712, 725, -1600, 745),  # row 3
    (-1712, 755, -1600, 775),  # row 4
]

# Region for each of the 4 stat rows — for colour checking
# These should cover the stat text including its colour
REFINED_STAT_ROW_REGIONS = [
    (-1532, 666, -1420, 685),  # row 1
    (-1532, 695, -1420, 715),  # row 2
    (-1532, 725, -1420, 745),  # row 3
    (-1532, 755, -1420, 775),  # row 4
]
# TRIAL AND ERROR
# Lock button X position (they're all at the same X, only Y changes per row)
# Set this to the X coordinate of any lock button
LOCK_BUTTON_X = -1790

# CLICK coordinates for each lock button, FROM CALIBRATION
LOCK_BUTTON_POSITIONS = [
    (LOCK_BUTTON_X, 515),  # lock 1
    (LOCK_BUTTON_X, 538),  # lock 2
    (LOCK_BUTTON_X, 552),  # lock 3
    (LOCK_BUTTON_X, 576),  # lock 4
]


# How close each channel needs to be to the target orange
ORANGE_R_TOLERANCE = 20
ORANGE_G_TOLERANCE = 20
ORANGE_B_TOLERANCE = 20

ORANGE_STAT_COLOUR = (205, 72, 7)  # true orange


#GAME BORDERS
TOP_LEFT_BORDER = (-1900,275)
BOTTOM_RIGHT_BORDER = (-1355,1220)

# Purely for visualisation to match game to correct place
# Found these by trial and error using the visualisation mode.
REFINE_BUTTON_VISUAL_ONLY   = (-1650, 945) # Y increase is down
SAVE_BUTTON_VISUAL_ONLY  = (-1475, 945)
CANCEL_BUTTON_VISUAL_ONLY  = (-1700, 825) # X increase is right
CONFIRM_BUTTON_VISUAL_ONLY   = (-1550, 825)
POPUP_PIXEL_POS_VISUAL_ONLY = (-1600, 750)
LOCK_BUTTON_X_VISUAL_ONLY = -1722


LOCK_BUTTON_POSITIONS_VISUAL_ONLY = [
    (-1725, 675),  # lock 1
    (-1725, 705),  # lock 2
    (-1725, 735),  # lock 3
    (-1725, 765),  # lock 4
]


# ─────────────────────────────────────────────
# STAT PREFERENCES — Edit these
# ─────────────────────────────────────────────

# Stats you WANT to keep — script will confirm if ANY of these appear.
# Use lowercase partial strings; the OCR text will be matched against each.
DESIRED_STATS = [ 
    "all skills",
    "luck"
]

DESIRED_STATS_AFTER_LOCK = [
    "poisoning",
    "summoning",
    "qi of infinity",
    "soul amulet",
    "healing"
]

DESIRED_STATS_NEEDED = 2
# ─────────────────────────────────────────────
# STONE BUDGET
# ─────────────────────────────────────────────

# Stop refining this gear after using this many stones - includes phase 2
MAX_STONES_PER_GEAR = 3500
ORANGE_BUFFER = 500
ALL_SKILLS_LIMIT = 1000 # stones used in search of all skills before reset

REFINE_DELAY = 1.0 # delay between refine click - match to game so refine stones usage is accurate
# Delay (seconds) between actions — increase if BlueStacks is slow 0.2 ia default
CLICK_DELAY       = 0.2

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

pyautogui.FAILSAFE = True   # move mouse to top-left corner to abort
pyautogui.PAUSE    = 0.1


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def clear_debug_files(directory, prefix=""):
    files = [f for f in os.listdir(directory) if f.startswith(prefix)]
    
    if not files:
        print(f"  No files found in '{directory}' with prefix '{prefix}'")
        return
    
    for f in files:
        os.remove(os.path.join(directory, f))
    
    print(f"  Deleted {len(files)} file(s) from '{directory}'")



def click(pos, delay=CLICK_DELAY):
    pyautogui.click(pos[0], pos[1])
    time.sleep(delay)

def get_refine_cost(locked_count):
    """Returns the stone cost for a refine based on how many stats are currently locked."""
    costs = {
        0: 4,   # no locks
        1: 8,   # 1 locked
        2: 16,  # 2 locked
        3: 32,  # 3 locked
    }
    return costs.get(locked_count, 4)  # default to base cost if unknown


def capture_region(region):
    # region is (left, top, right, bottom)
    print("region:" + str(region))
    left, top, right, bottom = region
    print("left,top,right,bottom:" + str(left)+","+ str(top)+","+ str(right)+","+ str(bottom))
    # Use ImageGrab with all_screens=True — handles negative coords on multi-monitor
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    return screenshot

from PIL import ImageEnhance, ImageFilter

def test_ocr_from_file(path):
    """Load a saved debug image and run OCR on it to test settings."""
    from PIL import ImageEnhance, ImageFilter
    
    img = Image.open(path)
    print(f"Loaded image: {path} | Size: {img.size}")
    
    # Apply same preprocessing as ocr_region
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(3.0)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)
    
    img.save("debug/test_ocr_preprocessed1.png")
    print("Saved preprocessed image to debug/test_ocr_preprocessed.png")
    
    text = pytesseract.image_to_string(img, config="--psm 6 --oem 3")
    text = clean_ocr_text(text)
    print(f"Raw OCR text : '{text}'")
    print(f"Lowercased   : '{text.lower()}'")
    
    print("\nEvaluating against your stat lists...")
    for a in DESIRED_STATS_AFTER_LOCK:
        print(a)

def clean_ocr_text(text):
    """Normalise common OCR errors before matching."""
    import re
    text = text.lower()
    text = re.sub(r'[\n\|]', ' ', text) # replaces /n and | with a space
    text = re.sub(r'\s+', ' ', text) # replaces more than 1 space with 1 space
    text = text.strip()
    return text

def ocr_region(region, debug=True):

    global capture_count

    img = capture_region(region)
    
    # Upscale more aggressively
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    
    # Convert to greyscale
    img = img.convert("L")
    
    # Boost contrast
    img = ImageEnhance.Contrast(img).enhance(3.0)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)  # twice helps
    
    os.makedirs("debug", exist_ok=True)
    img.save(f"debug/capture_{capture_count:04d}.png")
    print(f"  [DEBUG] Saved capture_{capture_count:04d}.png")
    capture_count += 1
    
    # PSm 7 = single line, better for short stat text
    text = pytesseract.image_to_string(img, config="--psm 6 --oem 3")
    text = clean_ocr_text(text)
    print(f"  [DEBUG] OCR raw text: '{text}'")
    return text.lower()



# new to be able to add to locked rows
def find_and_click_lock(target_stat):
    print(f"  Scanning rows to find '{target_stat}' and click its lock...")
    for i, region in enumerate(CURRENT_STAT_ROW_REGIONS):
        row_text = ocr_region(region)
        print(f"  Row {i+1}: '{row_text.strip()}'")
        if target_stat in row_text:
            lock_pos = lock(i)
            print(f"  Found '{target_stat}' in row {i+1} — clicked lock at {lock_pos}")
            return i  # ← return index instead of True
    print(f"  ✗ Could not find '{target_stat}' in any row")
    return None  # ← return None instead of False

def colours_match(c1, c2, tolerance=POPUP_COLOUR_TOLERANCE):
    """Check if two RGB colours are within tolerance of each other."""
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

# ----------------------------------------------------- ORANGE STATS ZONE ----------------------------------------------------------------

def lock(row_index):
    lock_pos = LOCK_BUTTON_POSITIONS[row_index]
    click(lock_pos)
    time.sleep(0.05)
    return lock_pos

def click_lock_for_row(row_index):
    lock_pos = lock(row_index)
    print(f"  Clicking lock for row {row_index+1} at {lock_pos}")


def unlock_all_rows(locked_rows):
    """Unlock all currently locked rows."""
    print("  Unlocking all locked rows...")
    for i in locked_rows:
        click_lock_for_row(i)
    # time.sleep(0.3)

def is_orange_pixel(pixel):
    r, g, b = pixel
    tr, tg, tb = ORANGE_STAT_COLOUR
    return (
        abs(r - tr) <= ORANGE_R_TOLERANCE and
        abs(g - tg) <= ORANGE_G_TOLERANCE and
        abs(b - tb) <= ORANGE_B_TOLERANCE
    )

def is_stat_orange(row_index, regions):
    region = regions[row_index]
    img = capture_region(region).convert("RGB")
    pixels = img.getdata()
    total_pixels = len(pixels)
    threshold = max(1, int(total_pixels * 0.01))
    orange_count = 0
    orange_pixels_idx = []

    for i, pixel in enumerate(pixels):
        if is_orange_pixel(pixel):
            orange_count += 1
            orange_pixels_idx.append(i)
            if orange_count >= threshold:
                break

    is_orange = orange_count >= threshold
    print(f"  Row {row_index+1} — orange pixels: {orange_count}/{total_pixels} "
          f"(threshold {threshold}) — {'ORANGE ✓' if is_orange else 'not orange ✗'}")

    if is_orange:
        os.makedirs("debug/orange", exist_ok=True)
        img.save(f"debug/orange/row_{row_index+1}_raw.png")
        debug_pixels = list(pixels)
        for i in orange_pixels_idx:
            debug_pixels[i] = (255, 0, 255)
        debug_img = img.copy()
        debug_img.putdata(debug_pixels)
        debug_img = debug_img.resize((debug_img.width * 6, debug_img.height * 6), Image.NEAREST)
        debug_img.save(f"debug/orange/row_{row_index+1}_matches_highlighted.png")
        print(f"  Saved debug images for row {row_index+1}")

    emergency_stop_check()
    return is_orange


def get_orange_rows(regions):
    """Return list of row indices that are currently orange."""
    return [i for i in range(4) if is_stat_orange(i, regions)]


def lock_orange_rows(regions):
    """Scan all rows, lock any that are orange. Returns list of locked row indices."""
    orange = get_orange_rows(regions)
    print(f"  Orange rows found: {[i+1 for i in orange]}")
    for i in orange:
        click_lock_for_row(i)
    return orange


def refine_for_orange(phase1_locked_rows,stones_used_phase1):
    print("\n=== PHASE 2: Refining for 3 orange stats ===")
    stones_used_phase2 = 0
    print(phase1_locked_rows)
    unlock_all_rows(phase1_locked_rows)
    locked_rows = list(lock_orange_rows(CURRENT_STAT_ROW_REGIONS))

    while len(locked_rows) < 3 and stones_used_phase2 < ORANGE_BUFFER:
        emergency_stop_check()

        print(f"\n[Phase 2 | Stone {stones_used_phase2 + get_refine_cost(len(locked_rows))}/{ORANGE_BUFFER}] "
              f"Locked orange: {len(locked_rows)}/3 — Clicking Refine...")
        click(REFINE_BUTTON)
        stones_used_phase2 += get_refine_cost(len(locked_rows))

        # Check if a popup appeared
        if wait_for_popup(timeout=0.001):
            print("  Popup detected — clicking cancel to check refined rows...")
            click(CANCEL_BUTTON)
            time.sleep(0.3)

            # Check refined rows for new orange stats
            new_orange = [i for i in get_orange_rows(REFINED_STAT_ROW_REGIONS) if i not in locked_rows]
            if new_orange:
                print(f"  New orange stats in rows: {[i+1 for i in new_orange]}")
                click(SAVE_BUTTON)
                time.sleep(0.3)
                for i in new_orange:
                    click_lock_for_row(i)
                    locked_rows.append(i)
                print(f"  Total locked: {len(locked_rows)}/3")
            else:
                # No new orange — reroll by clicking refine then confirm
                print("  No new orange stats — rerolling...")
                click(REFINE_BUTTON)
                time.sleep(0.01)
                click(CONFIRM_BUTTON)
                stones_used_phase2 += get_refine_cost(len(locked_rows))
        else:
            # No popup — check refined rows directly
            new_orange = [i for i in get_orange_rows(REFINED_STAT_ROW_REGIONS) if i not in locked_rows]
            if new_orange:
                print(f"  New orange stats in rows: {[i+1 for i in new_orange]}")
                click(SAVE_BUTTON)
                time.sleep(0.3)
                for i in new_orange:
                    click_lock_for_row(i)
                    locked_rows.append(i)
                print(f"  Total locked: {len(locked_rows)}/3")

    if len(locked_rows) >= 3:
        print(f"\n✅ Phase 2 complete — 3 orange stats locked! TOTAL REFINE STONES ON THIS GEAR = {stones_used_phase1+stones_used_phase2}")
    else:
        print(f"\n⚠ Ran out of stones in Phase 2 with {len(locked_rows)} orange stats locked.")

def popup_visible():
    """Check if popup is present by reading a specific pixel colour."""
    actual = pyautogui.pixel(POPUP_PIXEL_POS[0], POPUP_PIXEL_POS[1])
    visible = colours_match(actual, POPUP_PIXEL_COLOUR)
    print(f"  [DEBUG] Popup pixel colour: {actual} — {'POPUP DETECTED' if visible else 'no popup'}")
    return visible

def wait_for_popup(timeout=0.05):
    """
    Block until the popup pixel appears or timeout is reached.
    Returns True if popup appeared, False if timed out.
    """
    print("timeout: "+str(timeout))
    time.sleep(timeout)
    if popup_visible():
        return True
    return False

import threading

# Global stop flag
stop_flag = False

def listen_for_stop():
    keyboard.wait("f9")
    global stop_flag
    stop_flag = True
    print("\n🛑 F9 pressed — stopping after current action...")

# Start the listener in a background thread
stop_thread = threading.Thread(target=listen_for_stop, daemon=True)
stop_thread.start()


def emergency_stop_check():
    if stop_flag:
        print("🛑 Stopped.")
        sys.exit(0)


# ─────────────────────────────────────────────
# CALIBRATION MODE
# ─────────────────────────────────────────────

def calibration_mode():
    print("=== CALIBRATION MODE ===")
    print("Move your mouse to the positions below and wait 3 seconds each.")
    print("The coordinates will be printed so you can paste them above.\n")

    positions = [
        "REFINE button",
        "SAVE button",
        "CONFIRM / Accept button (popup)",
        "CANCEL / Revert button (popup)",
        "TOP-LEFT of popup text area",
        "BOTTOM-RIGHT of popup text area",
        "TOP-LEFT of stat ROW 1 text",
        "BOTTOM-RIGHT of stat ROW 1 text",
        "TOP-LEFT of stat ROW 2 text",
        "BOTTOM-RIGHT of stat ROW 2 text",
        "TOP-LEFT of stat ROW 3 text",
        "BOTTOM-RIGHT of stat ROW 3 text",
        "TOP-LEFT of stat ROW 4 text",
        "BOTTOM-RIGHT of stat ROW 4 text",
        "LOCK button (any one of them — X coordinate is all we need)",
    ]

    results = {}
    for label in positions:
        print(f"Hover over: {label}")
        time.sleep(3)
        pos = pyautogui.position()
        results[label] = pos
        print(f"  → {pos}\n")

    # Pretty print ready to paste
    r = results
    print("\n=== PASTE THIS INTO YOUR SCRIPT ===\n")
    print(f"REFINE_BUTTON  = {r['REFINE button']}")
    print(f"CONFIRM_BUTTON = {r['CONFIRM / Accept button (popup)']}")
    print(f"CANCEL_BUTTON  = {r['CANCEL / Revert button (popup)']}")
    print(f"POPUP_TEXT_REGION = ({r['TOP-LEFT of popup text area'][0]}, {r['TOP-LEFT of popup text area'][1]}, {r['BOTTOM-RIGHT of popup text area'][0]}, {r['BOTTOM-RIGHT of popup text area'][1]})")
    print(f"STAT_ROW_REGIONS = [")
    for i in range(1, 5):
        tl = r[f'TOP-LEFT of stat ROW {i} text']
        br = r[f'BOTTOM-RIGHT of stat ROW {i} text']
        print(f"    ({tl[0]}, {tl[1]}, {br[0]}, {br[1]}),  # row {i}")
    print(f"]")
    print(f"LOCK_BUTTON_X = {r['LOCK button (any one of them — X coordinate is all we need)'][0]}")

def visualise_coordinates():
    print("=== VISUALISE COORDINATES ===")

    from PIL import ImageDraw

    # Grab just the secondary monitor
    SECONDARY_LEFT   = -1920
    SECONDARY_TOP    = 275   # increase is up more
    SECONDARY_RIGHT  = 0
    SECONDARY_BOTTOM = 1225    # increase is down more

    screenshot = ImageGrab.grab(
        bbox=(SECONDARY_LEFT, SECONDARY_TOP, SECONDARY_RIGHT, SECONDARY_BOTTOM),
        all_screens=True
    )

    draw = ImageDraw.Draw(screenshot)

    def to_img(x, y):
        return (x - SECONDARY_LEFT, y - SECONDARY_TOP)

    def draw_marker(pos, label, colour):
        ix, iy = to_img(pos[0], pos[1])
        r = 10
        draw.ellipse((ix-r, iy-r, ix+r, iy+r), outline=colour, width=3)
        draw.line((ix-r, iy, ix+r, iy), fill=colour, width=2)
        draw.line((ix, iy-r, ix, iy+r), fill=colour, width=2)
        draw.text((ix+r+4, iy-10), label, fill=colour)

    def draw_region(region, label, colour):
        left, top, right, bottom = region
        il, it = to_img(left, top)
        ir, ib = to_img(right, bottom)
        draw.rectangle((il, it, ir, ib), outline=colour, width=3)
        draw.text((il, it-16), label, fill=colour)

    
    def draw_game_border():
        il, it = to_img(TOP_LEFT_BORDER[0], TOP_LEFT_BORDER[1])
        ir, ib = to_img(BOTTOM_RIGHT_BORDER[0], BOTTOM_RIGHT_BORDER[1])
        draw.rectangle((il, it, ir, ib), outline=(255, 165, 0), width=3)
        draw.text((il, it - 14), "GAME BORDER", fill=(255, 165, 0))

    draw_marker(REFINE_BUTTON_VISUAL_ONLY,   "REFINE",    (255, 80,  80))
    draw_marker(SAVE_BUTTON_VISUAL_ONLY, "SAVE", (255,0,0))
    draw_marker(CANCEL_BUTTON_VISUAL_ONLY,  "CANCEL",   (80,  255, 80))
    draw_marker(CONFIRM_BUTTON_VISUAL_ONLY,   "CONFIRM",    (80,  180, 255))
    draw_marker(POPUP_PIXEL_POS_VISUAL_ONLY, "PIX CHECK", (255, 255, 0))
    draw_region(POPUP_TEXT_REGION,"OCR REGION",(255, 140, 0))

    for i, pos in enumerate(LOCK_BUTTON_POSITIONS_VISUAL_ONLY):
        draw_marker(pos, f"LOCK {i+1}", (255, 165, 0))

    # Stat rows
    row_colours = [
        (200, 100, 255),
        (100, 255, 200),
        (255, 100, 150),
        (150, 200, 255),
    ]

    for i, row in enumerate(CURRENT_STAT_ROW_REGIONS):
        draw_region(row, f"ROW {i+1}", row_colours[i])
    
    for i, row in enumerate(REFINED_STAT_ROW_REGIONS):
        draw_region(row, f"ROW {i+1}", row_colours[i])


    draw_game_border()

    os.makedirs("debug", exist_ok=True)
    screenshot.save("debug/coordinate_visualisation.png")
    print("Saved to debug/coordinate_visualisation.png")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
#  TODO successful refining moves the click point for selecting the next gear, make sure after 6 moves it goes down instead then goes left 6 time etc in a snake
#  TODO deal with errors that will arise with incorrect lvl gear
#  TODO add luck maybe read gear type or dont

def evaluate_stat(text, stat_list, locked_all_skills=False):
    """
    Check if any desired stats appear in the text.
    Returns list of matched stats (empty if none found).
    """
    matched = []
    for good in stat_list:
        if good in text:
            print(f"  ✓ Found (contains '{good}'): {text.strip()}")
            matched.append(good)
    if not matched:
        print(f"  ? Unknown stat, rejecting: {text.strip()}")
    return matched


def refine_loop():
    stones_used = 0
    locked_all_skills = False
    locked_desired_count = 0
    locked_rows = []
    phase1_success = False
    lock_not_found = False

    looking_for_max_win = False

    print("=== Gear Refine Bot Starting ===")
    print(f"Max stones per gear : {MAX_STONES_PER_GEAR}")
    print(f"Refine stone cost   : {get_refine_cost(len(locked_rows))}")
    print(f"Desired stats       : {DESIRED_STATS}")
    print("Press F9 at any time to stop.\n")

    while stones_used < MAX_STONES_PER_GEAR - ORANGE_BUFFER:
        emergency_stop_check()

        if stones_used > ALL_SKILLS_LIMIT and not locked_all_skills:
            print(f"All skills not found after {ALL_SKILLS_LIMIT}, moving to phase 2")
            break

        print(f"[Stone {stones_used + get_refine_cost(len(locked_rows))}/{MAX_STONES_PER_GEAR}] Clicking Refine...")
        click(REFINE_BUTTON,delay=REFINE_DELAY)
        emergency_stop_check()

        if not wait_for_popup(timeout=0.001):
            print("  No popup appeared, continuing...")
            stones_used += get_refine_cost(len(locked_rows))
            continue

        # Popup detected — cancel it so we can read the refined stat rows
        click(CANCEL_BUTTON)
        time.sleep(0.2)

        # ── Scan refined stat rows ──
        if not locked_all_skills:
            # Look for all skills in refined rows
            for i, region in enumerate(REFINED_STAT_ROW_REGIONS):
                row_text = ocr_region(region)
                print(f"  Refined row {i+1}: '{row_text.strip()}'")
                if evaluate_stat(row_text, DESIRED_STATS):
                    click(SAVE_BUTTON)  # save first so all skills moves to current stat rows
                    time.sleep(0.3)     # wait for save
                    found = find_and_click_lock("all skills")
                    if found is not None:
                        locked_rows.append(found)
                        locked_all_skills = True
                        looking_for_max_win = True
                        print("  → All skills locked!")
                        break
                    else:
                        lock_not_found = True
                        print("  ⚠ Lock not found — stopping")
                        break

            if lock_not_found:
                break

            if not locked_all_skills:
                # Checkeed if All skills was hidden behind another rare stat popup but wasnt
                print("  All skills not found in refined rows, rerolling...")
                click(REFINE_BUTTON) # make popup reappear
                click(CONFIRM_BUTTON) # reroll from popup window
                continue

        if locked_all_skills:
            stat_row_region = []
            
            if looking_for_max_win: #save would have been clicked so need to check current rows, otherwise check refined rows
                stat_row_region = CURRENT_STAT_ROW_REGIONS
                looking_for_max_win = False
            else:
                stat_row_region = REFINED_STAT_ROW_REGIONS

            # Scan rows for desired after-lock stats
            any_after_lock_found = False
            for i, region in enumerate(stat_row_region):
                if i in locked_rows:
                    continue
                row_text = ocr_region(region)
                matched_after = evaluate_stat(row_text, DESIRED_STATS_AFTER_LOCK)
                if matched_after:
                    click(SAVE_BUTTON)
                    found = find_and_click_lock(matched_after[0])
                    if found is not None:
                        locked_rows.append(found)
                        locked_desired_count += 1
                        any_after_lock_found = True
                        print(f"  → Row {i+1} '{matched_after}' locked! --------------------------------------------------------------------------- MAX WIN ----------------------------------------------------------------------------------------------")
            # wrong place or something
            if not any_after_lock_found:
                # No desired stats found — bad rare stat, reroll
                print("  No desired after-lock stats found — rerolling...")
                click(REFINE_BUTTON)
                time.sleep(0.3)
                click(CONFIRM_BUTTON)
                stones_used += get_refine_cost(len(locked_rows))
            if locked_desired_count >= DESIRED_STATS_NEEDED:
                phase1_success = True
                print(f"  → Phase 1 complete! All skills + {locked_desired_count} desired stat(s)!")
                break

        stones_used += get_refine_cost(len(locked_rows))
        # time.sleep(CLICK_DELAY)

    if not phase1_success and not lock_not_found:
        print("\n⚠ Phase 1 incomplete — going to Phase 2 for 3 orange stats")
        refine_for_orange(locked_rows,stones_used)

    print(f"\n✅ Used {stones_used} stones. Time to recycle and start over!")



# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # # image test
    # i=1
    # for r in STAT_ROW_REGIONS:
    #     img = ImageGrab.grab(bbox=(r), all_screens=True)
    #     img.save(f"debug/multimon_test{i}.png")
    #     print("Saved — check debug/multimon_test.png")
    #     i+=1
    # img = ImageGrab.grab(bbox=(POPUP_TEXT_REGION), all_screens=True)
    # img.save(f"debug/multimon_test0.png")
    # print("Saved — check debug/multimon_test.png")

    # # popup pixel colour
    # import pyautogui, time
    # print("Waiting 3s — move mouse to a pixel that CHANGES when popup appears...")
    # time.sleep(3)
    # x, y = pyautogui.position()
    # print(f"Position: ({x}, {y})")
    # # Check colour at rest
    # print(f"Colour now: {pyautogui.pixel(x, y)}")
    # input("Now trigger the popup in BlueStacks, then press Enter...")
    # print(f"Colour with popup: {pyautogui.pixel(x, y)}")

    clear_debug_files("debug/orange")

    clear_debug_files("debug", prefix="capture_")

    if TEST_OCR_MODE:
        test_ocr_from_file(TEST_OCR_IMAGE)
    elif CALIBRATION_MODE:
        calibration_mode()
    elif VISUALISATION_MODE:
        visualise_coordinates()
    else:
        refine_loop()
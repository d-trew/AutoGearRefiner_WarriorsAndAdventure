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
import re

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

# From Calibration and visualisation mode
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

# REFINE_STONES_USED_REGION =  (-1477, 1005, -1430, 1030)
# REFINE_STONES_LEFT_REGION = (-1560, 850, -1512, 870)

REFINE_STONES_USED_REGION =  (-1700, 1005, -1430, 1030)
REFINE_STONES_LEFT_REGION = (-1650, 850, -1480, 870)

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
# INVENTORY NAVIGATION
# ─────────────────────────────────────────────

# Drag scroll in inventory — drag from bottom to top to scroll down
#  OLD
# INVENTORY_SCROLL_START = (-1731, 768)  # calibrate
# INVENTORY_SCROLL_END   =(-1730, 718)  # calibrate 1st
# INVENTORY_SCROLL_END   =(-1730, 465)  # calibrate 8th row
# INVENTORY_SCROLL_END   =(-1730, 415)  # calibrate 9th
# INVENTORY_SCROLL_END   =(-1730, 365)  # calibrate 10th

#  NEW
INVENTORY_SCROLL_START = (-1727, 779)
INVENTORY_SCROLL_END = (-1727, 293)
INVENTORY_SCROLL_MAX_SINGLE = 10 # based on inv scroll but need to figure out how it works

# INVENTORY_SCROLL_START = (-1731, 768)  # calibrate goes to 8th row
# INVENTORY_SCROLL_END   =(-1730, 465)  # calibrate

# --------------- gear detail view ---------
# RING_RECYCLE_BUTTON = (-1600, 620)  # calibrate
RING_REFINE_BUTTON = (-1600, 640) # calibrate
# LOCK_UNLOCK_BUTTON = (-1600,680) # calibrate

BOOTS_REFINE_BUTTON =(-1600, 652)
BELT_REFINE_BUTTON = (-1600, 700)
BRACER_REFINE_BUTTON =(-1600,635)
# BRACER_2_REFINE_BUTTON = (-1700, 850) # gold bracelet when on top row of inv has a different refine button - skipping might just be better tbh
NECKLACE_REFINE_BUTTON =(-1600,648)
ARMOR_REFINE_BUTTON =(-1600,651)
HELMET_REFINE_BUTTON =(-1600,648)
WEAPON_REFINE_BUTTON =(-1600,642)

GOLD_BRACER_REFINE_BUTTON = (-1602, 702)
GOLD_BRACER_REGION = (-1700, 450, -1570, 480)
# -----------------------------


GEAR_NAME_REGION = (-1650, 520, -1500, 700)

POPUP_DISMISS_BUTTON = (-1901, 704)

GEAR_NAME_KEYWORDS = {
    "boot": BOOTS_REFINE_BUTTON, 
    "ring": RING_REFINE_BUTTON,
    "belt": BELT_REFINE_BUTTON,
    "bracer":BRACER_REFINE_BUTTON,
    # "necklace":NECKLACE_REFINE_BUTTON,
    "armor":ARMOR_REFINE_BUTTON,
    "helmet":HELMET_REFINE_BUTTON,
    # "weapon":WEAPON_REFINE_BUTTON,
}


# First gear slot position in inventory
# GEAR_SLOT_START = (-1871, 667) # calibrate old ROW 2/4
GEAR_SLOT_START = (-1873, 628) # new row 1/4

# Grid layout of gear slots
GEAR_SLOT_COLS = 7
GEAR_SLOT_WIDTH = 50   # pixels between columns — calibrate
GEAR_SLOT_HEIGHT = 50  # pixels between rows — calibrate




# Back button to exit refine
BACK_BUTTON = (-1891, 844) # calibrate
# pack button to open inventory
PACK_BUTTON =  (-1850, 844)


# Region that shows lock status text — read to check if gear is locked before recycling
GEAR_LOCK_STATUS_REGION = (-1470, 910, -1405, 940)  # T&R

# Text that appears when gear IS locked — if this appears do not recycle
GEAR_LOCKED_TEXT = "unlock"

# How many items to process before scrolling again
# ITEMS_PER_SCROLL = 7

# Number of gear items to process in one session
MAX_GEAR_ITEMS = 20
# ─────────────────────────────────────────────
# STAT PREFERENCES
# ─────────────────────────────────────────────
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
MAX_STONES_PER_GEAR = 4000
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

def ocr_region(region, debug=False):

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

    if debug == True:
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

    global capture_count

    print(f"  Scanning rows to find '{target_stat}' and click its lock...")

    for i, region in enumerate(CURRENT_STAT_ROW_REGIONS):
        row_text = ocr_region(region)
        print(f"  Row {i+1}: '{row_text.strip()}'")
        if target_stat in row_text:
            lock_pos = lock(i)
            print(f"  Found '{target_stat}' in row {i+1} — clicked lock at {lock_pos}")
            os.makedirs("debug", exist_ok=True)
            img = capture_region(region)
            img.save(f"debug/capture_{capture_count:04d}.png")
            print(f"  [DEBUG] Saved capture_{capture_count:04d}.png")
            capture_count += 1
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

# TODO IF NO REFINE BUT GOES TO PHASE 2 - CURRENT GEAR CAN BE RECYCLED AAS THIS WAS PREVIOUSLY REFINED AND LOCATION IS KNOWN
def refine_for_orange(phase1_locked_rows,stones_used_phase1):
    print("\n=== PHASE 2: Refining for 3 orange stats ===")
    stones_used_phase2 = 0
    click(SAVE_BUTTON) # if have 3 orange already there will still be refined stats that will require a popup to remove - this is to prevent popup
    time.sleep(0.5)
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
                time.sleep(0.5)
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


# ------------------------------------------------------ INVENTORY NAVIGATION ZONE ---------------------------------------------------------------


# def scroll_inventory():
#     """Drag scroll the inventory to reveal more items."""
#     print("  Scrolling inventory...")
#     pyautogui.mouseDown(INVENTORY_SCROLL_START[0], INVENTORY_SCROLL_START[1])
#     time.sleep(0.1)
#     pyautogui.moveTo(INVENTORY_SCROLL_END[0], INVENTORY_SCROLL_END[1], duration=0.5)
#     time.sleep(0.1)
#     pyautogui.mouseUp()
#     time.sleep(0.3)

def scroll_inventory(target_row=None):
    """
    Drag scroll the inventory.
    target_row: if specified, scrolls to that row number. Otherwise performs a single default scroll.
    """
    print(f"  Scrolling inventory{f' to row {target_row}' if target_row else ''}...")

    if target_row is None:
        # Default behaviour — single scroll to max
        pyautogui.mouseDown(INVENTORY_SCROLL_START[0], INVENTORY_SCROLL_START[1])
        time.sleep(0.1)
        pyautogui.moveTo(INVENTORY_SCROLL_END[0], INVENTORY_SCROLL_END[1], duration=0.5)
        time.sleep(0.1)
        pyautogui.mouseUp()
        time.sleep(0.3)
    elif target_row <= INVENTORY_SCROLL_MAX_SINGLE:
        end_y = INVENTORY_SCROLL_END[1]
        start_y = INVENTORY_SCROLL_START[1]
        # 50 seems to be the scroll difference per row even  (scroll start - scroll end) / how many rows that moves
        # taking away from start_y means the mouse end point lowers - moving less distance (backwards as on second monitor)
        scroll_end_y = int(start_y - ((target_row) * 50)) 
        pyautogui.mouseDown(INVENTORY_SCROLL_START[0], INVENTORY_SCROLL_START[1])
        time.sleep(0.1)
        pyautogui.moveTo(INVENTORY_SCROLL_END[0], scroll_end_y, duration=0.5)
        time.sleep(0.1)
        pyautogui.mouseUp()
        time.sleep(0.3)
    else:
        # Multiple scrolls needed
        scrolls_needed = target_row // INVENTORY_SCROLL_MAX_SINGLE
        remainder = target_row % INVENTORY_SCROLL_MAX_SINGLE
        print(f"  Requires {scrolls_needed} full scroll(s) + remainder {remainder}")
        for s in range(scrolls_needed):
            print(f"  Full scroll {s+1}/{scrolls_needed}...")
            pyautogui.mouseDown(INVENTORY_SCROLL_START[0], INVENTORY_SCROLL_START[1])
            time.sleep(0.1)
            pyautogui.moveTo(INVENTORY_SCROLL_END[0], INVENTORY_SCROLL_END[1], duration=0.5)
            time.sleep(0.1)
            pyautogui.mouseUp()
            time.sleep(0.3)
        if remainder > 0:
            scroll_inventory(remainder)

def get_gear_slot_pos(slot_index):
    """
    Calculate screen position of a gear slot by index.
    Slots are numbered left to right, top to bottom.
    slot_index 0 = first item, 1 = second item, etc.
    """
    col = slot_index % GEAR_SLOT_COLS
    row = slot_index // GEAR_SLOT_COLS
    x = GEAR_SLOT_START[0] + col * GEAR_SLOT_WIDTH
    y = GEAR_SLOT_START[1] + row * GEAR_SLOT_HEIGHT
    return (x, y)


def select_gear(slot_index):
    """Click on a gear item in the inventory."""
    pos = get_gear_slot_pos(slot_index)
    print(f"  Selecting gear at slot {slot_index} → {pos}")
    click(pos)
    time.sleep(0.3)


def is_gear_locked():
    """Read the lock status region to check if gear is locked before recycling."""
    text = ocr_region(GEAR_LOCK_STATUS_REGION)
    locked = GEAR_LOCKED_TEXT in text
    print(f"  Gear lock status: '{text.strip()}' — {'LOCKED' if locked else 'not locked'}")
    return locked

def get_refine_button_for_gear(gear_name):
    """Return the correct refine button position based on gear name."""
    for keyword, button_pos in GEAR_NAME_KEYWORDS.items():
        if keyword in gear_name.lower():
            print(f"  Detected gear type '{keyword}' — using alternate refine button")
            if keyword == "bracer" and ocr_region(GOLD_BRACER_REGION) == "gold bracelet":
                return GOLD_BRACER_REFINE_BUTTON
            else:
                return button_pos
    return None

# def recycle_gear():
#     """
#     Recycle the current gear item.
#     Checks it is not locked before recycling.
#     Returns True if recycled, False if locked (skipped).
#     """
#     print("  Attempting to recycle gear...")
#     if is_gear_locked():
#         click(LOCK_UNLOCK_BUTTON)

#     click(RECYCLE_BUTTON)
#     time.sleep(0.3)
#     print("  ✓ Gear recycled")
#     return True


def go_back_to_inventory():
    """Click back button to return to inventory view."""
    print("  Going back to inventory...")
    click(BACK_BUTTON)
    click(PACK_BUTTON)
    time.sleep(0.5)



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
    print("Move your mouse to the positions below and wait 3 seconds each.\n")

    positions = [
        # Inventory navigation
        # "INVENTORY SCROLL start (bottom of drag)",
        # "INVENTORY SCROLL end (top of drag)",
        # "GEAR SLOT 1 (first item in inventory)",
        # "GEAR REFINE button (in gear detail view)",
# LOCK_UNLOCK_BUTTON = (-1600,680) # calibrate
        "BOOTS_REFINE_BUTTON",
        "BELT_REFINE_BUTTON",
        "BRACER_REFINE_BUTTON",
        "NECKLACE_REFINE_BUTTON",
        "ARMOR_REFINE_BUTTON",
        "HELMET_REFINE_BUTTON", 
        "WEAPON_REFINE_BUTTON"
        # "BACK button (return to inventory)",
        # "RECYCLE button (in gear detail view)",
        # "TOP-LEFT of gear lock status text area",
        # "BOTTOM-RIGHT of gear lock status text area",
    ]

    results = {}
    for label in positions:
        print(f"Hover over: {label}")
        time.sleep(10)
        pos = pyautogui.position()
        results[label] = pos
        print(f"  → {pos}\n")

    r = results

    # Inventory navigation
    # print(f"INVENTORY_SCROLL_START = {r['INVENTORY SCROLL start (bottom of drag)']}")
    # print(f"INVENTORY_SCROLL_END   = {r['INVENTORY SCROLL end (top of drag)']}")
    # print(f"GEAR_SLOT_START        = {r['GEAR SLOT 1 (first item in inventory)']}")
    # print(f"GEAR_REFINE_BUTTON     = {r['GEAR REFINE button (in gear detail view)']}")
    print(f"BOOTS_REFINE_BUTTON     = {r['BOOTS_REFINE_BUTTON']}")
    print(f"BELT_REFINE_BUTTON     = {r['BELT_REFINE_BUTTON']}")
    print(f"BRACER_REFINE_BUTTON     = {r['BRACER_REFINE_BUTTON']}")
    print(f"NECKLACE_REFINE_BUTTON     = {r['NECKLACE_REFINE_BUTTON']}")
    print(f"ARMOR_REFINE_BUTTON     = {r['ARMOR_REFINE_BUTTON']}")
    print(f"HELMET_REFINE_BUTTON     = {r['HELMET_REFINE_BUTTON']}")
    print(f"WEAPON_REFINE_BUTTON     = {r['WEAPON_REFINE_BUTTON']}")


    # print(f"BACK_BUTTON            = {r['BACK button (return to inventory)']}")
    # print(f"RECYCLE_BUTTON         = {r['RECYCLE button (in gear detail view)']}")

    # tl = r['TOP-LEFT of gear lock status text area']
    # br = r['BOTTOM-RIGHT of gear lock status text area']
    # print(f"GEAR_LOCK_STATUS_REGION = ({tl[0]}, {tl[1]}, {br[0]}, {br[1]})")

def visualise_coordinates():
    print("=== VISUALISE COORDINATES ===")
    from PIL import ImageDraw

    SECONDARY_LEFT   = -1920
    SECONDARY_TOP    = 275
    SECONDARY_RIGHT  = 0
    SECONDARY_BOTTOM = 1225

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

    # ── Refine view ──
    draw_marker(REFINE_BUTTON_VISUAL_ONLY,   "REFINE",     (255, 80,  80))
    draw_marker(SAVE_BUTTON_VISUAL_ONLY,     "SAVE",       (255, 0,   0))
    draw_marker(CANCEL_BUTTON_VISUAL_ONLY,   "CANCEL",     (80,  255, 80))
    draw_marker(CONFIRM_BUTTON_VISUAL_ONLY,  "CONFIRM",    (80,  180, 255))
    draw_marker(POPUP_PIXEL_POS_VISUAL_ONLY, "PIX CHECK",  (255, 255, 0))
    draw_region(POPUP_TEXT_REGION,           "OCR REGION", (255, 140, 0))

    # ── Lock buttons ──
    for i, pos in enumerate(LOCK_BUTTON_POSITIONS_VISUAL_ONLY):
        draw_marker(pos, f"LOCK {i+1}", (255, 165, 0))

    # ── Stat rows ──
    row_colours = [
        (200, 100, 255),
        (100, 255, 200),
        (255, 100, 150),
        (150, 200, 255),
    ]
    for i, row in enumerate(CURRENT_STAT_ROW_REGIONS):
        draw_region(row, f"CUR ROW {i+1}", row_colours[i])

    for i, row in enumerate(REFINED_STAT_ROW_REGIONS):
        draw_region(row, f"REF ROW {i+1}", row_colours[i])

    draw_region(GOLD_BRACER_REGION, "GOLD BRACER NAME",  (100, 200, 100))
    # draw_region(REFINE_STONES_LEFT_REGION, "REFINE STONES",  (100, 200, 100))
    # draw_region(REFINE_STONES_USED_REGION, "REFINE STONES",  (100, 200, 100))
    # draw_region(GEAR_NAME_REGION, "GEAR NAME",  (100, 200, 100))
    # ── Inventory navigation ──
    # draw_region(GEAR_LOCK_STATUS_REGION, "LOCK STATUS",  (100, 200, 100))

    draw_game_border()

    os.makedirs("debug", exist_ok=True)
    screenshot.save("debug/coordinate_visualisation.png")
    print("Saved to debug/coordinate_visualisation.png")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
# TODO deal with errors that will arise with incorrect lvl gear
# TODO add luck maybe read gear type or dont

def run_automation(starting_row=INVENTORY_SCROLL_MAX_SINGLE):
    """
    Master loop — iterates through gear items, refines each one,
    recycles if needed, and moves to the next.
    """
    print("=== AUTOMATION STARTING ===")
    print(f"Processing up to {MAX_GEAR_ITEMS} gear items")
    
    scroll_inventory(starting_row)


    current_slot = 0
    items_processed = 0

    while items_processed < MAX_GEAR_ITEMS and current_slot<=20: # after 20 slots is a new page of inventory, which would need to scroll further but 20 items checked is already good enough
        emergency_stop_check()

        print(f"\n{'='*60}")
        print(f"GEAR ITEM {items_processed + 1}/{MAX_GEAR_ITEMS} — slot {current_slot}")
        print(f"{'='*60}")

        # Select the gear item
        select_gear(current_slot)
        time.sleep(0.3)
        # Click the refine button to enter refine view
        # TODO MISSES FOR BOOTS - rwead gear name then use different click position, if no gear found click in a specific area to remove popup and move to next item

        # Read gear name to determine correct refine button position
        gear_name = ocr_region(GEAR_NAME_REGION, debug=True)
        print(f"  Gear name: '{gear_name.strip()}'")

        if not gear_name.strip():
            print("  No gear found in slot — dismissing any popup and moving to next slot...")
            click(POPUP_DISMISS_BUTTON)
            time.sleep(0.3)
            current_slot += 1
            continue

        # Get correct refine button for this gear type
        refine_button = get_refine_button_for_gear(gear_name)
        if refine_button is None:
            click(POPUP_DISMISS_BUTTON)
            time.sleep(0.3)
            current_slot += 1
            continue
        print("  Opening refine view...")
        click(refine_button)
        time.sleep(2) # refine stones need to load


        # Read refine stone counts
        # try:
        #     refine_stones_left = int(re.sub(r'[^0-9]', '',ocr_region(REFINE_STONES_LEFT_REGION,debug=True)))
        # except ValueError: # also catches when refine button was missed for whtever reason - weird gear item
        #     print("  ⚠ Could not read refine stones left — dismissing and skipping")
        #     click(POPUP_DISMISS_BUTTON)
        #     time.sleep(0.3)
        #     current_slot += 1
        #     continue

        # try:
        #     refine_stone_region_result = ocr_region(REFINE_STONES_USED_REGION,debug=True)
        #     refine_stones_used_before_refine = int(re.sub(r'[^0-9]', '',refine_stone_region_result))
        # except ValueError:
        #     print("  ⚠ Could not read refine stones used — defaulting to 0")
        #     refine_stones_used_before_refine = 0

        try:
            raw = ocr_region(REFINE_STONES_LEFT_REGION, debug=True)
            refine_stones_left = extract_first_number_after_colon(raw)
            if refine_stones_left is None:
                raise ValueError(f"No number found in: '{raw}'")
            print(f"  Refine stones left: {refine_stones_left}")
        except ValueError as e:
            # print("Trying alternate refine button") CBA
            print(f"  ⚠ Could not read refine stones left ({e}) — skipping")
            click(POPUP_DISMISS_BUTTON)
            time.sleep(0.3)
            current_slot += 1
            continue

        try:
            raw = ocr_region(REFINE_STONES_USED_REGION, debug=True)
            refine_stones_used_before_refine = extract_first_number_after_colon(raw) or 0
            print(f"  Refine stones used on item: {refine_stones_used_before_refine}")
        except ValueError:
            print("  ⚠ Could not read refine stones used — defaulting to 0")
            refine_stones_used_before_refine = 0

        if refine_stones_left > MAX_STONES_PER_GEAR: # refine_stones_used_before_refine == 0 and
            # Run the refine loop — returns whether phase 2 was needed
            #  TODO give refine loop refine stones used before result and start the refine stones from there and check current stats before starting
            refine_loop(refine_stones_used_before_refine)
            items_processed += 1
            print(f"\n  ✓ Gear {items_processed} refined successfully — keeping")
        else:
            print(f"\n  Not enough refine stones")
            break
        go_back_to_inventory()
        time.sleep(0.3)
        scroll_inventory(starting_row)
        current_slot += 1
        # INVENTORY ORDER BASED OFF ITEM CP SO ITEMS MOVE AFTER REFINE
        # if not successful_refine:
        #     # Phase 2 was run — gear needs recycling
        #     print(f"\n  Gear {items_processed + 1} needs recycling (phase 2 ran)")
        #     go_back_to_inventory()
        #     time.sleep(0.3)
        #     scroll_inventory()
        #     select_gear(current_slot)  # reselect same slot to get recycle option
        #     recycled = recycle_gear()

        #     if recycled:
        #         print(f"  Gear recycled — next gear will appear in same slot")
        #         # Stay on same slot index — new gear will be in same position
        #         # No need to increment current_slot
        #     else:
        #         print(f"  ⚠ Could not recycle — moving to next slot anyway")
        #         current_slot += 1
        # else:
        #     # Phase 1 success — keep gear, move to next slot
        #     print(f"\n  ✓ Gear {items_processed + 1} refined successfully — keeping")
        #     go_back_to_inventory()
        #     current_slot += 1



        # TODO
        # Scroll inventory every N items to reveal new gear
        # if current_slot > 0 and current_slot % ITEMS_PER_SCROLL == 0:
        #     print("  Scrolling inventory to reveal more items...")
        #     scroll_inventory()

        time.sleep(0.3)

    print(f"\n✅ Automation complete — processed {items_processed} gear items")


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

def extract_first_number_after_colon(text):
    """Extract the first number that appears after a colon in the text."""
    match = re.search(r':\s*([0-9]+)', text)
    if match:
        return int(match.group(1))
    # Fallback — just grab the first number found
    match = re.search(r'[0-9]+', text)
    if match:
        return int(match.group(0))
    return None

def refine_loop(stones_used = 0):
    """
    True if refining was successful, False if item needs recycling
    """
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



    # ── Pre-check: scan current stat rows before any refining ──
    print("  Pre-checking current stats before refining...")
    for i, region in enumerate(CURRENT_STAT_ROW_REGIONS):
        row_text = ocr_region(region)
        print(f"  Current row {i+1}: '{row_text.strip()}'")

        if not locked_all_skills:
            if evaluate_stat(row_text, DESIRED_STATS):
                found = find_and_click_lock("all skills")
                if found is not None:
                    locked_rows.append(found)
                    locked_all_skills = True
                    print("  → Pre-check: all skills found and locked!")

    if locked_all_skills:
        # Check remaining rows for desired after-lock stats
        print("  Pre-check: scanning for desired after-lock stats...")
        for i, region in enumerate(CURRENT_STAT_ROW_REGIONS):
            if i in locked_rows:
                continue
            row_text = ocr_region(region)
            matched_after = evaluate_stat(row_text, DESIRED_STATS_AFTER_LOCK)
            if matched_after:
                found = find_and_click_lock(matched_after[0])
                if found is not None:
                    locked_rows.append(found)
                    locked_desired_count += 1
                    print(f"  → Pre-check: row {i+1} '{matched_after}' locked!")

        if locked_desired_count >= DESIRED_STATS_NEEDED:
            print(f"  → Pre-check: already has all desired stats — phase 1 complete!")
            return True
        
        if locked_desired_count > 0:
            print(f"  → Pre-check: already has all skills and one skill, backup gear - skipping")
            return True



    while stones_used < MAX_STONES_PER_GEAR - ORANGE_BUFFER:
        emergency_stop_check()

        if stones_used > ALL_SKILLS_LIMIT and not locked_all_skills:
            print(f"All skills not found after {ALL_SKILLS_LIMIT}, moving to phase 2")
            break

        print(f"[Stone {stones_used + get_refine_cost(len(locked_rows))}/{MAX_STONES_PER_GEAR}] Clicking Refine...")
        if stones_used > 0 and stones_used % 100 == 0:
            print(f""" ╔══════════════════════════════════╗
                       ║  STONES USED: {stones_used:<5}  /  {MAX_STONES_PER_GEAR:<5}   ║
                       ╚══════════════════════════════════╝""")
            
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
                stones_used += get_refine_cost(len(locked_rows))
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
                        print(f"  → Row {i+1} '{matched_after}' locked!")
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
        return False

    print(f"\n✅ Used {stones_used} stones. Time to recycle and start over!")
    return True



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
    start_time = time.time()
    clear_debug_files("debug/orange")

    clear_debug_files("debug", prefix="capture_")

    if TEST_OCR_MODE:
        test_ocr_from_file(TEST_OCR_IMAGE)
    elif CALIBRATION_MODE:
        calibration_mode()
    elif VISUALISATION_MODE:
        visualise_coordinates()
    else:
        run_automation(22) # starting row index starts at 0 - determines what gear to start with as inv is in gear order


    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    print(f"\n Time Taken: {hours}h {minutes}m {seconds}s")
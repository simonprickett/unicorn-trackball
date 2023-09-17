# Figure out which device we are running on...
try:
    from galactic import GalacticUnicorn as Unicorn
    from picographics import DISPLAY_GALACTIC_UNICORN as DISPLAY
except ImportError:
    # TODO Handle the Stellar Unicorn when we have one to try it out on...
    from cosmic import CosmicUnicorn as Unicorn
    from picographics import DISPLAY_COSMIC_UNICORN as DISPLAY
    
from pimoroni_i2c import PimoroniI2C
from picographics import PicoGraphics
from breakout_trackball import BreakoutTrackball
from time import sleep, ticks_ms, ticks_diff

# Trackball setup.
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5, "baudrate": 100000}
i2c = PimoroniI2C(**PINS_BREAKOUT_GARDEN)
trackball = BreakoutTrackball(i2c)
last_pressed_time = 0
BUTTON_DEBOUNCE_TIME = 400
TRACKBALL_SENSITIVITY_H = 1.5
TRACKBALL_SENSITIVITY_V = 1.8
TRACKBALL_COLOURS = [
    { "r": 255, "g": 0, "b": 0, "w": 0 },
    { "r": 250, "g": 108, "b": 0, "w": 0 },
    { "r": 255, "g": 247, "b": 0, "w": 0 },
    { "r": 0, "g": 255, "b": 0, "w": 0 },
    { "r": 13, "g": 255, "b": 159, "w": 0 },
    { "r": 0, "g": 0, "b": 255, "w": 0 },
    { "r": 94, "g": 13, "b": 255, "w": 0 } 
]

# Unicorn graphics setup.
unicorn = Unicorn()
graphics = PicoGraphics(DISPLAY)
DISPLAY_WIDTH, DISPLAY_HEIGHT = graphics.get_bounds()
CURSOR_X_HOME = DISPLAY_WIDTH // 2
CURSOR_Y_HOME = DISPLAY_HEIGHT // 2
BLINK_IDLE_TIME = 500
last_blinked_time = 0

# Define the pens we will use to colour in the screen.
BLACK_PEN = graphics.create_pen(0, 0, 0)
ERASER_PEN = graphics.create_pen(255, 255, 255)

# We need one pen for each colour we are going to draw with.
COLOURED_PENS = []
for colour in TRACKBALL_COLOURS:
    COLOURED_PENS.append(graphics.create_pen(colour["r"], colour["g"], colour["b"]))

def clear_screen():
    graphics.set_pen(BLACK_PEN)
    graphics.clear()
    unicorn.update(graphics)
    
def beep():
    # TODO
    pass
    
# Main program begins here, clear screen and initialise trackball colour.
clear_screen()
current_colour = 0
blink_set_off = True
erase_mode = False
erase_mode_toggle_time = 0
current_brightness = 0.4
trackball.set_rgbw(**TRACKBALL_COLOURS[current_colour])
cursor_x = CURSOR_X_HOME
cursor_y = CURSOR_Y_HOME

graphics.set_pen(COLOURED_PENS[current_colour])
graphics.pixel(cursor_x, cursor_y)
unicorn.set_brightness(current_brightness)
unicorn.update(graphics)

while True:
    state = trackball.read()
    state_changed = False
    time_now = ticks_ms()
    
    if state[BreakoutTrackball.SW_PRESSED]:
        time_diff = ticks_diff(time_now, last_pressed_time)
        
        if time_diff >= BUTTON_DEBOUNCE_TIME:
            last_pressed_time = time_now
            current_colour = current_colour + 1 if current_colour < len(TRACKBALL_COLOURS) - 1 else 0
            trackball.set_rgbw(**TRACKBALL_COLOURS[current_colour])
            graphics.set_pen(COLOURED_PENS[current_colour])
            state_changed = True
            
    elif state[BreakoutTrackball.LEFT] > TRACKBALL_SENSITIVITY_H:
        if cursor_x > 0:
            cursor_x -= 1
            state_changed = True
        else:
            beep()

    elif state[BreakoutTrackball.RIGHT] > TRACKBALL_SENSITIVITY_H:
        if cursor_x < (DISPLAY_WIDTH - 1):
            cursor_x += 1
            state_changed = True
        else:
            beep()
        
    elif state[BreakoutTrackball.UP] > TRACKBALL_SENSITIVITY_V:
        if cursor_y > 0:
            cursor_y -= 1
            state_changed = True
        else:
            beep()
        
    elif state[BreakoutTrackball.DOWN] > TRACKBALL_SENSITIVITY_V:
        if cursor_y < (DISPLAY_HEIGHT - 1):
            cursor_y += 1
            state_changed = True            
        else:
            beep()

    # Check if button A (clear screen) was pressed...
    if unicorn.is_pressed(Unicorn.SWITCH_A):
        clear_screen()
        cursor_x = CURSOR_X_HOME
        cursor_y = CURSOR_Y_HOME
        # Keeping the current colour, you could argue this should reset to the initial colour...
        graphics.set_pen(COLOURED_PENS[current_colour])
        erase_mode = False
        state_changed = True
        
    # Check if button B (toggle erase mode) was pressed...
    if unicorn.is_pressed(Unicorn.SWITCH_B):
        time_diff = ticks_diff(time_now, erase_mode_toggle_time)
        
        if time_diff >= BUTTON_DEBOUNCE_TIME:
            erase_mode = not erase_mode
            erase_mode_toggle_time = time_now
        
    # Check if the brightness needs to be adjusted up or down...
    if unicorn.is_pressed(Unicorn.SWITCH_BRIGHTNESS_UP):
        if current_brightness < 1:
            current_brightness += 0.01
            state_changed = True
    
    if unicorn.is_pressed(Unicorn.SWITCH_BRIGHTNESS_DOWN):
        if current_brightness > 0.1:
            current_brightness -= 0.01
            state_changed = True

    unicorn.set_brightness(current_brightness)
    graphics.pixel(cursor_x, cursor_y)

    # If the state changed, update the display.
    if state_changed:
        unicorn.update(graphics)
    else:
        # No state change, so flash the current cursor position instead.
        # Alternate between painting the current pixel with the black pen and the current_colour pen.
        time_diff = ticks_diff(time_now, last_blinked_time)
        
        if time_diff >= BLINK_IDLE_TIME:
            if blink_set_off is True:
                graphics.set_pen(BLACK_PEN)
            else:
                graphics.set_pen(ERASER_PEN if erase_mode == True else COLOURED_PENS[current_colour])
  
            graphics.pixel(cursor_x, cursor_y)
            blink_set_off = not blink_set_off
            last_blinked_time = time_now
            unicorn.update(graphics)
            
        # Reset the pen to the current colour in case this is the last idle/blink before the
        # pen moves again.
        graphics.set_pen(COLOURED_PENS[current_colour] if erase_mode == False else BLACK_PEN)
        graphics.pixel(cursor_x, cursor_y)

    sleep(0.01)


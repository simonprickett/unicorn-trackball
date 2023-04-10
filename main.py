from galactic import GalacticUnicorn
from pimoroni_i2c import PimoroniI2C
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY
from breakout_trackball import BreakoutTrackball
from time import sleep, ticks_ms, ticks_diff

# Trackball setup.
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5, "baudrate": 100000}
i2c = PimoroniI2C(**PINS_BREAKOUT_GARDEN)
trackball = BreakoutTrackball(i2c)
last_pressed_time = 0
BUTTON_DEBOUNCE_TIME = 400
TRACKBALL_SENSITIVITY = 1.8
TRACKBALL_COLOURS = [
    { "r": 255, "g": 0, "b": 0, "w": 0 },
    { "r": 0, "g": 255, "b": 0, "w": 0 },
    { "r": 0, "g": 0, "b": 255, "w": 0 }
]

# Galactic Unicorn graphics setup.
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)
DISPLAY_WIDTH, DISPLAY_HEIGHT = graphics.get_bounds()
CURSOR_X_HOME = DISPLAY_WIDTH // 2
CURSOR_Y_HOME = DISPLAY_HEIGHT // 2
BLINK_IDLE_TIME = 500
last_blinked_time = 0

# First pen (0 index) is black, 1... end are colours to use for painting.
BLACK = 0
COLOURED_PENS = [
    graphics.create_pen(0, 0, 0),
    graphics.create_pen(255, 0, 0),
    graphics.create_pen(0, 255, 0),
    graphics.create_pen(0, 0, 255)
]

def clear_screen():
    # Use the black pen.
    graphics.set_pen(COLOURED_PENS[BLACK])
    graphics.clear()
    gu.update(graphics)
    
def beep():
    # TODO
    pass
    
# Main program begins here, clear screen and initialise trackball colour.
clear_screen()
current_colour = 1
blink_set_off = True
current_brightness = 0.5
trackball.set_rgbw(**TRACKBALL_COLOURS[current_colour - 1])
cursor_x = CURSOR_X_HOME
cursor_y = CURSOR_Y_HOME

graphics.set_pen(COLOURED_PENS[current_colour])
graphics.pixel(cursor_x, cursor_y)
gu.set_brightness(current_brightness)
gu.update(graphics)

while True:
    state = trackball.read()
    state_changed = False
    time_now = ticks_ms()
    
    if state[BreakoutTrackball.SW_PRESSED]:
        time_diff = ticks_diff(time_now, last_pressed_time)
        
        if time_diff >= BUTTON_DEBOUNCE_TIME:
            last_pressed_time = time_now
            current_colour = current_colour + 1 if current_colour < len(TRACKBALL_COLOURS) else 1
            trackball.set_rgbw(**TRACKBALL_COLOURS[current_colour - 1])
            graphics.set_pen(COLOURED_PENS[current_colour])
            state_changed = True
            
    elif state[BreakoutTrackball.LEFT] > TRACKBALL_SENSITIVITY:
        if cursor_x > 0:
            cursor_x -= 1
            state_changed = True
        else:
            beep()

    elif state[BreakoutTrackball.RIGHT] > TRACKBALL_SENSITIVITY:
        if cursor_x < (DISPLAY_WIDTH - 1):
            cursor_x += 1
            state_changed = True
        else:
            beep()
        
    elif state[BreakoutTrackball.UP] > TRACKBALL_SENSITIVITY:
        if cursor_y > 0:
            cursor_y -= 1
            state_changed = True
        else:
            beep()
        
    elif state[BreakoutTrackball.DOWN] > TRACKBALL_SENSITIVITY:
        if cursor_y < (DISPLAY_HEIGHT - 1):
            cursor_y += 1
            state_changed = True            
        else:
            beep()

    # Check if button A (clear screen) was pressed...
    if gu.is_pressed(GalacticUnicorn.SWITCH_A):
        clear_screen()
        cursor_x = CURSOR_X_HOME
        cursor_y = CURSOR_Y_HOME
        # Keeping the current colour, you could argue this should reset to the initial colour...
        graphics.set_pen(COLOURED_PENS[current_colour])
        state_changed = True
        
    # Check if the brightness needs to be adjusted up or down...
    if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP):
        if current_brightness < 1:
            current_brightness += 0.01
            state_changed = True
    
    if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN):
        if current_brightness > 0.1:
            current_brightness -= 0.01
            state_changed = True

    gu.set_brightness(current_brightness)
    graphics.pixel(cursor_x, cursor_y)

    # Only update the display if something changed.
    if state_changed:
        gu.update(graphics)
        last_blinked_time = 0
    else:
        # No state change, so flash the current cursor position.
        # Alternate between painting the current pixel with the black pen and the current_colour pen.
        time_diff = ticks_diff(time_now, last_blinked_time)
        
        if time_diff >= BLINK_IDLE_TIME:            
            graphics.set_pen(COLOURED_PENS[BLACK if blink_set_off is True else current_colour])
            graphics.pixel(cursor_x, cursor_y)
            blink_set_off = not blink_set_off
            last_blinked_time = time_now
            gu.update(graphics)
            
        # Reset the pen to the current colour in case this is the last idle/blink before the
        # pen moves again.
        graphics.set_pen(COLOURED_PENS[current_colour])
        graphics.pixel(cursor_x, cursor_y)
        
    sleep(0.02)

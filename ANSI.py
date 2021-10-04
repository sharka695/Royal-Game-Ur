class ANSI:
    esc = "\x1b" # esc = "\033"
    next_line = esc + "e"
    index = esc + "d"
    reverse_index = esc + "m"
    horizontal_tab_set = esc + "h"
    # send_vt100_identification_string = esc + "z"
    # save_cursor_and_attributes = esc + "7"
    # restore_cursor_and_attributes = esc + "8"
    # save_cursor_and_attributes = esc + "[s"
    # restore_cursor_and_attributes = esc + "[u"
    reset_to_initial_state = esc + "c"
    visual_bell = esc + "g"
    cursor_invisible = esc + "6p"
    cursor_visible = esc + "7p"
    # application_keypad_mode = esc + "="
    # numeric_keypad_mode = esc + ">"
    fill_screen_with_e = esc + "#8"
    direct_cursor_addressing = (lambda pn, pm: esc + "[" + pn + ";" + pm + "h")
    erase_from_cursor_to_end_of_screen = esc + "[0j"
    erase_from_beginning_of_screen_to_cursor = esc + "[1j"
    erase_entire_screen = esc + "[2j"
    erase_from_cursor_to_end_of_line = esc + "[0k"
    erase_from_beginning_of_line_to_cursor = esc + "[1k"
    erase_entire_line = esc + "[2k"
    erase_character = (lambda pn: esc + "[" + pn + "x")
    cursor_up = (lambda pn: esc + "[" + pn + "a")
    cursor_down = (lambda pn: esc + "[" + pn + "b")
    cursor_right = (lambda pn: esc + "[" + pn + "c")
    cursor_left = (lambda pn: esc + "[" + pn + "d")
    cursor_next_line = (lambda pn: esc + "[" + pn + "e")
    cursor_previous_line = (lambda pn: esc + "[" + pn + "f")
    cursor_horizontal_position = (lambda pn: esc + "[" + pn + "g")
    cursor_vertical_position = (lambda pn: esc + "[" + pn + "d")
    default_rendition = esc + "[0m"
    bold = esc + "[1m"
    faint = esc + "[2m"
    standout_mode = esc + "[3m"
    underlined = esc + "[4m"
    blinking = esc + "[5m"
    negative_image = esc + "[7m"
    normal_intensity = esc + "[22m"
    standout_mode_off = esc + "[23m"
    not_underlined = esc + "[24m"
    not_blinking = esc + "[25m"
    positive_image = esc + "[27m"
    foreground_black = esc + "[30m"
    foreground_red = esc + "[31m"
    foreground_green = esc + "[32m"
    foreground_yellow = esc + "[33m"
    foreground_blue = esc + "[34m"
    foreground_magenta = esc + "[35m"
    foreground_cyan = esc + "[36m"
    foreground_white = esc + "[37m"
    foreground_default = esc + "[39m"
    background_black = esc + "[40m"
    background_default = esc + "[49m"
    clear_tab_at_current_position = esc + "[0g"
    clear_all_tabs = esc + "[3g"
    set_scrolling_region = (lambda pn, pm: esc + "[" + pn + ";" + pm + "r")
    horizontal_tab = (lambda pn: esc + "[" + pn + "i")
    backward_tab = (lambda pn: esc + "[" + pn + "z")
    insert_line = (lambda pn: esc + "[" + pn + "l")
    delete_line = (lambda pn: esc + "[" + pn + "m")
    insert_character = (lambda pn: esc + "[" + pn + "@")
    delete_character = (lambda pn: esc + "[" + pn + "p")
    scroll_scrolling_region_up = (lambda pn: esc + "[" + pn + "s")
    scroll_scrolling_region_down = (lambda pn: esc + "[" + pn + "t")

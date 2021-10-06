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
    erase_from_cursor_to_end_of_screen = esc + "[0J"
    erase_from_beginning_of_screen_to_cursor = esc + "[1J"
    erase_entire_screen = esc + "[2J"
    erase_from_cursor_to_end_of_line = esc + "[0k"
    erase_from_beginning_of_line_to_cursor = esc + "[1k"
    erase_entire_line = esc + "[2k"
    normal = esc + "[0m"
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
    background_red = esc + "[41m"
    background_green = esc + "[42m"
    background_yellow = esc + "[43m"
    background_blue = esc + "[44m"
    background_magenta = esc + "[45m"
    background_cyan = esc + "[46m"
    background_white = esc + "[47m"
    background_default = esc + "[49m"
    clear_tab_at_current_position = esc + "[0g"
    clear_all_tabs = esc + "[3g"
    @staticmethod
    def direct_cursor_addressing(pn, pm):
        return ANSI.esc + "[" + str(pn) + ";" + str(pm) + "h"
    @staticmethod
    def erase_character(pn):
        return ANSI.esc + "[" + str(pn) + "x"
    @staticmethod
    def cursor_up(pn):
        return ANSI.esc + "[" + str(pn) + "a"
    @staticmethod
    def cursor_down(pn):
        return ANSI.esc + "[" + str(pn) + "b"
    @staticmethod
    def cursor_right(pn):
        return ANSI.esc + "[" + str(pn) + "c"
    @staticmethod
    def cursor_left(pn):
        return ANSI.esc + "[" + str(pn) + "d"
    @staticmethod
    def cursor_next_line(pn):
        return ANSI.esc + "[" + str(pn) + "e"
    @staticmethod
    def cursor_previous_line(pn):
        return ANSI.esc + "[" + str(pn) + "f"
    @staticmethod
    def cursor_horizontal_position(pn):
        return ANSI.esc + "[" + str(pn) + "g"
    @staticmethod
    def cursor_vertical_position(pn):
        return ANSI.esc + "[" + str(pn) + "d"
    @staticmethod
    def set_scrolling_region(pn, pm):
        return ANSI.esc + "[" + str(pn) + ";" + str(pm) + "r"
    @staticmethod
    def horizontal_tab(pn):
        return ANSI.esc + "[" + str(pn) + "i"
    @staticmethod
    def backward_tab(pn):
        return ANSI.esc + "[" + str(pn) + "z"
    @staticmethod
    def insert_line(pn):
        return ANSI.esc + "[" + str(pn) + "l"
    @staticmethod
    def delete_line(pn):
        return ANSI.esc + "[" + str(pn) + "m"
    @staticmethod
    def insert_character(pn):
        return ANSI.esc + "[" + str(pn) + "@"
    @staticmethod
    def delete_character(pn):
        return ANSI.esc + "[" + str(pn) + "p"
    @staticmethod
    def scroll_scrolling_region_up(pn):
        return ANSI.esc + "[" + str(pn) + "s"
    @staticmethod
    def scroll_scrolling_region_down(pn):
        return ANSI.esc + "[" + str(pn) + "t"

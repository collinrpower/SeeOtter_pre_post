
class Modifier:
    SHIFT = "shift"
    CTRL = "ctrl"
    ALT = "alt"
    SUPER = "meta"


class KeyCode:

    # Modifiers
    L_ALT = 308
    R_ALT = 307
    L_CTRL = 305
    R_CTRL = 306
    L_SHIFT = 304
    R_SHIFT = 303
    L_SUPER = 309
    R_SUPER = 1073742055
    MODIFIERS = [L_ALT, R_ALT, L_CTRL, R_CTRL, L_SHIFT, R_SHIFT, L_SUPER, R_SUPER]

    # Navigation > Primary
    UP = 273
    DOWN = 274
    LEFT = 276
    RIGHT = 275
    NAVIGATION_PRIMARY = [UP, DOWN, LEFT, RIGHT]

    # Navigation > Page
    PAGE_UP = 280
    PAGE_DOWN = 281
    NAVIGATION_PAGE = [PAGE_UP, PAGE_DOWN]

    # Navigation > Line
    HOME = 278
    END = 279
    NAVIGATION_LINE = [HOME, END]

    NAVIGATION = NAVIGATION_PRIMARY + NAVIGATION_PAGE + NAVIGATION_LINE

    # State Toggles
    CAPS_LOCK = 301
    NUM_LOCK = 300
    SCREEN_LOCK = 145
    STATE_TOGGLES = [CAPS_LOCK, NUM_LOCK, SCREEN_LOCK]

    # Commands
    BACKSPACE = 8
    COMPOSE = 311
    DELETE = 127
    ENTER = 13
    ESCAPE = 27
    INSERT = 277
    PAUSE = 19
    PRINT = 144
    COMMANDS = [BACKSPACE, COMPOSE, DELETE, ENTER, ESCAPE, INSERT, PAUSE, PRINT]

    # WhiteSpace
    SPACE = 32
    TAB = 9
    WHITESPACE = [SPACE, TAB]

    # Unknown
    PIPE = 310

    # Letters
    A = 97
    B = 98
    C = 99
    D = 100
    E = 101
    F = 102
    G = 103
    H = 104
    I = 105
    J = 106
    K = 107
    L = 108
    M = 109
    N = 110
    O = 111
    P = 112
    Q = 113
    R = 114
    S = 115
    T = 116
    U = 117
    V = 118
    W = 119
    X = 120
    Y = 121
    Z = 122
    LETTERS = [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z]

    # Accented_Letters
    A_GRAVE = 224  # À
    E_ACUTE = 233  # É
    E_GRAVE = 232  # È
    U_GRAVE = 249  # Ù
    ACCENTED_LETTERS = [A_GRAVE, E_ACUTE, E_GRAVE, U_GRAVE]

    # Numbers
    NUM_0 = 48
    NUM_1 = 49
    NUM_2 = 50
    NUM_3 = 51
    NUM_4 = 52
    NUM_5 = 53
    NUM_6 = 54
    NUM_7 = 55
    NUM_8 = 56
    NUM_9 = 57
    NUMBERS = [NUM_0, NUM_1, NUM_2, NUM_3, NUM_4, NUM_5, NUM_6, NUM_7, NUM_8, NUM_9]

    # Numpad
    NUMPAD_0 = 256
    NUMPAD_1 = 257
    NUMPAD_2 = 258
    NUMPAD_3 = 259
    NUMPAD_4 = 260
    NUMPAD_5 = 261
    NUMPAD_6 = 262
    NUMPAD_7 = 263
    NUMPAD_8 = 264
    NUMPAD_9 = 265
    NUMPAD_KEYS = [NUMPAD_0, NUMPAD_1, NUMPAD_2, NUMPAD_3, NUMPAD_4, NUMPAD_5, NUMPAD_6, NUMPAD_7, NUMPAD_8, NUMPAD_9]

    NUMPAD_ADD = 270
    NUMPAD_DECIMAL = 266
    NUMPAD_DIVIDE = 267
    NUMPAD_ENTER = 271
    NUMPAD_MULTIPLY = 268
    NUMPAD_SUBTRACT = 269
    NUMPAD_SYMBOLS = [NUMPAD_ADD, NUMPAD_DECIMAL, NUMPAD_DIVIDE, NUMPAD_ENTER, NUMPAD_MULTIPLY, NUMPAD_SUBTRACT]

    # F1 - F15
    F1 = 282
    F2 = 283
    F3 = 284
    F4 = 285
    F5 = 286
    F6 = 287
    F7 = 288
    F8 = 289
    F9 = 290
    F10 = 291
    F11 = 292
    F12 = 293
    F13 = 294
    F14 = 295
    F15 = 296
    F_KEYS = [F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15]

    # Brackets
    L_ANGLE = 60  # <
    R_ANGLE = 62  # >
    L_BRACE = 123  # {
    R_BRACE = 125  # }
    L_BRACKET = 91  # [
    R_BRACKET = 93  # ]
    L_PAREN = 40  # (
    R_PAREN = 41  # )
    BRACKETS = [L_ANGLE, R_ANGLE, L_BRACE, R_BRACE, L_BRACKET, R_BRACKET, L_PAREN, R_PAREN]

    # Symbols
    ACUTE_ACCENT = 180  # ´
    AMPERSAND = 38  # &
    ASTERISK = 42  # *
    AT = 64  # @
    BACKSLASH = 92  # \
    BACKTICK = 96  # `
    BAR = 124  # |
    BROKEN_BAR = 166  # ¦
    CARET = 94  # ^
    COLON = 58  # :
    COMMA = 44  # ,
    DASH = 45  # -
    DIAERESIS = 168  # ¨
    DOLLAR = 36  # $
    ELLIPSIS = 8230  # …
    EQUALS = 61  # =
    EXCLAMATION = 33  # !
    FORWARDSLASH = 47  # /
    NOT = 172  # ¬
    PERCENT = 37  # %
    PERIOD = 46  # .
    PLUS = 43  # +
    POUND = 35  # #
    QUESTION = 47  # ?
    QUOTE = 34  # "
    SEMICOLON = 59  # ;
    SINGLEQUOTE = 39  # '
    TILDE = 126  # ~
    UNDERSCORE = 95  # _
    SYMBOLS = BRACKETS + [ACUTE_ACCENT, AMPERSAND, ASTERISK, AT, BACKSLASH, BACKTICK, BAR, BROKEN_BAR, CARET, COLON,
                          COMMA, DASH, DIAERESIS, DOLLAR, ELLIPSIS, EQUALS, EXCLAMATION, FORWARDSLASH, NOT, PERCENT,
                          PERIOD, PLUS, POUND, QUESTION, QUOTE, SEMICOLON, SINGLEQUOTE, TILDE, UNDERSCORE]

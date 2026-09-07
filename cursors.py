import ctypes
import ctypes.util
import enum

import pygame


class CursorType(enum.Enum):
    # https://www.w3schools.com/cssref/tryit.php?filename=trycss_cursor
    # ls -l /usr/share/icons/Adwaita/cursors/

    ARROW = (b'arrow', pygame.SYSTEM_CURSOR_ARROW)
    WAIT = (b'wait', pygame.SYSTEM_CURSOR_WAIT)

    HAND = (b'pointer', pygame.SYSTEM_CURSOR_HAND)
    GRAB = (b'grab', pygame.SYSTEM_CURSOR_HAND)
    GRABBING = (b'grabbing', pygame.SYSTEM_CURSOR_HAND)

    CROSSHAIR = (b'crosshair', pygame.SYSTEM_CURSOR_CROSSHAIR)
    CELL = (b'cell', pygame.SYSTEM_CURSOR_ARROW)


_cursor_use_x11 = False
_CURSOR = ctypes.c_uint32
_cursors: dict[bytes, _CURSOR] | dict[int, pygame.cursors.Cursor] = {}

_window: ctypes.c_uint32 | None = None
_display: ctypes.c_void_p | None = None

_x_cursor = None
_x11 = None


def init() -> bool:
    """Should be called after the pygame.display is created"""

    global _cursors
    if pygame.display.get_driver() != 'x11':
        return False

    wm_info = pygame.display.get_wm_info()
    global _window, _display
    _window = wm_info['window']
    _display = ctypes.c_void_p(_get_capsule_value(wm_info['display']))

    try:
        dllist = ctypes.util.dllist()  # Available since Python 3.14
    except AttributeError:  # dllist not available
        # TODO: Fallback using /proc/self/maps on Linux
        return False

    x_cursor_library_path, = filter(lambda s: 'libXcursor' in s, dllist)
    print('Using Xcursor:', x_cursor_library_path)
    global _x_cursor
    _x_cursor = ctypes.CDLL(x_cursor_library_path)

    _x_cursor.XcursorLibraryLoadCursor.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    _x_cursor.XcursorLibraryLoadCursor.restype = _CURSOR

    x11_library_path, = filter(lambda s: 'libX11.so' in s, dllist)
    print('Using X11:', x11_library_path)
    global _x11
    _x11 = ctypes.CDLL(x11_library_path)

    _x11.XDefineCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CURSOR]

    global _cursor_use_x11
    _cursor_use_x11 = True
    return True


def set_cursor(cursor: CursorType = CursorType.ARROW) -> None:
    """Not thread-safe"""

    # TODO: Check if the cursor is using Xcursor or xfont
    #const char *theme = XcursorGetTheme(dpy);
    #int size = XcursorGetDefaultSize(dpy);
    #XcursorImage *image =
    #    XcursorLibraryLoadImage("pencil", theme, size);
    #if (image) {
    #    Cursor cursor = XcursorImageLoadCursor(dpy, image);
    #    XcursorImageDestroy(image);
    #    XDefineCursor(dpy, window, cursor);
    #}

    if not _cursor_use_x11:
        c = cursor.value[1]
        if c not in _cursors:
            _cursors[c] = pygame.cursors.Cursor(c)
        pygame.mouse.set_cursor(_cursors[cursor.value[1]])
        return

    cursor_name = cursor.value[0]
    if cursor_name not in _cursors:
        c = _x_cursor.XcursorLibraryLoadCursor(_display, cursor_name)
        _cursors[cursor_name] = c

    _x11.XDefineCursor(_display, _window, _cursors[cursor_name])


ctypes.pythonapi.PyCapsule_GetName.restype = ctypes.c_char_p
ctypes.pythonapi.PyCapsule_GetName.argtypes = [ctypes.py_object]

ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]


def _get_capsule_value(capsule) -> int:
    # https://stackoverflow.com/a/74738224

    name = ctypes.pythonapi.PyCapsule_GetName(capsule)
    addr = ctypes.pythonapi.PyCapsule_GetPointer(capsule, name)
    return addr


if __name__ == '__main__':
    import faulthandler
    import os

    faulthandler.enable()

    os.environ['SDL_VIDEODRIVER'] = 'x11'
    pygame.init()
    pygame.display.init()
    assert pygame.display.get_driver() == 'x11'

    screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)
    pygame.display.set_caption('Yoyoyo')

    # print(screen)
    # pygame._sdl2.Window.from_display_module()
    # window = pygame._sdl2.Window(size=(800, 800), resizable=True)
    #
    # print(window.get_sdl_window)
    #
    # screen = window.get_surface()

    # print(pygame.display.get_wm_info())
    wm_info = pygame.display.get_wm_info()
    window = wm_info['window']
    display = ctypes.c_void_p(_get_capsule_value(wm_info['display']))

    dllist = ctypes.util.dllist()  # Available since Python 3.14
    sdl_library_path, = filter(lambda s: 'libSDL2' in s and s[s.index('libSDL2') + 7] != '_', dllist)

    print('Using sdl:', sdl_library_path)
    sdl = ctypes.CDLL(sdl_library_path)

    sdl.SDL_GetError.argtypes = []
    sdl.SDL_GetError.restype = ctypes.c_char_p

    # sdl.SDL_GetWindowWMInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(SDL_WMInfo)]
    # sdl.SDL_GetWindowWMInfo.restype = ctypes.c_bool
    # wm_info = SDL_WMInfo()
    # if not sdl.SDL_GetWindowWMInfo(window, ctypes.pointer(wm_info)):
    #     raise RuntimeError(sdl.SDL_GetError())

    # sdl.SDL_WasInit.argtypes = [ctypes.c_uint32]
    # sdl.SDL_WasInit.restype = ctypes.c_uint32
    # print('Was init:', bin(sdl.SDL_WasInit(0)))

    x_cursor_library_path, = filter(lambda s: 'libXcursor' in s, dllist)
    print('Using Xcursor:', x_cursor_library_path)
    x_cursor = ctypes.CDLL(x_cursor_library_path)

    CURSOR = ctypes.c_uint32
    x_cursor.XcursorLibraryLoadCursor.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    x_cursor.XcursorLibraryLoadCursor.restype = CURSOR
    c = x_cursor.XcursorLibraryLoadCursor(display, b'crosshair')

    x11_library_path, = filter(lambda s: 'libX11.so' in s, dllist)
    print('Using X11:', x11_library_path)
    x11 = ctypes.CDLL(x11_library_path)

    # x11.XCreateFontCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    # x11.XCreateFontCursor.restype = CURSOR
    # c = x11.XCreateFontCursor(display, 8)

    x11.XDefineCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CURSOR]

    # XID: uint32

    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        x11.XDefineCursor(display, window, c)

        pygame.display.update()

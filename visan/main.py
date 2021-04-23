# Copyright (C) 2002-2021 S[&]T, The Netherlands.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Startup code for VISAN.
"""

import os
import sys


def main():
    try:
        import traceback
        sys.argv[0] = "visan"
        from .app import VisanApp
        app = VisanApp()
        app.MainLoop()
    except Exception:
        type, value, sys.last_traceback = sys.exc_info()
        lines = traceback.format_exception(type, value, sys.last_traceback)
        text = "Uncaught exception.\n\n" + "".join(lines)
        if sys.platform == 'win32':
            from ctypes import c_int, WINFUNCTYPE, windll
            from ctypes.wintypes import HWND, LPCSTR, UINT
            prototype = WINFUNCTYPE(c_int, HWND, LPCSTR, LPCSTR, UINT)
            paramflags = (1, "hwnd", 0), (1, "text", "Hi"), (1, "caption", None), (1, "flags", 0)
            MessageBox = prototype(("MessageBoxA", windll.user32), paramflags)
            MessageBox(text=text, caption="VISAN Error")
        else:
            sys.__stderr__.write(text)


if __name__ == "__main__":
    main()

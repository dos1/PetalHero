import os, sys

DEFAULT_PATH = '/flash/apps/PetalHero'

if __name__ == '__main__':
    __path__, __name__ = os.path.split(DEFAULT_PATH)
    sys.path.append(__path__)
    __path__ = None

from st3m.ui.view import BaseView, ViewTransitionBlend, ViewTransitionDirection
from st3m.input import InputState
from ctx import Context
import st3m.run
import st3m.wifi
import st3m.settings
import urequests
import sys
import _thread

from . import flower
from . import utils
from . import download

index_lock = _thread.allocate_lock()

def index_thread(self):
    index_lock.acquire(1)
    try:
        req = urequests.get(f'{utils.SONGS_REPO}/-/raw/main/index.json')
        if req.status_code != 200:
            raise Exception(req.status_code)
        self.index = req.json()
    except Exception as e:
        sys.print_exception(e)
        self.error = True
    index_lock.release()

class ConnectingView(BaseView):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.error = False
        self.index = None
        self.thread = False

    def draw(self, ctx: Context) -> None:
        utils.clear(ctx)
        ctx.save()
        ctx.gray(1.0)
        ctx.font = "Camp Font 3"
        ctx.font_size = 24
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        if st3m.wifi.is_connected() or self.error:
            ctx.move_to(0, 0)
            ctx.text("Downloading..." if not self.error else "Download failed.")
        else:
            ctx.move_to(0, -15)
            ctx.text("Connecting..." if st3m.wifi.is_connecting() else "No connection.")

            ctx.gray(0.75)
            ctx.move_to(0, 40)
            ctx.font_size = 16
            ctx.text("Press the button to")
            ctx.move_to(0, 55)
            ctx.text("enter Wi-Fi settings.")

        ctx.restore()
        
    def show_icons(self) -> bool:
        return True

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        
        if st3m.wifi.is_connected():
            if not self.thread:
                _thread.start_new_thread(index_thread, (self,))
                self.thread = True
            if self.index:
                self.vm.replace(download.DownloadView(self.app, self.index['songs']), ViewTransitionBlend())
        else:
            if self.input.buttons.app.middle.pressed:
                st3m.wifi.run_wifi_settings(self.vm)
            return

    def on_enter(self, vm):
        super().on_enter(vm)
        self.index = None
        self.thread = False
        self.error = False

    def on_enter_done(self):
        if st3m.settings.onoff_wifi_preference.value:
            st3m.wifi.setup_wifi()

    def on_exit(self):
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            utils.play_back(self.app)
            st3m.wifi.disable()
        # wait for the thread to exit
        index_lock.acquire(1)
        index_lock.release()

#if not __path__:
#    st3m.run.run_view(ConnectingView(None))

from st3m.ui.view import BaseView, ViewTransitionBlend
import gc
import time

import song
import utils

class LoadingView(BaseView):
    def __init__(self, app, song, difficulty):
        super().__init__()
        self.app = app
        self.song = song
        self.difficulty = difficulty

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font = "Camp Font 3"

        ctx.font_size = 32
        while ctx.text_width(self.song.name) > 220:
            ctx.font_size -= 1
        ctx.move_to (0, 0)
        ctx.gray(1.0)
        ctx.text(self.song.name)

        name_size = ctx.font_size
        ctx.font_size = min(22, name_size)
        while ctx.text_width(self.song.artist) > 220:
            ctx.font_size -= 1
        ctx.move_to (0, -name_size)
        ctx.gray(0.75)
        ctx.text(self.song.artist)

        ctx.font_size = 18
        ctx.move_to (0, 60)
        ctx.gray(0.5)
        ctx.text("Loading...")

    def think(self, ins: InputState, delta_ms: int) -> None:
        utils.blm_timeout(self, delta_ms)
        
    def on_enter_done(self):
        #gc.collect()
        t = time.ticks_ms()
        view = song.SongView(self.app, self.song, self.difficulty)
        t = time.ticks_ms() - t
        if t < 2000:
            time.sleep_ms(2000 - t)
        self.vm.replace(view, ViewTransitionBlend())
        gc.collect()

from st3m.ui.view import BaseView, ViewTransitionBlend
import gc

import song

class LoadingView(BaseView):
    def __init__(self, app, song, difficulty):
        super().__init__()
        self.app = app
        self.song = song
        self.difficulty = difficulty
        self.delay = 500
        self.view = None

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.font = "Camp Font 3"
        ctx.font_size = 32
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to (0, 0)
        ctx.gray(1.0)
        ctx.text("Loading...")

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        if delta_ms > 100:
            delta_ms = 0
        self.delay -= delta_ms
        if self.delay < 0:
            if self.view:
                self.vm.replace(self.view, ViewTransitionBlend())
            else:
                gc.collect()
                self.view = song.SongView(self.app, self.song, self.difficulty)
            self.delay = 500

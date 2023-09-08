from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeLeft, ViewTransitionSwipeRight, ViewTransitionBlend
from st3m.application import Application, ApplicationContext
from st3m.ui.interactions import ScrollController
import st3m.run
import media
import math
import random
import sys_display

if __name__ == '__main__':
    import sys
    sys.path.append('/flash/apps/PetalHero')

import flower
import loading
import utils
import midireader

class ScoreView(BaseView):
    def __init__(self, app, data, streak):
        super().__init__()
        self.app = app
        self.data = data
        self.flower = flower.Flower(0)
        self.time = 0
        self.streak = streak
        self.played = False
        if not self.data:
            self.accuracy = 0.42
        else:
            events = data.track.getAllEvents()
            self.accuracy = len(set(filter(lambda x: isinstance(x, midireader.Note) and x.played, events))) / len(events)
        self.stars = int(5.0 * (self.accuracy + 0.05))

    def draw(self, ctx: Context) -> None:
        
        #utils.background(ctx)
        ctx.gray(0)
        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()

        ctx.save()
        ctx.translate(-90, 1)
        ctx.scale(0.325, 0.325)
        for i in range(5):
            if i < self.stars:
                utils.fire_gradient(ctx)
            else:
                ctx.gray(0.15)
            self.flower.draw(ctx)
            ctx.translate(45 / 0.325, 0)
        ctx.restore()
        
        ctx.save()

        offset = 0

        ctx.font = "Camp Font 3"
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        ctx.move_to(0, 0)

        ctx.restore()
        
        """
        ctx.rectangle(-120, 65, 240, 55)
        ctx.fill()
        """
        utils.fire_gradient(ctx)
        
        ctx.font = "Camp Font 1"
        ctx.font_size = 38
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to (0, -78)
        ctx.text("SONG")
        ctx.move_to (0, -42)
        ctx.text("COMPLETE")
                
        ctx.gray(1.0)
        ctx.font = "Camp Font 3"
        ctx.font_size = 18
        ctx.move_to (0,37)
        ctx.text(f"Accuracy: {int(self.accuracy * 100)}%")
        ctx.move_to(0,58)
        ctx.text(f"Longest streak: {self.streak}")
                
        ctx.font = "Camp Font 3"
        ctx.font_size = 16
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.gray(0.5)
        ctx.move_to(0, 84 - math.sin(self.time * 4) * 2)
        ctx.text("Press the button...")

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        media.think(delta_ms)
        self.time += delta_ms / 1000
        
        if self.time > 1.5 and not self.played:
            self.played = True
            taunt = None
            if self.accuracy == 0:
                taunt = "jurgen1"
            elif self.accuracy >= 0.99:
                taunt = "myhero"
            elif self.stars in [0, 1]:
                taunt = random.choice(["jurgen2", "jurgen3", "jurgen4", "jurgen5"])
            elif self.stars == 5:
                taunt = random.choice(["perfect1", "perfect2", "perfect3"])
            if self.app and taunt:
                media.load(self.app.path + "/sounds/" + taunt + ".mp3")

        if self.input.buttons.app.middle.pressed:
            self.vm.pop(ViewTransitionBlend())

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        if self.app:
            self.app.after_score = True

    def on_exit(self):
        sys_display.set_mode(0)
        super().on_exit()
        if self.app:
            utils.play_go(self.app)

if __name__ == '__main__':
    view = ScoreView(None, None, 420)
    st3m.run.run_view(view)

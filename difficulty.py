from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeLeft, ViewTransitionBlend
from st3m.application import Application, ApplicationContext
from st3m.ui.interactions import ScrollController
import media
import math
import random

import flower
import loading
import utils

class DifficultyView(BaseView):
    def __init__(self, app, song):
        super().__init__()
        self.app = app
        self.flower = flower.Flower(0.001)
        self._sc = ScrollController()
        self.song = song
        self._sc.set_item_count(len(self.song.difficulties))
        if len(self.song.difficulties) > 2:
            self._sc.scroll_right()
        self._scroll_pos = 0

    def draw(self, ctx: Context) -> None:
        
        utils.background(ctx)

        ctx.save()
        ctx.scale(1.9, 1.9)
        ctx.translate(0, 56)
        ctx.rgba(0.1, 0.4, 0.3, 0.42)
        self.flower.draw(ctx)
        ctx.restore()
        
        ctx.save()
        ctx.gray(1.0)
        ctx.rectangle(
            -120.0,
            -15.0,
            240.0,
            30.0,
        ).fill()

        ctx.translate(0, -30 * self._sc.current_position())

        offset = 0

        ctx.font = "Camp Font 3"
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        ctx.move_to(0, 0)
        for idx, diff in enumerate(self.song.difficulties):
            target = idx == self._sc.target_position()
            if target:
                ctx.gray(0.0)
            else:
                ctx.gray(1.0)

            distance = self._sc.current_position() - idx
            if abs(distance) <= 3:
                xpos = 0.0
                ctx.font_size = 24 - abs(distance) * 3
                if target and (width := ctx.text_width(str(diff))) > 220:
                    xpos = math.sin(self._scroll_pos) * (width - 220) / 2
                ctx.move_to(xpos, offset + distance * abs(distance) * 2)
                ctx.global_alpha = max(0.0, 1.0 - abs(distance) / 2.5)
                ctx.text(str(diff))
                ctx.global_alpha = 1.0
            offset += 30

        ctx.restore()
        
        ctx.rgba(1.0, 1.0, 1.0, 0.05)
        ctx.rectangle(-120, -120, 240, 55)
        ctx.fill()
        """
        ctx.rectangle(-120, 65, 240, 55)
        ctx.fill()
        """
        utils.fire_gradient(ctx)
        
        ctx.font = "Camp Font 1"
        ctx.font_size = 25
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to (0, -80)
        ctx.text("DIFFICULTY")
        
        """
        ctx.font_size = 15
        ctx.move_to(0, 78)
        ctx.text("Put songs into")
        ctx.move_to(0, 94)
        ctx.font_size = 15
        ctx.gray(0.75)
        ctx.text("/sd/PetalHero")
        """

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms)
        self._sc.think(ins, delta_ms)
        media.think(delta_ms)
        self.flower.think(delta_ms)
        self._scroll_pos += delta_ms / 1000

        if self.input.buttons.app.left.pressed:
            self._sc.scroll_left()
            self._scroll_pos = 0.0
            utils.play_crunch(self.app)
        elif self.input.buttons.app.right.pressed:
            self._sc.scroll_right()
            self._scroll_pos = 0.0
            utils.play_crunch(self.app)
            
        if self.input.buttons.app.middle.pressed:
            self.app.in_sound.signals.trigger.start()
            self.vm.replace(loading.LoadingView(self.app, self.song, self.song.difficulties[self._sc.target_position()]), ViewTransitionBlend())
            
        if self.input.buttons.os.middle.pressed:
            self.app.out_sound.signals.trigger.start()

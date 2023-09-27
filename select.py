from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeLeft
from st3m.ui.interactions import ScrollController
import math
import os, stat
import time
try:
    import media
    from st3m.ui.view import ViewTransitionDirection
except ImportError:
    pass

import flower
import difficulty
import songinfo
import utils

class LazySong(songinfo.SongInfo):
    def __init__(self, dirpath):
        self.dirpath = dirpath
        self.loaded = False
        
    def load(self):
        if not self.loaded:
            try:
                super().__init__(self.dirpath)
            except Exception as e:
                print(f"Failed to read the song from {self.dirpath}: {e}")
            self.loaded = True
        return self


def discover_songs(path: str, songs, to_process):
    path = path.rstrip("/")
    try:
        l = os.listdir(path)
    except Exception as e:
        print(f"Could not discover songs in {path}: {e}")
        l = []

    for d in l:
        dirpath = path + "/" + d
        st = os.stat(dirpath)
        if not stat.S_ISDIR(st[0]):
            continue

        inipath = dirpath + "/song.ini"
        try:
            st = os.stat(inipath)
            if not stat.S_ISREG(st[0]):
                continue
        except Exception:
            continue

        s = LazySong(dirpath)
        songs.append(s)

        inipath = dirpath + "/.diff.pet"
        try:
            st = os.stat(inipath)
            if not stat.S_ISREG(st[0]):
                to_process.append(s)
        except Exception:
            to_process.append(s)
            
        yield s

class SelectView(BaseView):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.flower = flower.Flower(0.001)
        self._sc = ScrollController()
        self.songs = []
        self.to_process = []
        self.discovery_iter = discover_songs("/sd/PetalHero", self.songs, self.to_process)
        self.processing_now = None
        self.loading = True
        self._scroll_pos = 0
        self.pos = -1
        self.repeat_count = 0
        self.first_scroll_think = False
        
    def discover(self, timeout = 100, play = True):
        if not self.loading:
            return
        try:
            start = time.ticks_ms()
            while time.ticks_ms() - start <= timeout:
                next(self.discovery_iter)
        except StopIteration:
            self.total_process = len(self.to_process)
            self._sc.set_item_count(len(self.songs))
            self.loading = False
            if not self.to_process and play:
                self.play()

    def draw(self, ctx: Context) -> None:
        
        utils.background(ctx)

        ctx.save()
        ctx.scale(1.9, 1.9)
        ctx.translate(-52, 0)
        ctx.rgba(0.1, 0.4, 0.3, 0.42)
        self.flower.draw(ctx)
        ctx.restore()
        
        if self.processing_now and self.is_active():
            self.processing_now.load()
            self.processing_now.getDifficulties()
            self.processing_now.saveDifficulties()
            self.processing_now = None
            if not self.to_process:
                self.play()
            
        if self.to_process and not self.loading:
            if not self.vm.transitioning:
                self.processing_now = self.to_process.pop()

            utils.fire_gradient(ctx)
            
            ctx.font = "Camp Font 1"
            ctx.font_size = 18
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.move_to (0, -10)
            ctx.text("PROCESSING NEW SONGS")
            
            ctx.rgba(0.8, 0.8, 0.8, 0.15)
            ctx.rectangle(-120.0, 3.0, 240.0, 10.0).fill()
            ctx.gray(0.8)
            ctx.rectangle(
                -120.0,
                3.0,
                240.0 * (self.total_process - len(self.to_process)) / self.total_process,
                10.0,
            ).fill()

            return
        
        if self.loading:
            ctx.gray(1.0)
            ctx.move_to(0,0)
            
            ctx.font = "Camp Font 3"
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.font_size = 18
            ctx.text("Loading...")
            
            if self.is_active():
                self.discover()
        else:
            
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
            if not self.songs:
                ctx.gray(0.0)
                ctx.font_size = 24
                ctx.text("No songs found!")

            for idx, song in enumerate(self.songs):
                distance = self._sc.current_position() - idx
                target = idx == self._sc.target_position()
                if target:
                    ctx.gray(0.0)
                else:
                    ctx.gray(0.5 + min(abs(distance / 2), 0.5))

                if abs(distance) < 3:
                    song.load()
                    xpos = 0.0
                    ctx.font_size = 24 - abs(distance) * 3
                    if target and (width := ctx.text_width(song.name)) > 220:
                        xpos = math.sin(self._scroll_pos) * (width - 220) / 2
                    ctx.move_to(xpos, offset + distance * abs(distance) * 2)
                    ctx.global_alpha = max(0.0, 1.0 - abs(distance) / 2.5)
                    ctx.text(song.name)
                    ctx.global_alpha = 1.0
                offset += 30

            ctx.restore()
        
        ctx.rgba(1.0, 1.0, 1.0, 0.05)
        ctx.rectangle(-120, -120, 240, 55)
        ctx.fill()
        ctx.rectangle(-120, 65, 240, 55)
        ctx.fill()
        
        utils.fire_gradient(ctx)
        
        ctx.font = "Camp Font 1"
        ctx.font_size = 25
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to (0, -80)
        ctx.text("SELECT SONG")
        
        ctx.font_size = 15
        ctx.move_to(0, 78)
        ctx.text("Put songs into")
        ctx.move_to(0, 94)
        ctx.font_size = 15
        ctx.gray(0.75)
        ctx.text("/sd/PetalHero")

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        utils.blm_timeout(self, delta_ms)
        if not self.to_process and not self.processing_now:
            media.think(delta_ms)
        self.flower.think(delta_ms)
        self._scroll_pos += delta_ms / 1000

        cur_target = self._sc.target_position()
        if cur_target < 0: cur_target = 0
        if cur_target > len(self.songs) - 1: cur_target = len(self.songs) - 1

        if not self.is_active():
            self._sc.think(ins, delta_ms)
            return
        
        if self.processing_now or self.to_process or self.loading:
            return

        if self.input.buttons.app.left.pressed or (self.input.buttons.app.left.repeated and not self._sc.at_left_limit()):
            utils.play_crunch(self.app)
            for i in range(10 if self.repeat_count >= 10 else 1):
                self._sc.scroll_left()
            self._scroll_pos = 0.0
        elif self.input.buttons.app.right.pressed or (self.input.buttons.app.right.repeated and not self._sc.at_right_limit()):
            for i in range(10 if self.repeat_count >= 10 else 1):
                self._sc.scroll_right()
            self._scroll_pos = 0.0
            utils.play_crunch(self.app)
            
        if self.input.buttons.app.left.repeated or self.input.buttons.app.right.repeated:
            self.repeat_count += 1
        if self.input.buttons.app.left.released or self.input.buttons.app.right.released:
            self.repeat_count = 0

        pos = self._sc.target_position()
        if pos < 0: pos = 0
        if pos > len(self.songs) - 1: pos = len(self.songs) - 1

        if pos != cur_target:
            song = self.songs[pos].load()
            media.load(song.dirName + "/song.mp3")
            self.first_scroll_think = True

        if media.get_position() == media.get_duration():
            media.seek(0)

        if self.input.buttons.app.middle.pressed:
            utils.play_go(self.app)
            if self.songs:
                self.vm.push(difficulty.DifficultyView(self.app, self.songs[pos]), ViewTransitionSwipeLeft())

        if self.first_scroll_think:
            self._sc.think(ins, min(20, delta_ms))
            self.first_scroll_think = False
        else:
            self._sc.think(ins, delta_ms)

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        if self.vm.direction == ViewTransitionDirection.FORWARD or (self.app and self.app.after_score):
            if not self.to_process and not self.loading:
                self.play()
            if self.app:
                self.app.after_score = False

    def play(self):
        if self.songs:
            song = self.songs[self._sc.target_position()].load()
            media.load(song.dirName + "/song.mp3")
        else:
            media.stop()

    def on_exit(self):
        super().on_exit()
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            utils.play_back(self.app)

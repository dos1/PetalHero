import os, sys

DEFAULT_PATH = '/flash/apps/PetalHero'

if __name__ == '__main__':
    __path__, __name__ = os.path.split(DEFAULT_PATH)
    sys.path.append(__path__)
    __path__ = None

from st3m.ui.view import BaseView, ViewTransitionBlend, ViewTransitionDirection
from ctx import Context
from st3m.input import InputState
import st3m.run
import math
import random
import st3m.wifi
import st3m.ui.led_patterns
import st3m.settings
import leds
import time
import urequests
import gc
import sys
import _thread

from . import flower
from . import utils
from . import select

download_lock = _thread.allocate_lock()

def download_thread(self):
    download_lock.acquire(1)
    while self.file_list and not self.cancel:
        self.current_song = self.file_list.pop(0)
        self.file_no += 1
        self.file_progress = 0
        dirname = f"/sd/PetalHero/{self.current_song[2]} - {self.current_song[3]}"

        try:
            l = os.listdir(dirname)
        except Exception as e:
            try:
                os.mkdir(dirname)
            except Exception as e:
                print("Could not create song dir!")
                sys.print_exception(e)
                self.error = True
                break

        try:
            req = urequests.get(self.current_song[0] + self.current_song[1])
            if req.status_code != 200:
                raise Exception(req.status_code)
            file_name = f"{dirname}/{self.current_song[1]}"
            total_size = int(req.headers["Content-Length"])
            
            if os.path.exists(file_name):
                stat = os.stat(file_name)
                if stat[6] == total_size:
                    req.close()
                    self.file_progress = 1.0
                    continue
            
            rec_size = 0
            with open(file_name, "wb") as f:
                try:
                    while True:
                        new_data = req.raw.read(1024 * 32)
                        rec_size += len(new_data)
                        self.file_progress = rec_size / total_size
                        f.write(new_data)
                        if self.cancel:
                            raise Exception("Cancelled")
                        if not new_data:
                            break
                except Exception as e:
                    os.unlink(file_name)
                    raise e
                finally:
                    req.close()
        except Exception as e:
            sys.print_exception(e)
            self.error = True
            break
    if not self.error:
        try:
            if self.app:
                self.app.select = select.SelectView(self.app)
        except Exception as e:
            sys.print_exception(e)
        self.finished = True
    download_lock.release()

class DownloadView(BaseView):
    def __init__(self, app, songs):
        super().__init__()
        self.songs = songs
        self.app = app
        self.flowers = [flower.Flower((0.0002 + random.random() * 0.0008) * (-1 if random.random() > 0.5 else 1),
                                      random.random() * 240 - 120, 
                                      random.random() * 160 - 120,
                                      0.1 + random.random() * 0.2) for i in range(24)]
        self._scroll_pos = 0
        self.led_timeout = 1000
        self.progress = 0
        self.file_progress = 0
        self.file_no = 0
        self.error = False
        self.cancel = False
        self.finished = False
        
        self.file_list = []
        for song in self.songs:
            prefix = f'{utils.SONGS_REPO}/-/raw/{song["branch"]}/'
            for f in ["song.mp3", "notes.mid", "song.ini", "COPYING"]:
                self.file_list.append((prefix, f, song["artist"], song["title"]))
            
        self.files_total = len(self.file_list)
        self.current_song = None
        self.time = 0

    def draw(self, ctx: Context) -> None:
        
        utils.clear(ctx)
        
        if self.error:
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.font = "Camp Font 3"
            ctx.font_size = 28
            ctx.gray(1.0)
            ctx.move_to(0, 0)
            ctx.text("Download failed.")
            return

        ctx.save()
        utils.fire_gradient(ctx)
        for flower in self.flowers:
            flower.draw(ctx)
        ctx.restore()
        
        ctx.linear_gradient(0, 0, 0, 120)

        ctx.add_stop(0.0, (0, 0, 0), 0.0)
        ctx.add_stop(0.2, (0, 0, 0), 1.0)

        ctx.rectangle(-120, -60, 240, 120)
        ctx.fill()
        
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font = "Camp Font 3"
        ctx.font_size = 32
        utils.fire_gradient(ctx)
        ctx.move_to(0, 20)
        ctx.text("Downloading..." if not self.finished else "All done!")
        
        if self.current_song and not self.finished:
            song_name = self.current_song[3]
            song_artist = self.current_song[2]
        
            ctx.font_size = 18
            while ctx.text_width(song_name) > 180:
                ctx.font_size -= 1
            ctx.move_to (0, 69)
            ctx.gray(1.0)
            ctx.text(song_name)

            name_size = ctx.font_size
            while ctx.text_width(song_artist) > 180:
                ctx.font_size -= 1
            ctx.move_to (0, -name_size * 1.1 + 69)
            ctx.gray(0.75)
            ctx.text(song_artist)

        if not self.finished:
            ctx.gray(0.5)
            ctx.font_size = 18
            ctx.move_to(0, 95)
            ctx.text(f"File {self.file_no} of {self.files_total}")
        
        ctx.rgba(1.0, 1.0, 1.0, 0.5)
        ctx.font = "Material Icons"
        ctx.font_size = 120
        ctx.move_to(0, -20)
        ctx.text("\ue2c4")
        
        ctx.save()
        ctx.gray(1.0)
        ctx.rectangle(-120, -96, 240, int(86 * self.file_progress))
        ctx.clip()
        ctx.move_to(0, -20)
        ctx.text("\ue2c4")
        ctx.restore()
        
        ctx.gray(0.2)
        ctx.font_size = 12
        ctx.font = "Camp Font 3"
        ctx.move_to(0, -60)
        ctx.text(str(int(self.file_progress * 100)) + "%")
        
        if self.finished:
            ctx.font_size = 18
            ctx.move_to (0, 46)
            ctx.gray(0.8)
            ctx.text("Successfully fetched")
            ctx.move_to (0, 65)
            ctx.text(f"and saved {len(self.songs)} songs.")

            ctx.font_size = 16
            ctx.gray(0.5)
            ctx.move_to(0, 88 - math.sin(self.time * 4) * 2)
            ctx.text("Press the button...")

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        self.time += delta_ms / 1000

        for flower in self.flowers:
            flower.y += (delta_ms / 16) * abs(flower.rot_speed) / 0.001
            if flower.y > 40:
                flower.x = random.random() * 240 - 120
                flower.y = -150
                flower.scale = 0.1 + random.random() * 0.2
                flower.rot_speed = (0.0002 + random.random() * 0.0008) * (-1 if random.random() > 0.5 else 1)
            flower.think(delta_ms)

        if self.files_total:
            self.progress = ((self.file_no - 1) // 4) / (self.files_total // 4) + (self.file_progress if self.file_no % 4 == 1 else 1.0) / (self.files_total // 4)
            if self.file_no == 0:
                self.progress = 0
        else:
            self.progress = 1.0
        if self.progress < 0:
            self.progress = 0
            
        if not self.is_active():
            return
            
        self.led_timeout -= delta_ms
        if self.led_timeout < 0:
            leds.set_slew_rate(32)
            st3m.ui.led_patterns.pretty_pattern()
            for i in range(round(self.progress * 40), 40):
                leds.set_rgb(i, 0, 0, 0)
            leds.update()
            self.led_timeout = 500
            
        if self.error:
            leds.set_slew_rate(255)
            leds.set_all_rgb(0, 0, 0)
            leds.update()
            
        utils.blm_timeout(self, delta_ms)

        self._scroll_pos += delta_ms / 1000
        
        if self.finished and self.input.buttons.app.middle.pressed and self.app:
            utils.play_go(self.app)
            self.vm.replace(self.app.select, ViewTransitionBlend())

    def on_enter(self, vm):
        super().on_enter(vm)
        leds.set_slew_rate(255)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        leds.set_gamma(1.0, 1.0, 1.0)
        leds.set_brightness(st3m.settings.num_leds_brightness.value)

        _thread.start_new_thread(download_thread, (self,))

    def on_exit(self):
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            utils.play_back(self.app)
        if not self.error:
            self.cancel = True
        leds.set_slew_rate(255)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        # wait for the thread to exit
        download_lock.acquire(1)
        download_lock.release()
        st3m.wifi.disable()
        return True

#if not __path__:
#    st3m.wifi.setup_wifi()
#    while not st3m.wifi.is_connected():
#        time.sleep(1)
#    req = urequests.get(f'{utils.SONGS_REPO}/-/raw/main/index.json')
#    st3m.run.run_view(DownloadView(None, req.json()['songs']))

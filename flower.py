class Flower:
    def __init__(self, rot_speed: float) -> None:
        self.rot = 0.0
        self.rot_speed = rot_speed

    def think(self, delta_ms: float) -> None:
        self.rot += float(delta_ms) * self.rot_speed

    def draw(self, ctx: Context, fill: bool = True) -> None:
        ctx.save()
        ctx.rotate(self.rot)
        ctx.translate(-74, -74)
        ctx.move_to(76.221727, 3.9788409).curve_to(
            94.027758, 31.627675, 91.038918, 37.561293, 94.653428, 48.340473
        ).rel_curve_to(
            25.783102, -3.90214, 30.783332, -1.52811, 47.230192, 4.252451
        ).rel_curve_to(
            -11.30184, 19.609496, -21.35729, 20.701768, -35.31018, 32.087063
        ).rel_curve_to(
            5.56219, 12.080061, 12.91196, 25.953973, 9.98735, 45.917643
        ).rel_curve_to(
            -19.768963, -4.59388, -22.879866, -10.12216, -40.896842, -23.93099
        ).rel_curve_to(
            -11.463256, 10.23025, -17.377386, 18.2378, -41.515124, 25.03533
        ).rel_curve_to(
            0.05756, -29.49286, 4.71903, -31.931936, 10.342734, -46.700913
        ).curve_to(
            33.174997, 77.048676, 19.482194, 71.413009, 8.8631648, 52.420793
        ).curve_to(
            27.471602, 45.126773, 38.877997, 45.9184, 56.349456, 48.518302
        ).curve_to(
            59.03275, 31.351935, 64.893201, 16.103886, 76.221727, 3.9788409
        ).close_path();
        if fill:
            ctx.fill()
        else:
            ctx.stroke()
        ctx.restore()

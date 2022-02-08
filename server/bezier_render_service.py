import os
import multiprocessing
import potrace
import numpy as np
import cv2


def get_trace(data):
    for row in data:
        row[row > 1] = 1
    bmp = potrace.Bitmap(data)
    path = bmp.trace(2, potrace.TURNPOLICY_MINORITY, 1.0, 1, .5)
    return path


class BezierRenderService:
    def __init__(self):
        self.config = None
        self.frame = multiprocessing.Value('i', 0)
        self.height = multiprocessing.Value('i', 0, lock = False)
        self.width = multiprocessing.Value('i', 0, lock = False)
        self.frame_latex = []

    def get_expressions(self, frame):
        exprid = 0
        exprs = []
        for expr in self._get_latex(f"/frame{frame+1}.{self.config.FILE_EXT}"):
            exprid += 1
            exprs.append({'id': 'expr-' + str(exprid), 'latex': expr, 'color': self.config.COLOUR, 'secret': True})
        return exprs

    def get_block(self, frame):
        num_frames = self.get_total_frames()
        if frame >= num_frames:
            return None

        block = []
        if not self.config.DYNAMIC_BLOCK:
            number_of_frames = min(frame + self.config.BLOCK_SIZE, num_frames) - frame
            for i in range(frame, frame + number_of_frames):
                block.append(self.frame_latex[i])
        else:
            number_of_frames = 0
            total = 0
            i = frame
            while total < self.config.MAX_EXPR_PER_BLOCK:
                if i >= len(self.frame_latex):
                    break
                number_of_frames += 1
                total += len(self.frame_latex[i])
                block.append(self.frame_latex[i])
                i += 1
        return block, number_of_frames

    def get_total_frames(self):
        return len(os.listdir(self.config.FRAME_DIR))

    def _get_latex(self, filename):
        latex = []
        path = get_trace(self._get_contours(filename))

        for curve in path.curves:
            segments = curve.segments
            start = curve.start_point
            for segment in segments:
                x0, y0 = start
                if segment.is_corner:
                    x1, y1 = segment.c
                    x2, y2 = segment.end_point
                    latex.append(f'((1-t){x0}+t{x1},(1-t){y0}+t{y1})')
                    latex.append(f'((1-t){x1}+t{x2},(1-t){y1}+t{y2})')
                else:
                    x1, y1 = segment.c1
                    x2, y2 = segment.c2
                    x3, y3 = segment.end_point
                    latex.append(
                        f'((1-t)((1-t)((1-t){x0}+t{x1})+t((1-t){x1}+t{x2}))+t((1-t)((1-t){x1}+t{x2})+t((1-t){x2}+t{x3})),\
                        (1-t)((1-t)((1-t){y0}+t{y1})+t((1-t){y1}+t{y2}))+t((1-t)((1-t){y1}+t{y2})+t((1-t){y2}+t{y3})))'
                    )
                start = segment.end_point
        return latex

    def _get_contours(self, filename, nudge = .33):
        image = cv2.imread(filename)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.config.BILATERAL_FILTER:
            median = max(10, min(245, np.median(gray)))
            lower = int(max(0, (1 - nudge) * median))
            upper = int(min(255, (1 + nudge) * median))
            filtered = cv2.bilateralFilter(gray, 5, 50, 50)
            edged = cv2.Canny(filtered, lower, upper, L2gradient = self.config.USE_L2_GRADIENT)
        else:
            edged = cv2.Canny(gray, 30, 200)

        with self.frame.get_lock():
            self.frame.value += 1
            self.height.value = max(self.height.value, image.shape[0])
            self.width.value = max(self.width.value, image.shape[1])
        print(f'\r--> Frame {self.frame.value}/{self.get_total_frames()}', end='')

        return edged[::-1]

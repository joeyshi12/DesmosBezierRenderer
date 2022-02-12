import os
import multiprocessing
import numpy as np
import cv2
import util


class BezierRenderService:
    def __init__(self):
        self.config = None
        self.num_frames = 0
        self.frame_latex = []
        self.frame = multiprocessing.Value('i', 0)
        self.height = multiprocessing.Value('i', 0, lock = False)
        self.width = multiprocessing.Value('i', 0, lock = False)

    def set_config(self, config):
        self.config = config
        self.num_frames = len(os.listdir(self.config.FRAME_DIR))

    def init_frame_latex(self, pool):
        self.frame_latex = pool.map(self.__get_expressions, range(self.num_frames))

    def get_block(self, frame):
        if not self.config or frame >= self.num_frames:
            return None

        block = []
        if not self.config.DYNAMIC_BLOCK:
            number_of_frames = min(frame + self.config.BLOCK_SIZE, self.num_frames) - frame
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

    def __get_expressions(self, frame):
        exprid = 0
        exprs = []
        filename = f"/frame{frame+1}.{self.config.FILE_EXT}"
        for expr in self.__get_latex(filename):
            exprid += 1
            exprs.append({'id': 'expr-' + str(exprid), 'latex': expr, 'color': self.config.COLOUR, 'secret': True})
        return exprs

    def __get_latex(self, filename):
        latex = []
        path = util.get_trace(self.__get_contours(filename))

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

    def __get_contours(self, filename, nudge = .33):
        assert self.config
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
        print(f'\r--> Frame {self.frame.value}/{self.num_frames}', end='')

        return edged[::-1]

import sys
import multiprocessing
from time import time
import json

from flask import Flask, request
from flask_cors import CORS
import cv2

import util
from bezier_render_service import BezierRenderService


app = Flask(__name__)
CORS(app)
service = BezierRenderService()


@app.route("/")
def index():
    frame = int(request.args.get("frame"))
    block, number_of_frames = service.get_block(frame)
    if not block:
        return {"result": block}
    return json.dumps({"result": block, "number_of_frames": number_of_frames}) # Number_of_frames is the number of newly loaded frames, not the total frames


@app.route("/init")
def init():
    return json.dumps({
        "height": service.height.value,
        "width": service.width.value,
        "total_frames": service.num_frames,
        "download_images": service.config.DOWNLOAD_IMAGES,
        "show_grid": service.config.SHOW_GRID
    })


def main():
    service.set_config(util.get_config())
    with multiprocessing.Pool(processes = multiprocessing.cpu_count()) as pool:
        util.print_start_message(service.num_frames)
        start = time()

        try:
            service.init_frame_latex(pool)
        except cv2.error:
            util.print_error_message()
            sys.exit(2)

        print(f"\r--> Processing complete in {(time() - start):.1f} seconds\n")
        # with open("cache.json", "w+") as f:
        #     json.dump(frame_latex, f)
        app.run()


if __name__ == "__main__":
    main()

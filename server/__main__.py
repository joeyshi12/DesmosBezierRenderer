import sys
import traceback
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
    num_frames = service.get_total_frames()
    if frame >= num_frames:
        return {"result": None}

    block = []
    if not service.config.DYNAMIC_BLOCK:
        number_of_frames = min(frame + service.config.BLOCK_SIZE, num_frames) - frame
        for i in range(frame, frame + number_of_frames):
            block.append(service.frame_latex[i])
    else:
        number_of_frames = 0
        total = 0
        i = frame
        while total < service.config.MAX_EXPR_PER_BLOCK:
            if i >= len(service.frame_latex):
                break
            number_of_frames += 1
            total += len(service.frame_latex[i])
            block.append(service.frame_latex[i])
            i += 1
    return json.dumps({"result": block, "number_of_frames": number_of_frames}) # Number_of_frames is the number of newly loaded frames, not the total frames


@app.route("/init")
def init():
    return json.dumps({
        "height": service.height.value,
        "width": service.width.value,
        "total_frames": service.get_total_frames(),
        "download_images": service.config.DOWNLOAD_IMAGES,
        "show_grid": service.config.SHOW_GRID
    })



def main():
    service.config = util.get_config()
    num_frames = service.get_total_frames()

    with multiprocessing.Pool(processes = multiprocessing.cpu_count()) as pool:
        print("Desmos Bezier Renderer")
        print("Junferno 2021")
        print("https://github.com/kevinjycui/DesmosBezierRenderer")
        print("-----------------------------")
        print(f"Processing {num_frames} frames... Please wait for processing to finish before running on frontend\n")

        start = time()

        try:
            service.frame_latex = pool.map(service.get_expressions, range(num_frames))
        except cv2.error:
            print("[ERROR] Unable to process one or more files. \
                  Remember image files should be named <DIRECTORY>/frame<INDEX>.<EXTENSION> \
                  where INDEX represents the frame number starting from 1 and DIRECTORY and EXTENSION are defined by command line arguments (e.g. frames/frame1.png). \
                  Please check if: \
                  \n\tThe files exist \
                  \n\tThe files are all valid image files \
                  \n\tThe name of the files given is correct as per command line arguments \
                  \n\tThe program has the necessary permissions to read the file. \
                  \n\nUse backend.py -h for further documentation\n")
            print("-----------------------------")
            print("Full error traceback:\n")
            traceback.print_exc()
            sys.exit(2)

        print(f"\r--> Processing complete in {(time() - start):.1f} seconds\n")

        # with open("cache.json", "w+") as f:
        #     json.dump(frame_latex, f)

        app.run()


if __name__ == "__main__":
    main()

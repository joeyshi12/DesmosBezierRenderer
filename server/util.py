import sys
import getopt
from dataclasses import dataclass
import potrace
import traceback


@dataclass
class Config:
    DYNAMIC_BLOCK: bool = True # Automatically find the right block size
    BLOCK_SIZE: int = 25 # Number of frames per block (ignored if DYNAMIC_BLOCK is true)
    MAX_EXPR_PER_BLOCK: int = 7500 # Maximum lines per block, doesn't affect lines per frame (ignored if DYNAMIC_BLOCK is false)

    FRAME_DIR: str = 'frames' # The folder where the frames are stored relative to this file
    FILE_EXT: str = 'png' # Extension for frame files
    COLOUR: str = '#2464b4' # Hex value of colour for graph output

    BILATERAL_FILTER: bool = False # Reduce number of lines with bilateral filter
    DOWNLOAD_IMAGES: bool = False # Download each rendered frame automatically (works best in firefox)
    USE_L2_GRADIENT: bool = False # Creates less edges but is still accurate (leads to faster renders)
    SHOW_GRID: bool = True # Show the grid in the background while rendering


def get_config():
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hf:e:c:bdlg", ['static', 'block=', 'maxpblock='])
    except getopt.GetoptError:
        print('Error: Invalid argument(s)\n')
        print_help_message()

    config = Config()
    try:
        for opt, arg in opts:
            if opt == '-h':
                print_help_message()
                sys.exit()
            elif opt == '-f':
                config.FRAME_DIR = arg
            elif opt == '-e':
                config.FILE_EXT = arg
            elif opt == '-c':
                config.COLOUR = arg
            elif opt == '-b':
                config.BILATERAL_FILTER = True
            elif opt == '-d':
                config.DOWNLOAD_IMAGES = True
            elif opt == '-l':
                config.USE_L2_GRADIENT = True
            elif opt == '-g':
                config.SHOW_GRID = False
            elif opt == '--static':
                config.DYNAMIC_BLOCK = False
            elif opt == '--block':
                config.BLOCK_SIZE = int(arg)
            elif opt == '--maxpblock':
                config.MAX_EXPR_PER_BLOCK = int(arg)
    except TypeError:
        print('Error: Invalid argument(s)\n')
        print_help_message()
        sys.exit(2)
    return config

def get_trace(data):
    for row in data:
        row[row > 1] = 1
    bmp = potrace.Bitmap(data)
    path = bmp.trace(2, potrace.TURNPOLICY_MINORITY, 1.0, 1, .5)
    return path

def print_help_message():
    print('backend.py -f <source> -e <extension> -c <colour> -b -d -l -g --static --block=<block size> --maxpblock=<max expressions per block>\n')
    print('\t-h\tGet help\n')
    print('-Render options\n')
    print('\t-f <source>\tThe directory from which the frames are stored (e.g. frames)')
    print('\t-e <extension>\tThe extension of the frame files (e.g. png)')
    print('\t-c <colour>\tThe colour of the lines to be drawn (e.g. #2464b4)')
    print('\t-b\t\tReduce number of lines with bilateral filter for simpler renders')
    print('\t-d\t\tDownload rendered frames automatically')
    print('\t-l\t\tReduce number of lines with L2 gradient for quicker renders')
    print('\t-g\t\tHide the grid in the background of the graph\n')
    print('-Optimisational options\n')
    print('\t--static\t\t\t\t\tUse a static number of expressions per request block')
    print('\t--block=<block size>\t\t\t\tThe number of frames per block in dynamic blocks')
    print('\t--maxpblock=<maximum expressions per block>\tThe maximum number of expressions per block in static blocks')

def print_start_message(num_frames):
    print("Desmos Bezier Renderer")
    print("Junferno 2021")
    print("https://github.com/kevinjycui/DesmosBezierRenderer")
    print("-----------------------------")
    print(f"Processing {num_frames} frames... Please wait for processing to finish before running on frontend\n")

def print_error_message():
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

import sys
import getopt
from dataclasses import dataclass


@dataclass
class Config:
    DYNAMIC_BLOCK = True # Automatically find the right block size
    BLOCK_SIZE = 25 # Number of frames per block (ignored if DYNAMIC_BLOCK is true)
    MAX_EXPR_PER_BLOCK = 7500 # Maximum lines per block, doesn't affect lines per frame (ignored if DYNAMIC_BLOCK is false)

    FRAME_DIR = 'frames' # The folder where the frames are stored relative to this file
    FILE_EXT = 'png' # Extension for frame files
    COLOUR = '#2464b4' # Hex value of colour for graph output

    BILATERAL_FILTER = False # Reduce number of lines with bilateral filter
    DOWNLOAD_IMAGES = False # Download each rendered frame automatically (works best in firefox)
    USE_L2_GRADIENT = False # Creates less edges but is still accurate (leads to faster renders)
    SHOW_GRID = True # Show the grid in the background while rendering


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

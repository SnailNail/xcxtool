import colorama
from plumbum import cli, colors
from plumbum.cli import terminal

#colorama.init()
colors.use_color = 3


class MyCommand(cli.Application):
    PROGNAME = colors.fg[179]
    VERSION = "0.1.0"
    verbose = cli.Flag(["-v", "--verbose"], help="Enable maximum verbiage")

    def main(self, *args):
        print(terminal.get_terminal_size())


if __name__ == '__main__':
    MyCommand.run()

"""Monitor Cemu process for changes"""

from plumbum import cli

from xcxtools.monitor import monitor
from xcxtools import memory_reader


class MonitorCemu(cli.Application):
    """Monitor Cemu process memory for changes"""

    def main(self):
        incs = [range(205952, 233736)]  # first big unknown block
        excs = [
            range(0x0, 0xC620),  # Character & skell data
            range(0xC820, 0xC82C),  # Miranium, credits, tickets
            range(0xC850, 0x32228),  # Inventory,
            range(0x39108, 0x39168),  # BLADE greetings
            range(0x39174, 0x39180),  # BLADE level, points, division
            range(0x39540, 0x45D68),  # BLADE Affinity characters, BLADE medals, save time
            range(0x45D71, 0x45E18),  # Fast travel mysteries
            range(0x45E40, 0x45E44),  # Play time
            range(0x480C0, 0x48274),  # FrontierNav layout
            range(0x48AC8, 0x48ACB),  # Field skill levels
        ]
        reader = memory_reader.connect_cemu()
        if reader is None:
            exit(1)
        comp = monitor.Comparator(reader, exclude=excs)
        # comp.monitor_and_record(aggregate_runs=False)
        comp.monitor()
        reader.close()

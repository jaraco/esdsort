"""
/*                                ESDSORT.py                              *
 *   This program takes a result file from an ElectroStatic Discharge     *
 * evaluation and compiles the information into four different files that *
 * are more useful and understandable.  Detailed documentation is located *
 * in a file called ESDSORT.DOC.                                          *
 *                   copyright Signetics  1992                            *
 *                    written by Jason Coombs                             */
"""

import sys
import ctypes
import itertools
import functools

FAIL = 0
PASS = 1
MAXLINE = 100
MAXPARTS = 3000
MAXVOLTAGES = 10
EOF = -1

FF = 12
"""Character for form feed"""

MAXNAME = 17
"""Maximum length for process and design names"""

buf = ''

OUTPUT_FILENAME = "esdsort.dat"

banner = """

                 ESD data file sorting utility
                    written by Jason Coombs
                   Copyright Signetics  1992

"""


class Type:
    icc = 0
    ipd = 0
    inph = 0
    inpl = 0
    iodh = 0
    iodl = 0
    iozh = 0
    iozl = 0
    odh = 0
    odl = 0
    ozh = 0
    ozl = 0
    cont = 0


class Part:
    sn = 0
    voltage = 0
    pass_ = chr(0)
    sr = chr(0)
    resval = 0
    design = chr(0)
    process = chr(0)

    def __init__(self):
        self.processname = ctypes.create_string_buffer(MAXNAME)
        self.designname = ctypes.create_string_buffer(MAXNAME)
        self.failtype = Type()

    @classmethod
    def from_line(cls, inline, statfile):
        part = cls()
        part._read_voltage(inline)
        part._read_sn(inline)
        part._read_failcode(inline, statfile)
        part._read_938(inline)
        part._read_fail(inline)
        return part

    def _read_voltage(self, inline):
        position = textfind(inline, "@")
        if position == EOF:
            return
        val, _, _ = inline[position + 1].partition(' ')
        self.voltage = self._parse_voltage(val)

    @staticmethod
    def _parse_voltage(val):
        val = val.upper()
        base = int(val.strip('K'))
        multiplier = 1000 if val.endswith('K') else 1
        return base * multiplier

    def _read_sn(self, inline):
        position = textfind(inline, "S/N")
        if position == EOF:
            return
        position = position + 6
        self.sr = 'N'
        self.failtype.icc = \
            self.failtype.ipd = \
            self.failtype.inph = \
            self.failtype.inpl = \
            self.failtype.iodh = \
            self.failtype.iodl = \
            self.failtype.iozh = \
            self.failtype.iozl = \
            self.failtype.odh = \
            self.failtype.odl = \
            self.failtype.ozh = \
            self.failtype.ozl = \
            self.failtype.cont = 0
        self.pass_ = 'Y'

        if inline[position] == ' ':
            if inline[position + 1] == ' ':
                position = position + 2
            else:
                position = position + 1

        self.sn = int(inline[position:position+4])

        if ser2pro(self.sn) is not None:
            self.processname = \
                ser2pro(self.sn)
            self.process = self.processname[0]
        else:
            self.processname = "P Process"
            self.process = 'P'

    def _read_failcode(self, inline, statfile):
        if textfind(inline, "   ****") == EOF:
            return
        self.pass_ = 'N'
        failcode = int(inline[3:6])
        if failcode == 860 or failcode == 881:
            self.failtype.icc += 1
        elif failcode == 790 or failcode == 813:
            self.failtype.ipd += 1
        elif failcode == 524:
            self.failtype.inph += 1
        elif failcode == 544:
            self.failtype.inpl += 1
        elif failcode == 615:
            self.failtype.iodh += 1
        elif failcode == 634:
            self.failtype.iodl += 1
        elif failcode == 574:
            self.failtype.iozh += 1
        elif failcode == 593:
            self.failtype.iozl += 1
        elif failcode == 697:
            self.failtype.odh += 1
        elif failcode == 716:
            self.failtype.odl += 1
        elif failcode == 656:
            self.failtype.ozh += 1
        elif failcode == 675:
            self.failtype.ozl += 1
        elif failcode == 315:
            self.failtype.cont += 1
        elif failcode == 938:
            print("Identity fail.  Check status file", OUTPUT_FILENAME)
            print(
                "Identity fail on sn%d" % self.sn,
                file=statfile)
            print(
                "Zapped at %d volts\n" % self.voltage,
                file=statfile)
        else:
            print("Error!!!  Undefined fail code %d." % failcode)

    def _read_938(self, inline):
        if self.failcode != 938:
            return
        self.resval = int(inline[14:17])
        if res2des(self.resval) is not None:
            self.designname = \
                res2des(self.resval)
            self.design = self.designname[0]
        else:
            self.designname = "D Design"
            self.design = 'D'

    def _read_fail(self, inline):
        if textfind(inline, "FAIL") == 20:
            self.pass_ = 'N'
            self.sr = 'Y'
        else:
            self.sr = 'N'


def main(argv):

    propage = ''
    despage = ''

    position = 0
    count = 0
    i = 0
    e = 0
    save = 0
    paglen = 0
    newdes = 0
    voltages = [None] * MAXVOLTAGES
    total = [None] * 30
    fails = [None] * 30

    # files
    resultfile = None

    print(banner)
    truncate(OUTPUT_FILENAME)

    part = count_parts(argv)
    part_count = len(part)

    if part_count <= 0:
        return

    print("Total parts: %d" % part_count)

    #              Make Result Files                   #

    try:
        resultfile = open("results.fails", "w")
    except Exception:
        print(
            "\nCannot open output file as %s." % "results.fails",
            file=sys.stderr,
        )
        sys.exit(1)

    header = \
        "SN     P  SR  ICC  IPD  INPH INPL IODH IODL IOZH IOZL ODH ODL OZH OZL CONT"
    print("\nCreating result files.")
    pagelen = save = 0

    position = 1
    while position <= part_count:
        if part[position].voltage != part[save].voltage:
            save = position
            propage = 'A'

        while propage < 'M':
            despage = 'A'

            for i in range(part_count):
                if part[i].voltage == part[save].voltage and \
                        part[i].process == propage:
                    while despage < 'M':
                        newdes = 'Y'
                        for e in range(part_count):

                            if paglen > 60 or pagelen == 0:
                                print(
                                    "%c\n%dV\n%s" %
                                    (FF, part[save].voltage, header),
                                    file=resultfile,
                                )
                                for count in range(76):
                                    print('=', end='', file=resultfile)
                                print(
                                    "\n%s" % part[i].processname,
                                    file=resultfile,
                                )
                                paglen = 6
                            if (
                                part[e].voltage == part[save].voltage and
                                part[e].process == propage and
                                part[e].design == despage
                            ):
                                if newdes == 'Y':
                                    print(file=resultfile)
                                    paglen += 1
                                    newdes = 'N'
                                pagelen += 1
                            print(
                                "%c %4d %c  %c" % (
                                    part[e].design, part[e].sn,
                                    part[e].pass_, part[e].sr,
                                    ),
                                end='',
                                file=resultfile,
                            )
                            if part[e].failtype.icc > 0:
                                print(
                                    "   %d" % part[e].failtype.icc,
                                    file=resultfile,
                                    end='',
                                )
                            else:
                                print("    ", file=resultfile, end='')
                            if part[e].failtype.ipd > 0:
                                print(
                                    "    %d" % part[e].failtype.ipd,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.inph > 0:
                                print(
                                    "    %d" % part[e].failtype.inph,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.inpl > 0:
                                print(
                                    "    %d" % part[e].failtype.inpl,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.iodh > 0:
                                print(
                                    "    %d" % part[e].failtype.iodh,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.iodl > 0:
                                print(
                                    "    %d" % part[e].failtype.iodl,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.iozh > 0:
                                print(
                                    "    %d" % part[e].failtype.iozh,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.iozl > 0:
                                print(
                                    "    %d" % part[e].failtype.iozl,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.odh > 0:
                                print(
                                    "    %d" % part[e].failtype.odh,
                                    file=resultfile,
                                )
                            else:
                                print("     ", file=resultfile, end='')
                            if part[e].failtype.odl > 0:
                                print(
                                    "   %d" % part[e].failtype.odl,
                                    file=resultfile,
                                )
                            else:
                                print("    ", file=resultfile, end='')
                            if part[e].failtype.ozh > 0:
                                print(
                                    "   %d" % part[e].failtype.ozh,
                                    file=resultfile,
                                )
                            else:
                                print("    ", file=resultfile, end='')
                            if part[e].failtype.ozl > 0:
                                print(
                                    "   %d" % part[e].failtype.ozl,
                                    file=resultfile,
                                )
                            else:
                                print("    ", file=resultfile, end='')
                            if part[e].failtype.cont > 0:
                                print(
                                    "     %d" % part[e].failtype.cont,
                                    file=resultfile,
                                )
                            else:
                                print("    \n", file=resultfile, end='')
                        despage += 1

            paglen = 0
            propage += 1
        position += 1
    resultfile.close()

    position = 1
    while position <= part_count:
        for count in range(MAXVOLTAGES):
            if part[position].voltage == voltages[count]:
                break
            if voltages[count] == 0:
                voltages[count] = part[position].voltage
                break
        position += 1

    try:
        resultfile = open("results.proc", "w")
    except Exception:
        resultfile = None
    if resultfile is None:
        print(
            "\nCannot open output file %s." % "results.proc",
            file=sys.stderr,
            end='',
        )
        sys.exit(1)

    propage = 'A'
    while propage < 'M':
        paglen = 0
        despage = 'A'
        while despage < 'M':
            count = 1
            while count <= part_count:
                position = 0
                while voltages[position] != 0:
                    total[position] = fails[position] = 0
                    if (
                        part[count].process == propage
                        and part[count].design == despage
                    ):
                        if paglen == 0 or paglen > 60:
                            paglen = 6
                            print(
                                "%c\nPROCESS %s\n           DESIGN    " %
                                (FF, part[count].processname),
                                file=resultfile,
                                end='',
                            )
                            i = 0
                            while voltages[i] != 0:
                                print(
                                    "%3.1fKV  " % voltages[i]/1000,
                                    file=resultfile,
                                    end='',
                                )
                                i += 1
                            print(file=resultfile)
                            for i in range(76):
                                print('=', file=resultfile, end='')
                            print("\n", file=resultfile)

                        e = 1
                        while e < part_count:
                            if (
                                part[e].process == propage
                                and part[e].design == despage
                                and part[e].voltage == voltages[position]
                            ):
                                total[position] += 1
                                if part[e].pass_ == 'N':
                                    fails[position] += 1
                            e += 1
                    position += 1
                if (
                    part[count].design == despage
                    and part[count].process == propage
                ):

                    print(
                        "%17s    " % part[count].designname,
                        file=resultfile,
                        end='',
                    )
                    position = 0
                    while voltages[position] != 0:
                        if total[position] != 0:
                            print(
                                "%2d/%2d  " %
                                (fails[position], total[position]),
                                file=resultfile,
                                end='',
                            )
                        else:
                            print("       ", file=resultfile, end='')
                        position += 1
                    print(file=resultfile)
                    for i in range(76):
                        print("_", file=resultfile, end='')
                    print("\n", file=resultfile)
                    paglen = paglen + 3
                    break
                count += 1
            despage = chr(ord(despage) + 1)
        propage = chr(ord(propage) + 1)
    resultfile.close()

    try:
        resultfile = open("results.volt", "w")
    except Exception:
        resultfile = None

    if resultfile is None:
        print(
            "\nCannot open output file %s." % "results.volt",
            file=sys.stderr,
            end='',
        )
        sys.exit(1)

    position = 0
    while voltages[position] != 0:
        paglen = 0
        despage = 'A'
        while despage < 'M':
            count = 1
            while count <= part_count:
                propage = 'A'
                while propage < 'M':
                    total[propage - ord('A')] = fails[propage - ord('A')] = 0
                    if (
                        part[count].voltage == voltages[position]
                        and part[count].design == despage
                    ):
                        if paglen == 0 or paglen > 60:
                            paglen = 6

                            print(
                                "%c\nVOLTAGE %4d\t\t\tPROCESS\n           DESIGN   " %
                                (FF, voltages[position]),
                                file=resultfile,
                                end='',
                            )
                            i = 'A'
                            while i < 'M':
                                if i == 'L':
                                    print(
                                        i,
                                        file=resultfile,
                                        end='',
                                    )
                                else:
                                    print(
                                        "%c       " % i,
                                        file=resultfile,
                                        end='',
                                    )
                                i = chr(ord(i) + 2)
                            print(
                                "\n                 ",
                                file=resultfile,
                                end='',
                            )
                            i = 'B'
                            while i < 'N':
                                print(
                                    "       %c" % i,
                                    file=resultfile,
                                    end='',
                                )
                                i = chr(ord(i) + 2)
                            print(file=resultfile)
                            for i in range(76):
                                print("=", file=resultfile, end="")
                            print("\n", file=resultfile)

                        e = 1
                        while e <= part_count:
                            if (
                                part[e].process == propage
                                and part[e].design == despage
                                and part[e].voltage == voltages[position]
                            ):
                                total[propage-ord('A')] += 1
                                if part[e].pass_ == 'N':
                                    fails[propage-ord('A')] += 1
                            e += 1
                    propage = chr(ord(propage) + 1)
                if (
                    part[count].design == despage
                    and part[count].voltage == voltages[position]
                ):

                    print(
                        "%17s   " % part[count].designname,
                        file=resultfile,
                        end='',
                    )
                    propage = 'A'
                    while propage < 'M':
                        if total[propage-ord('A')] != 0:
                            print(
                                "%2d/%2d   " % (
                                    fails[propage-ord('A')],
                                    total[propage-ord('A')],
                                ),
                                file=resultfile,
                                end='',
                            )
                        else:
                            print("        ", file=resultfile, end='')
                        propage = chr(ord(propage) + 2)

                    print(
                        "\n                        ",
                        file=resultfile,
                        end="",
                    )
                    propage = 'B'
                    while propage < 'N':
                        if total[propage-ord('A')] != 0:
                            print(
                                "%2d/%2d   " % (
                                    fails[propage-ord('A')],
                                    total[propage-ord('A')],
                                ),
                                file=resultfile,
                                end='',
                            )
                        else:
                            print("        ", file=resultfile, end="")
                        propage = chr(ord(propage) + 2)
                    print(file=resultfile)
                    for i in range(76):
                        print("_", file=resultfile, end="")
                    print("\n", file=resultfile)
                    paglen = paglen + 3
                    break
                count += 1
            despage = chr(ord(despage) + 1)
        position += 1
    resultfile.close()


def count_parts(argv):
    parts = []

    if len(argv) == 1:
        print(
            "Please re-enter command line with the name "
            "of the file to be sorted.",
            file=sys.stderr)
        return parts

    for filename in argv[1:]:
        try:
            infile = open(filename)
        except Exception:
            print(
                "Can't open %s.\nPlease check path and filename."
                % filename,
                file=sys.stderr)
            sys.exit(1)

        print("Processing file %s\n" % filename)
        try:
            statfile = open(OUTPUT_FILENAME, "a")
        except Exception:
            print(
                "Cannot open output file %s." % OUTPUT_FILENAME,
                file=sys.stderr)
            sys.exit(1)

        for inline in infile:
            part = Part.from_line(inline, statfile)
            parts.append(part)

        print("Sorting successful!\n")
        infile.close()
        statfile.close()

    return parts


def filecopy(infile):
    while True:
        c = infile.read(1)
        if not c:
            break
        sys.stdout.write(c, flush=True)


def textfind(line, text):
    """
    Search for text in line
    """
    i = 0
    n = 0
    status = 0

    while line[i] != '\n':
        if line[i] == text[n]:
            for n in range(len(text)):
                if line[i+n] != text[n]:
                    status = FAIL
                    break
                else:
                    status = PASS
            if status == PASS:
                return i + 1
            else:
                i += 1
                n = 0
        else:
            i += 1
    return EOF


def get_digits(s):
    """
    Return all digits appearing at the beginning of s
    """
    def is_digit(char):
        return char.isdigit()

    return itertools.takewhile(is_digit, s)


def ord_zero(digit):
    """
    Return the ordinal of the given digit.

    >>> ord_zero('1')
    1
    """
    return ord(digit) - ord('0')


def ten_x(a, b):
    return a*10 + b


def atoi(s):
    """
    Convert list of characters s to integer value
    """
    digits = get_digits(s)
    ordinals = map(ord_zero, digits)
    return functools.reduce(ten_x, ordinals, 0)


def ser2pro(sn):
    global buf
    try:
        init = open("PROCESS.DAT", "r")
    except Exception:
        init = None

    if init is not None:
        while True:
            inline = init.read(MAXLINE)
            if not inline:
                break
            if inline[0] < '0' or inline[0] > '9':
                continue
            counter = atoi(inline)
            for i in range(counter):
                low = atoi(inline[2 + (10*i):])
                high = atoi(inline[7 + (10*i):])
                if sn >= low and sn <= high:
                    buf = inline[2 + (10*counter):]

        for i in range(MAXNAME):
            if buf[i] == '\n':
                buf = buf[:i]
                break

        init.close()
        return buf

    init.close()
    return None


def res2des(resval):
    global buf
    try:
        init = open("DESIGN.DAT", "r")
    except Exception:
        init = None

    if init is not None:
        while True:
            inline = init.read(MAXLINE)
            if not inline:
                break
            if inline[0] < '0' or inline[0] > '9':
                continue
            counter = atoi(inline)
            for i in range(counter):
                low = atoi(inline[2 + (10*i):])
                high = atoi(inline[7 + (10*i):])
                if resval >= low and resval <= high:
                    buf = inline[2 + (10*counter):]

        for i in range(MAXNAME):
            if buf[i] == '\n':
                buf = buf[:i]
                break

        init.close()
        return buf

    init.close()
    return None


def truncate(filename):
    """
    Unconditionally ensure the named file exists and is truncated.
    """
    open(filename, 'w').close()


if __name__ == '__main__':
    main(sys.argv)

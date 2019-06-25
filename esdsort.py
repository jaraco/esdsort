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


def main(argc, argv):
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

    part = [Part() for _ in range(MAXPARTS)]

    tempstring = []
    propage = ''
    despage = ''

    position = 0
    part_count = 0
    count = 0
    failcode = 0
    i = 0
    e = 0
    save = 0
    paglen = 0
    newdes = 0
    voltages = [None] * MAXVOLTAGES
    total = [None] * 30
    fails = [None] * 30

    # files
    infile = statfile = resultfile = None

    print("\n\n                 ESD data file sorting utility")
    print("                    written by Jason Coombs")
    print("                   Copyright Signetics  1992\n\n")

    try:
        open("esdsort.dat", 'w')
    except Exception:
        pass

    if argc == 1:
        print(
            "Please re-enter command line with the name "
            "of the file to be sorted.",
            file=sys.stderr)
    else:
        while True:
            argc -= 1
            if argc == 0:
                break
            argv = argv[1:]
            try:
                infile = open(argv[0])
            except Exception:
                print(
                    "Can't open %s.\nPlease check path and filename."
                    % argv[0],
                    file=sys.stderr)
                sys.exit(1)
            else:
                print("Processing file %s\n" % argv)
                try:
                    statfile = open("esdsort.dat", "a")
                except Exception:
                    print(
                        "Cannot open output file %s." % "esdsort.dat",
                        file=sys.stderr)
                    sys.exit(1)
                else:
                    while True:
                        inline = infile.read(MAXLINE)
                        if not inline:
                            break
                        position = textfind(inline, "@")
                        if position != EOF:
                            position += 1
                            count = 0
                            while inline[position + count] != ' ':
                                tempstring[count:count+1] = inline[position + count]
                                count += 1
                            tempstring[count:count+1] = '\x00'
                            part[part_count].voltage = atoi(tempstring)
                            if tempstring[1].upper() == 'K':
                                part[part_count].voltage = part[part_count].voltage * 1000

                        position = textfind(inline, "S/N")
                        if position != EOF:
                            position = position + 6
                            part_count += 1
                            part[part_count].sr = 'N'
                            part[part_count].failtype.icc = \
                                part[part_count].failtype.ipd = \
                                part[part_count].failtype.inph = \
                                part[part_count].failtype.inpl = \
                                part[part_count].failtype.iodh = \
                                part[part_count].failtype.iodl = \
                                part[part_count].failtype.iozh = \
                                part[part_count].failtype.iozl = \
                                part[part_count].failtype.odh = \
                                part[part_count].failtype.odl = \
                                part[part_count].failtype.ozh = \
                                part[part_count].failtype.ozl = \
                                part[part_count].failtype.cont = 0
                            part[part_count].pass_ = 'Y'

                            if inline[position] == ' ':
                                if inline[position+1] == ' ':
                                    position = position + 2
                                else:
                                    position = position + 1

                            count = 0
                            while count < 4:
                                tempstring[count:count+1] = inline[position + count]
                                count += 1

                            tempstring[count:count+1] = '\x00'
                            part[part_count].sn = atoi(tempstring)
                            if ser2pro(part[part_count].sn) is not None:
                                part[part_count].processname = \
                                    ser2pro(part[part_count].sn)
                                part[part_count].process = part[part_count].processname[0]
                            else:
                                part[part_count].processname = "P Process"
                                part[part_count].process = 'P'

                        if textfind(inline, "   ****") != EOF:
                            part[part_count].pass_ = 'N'
                            count = 0
                            while count < 3:
                                tempstring[count:count+1] = inline[count + 3]
                                count += 1
                            tempstring[count:count+1] = '\x00'
                            failcode = atoi(tempstring)
                            if failcode == 860 or failcode == 881:
                                part[part_count].failtype.icc += 1
                            elif failcode == 790 or failcode == 813:
                                part[part_count].failtype.ipd += 1
                            elif failcode == 524:
                                part[part_count].failtype.inph += 1
                            elif failcode == 544:
                                part[part_count].failtype.inpl += 1
                            elif failcode == 615:
                                part[part_count].failtype.iodh += 1
                            elif failcode == 634:
                                part[part_count].failtype.iodl += 1
                            elif failcode == 574:
                                part[part_count].failtype.iozh += 1
                            elif failcode == 593:
                                part[part_count].failtype.iozl += 1
                            elif failcode == 697:
                                part[part_count].failtype.odh += 1
                            elif failcode == 716:
                                part[part_count].failtype.odl += 1
                            elif failcode == 656:
                                part[part_count].failtype.ozh += 1
                            elif failcode == 675:
                                part[part_count].failtype.ozl += 1
                            elif failcode == 315:
                                part[part_count].failtype.cont += 1
                            elif failcode == 938:
                                print("Identity fail.  Check status file esdsort.dat")
                                print(
                                    "Identity fail on sn%d" % part[part_count].sn,
                                    file=statfile)
                                print(
                                    "Zapped at %d volts\n" % part[part_count].voltage,
                                    file=statfile)
                            else:
                                print("Error!!!  Undefined fail code %d." % failcode)

                        if textfind(inline, "938") == 4:
                            count = 0
                            while count < 3:
                                tempstring[count:count+1] = inline[14 + count]
                                count += 1
                            tempstring[count:count+1] = '\x00'
                            part[part_count].resval = atoi(tempstring)
                            if res2des(part[part_count].resval) is not None:
                                part[part_count].designname = \
                                    res2des(part[part_count].resval)
                                part[part_count].design = part[part_count].designname[0]
                            else:
                                part[part_count].designname = "D Design"
                                part[part_count].design = 'D'

                        if textfind(inline, "FAIL") == 20:
                            part[part_count].pass_ = 'N'
                            part[part_count].sr = 'Y'
                        else:
                            part[part_count].sr = 'N'

            print("Sorting successful!\n")
            infile.close()
            statfile.close()

    if part_count > 0:
        print("Total parts: %d" % part_count)

        #              Make Result Files                   #

        try:
            resultfile = open("results.fails", "w")
        except Exception:
            resultfile = None
        if resultfile is None:
            print(
                "\nCannot open output file as %s." % "results.fails",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
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
        else:
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
        else:
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


def atoi(s):
    """
    Convert list of characters s to integer value
    """
    n = 0
    i = 0

    while s[i] >= '0' and s[i] <= '9':
        n = 10*n + ord(s[i]) - ord('0')
        i += 1

    return n


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


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)

# Verilog_Formatter
By Dr. Liu, refined by Tianhao Li, Zhuoqian Li

## basic information for code

    filename:      verilog_format.py
    description:   format verilog file
    author:        liusheng

### revision List:

    (rn: date : modifier: description)
    r1: 2021.09.08 liusheng create it
    r2: 2021.09.10 liusheng add the declaration align role.
    r3: 2021.10.03 lizhuoqian add the config format
    r4: 2021.10.03 litianhao add the conf/prim/spcfy/table judge code
    r5: 2021.10.10 litianhao add the table formatter, but need to fix
    r6: 2021.10.17 litianhao add the blank format to keep two blank lines only
                        and debug for last code
    r7: 2021.11.08 litianhao add the assign align and format of assign's formula
                        and debug for code of table module
    r8: 2022.03.31 litianhao optimize the details of formatter

### work to be done:

    0) add the config/primitive/specify/table judge code   (need to check)
    1) multi blank lines only keep two blank lines         (need to check)
    2) assign align
    3) inst align
    4) translate Chinese into English
#!/usr/bin/python
# company:       nudt-wdzs-671
# filename:      verilog_format.py
# description:   format verilog file
# author:        liusheng
# revision List:
# (rn: date : modifier: description)
# r1: 2021.09.08 liusheng create it
# r2: 2021.09.10 liusheng add the declaration align role.
# r3: 2021.10.03 lizhuoqian add the config format
# r4: 2021.10.03 litianhao add the conf/prim/spcfy/table judge code
# r5: 2021.10.10 litianhao add the table formatter, but need to fix
# r6: 2021.10.17 litianhao add the blank format to keep two blank lines only
#                      and debug for last code
# r7: 2021.11.08 litianhao add the assign align and format of assign's formula
#                      and debug for code of table module
# work to be done:
# 0) add the config/primitive/specify/table judge code
# 1) multi blank lines only keep two blank lines
# 2) assign align
# 3) inst align
# 4) translate chinese into english

import sys
import re
import os


# RTL modole Judging
def rtl_has(string, key):
    if (string.find(" " + key + " ") != -1):  # 0: ##_key_##
        return True
    if (string.find(" " + key + "(") != -1):  # 1: ##_key(##
        return True
    if (string.find(" " + key + ":") != -1):  # 2: ##_key:##
        return True
    elif (string.find(")" + key + " ") != -1):  # 3: ##)key_##
        return True
    elif (string.find(")" + key + ":") != -1):  # 4: ##)key:##
        return True
    elif (string.find(" " + key + "(") != -1):  # 5: ##_key(##
        return True
    # elif (string.find(":" + key + ' ') != -1):  # new: ##:key_##
    #     return True
    elif (string.startswith(key + ' ')):  # 6: key_###
        return True
    elif (string.startswith(key + '(')):  # 7: key(###
        return True
    elif (string.startswith(key + ':')):  # 8: key:###
        return True
    elif (string.endswith(' ' + key)):  # 9: ###_key
        return True
    elif (string.endswith(')' + key)):  # 10: ###)key
        return True
    elif (string.endswith(':' + key)):  # new: ###:key
        return True
    elif (string.startswith(key) and string.endswith(key)):  # 11: key###key
        return True
    else:
        return False


def rtl_real_has(string, key1, key2):
    if (rtl_has(string, key1)):
        if (not rtl_has(string, key2)):
            return True
        else:
            return False
    return False


def rtl_just_has(string, key):
    if (string.find(key) != -1):
        return True
    else:
        return False

# To find the mapping of {} or if/endif or [] or so on....

def rtl_real_just_has(string, key1, key2):
    if (rtl_just_has(string, key1)):
        if (not rtl_just_has(string, key2)):
            return True
        else:
            return False
    return False


# To get the comment and delete it
def del_comment(type, string):
    if (type == 0):  # 0:no comment
        return string + " "
    elif (type == 1):  # 1:all comment
        return '' + " "
    elif (type == 2):  # 2:#####//
        num = string.find('//')
        temp1 = string[0:num]
        return temp1 + " "
    elif (type == 3):  # 3:#####/*
        num = string.find('/*')
        temp1 = string[0:num]
        return temp1 + " "
    elif (type == 4):  # 4:*/#####
        num = string.rfind('*/')
        temp1 = string[num + 2:]
        return temp1 + " "
    elif (type == 5):  # 5:####/*...*/#####
        num1 = string.find('/*')
        num2 = string.rfind('*/')
        temp1 = string[0:num1] + " " + string[num2 + 2:]
        return temp1 + " "
    else:
        return " "


# To change the format to the Standard Form
def line_format(type, string):
    if (type != 1 and (type != 2)):
        string = re.sub(': ', ':', string)
        string = re.sub(' :', ':', string)
        string = re.sub(' ;', ';', string)
        string = re.sub(' ,', ',', string)
    if (type == 0):  # 0:no comment
        temp1 = string.replace('\t', ' ')
        temp2 = ' '.join(temp1.split())
        temp2.lstrip()
        return temp2
    elif (type == 1):  # 1:all comment
        temp1 = string[0:-1]
        temp2 = ' '.join(temp1.split())
        temp2.lstrip()
        temp2 = "  " + temp2
        return temp2
    elif (type == 2):  # 2:#####//
        num = string.find('//')
        temp1 = string[0:num]
        temp2 = temp1.replace('\t', ' ')
        temp2 = ' '.join(temp1.split())
        temp2.lstrip()
        return temp2 + string[num:-1]
    elif (type == 3):  # 3:#####/*
        num = string.find('/*')
        temp1 = string[0:num]
        temp2 = temp1.replace('\t', ' ')
        temp2 = ' '.join(temp1.split())
        temp2.lstrip()
        return temp2 + string[num:-1]
    elif (type == 4):  # 4:*/#####
        num = string.rfind('/*')
        temp1 = string[num + 2:]
        temp2 = temp1.replace('\t', ' ')
        temp2 = ' '.join(temp1.split())
        temp2.lstrip()
        temp3 = string[0:num + 2]
        temp3.lstrip()
        return temp3 + temp2
    elif (type == 5):  # 5:####/*...*/#####
        num1 = string.find('/*')
        num2 = string.rfind('*/')
        temp1 = string[0:num1]
        temp2 = string[num2 + 2:]
        temp3 = temp1.replace('\t', ' ')
        temp3 = ' '.join(temp3.split())
        temp3.lstrip()
        temp4 = temp2.replace('\t', ' ')
        temp4 = ' '.join(temp4.split())
        temp4.lstrip()
        return temp3 + string[num1:num2 + 2] + temp4
    else:
        return ""


# To get same align for input / inout / ...
def declare_align(string):
    can_align = 0
    pos1 = 0
    pos2 = 0
    list0 = ['input[', 'output[', 'inout[', 'wire[', 'reg[', 'logic[', 'bit[']
    list1 = ['input', 'output', 'inout', 'rand']
    list2 = ['wire', 'reg', 'logic', 'bit']
    for x in list0 + list1 + list2:
        if (string.startswith(x)):
            string = re.sub('\[', ' [', string)
            string = re.sub(' ;', ';', string)
            string = re.sub(' ,', ',', string)
    temp1 = string.split()
    if (len(temp1) > 0):
        # eg: reg [35:0]     araddr
        if (temp1[0] in list2):
            pos0 = 5
            pos1 = 15
            pos2 = 40
            can_align = 1
    if (len(temp1) > 1):
        # eg: input [35:0]   addr;
        if ((temp1[0] in list1) and (not (temp1[1] in list2))):
            pos0 = 7
            pos1 = 17
            pos2 = 40
            can_align = 2
        # eg: output reg [5:0]     id;
        if ((temp1[0] in list1) and ((temp1[1] in list2))):
            pos0 = 12
            pos1 = 22
            pos2 = 40
            can_align = 3
    # print 	pos1
    # print 	pos2
    # print  can_align
    # print  temp1
    if (can_align == 1 or can_align == 2 or can_align == 3):
        string = re.sub(']', '] ', string)
        string = re.sub(' ]', ']', string)
        string = re.sub('\[ ', '[', string)

        temp1 = string.split()
        if (can_align == 1):
            string = ''
        else:
            string = '' + (temp1[0])
            string = string.ljust(7, ' ')
            temp1 = temp1[1:]
        if (temp1[0] in list2):
            string = string + (temp1[0])
            temp1 = temp1[1:]
        if (str(temp1[0]).startswith('[')):
            string = string.ljust(pos0, ' ')
            string = string + (temp1[0])
            temp1 = temp1[1:]
        if (len(string)) < pos1:
            string = string.ljust(pos1, ' ')
        temp1 = ' '.join(temp1)
        temp1 = temp1.split('//')
        if (len(temp1) == 1):
            string = string + ''.join(temp1)
            return string
        else:
            string = string + temp1[0]
            if (len(string)) < pos2:
                string = string.ljust(pos2, ' ')
            temp1 = temp1[1:]
            string = string + '//' + '//'.join(temp1)
            return string
    else:
        return string
    
# Assign align

def is_signal(string):
    signal = -1
    list2 = ["<=", "=="]
    list1 = ["=", "+", "-", "*", "/", "&", "|", "!", "?", ":"]
    list0 = ["(", ")", "[", "]", "{", "}"]
    if string[0:2] in list2:
        signal = string[0:2]
    elif string[0] in list1:
        signal = string[0]
    elif string[0] in list0:
        signal = string[0]
    else:
        if string[0].isalnum() or string[0] == "_":
            signal = -1
    return signal
        

def assign_align(string):
    can_align = 0
    pos1, pos2 = 0, 0
    list0 = ["assign"]
    bracket = ["(", ")", "{", "}", "[", "]"]
    temp = string.split()
    if len(temp) == 0:
        return string
    if not (temp[0] in list0):
        return string
    NoBlankString = "".join(temp[1:])
    # print(NoBlankString)
    putpos = []
    BlankString = ""
    range_list = list(range(len(NoBlankString)))
    InMiddleBracket = False
    for i in range_list:
        signal = is_signal(NoBlankString[i:])
        
        if signal != -1:
            if not (signal in bracket):
                if not InMiddleBracket:
                    BlankString += " " + signal + " "
            else:
                BlankString += signal
                if signal == "[":
                    InMiddleBracket = True
                elif signal == "]":
                    InMiddleBracket = False
                    
            if len(signal) > 1:
                for j in range(len(signal) - 1):
                    range_list.remove(i + j)
                    
        else:
            BlankString += NoBlankString[i]
    return temp[0] + " " + BlankString
    # return string

# config's formatter
# just for small portion of all codes...
def config_format(string): 
	pos0 = 0;
	pos1 = 0;
	list0 = ['design', 'default', 'instance']
	for x in list0:
		if(string.startswith(x)):					
			string=re.sub(' ;',';',string)
			string=re.sub(' ,',',',string)
	temp = string.split()
	if(len(temp) > 0):
		if(temp[0] == list0[0]):
			string = temp[0].ljust(7, ' ')
			string = string + temp[1]
		elif(temp[0] == list0[1]):
			string = temp[0].ljust(8, ' ')
			string = string + temp[1].ljust(8, ' ')
			temp = ' '.join(temp)
			string = string + temp
		elif(temp[0] == list0[2]):
			string = temp[0].ljust(9, ' ')
			string = string + temp[1].ljust(15, ' ')
			string = string + temp[2].ljust(8, ' ')
			temp = ' '.join(temp)
			string = string + temp

# need to fix...
def get_data_length(line):
    temp1 = line.split()
    input_number = len(temp1) - 1
    data_length = []
    pos1 = 0
    pos2 = 0
    pos_colon = 0
    line = re.sub('\\*\\', '', line)
    for i in range(len(line)):
        if line[i] == ':':
            pos_colon = i
        if i != 0:
            if line[i - 1] == ' ' and line[i] != ' ':
                pos1 = i
            if line[i - 1] != ' ' and line[i] == ' ':
                data_length.append(pos1 - pos2 + (i - pos1) / 2)
                pos2 = i - 1
    return input_number, data_length

# make table keep one ' ' between 0/1/:
def table_formatter(line):
    temp1 = line.split(' ')
    temp2 = []
    for temp in temp1:
        if temp != ":" and temp.find(":") != -1:
            poscolon = temp.find(":")
            if poscolon != 0:
                temp2.append(temp[0: poscolon])
            temp2.append(":")
            if poscolon != len(temp) - 1:
                temp2.append(temp[poscolon + 1: ])
        else:
            temp2.append(temp)
    line = ' '.join(temp2)
    # print(line)
    return line

# To judge if all the line only has blank words
def Judge_Blank(line):
    for word in line:
        if word != ' ' and word != '\t' and word != '\n':
            # print(word, file=fileout)
            return 0
    return 1

#### main ###########################################################################################


if (sys.argv[1] == '-h'):
    print('This tool can format verilog file.')
    print('please type "verilog_format.py name.v", it will geneate the formatted name.v')
    print('please type "verilog_format.py old_name.v new_name.v", it will geneate the formatted new_name.v')
    print('The author of this sofware is liusheng from NUDTWDZS, China.')
    sys.exit()

filepath = sys.argv[1]

os.system("dos2unix -q %s" % filepath)

filein = open(filepath, "r")
if (len(sys.argv) == 2):
    output_file = sys.argv[1]
elif (len(sys.argv) == 3):
    output_file = sys.argv[2]
else:
    print("not support!")
fileout = open(".123.v", "w")

line = filein.readline()
grade = 0
line1 = ""
line2 = ""
lastline = ""
llastline = ""
comment_keep = 0
comment_type = 0
table_keep = 0
delt1 = 0
delt2 = 0
blank_keep = 0
# 0: no comment
# 1: all comment
# 2: #####//
# 3: #####/*
# 4: */#####
# 5: ####/*...*/####

while line:
    
    if (line.find("//") != -1):
        comment_type = 2
    if ((line.find("/*") != -1) and (line.find("*/") == -1)):
        comment_keep = 1
        comment_type = 3
    elif ((line.find("*/") != -1) and (line.find("/*") == -1)):
        comment_keep = 0
        comment_type = 4
    elif ((line.find("*/") != -1) and (line.find("/*") != -1)):
        comment_keep = 0
        comment_type = 5
    elif (comment_keep == 1):
        comment_type = 1

    # print comment_type

    line1 = line_format(comment_type, line)
    # print ('line1    :', line1, file=fileout)
    line2 = del_comment(comment_type, line)
    # print ('line2 - 1:', line2, file=fileout)
    line2 = line_format(comment_type, line2)
    # print ('line2 - 2:', line2, file=fileout)
    # print(line2 + "  --line2", file = fileout)
    if table_keep:
        # if line1.find('//'):
        #     Input_number, Data_length = get_data_length(line1) # Get from the comment
        # else:
        #     line1 = table_formatter(line1, Input_number, Data_length) # the table format
        #     print ('line1    ', line1, " --after modify", file=fileout)
        line1 = table_formatter(line1) # the table format
        # print ('line1    ', line1, " --after modify")
    
    if (rtl_real_has(line2, 'end', 'begin')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endmodule', 'module')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endfunction', 'function')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endtask', 'task')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endgenerate', 'generate')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endspecify', 'specify')):  # new
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endconfig', 'config')):  # new
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endtable', 'table')):  # new
        grade -= 1
        delt1 = 0
        delt2 = 0
        table_keep = 0
    elif (rtl_real_has(line2, 'endprimitive', 'primitive')):  # new
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'join', 'fork')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, '`else', '`endif')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif ((rtl_real_has(line2, '`endif', '`ifdef'))
          or rtl_real_has(line2, '`endif', '`ifndef')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif ((rtl_real_has(line2, 'endcase', 'case'))
          or rtl_real_has(line2, 'endcase', 'casez')
          or rtl_real_has(line2, 'endcase', 'casex')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_has(line2, 'endclass', 'class')):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_real_just_has(line2, '}', '{') and line2.startswith("}")):
        grade -= 1
        delt1 = 0
        delt2 = 0
    elif (rtl_has(line2, 'if')):
        delt2 = 0
    elif (rtl_has(line2, 'else')):
        delt1 = 0
    else:
        line1 = declare_align(line1)
        line1 = assign_align(line1)

    # new
    Can_Be_Print = 1
    if Judge_Blank(line1):
        if blank_keep >= 2:
            Can_Be_Print = 0
        blank_keep += 1
    else:
        Can_Be_Print = 1
        blank_keep = 0
    
    # print ('line1: ', line1, file=fileout)
    if Can_Be_Print: # new
        print(((" " * (grade + delt1 + delt2) * 4) + line1), file=fileout)
    # print >> fileout, " " * (grade + delt1 + delt2) * 4 + line1
    # print >> fileout, str(grade + delt1 + delt2) + " " * (grade + delt1 + delt2) * 4 + line1
    delt1 = 0
    delt2 = 0

    if (rtl_real_has(line2, 'begin', 'end')):
        # print('lalala', file = fileout)
        grade += 1
    elif (rtl_real_has(line2, 'module', 'endmodule')):
        grade += 1
    elif (rtl_real_has(line2, 'function', 'endfunction')):
        grade += 1
    elif (rtl_real_has(line2, 'task', 'endtask')):
        grade += 1
    elif (rtl_real_has(line2, 'generate', 'endgenerate')):
        grade += 1
    elif (rtl_real_has(line2, 'specify', 'endspecify')):  # new
        grade += 1
    elif (rtl_real_has(line2, 'config', 'endconfig')):  # new
        grade += 1
    elif (rtl_real_has(line2, 'table', 'endtable')):  # new
        grade += 1
        table_keep = 1
    elif (rtl_real_has(line2, 'primitive', 'endprimitive')):  # new
        grade += 1
    elif (rtl_real_has(line2, 'fork', 'join')):
        grade += 1
    elif (rtl_real_has(line2, '`ifdef', '`endif')):
        grade += 1
    elif (rtl_real_has(line2, '`ifndef', '`endif')):
        grade += 1
    elif (rtl_real_has(line2, '`else', '`endif')):
        grade += 1
    elif (rtl_real_has(line2, 'case', 'endcase')):
        grade += 1
    elif (rtl_real_has(line2, 'casez', 'endcase')):
        grade += 1
    elif (rtl_real_has(line2, 'casex', 'endcase')):
        grade += 1
    elif (rtl_real_has(line2, 'class', 'endclass')):
        grade += 1
    elif (rtl_real_just_has(line2, '{', '}')):
        grade += 1
    elif (rtl_real_just_has(line2, '}', '{') and (not line2.startswith('}'))):
        grade -= 1
    elif (rtl_has(line2, 'if') and (not line2.endswith(';'))):
        delt1 = 1
    elif (line2.endswith('else') and not (line2.endswith(';'))):
        delt2 = 1

    line = filein.readline()
    comment_type = 0

fileout.close()
filein.close()
os.system("cp -rf .123.v %s" % str(output_file))
os.system("rm -rf .123.v ")

#### main ###########################################################################################

import os, re, sys
from string import Template


def convert_header(contents):
    """Convert of vtt header to srt format
       Keyword arguments:
       contents
       """
    replacement = re.sub(r"WEBVTT\n", "", contents)
    replacement = re.sub(r"Kind:[ \-\w]+\n", "", replacement)
    replacement = re.sub(r"Language:[ \-\w]+\n", "", replacement)
    return replacement


def padding_timestamp(contents):
    """Add 00 to padding timestamp of to srt format
       Keyword arguments:
       contents
       """
    find_srt = Template(r'$a,$b --> $a,$b(?:[ \-\w]+:[\w\%\d:,.]+)*\n')
    minute = r"((?:\d\d:){1}\d\d)"
    second = r"((?:\d\d:){0}\d\d)"
    padding_minute = find_srt.substitute(a=minute, b=r"(\d{0,3})")
    padding_second = find_srt.substitute(a=second, b=r"(\d{0,3})")
    replacement = re.sub(padding_minute, r"00:\1,\2 --> 00:\3,\4\n", contents)
    return re.sub(padding_second, r"00:00:\1,\2 --> 00:00:\3,\4\n", replacement)


def convert_timestamp(contents):
    """Convert timestamp of vtt file to srt format
       Keyword arguments:
       contents
       """
    find_vtt = Template(r'$a.$b --> $a.$b(?:[ \-\w]+:[\w\%\d:,.]+)*\n')
    all_timestamp = find_vtt.substitute(a=r"((?:\d\d:){0,2}\d\d)", b=r"(\d{0,3})")
    return padding_timestamp(re.sub(all_timestamp, r"\1,\2 --> \3,\4\n", contents))

def timestamp_line(content):
    """Check if line is a timestamp srt format
       Keyword arguments:
       contents
       """
    return re.match(r"((\d\d:){2}\d\d),(\d{3}) --> ((\d\d:){2}\d\d),(\d{3})", content) is not None


def add_sequence_numbers(contents):
    """Adds sequence numbers to subtitle contents and returns new subtitle contents
       Keyword arguments:
       contents
       """
    output = ''
    lines = contents.split(os.linesep)

    i = 1
    for line in lines:
        if timestamp_line(line):
            output += str(i) + os.linesep
            i += 1
        output += line + os.linesep
    return output

def convert_content(contents):
    """Convert content of vtt file to srt format
       Keyword arguments:
       contents
       """
    replacement = convert_timestamp(contents)
    replacement = convert_header(replacement)
    replacement = re.sub(r"<c[.\w\d]*>", "", replacement)
    replacement = re.sub(r"</c>", "", replacement)
    replacement = re.sub(r"<\d\d:\d\d:\d\d.\d\d\d>", "", replacement)
    replacement = re.sub(r"::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n", "", replacement)
    replacement = re.sub(r"Style:\n##\n", "", replacement)
    replacement = add_sequence_numbers(replacement)
    return replacement
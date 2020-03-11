import datetime
from datetime import datetime, timedelta, timezone
import dateutil.parser

import pytz
from pytz import timezone

def markdown(job_id, job_backtrace):
    lines = []
    time = ''
    
    for event in job_backtrace:
        operation = event.get('operation')
        
        if operation == 'initialize':
            time = get_time(event)
            date = get_date(event)
            lines.append("## Job {} on {}".format(job_id, date))
#             lines.append("## {}: Started protocol".format(time))
            lines.append("<hr>\n")
            
        elif operation == 'next':
            # The time of the next event
            time = get_time(event)
            continue
            
        elif operation == 'display':
            lines.append("### {}".format(time))
            lines += format_display(event)
            lines.append("<hr>\n")
            
        elif operation == 'complete':
            lines.append("## {}: Completed protocol".format(time))

        else:
            raise "Unrecognized operation {}".format(operation)
        
    return '\n'.join(lines)
            
def format_display(event):
    lines = []
    
    for obj in event.get('content'):
        
        if not len(obj) == 1:
            raise "Unexpected content remaining in {}".format(str(obj))
            
        method = list(obj.keys())[0]
        content = obj[method]
        
        if method == 'title':
            lines.append("## " + content)
            
        elif method == 'check':
            lines.append("&#9745;&nbsp;" + content)
            lines.append("\n")
            
        elif method == 'note':
            lines.append(content)
            lines.append("\n")
            
        elif method == 'warning':
            style = "background-color: yellow"
            lines.append("<span style=\"{}\">{}</span>".format(style, content))
            lines.append("\n")

        elif method == 'table':
            lines += format_table(content)
            lines.append("\n")

        elif method == 'separator':
            lines.append("{}\n".format("—"*20))
            lines.append("\n")

        elif method == 'take':
            lines.append("{} ({}) from {}\n".format(
                content['id'],
                content['sample'],
                content['location']
            ))
            lines.append("\n")

        else:
            lines.append("{}: {}".format(method, content))
            lines.append("\n")
            
    return lines

def format_table(ary):
    formatted = ["<table>"]
    style = "border: 1px solid gray; text-align: center"
    for row in ary:
        newrow = ""
        for cell in row:
            this_style = style

            if isinstance(cell, dict):
                newcell = cell.get("content") or "?"
                checkable = cell.get("check")
                if cell.get("class") == "td-filled-slot" or checkable:
                    this_style = style + "; background-color: lightskyblue"

            else:
                newcell = cell

            newrow += "<td style=\"{}\">{}</td>".format(this_style, newcell)
        formatted.append("<tr>{}</tr>".format(newrow))

    formatted.append("</table>\n")
    return formatted

def get_pacific_datetime(event, tz_name='US/Pacific'):
    ts = dateutil.parser.parse(event.get('time'))
    return ts.astimezone(pytz.timezone(tz_name))

def get_time(event):
    ts = get_pacific_datetime(event)
    return ts.strftime("%-H:%M %p")

def get_date(event):
    ts = get_pacific_datetime(event)
    return ts.strftime("%m/%d/%Y")
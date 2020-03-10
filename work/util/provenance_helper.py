import sys
import json
import pprint
import re

import datetime
from datetime import datetime, timedelta, timezone
import dateutil.parser

import pytz
from pytz import timezone

from IPython.display import display, Markdown, Latex

from pydent import AqSession, __version__
    
def get_session():
    with open('secrets.json', 'r') as f:
        secrets = json.load(f)
    
    aq_session = AqSession(
        secrets.get('username'),
        secrets.get('password'),
        secrets.get('url')
    )

    msg = "Connected to Aquarium at {} using pydent version {}"
    print(msg.format(aq_session.url, str(__version__)))

    me = aq_session.User.where({'login': secrets.get('username')})[0]
    print('Logged in as {}\n'.format(me.name))
    
    return aq_session

def get_provenance(aq_session, plan_ids):
    sys.path.append("/home/jupyter/tacc-work/lib/aquarium-provenance/src")
    from aquarium.trace.factory import TraceFactory
    from aquarium.trace.patch import create_patch_visitor
    
    plans = aq_session.Plan.where({"id": plan_ids})
    
    visitor = create_patch_visitor()

    trace = TraceFactory.create_from(
        session=aq_session,
        plans=plans,
        visitor=visitor,
        experiment_id=''
    )

    print("{} Operations found for Plans {}".format(len(trace.operations), ', '.join([str(i) for i in plan_ids])))
    
    return [plans, trace]

def jobs_for(operation_type_name, trace):
    return [j for j in trace.get_jobs() if j.operation_type.name == operation_type_name]
    
def list_methods(obj):
    print("Methods available in {}".format(obj.__class__.__name__))
    for d in dir(obj):
        if not d.startswith('_'):
            print(d)
            
def get_backtrace(job_id, aq_session):
    return aq_session.Job.find(job_id).state

def get_pacific_datetime(event, tz_name='US/Pacific'):
    ts = dateutil.parser.parse(event.get('time'))
    return ts.astimezone(pytz.timezone(tz_name))

def get_time(event):
    ts = get_pacific_datetime(event)
    return ts.strftime("%-H:%M %p")

def get_date(event):
    ts = get_pacific_datetime(event)
    return ts.strftime("%m/%d/%Y")

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
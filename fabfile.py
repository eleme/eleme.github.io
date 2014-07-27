#!/usr/bin/env python

import datetime


def new():
    filename = raw_input('Filename: ')
    filename = filename.replace(' ', '-')
    author = raw_input('Author: ')
    now = datetime.datetime.now()
    filepath = '_posts/%s-%s.md' % (now.strftime('%Y-%m-%d'), filename)

    with open(filepath, 'wb') as f:
        f.write('---\n')
        f.write('layout: post\n')
        f.write('title: %s\n' % filename)
        f.write('author: %s\n' % author)
        f.write('---\n')

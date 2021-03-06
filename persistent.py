#! /usr/bin/python2
# vim: set fileencoding=utf-8
import cPickle as pickle


def save_var(filename, d):
    print 'persistent.py/save_var'
    with open(filename, 'wb') as f:
        pickle.dump(d, f, 2)


def load_var(filename):
    print 'persistent.py/load_var'
    try:
        with open(filename, 'rb') as f:
            d = pickle.load(f)
    except IOError:
        raise
    return d

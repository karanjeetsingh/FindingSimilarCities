#! /usr/bin/python2
# vim: set fileencoding=utf-8


# from https://stackoverflow.com/a/1336821
class Chunker(object):
    """Split `iterable` on evenly sized chunks.
    Leftovers are yielded at the end.
    """
    def __init__(self, chunksize):
        #print 'Chunker.py/Chunker/__init__'
        assert chunksize > 0
        self.chunksize = chunksize
        self.chunk = []

    def __call__(self, iterable):
        """Yield items from `iterable` `self.chunksize` at the time."""
        #print 'Chunker.py/Chunker/__call__'
        assert len(self.chunk) < self.chunksize
        for item in iterable:
            self.chunk.append(item)
            if len(self.chunk) == self.chunksize:
                yield self.chunk
                self.chunk = []

        if len(self.chunk) > 0:
            yield self.chunk

if __name__ == '__main__':
    print 'Chunker.py/__main__'
    chunker = Chunker(3)
    res = [''.join(chunk) for chunk in chunker('abcdefghij')]
    assert res == ['abc', 'def', 'ghi', 'j']

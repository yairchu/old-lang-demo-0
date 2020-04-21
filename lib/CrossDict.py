class CrossDict(object):
    def __init__(self):
        self.dict = {}
        self.cross = {}
    def __getitem__(self, key):
        return self.dict[key]
    def __delitem__(self, key):
        val = self[key]
        del self.dict[key]
        cross = self.cross[val]
        cross.remove(key)
        if not cross:
            del self.cross[val]
    def __setitem__(self, key, val):
        if key in self:
            del self[key]
        self.dict[key] = val
        if val not in self.cross:
            self.cross[val] = set()
        self.cross[val].add(key)
    def __contains__(self, key):
        return key in self.dict
    def refs(self, val):
        if val not in self.cross:
            return set()
        return self.cross[val]
    def iteritems(self):
        return self.dict.iteritems()

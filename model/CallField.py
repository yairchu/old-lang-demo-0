class CallField(object):
    """Association of a class call with one of its input/output"""
    def __init__(self, call, field):
        self.call = call
        self.field = field
    def __str__(self):
        return self.field.label
    def __repr__(self):
        return '%s.%s' % (self.call, self.field)
    def __hash__(self):
        return hash((self.call, self.field))
    def __cmp__(self, other):
        return cmp(type(self), type(other)) or cmp((self.call, self.field), (other.call, other.field))
    def is_input(self, cls):
        return self.can_be_dst()
    def is_output(self, cls):
        return self.can_be_src()
    def can_be_dst(self):
        return self.field.is_input(self.call.cls)
    def can_be_src(self):
        return self.field.is_output(self.call.cls)


from functools import total_ordering

@total_ordering
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
    def __lt__(self, other):
        if type(self) < type(other):
            return True
        if type(self) > type(other):
            return False
        return (self.call, self.field) < (other.call, other.field)
    def __eq__(self, other):
        return type(self) == type(other) and (self.call, self.field) == (other.call, other.field)
    def is_input(self, cls):
        return self.can_be_dst()
    def is_output(self, cls):
        return self.can_be_src()
    def can_be_dst(self):
        return self.field.is_input(self.call.cls)
    def can_be_src(self):
        return self.field.is_output(self.call.cls)


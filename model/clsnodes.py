from .CallField import CallField

class ClassNode(object):
    """Any of the potential value-holders in a class"""
    attr_names = ()
    def __init__(self, *args):
        for attr_name, arg in zip(self.attr_names, args):
            setattr(self, attr_name, arg)
    def attr_values(self):
        for name in self.attr_names:
            yield getattr(self, name) 
    def __repr__(self):
        return ', '.join(map(repr, self.attr_values()))
    def copy(self):
        pycls = type(self)
        return pycls(*self.attr_values())
    def is_input(self, cls):
        return False
    def is_output(self, cls):
        return False
    def class_del_self(self, cls):
        cls.remove_links(self)
    def can_be_dst(self):
        return False
    def can_be_src(self):
        return False

class Field(ClassNode):
    """An input or output of the class"""
    attr_names = ('label',)
    def is_input(self, cls):
        return cls.is_field_input(self)
    def is_output(self, cls):
        return cls.is_field_output(self)
    def __str__(self):
        return self.label
    def can_be_dst(self):
        return True
    def can_be_src(self):
        return True

class Constant(ClassNode):
    attr_names = ('label', 'value')
    def __str__(self):
        return self.label
    def can_be_src(self):
        return True
    def set_value(self, value, cls):
        self.value = value
        cls.node_changed(self)

class ClassCall(ClassNode):
    """Use of another class processing in a class"""
    attr_names = ('cls',)
    def class_del_self(self, cls):
        for node in self.cls.nodes:
            if isinstance(node, Field):
                cls.remove_links(CallField(self, node))

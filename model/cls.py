# TODO:
# - make method to know which inputs are bound to a value from parent
# - consider splitting the ultra-generic Field into InputField and OutputField (and perhaps Proxy as well)

from .CallField import CallField
from .clsnodes import Constant, Field, ClassCall

class BaseClass(object):
    def __init__(self, label, nodes):
        self.label = label
        self.nodes = nodes
        import weakref
        self._instances = weakref.WeakValueDictionary()
    def __repr__(self):
        return self.label
    def add_instance(self, obj):
        self._instances[id(obj)] = obj
    def instances(self):
        return list(self._instances.values())
    def inputs(self):
        for node in self.nodes:
            if node.is_input(self):
                yield node
    def outputs(self):
        for node in self.nodes:
            if node.is_output(self):
                yield node

class Class(BaseClass):
    """Abstract description of functional processing
    Composed of a set of linked classnodes"""
    def __init__(self, label, nodes):
        super(Class, self).__init__(label, nodes)
        from lib.CrossDict import CrossDict
        self.links = CrossDict()
    def is_field_input(self, field):
        return field not in self.links
    def is_field_output(self, field):
        return not self.links.refs(field) and not field.is_input(self)
    def state_change(self, instance, key):
        if isinstance(key, ClassCall):
            for out in key.cls.outputs():
                if out in instance[key]:
                    self.state_change(instance, CallField(key, out))
            instance.updated()
            return
        if key in instance:
            val = instance[key]
            for link in self.links.refs(key):
                instance[link] = val
        else:
            for link in self.links.refs(key):
                if link in instance:
                    del instance[link]
        instance.updated()
    def link(self, src, dst):
        self.links[dst] = src
        for obj in self.instances():
            if src not in obj:
                if dst in obj:
                    del obj[dst]
                obj.updated()
                continue
            obj[dst] = obj[src]
    def unlink(self, dst):
        if dst in self.links:
            del self.links[dst]
        for obj in self.instances():
            obj.updated()
    def node_changed(self, node):
        for obj in self.instances():
            self.state_change(obj, node)
    def delete_node(self, node):
        self.nodes.remove(node)
        node.class_del_self(self)
        for obj in self.instances():
            obj.class_del_node(node)
    def remove_links(self, key):
        self.unlink(key)
        for cross in list(self.links.refs(key)):
            self.unlink(cross)
    def add_node(self, node):
        self.nodes.append(node)
        for obj in self.instances():
            obj.class_new_node(node)

class MagicFunc(BaseClass):
    """A class that has special magic relations between its fields"""
    def __init__(self, label, inputs, outputs, pyfunc):
        super(MagicFunc, self).__init__(label, inputs+outputs)
        self._inputs = inputs
        self._outputs = outputs
        self.pyfunc = pyfunc
        self.fields = dict((x.label.lstrip('_'), x) for x in self._inputs+self._outputs)
        for node in self.nodes:
            if node.label.startswith('_'):
                node.label = ''
    def is_field_input(self, field):
        return field in self._inputs
    def is_field_output(self, field):
        return field in self._outputs
    def state_change(self, instance, key):
        if key not in self._inputs:
            return
        input = [(instance[x] if x in instance else None)
                 for x in self._inputs]
        output = self.pyfunc(*input)
        for key, val in zip(self._outputs, output):
            if val is None:
                if key in instance:
                    del instance[key]
            else:
                instance[key] = val

    # Disallow modifications to the magic
    def unlink(self, node):
        pass
    def delete_node(self, node):
        pass
    def add_node(self, node):
        pass

class Error(object):
    def __init__(self, description):
        self.description = description
    def __repr__(self):
        return 'Error: \n' + self.description
    def __setitem__(self, key, value):
        pass
    def __delitem__(self, key):
        pass
    def __getitem__(self, key):
        return self
    def __contains__(self, key):
        return True

class Instance(object):
    """A class associated with actual state (processing takes place)"""
    def __init__(self, cls, container = None, depth = 0):
        from lib.Event import Event
        self.updated = Event()

        self.cls = cls
        self.cls.add_instance(self)
        self.state = {}
        self.container = container
        self.depth = depth
        for node in self.cls.nodes:
            if isinstance(node, ClassCall):
                self.class_new_node(node)
        for node in self.cls.nodes:
            if isinstance(node, Constant):
                self.class_new_node(node)
        for node in self.cls.nodes:
            self.state_change(node)

    def class_new_node(self, node):
        if isinstance(node, ClassCall):
            if self.depth > 10:
                self.state[node] = Error("Max recursion depth\nexceeded")
            else:
                self.state[node] = Instance(node.cls, (self, node), self.depth + 1)
        elif isinstance(node, Constant):
            self.cls.state_change(self, node)
        self.updated()
    def class_del_node(self, node):
        if node in self.state:
            del self.state[node]
        self.updated()
    def __setitem__(self, key, val):
        if isinstance(key, CallField):
            self.state[key.call][key.field] = val
            return
        if not key in self.cls.nodes:
            raise KeyError('no such key', key)
        self.state[key] = val
        self.state_change(key)
    def __getitem__(self, key):
        if isinstance(key, Constant):
            return key.value
        if isinstance(key, CallField):
            return self.state[key.call][key.field]
        return self.state[key]
    def __delitem__(self, key):
        if isinstance(key, CallField):
            del self.state[key.call][key.field]
            return
        del self.state[key]
        self.state_change(key)
    def state_change(self, key):
        self.cls.state_change(self, key)
        if self.container is not None:
            obj, node = self.container
            obj.cls.state_change(obj, CallField(node, key))
        self.updated()
    def __contains__(self, key):
        if isinstance(key, Constant):
            return key.value is not None
        if isinstance(key, CallField):
            # Someone may be stupid and look for a CallField for a
            # call that doesn't even exist in the class (specifically,
            # this happens when animating a no-longer existent call
            # node), that's why we have to check key.call is in state
            # at all.
            return key.call in self.state and key.field in self.state[key.call]
        return key in self.state
    def __str__(self):
        return str(self.cls)
    def __repr__(self):
        return 'instance of %r' % (self.cls, )

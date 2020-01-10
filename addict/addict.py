import os
import json
import copy


class Dict(dict):

    def __init__(__self, *args, build=True, **kwargs):
        object.__setattr__(__self, '__finalized', False)
        object.__setattr__(__self, '__parent', kwargs.pop('__parent', None))
        object.__setattr__(__self, '__key', kwargs.pop('__key', None))
        for arg in args:
            if not arg:
                continue
            elif isinstance(arg, dict):
                for key, val in arg.items():
                    __self[key] = __self._hook(val)
            elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
                __self[arg[0]] = __self._hook(arg[1])
            else:
                for key, val in iter(arg):
                    __self[key] = __self._hook(val)

        for key, val in kwargs.items():
            __self[key] = __self._hook(val)

        if build:
            __self.build()
            __self._finalize()

    def _assert_finalized(self):
        if object.__getattribute__(self, '__finalized'):
            raise RuntimeError('This addict has been finalized and cannot be modified')

    def build(self):
        print('Warning: The addict build method is not overridden, all instantiations need to happen in the constructor')

    def _finalize(self):
        object.__setattr__(self, '__finalized', True)

        for k in self:
            if isinstance(self[k], Dict):
                self[k]._finalize()

    def __setattr__(self, name, value):
        self._assert_finalized()
        if hasattr(self.__class__, name):
            raise AttributeError("'Dict' object attribute "
                                 "'{0}' is read-only".format(name))
        else:
            self[name] = value

    def __setitem__(self, name, value):
        self._assert_finalized()
        super(Dict, self).__setitem__(name, value)
        try:
            p = object.__getattribute__(self, '__parent')
            key = object.__getattribute__(self, '__key')
        except AttributeError:
            p = None
            key = None
        if p is not None:
            p[key] = self
            object.__delattr__(self, '__parent')
            object.__delattr__(self, '__key')

    def __add__(self, other):
        self._assert_finalized()
        if not self.keys():
            return other
        else:
            self_type = type(self).__name__
            other_type = type(other).__name__
            msg = "unsupported operand type(s) for +: '{}' and '{}'"
            raise TypeError(msg.format(self_type, other_type))

    @classmethod
    def _hook(cls, item):
        if isinstance(item, dict):
            return cls(item)
        elif isinstance(item, (list, tuple)):
            return type(item)(cls._hook(elem) for elem in item)
        return item

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, name):
        if name not in self:
            self._assert_finalized()
            return Dict(__parent=self, __key=name, build=False)
        return super(Dict, self).__getitem__(name)

    def __missing__(self, name):
        return self.__class__(__parent=self, __key=name)

    def __delattr__(self, name):
        del self[name]

    def __repr__(self):
        json_string = json.dumps(self.to_dict(), indent=4)
        return json_string

    def to_dict(self):
        base = {}
        for key, value in self.items():
            if isinstance(value, type(self)):
                base[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                base[key] = type(value)(
                    item.to_dict() if isinstance(item, type(self)) else
                    item for item in value)
            else:
                base[key] = value
        return base

    def copy(self):
        return copy.copy(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    def __deepcopy__(self, memo):
        other = self.__class__()
        memo[id(self)] = other
        for key, value in self.items():
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def update(self, *args, **kwargs):
        other = {}
        if args:
            if len(args) > 1:
                raise TypeError()
            other.update(args[0])
        other.update(kwargs)
        for k, v in other.items():
            if ((k not in self) or
                (not isinstance(self[k], dict)) or
                (not isinstance(v, dict))):
                self[k] = v
            else:
                self[k].update(v)

    def __getnewargs__(self):
        return tuple(self.items())

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        else:
            self[key] = default
            return default

    def dump(self, filename=None):
        json_string = json.dumps(self.to_dict(), indent=4)
        if filename is not None:
            f = open(filename, "w")
            f.write(json_string)
            f.close()
        return json_string

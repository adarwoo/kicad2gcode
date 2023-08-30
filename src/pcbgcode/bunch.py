#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Bunch(dict):
    def __contains__(self, k):
        try:
            return dict.__contains__(self, k) or hasattr(self, k)
        except:
            return False
    
    # only called if k not found in normal places 
    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError:
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)
    
    def __setattr__(self, k, v):
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                self[k] = v
            except:
                raise AttributeError(k)
        else:
            object.__setattr__(self, k, v)
    
    def __delattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)
    
    def toDict(self):
        return unbunchify(self)
    
    @staticmethod
    def fromDict(d):
        return bunchify(d)


def bunchify(x):
    if isinstance(x, dict):
        return Bunch( (k, bunchify(v)) for k,v in x.items() )
    elif isinstance(x, (list, tuple)):
        return type(x)( bunchify(v) for v in x )
    else:
        return x

def unbunchify(x):
    if isinstance(x, dict):
        return dict( (k, unbunchify(v)) for k,v in x.items() )
    elif isinstance(x, (list, tuple)):
        return type(x)( unbunchify(v) for v in x )
    else:
        return x

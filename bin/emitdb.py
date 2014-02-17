import os
import git
import json
import argparse

from emitvalue import EmitValue
from gitdb import IStream
from cStringIO import StringIO
import jsonpointer

class EmitException(Exception):
    pass

class EmitDb:
    """Represents a JsonDatabase using GitRepository as a backend"""
    def __init__(self, repo):
        self.repo   = repo
        self.head   = repo.head
        self.master = repo.head.reference

        head   = repo.head
        master = head.reference
        hc     = repo.head.commit
        hct    = hc.tree

    @property
    def tree(self):
        return EmitValue(self.repo.head.commit.tree, self)

    def getJson(self, node=None, pretty=True, depth=0):
        if node is None:
            node = self.repo.head.commit.tree
        gitjson = EmitValue(node)
        return gitjson.json

    def render(self, node=None):
        emitvalue = EmitValue(node)
        return emitvalue.json

    def renderPath(self, path):
        node = self.getNode(path)
        self.render(node)

    def getNode(self, path):
        if path == '.':
            return self.head.commit.tree
        else:
            return self.head.commit.tree[path]

    def parseJson(self, jsonstring):
        try:
            return json.loads(jsonstring)
        except ValueError as e:
            raise EmitException('Invalid JSON value: %s' % jsonstring)

    def remove(self, path, commit=True):
        tree = self.head.commit.tree
        node = tree[path]

        index = self.repo.index # Cannot commit

        print 'removing %s' % path
        index.remove([path], r=True)
        index.write()

        if commit:
            commit = index.commit("removed %s" % path)


    def commit(self, message=''):
        index = self.repo.index
        print 'Commit: %s' % message
        index.commit(message)

    def exists(self, path):
        return path in self.repo.head.commit.tree


    def storeBlob(self, value, path=None):
        # Create a stream for the value
        istream = IStream("blob", len(value), StringIO(value))

        # Store in Repository
        self.repo.odb.store(istream)

        # Get Blob
        blob = self.repo.rev_parse(istream.hexsha)
        blob.mode = 33188 # File

        if path:
            blob.path = path

        return blob

    def add(self, pointer, jsonstring, commit=True):
        if not isinstance(pointer, jsonpointer.JsonPointer):
            pointer =  jsonpointer.JsonPointer(pointer)

        path = '/'.join(pointer.parts)
        
        value = self.parseJson(jsonstring)

        if isinstance(value, dict):
            for key in value:
                subpath     = os.path.join(path, key)
                subvalue    = json.dumps(value[key])
                self.add(subpath, subvalue, commit=False)
            self.commit('adding Json object %s: %s' % (path, value))
            return

        if isinstance(value, list):
            if self.exists(path):
                self.remove(path)
            for (index, item) in enumerate(value):
                subpath     = os.path.join(path, str(index))
                subvalue    = json.dumps(item)
                self.add(subpath, subvalue, commit=False)
            self.commit('adding "%s": %s' % (path, jsonstring))
            return

        index = self.repo.index

        print ' Adding: %s: %s' % (path, value)


        method = 'new'

        if method == 'new':
            root = EmitValue(self.head.commit.tree, self)
            node,_ = pointer.to_last(root)

            node[pointer.parts[-1]] = value

            index.write()
            index.commit('Woot, new adding method')
        else:
            blob = self.storeBlob(value, path=path)

            index.add([blob])
            index.write()

            # Not needed. Useful to get tree from modified index
            #tree = index.write_tree()

            #print " committing"
            if commit:
                # Commiting will create a new tree
                index.commit('added %s: %s'% (path, value))

    def patch(self, patchstring):
        patch   = self.parseJson(patchstring)
        op      = patch['op']
        path    = patch['path']

        if op == 'add':
            if self.exists(path):
                pass
            else:
                pass

    def resolve(self, jsonpointer):
        tree = self.repo.head.commit.tree
        return EmitValue(tree, self).resolve(jsonpointer)

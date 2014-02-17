#!/usr/bin/python

import os
import sys
import git
import json
import argparse

from emitvalue import EmitValue

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

    def nodeType(self, node):
        if node.type == 'blob':
            data = json.load(node.data_stream)
            return type(data)
        elif node.type == 'tree':
            for (index, entry) in enumerate(node):
                if str(index) != entry.name:
                    return dict
            return list


    def getJson(self, node=None, pretty=True, depth=0):
        if node is None:
            node = self.repo.head.commit.tree
        gitjson = EmitValue(node)
        return gitjson.json

    def render(self, node=None):
        for buff in self.getJson(node):
            sys.stdout.write(buff)

    def renderPath(self, path):
        node = self.getNode(path)
        self.render(node)

    def getNode(self, path):
        if path == '.':
            return self.head.commit.tree
        else:
            return self.head.commit.tree[path]

    def parseJson(self, value):
        try:
            return json.loads(value)
        except ValueError as e:
            raise EmitException('Invalid JSON value: %s' % value)

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

    def add(self, path, value, commit=True):
        jsonobject = self.parseJson(value)

        if isinstance(jsonobject, dict):
            for key in jsonobject:
                subpath     = os.path.join(path, key)
                subvalue    = json.dumps(jsonobject[key])
                self.add(subpath, subvalue, commit=False)
                # print 'Adding %s: %s' % (subpath, subvalue)
            self.commit('adding Json object %s: %s' % (path, value))
            return

        if isinstance(jsonobject, list):
            if self.exists(path):
                self.remove(path)
            for (index, item) in enumerate(jsonobject):
                subpath     = os.path.join(path, str(index))
                subvalue    = json.dumps(item)
                self.add(subpath, subvalue, commit=False)
            self.commit('adding "%s": %s' % (path, value))
            return

        from gitdb import IStream
        from cStringIO import StringIO

        # Create a stream for the value
        istream = IStream("blob", len(value), StringIO(value))

        # Store in Repository
        self.repo.odb.store(istream)

        directory   = path.split('/')
        name        = directory.pop()
        directory   = '/'.join(directory)

        binsha  = istream.binsha
        hexsha  = istream.hexsha
        mode    = 33188

        index = self.repo.index

        print ' Adding: %s: %s' % (path, value)
        blob = self.repo.rev_parse(hexsha)
        blob.path = path
        blob.mode = mode

        index.add([blob])

        # Not needed. Useful to get tree from modified index
        #tree = index.write_tree()

        # Flushing index changes index, committing. Will create new tree.
        #print " committing"
        index.write()
        if commit:
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


if __name__ == "__main__":
    #parser = argparse.ArgumentParser()
    #parser.add_argument('render', 'Render database into JSON')
    #parser.parse_args()

    #sys.exit(0)

    cwd         = os.getcwd()
    repo        = git.Repo(cwd)
    emitdb      = EmitDb(repo=repo)
    working_dir = emitdb.repo.working_dir
    rel_path    = os.path.relpath(cwd, working_dir)

    args        = sys.argv[1:]

    if len(args) == 0:
        command = 'help'
    else:
        command = args.pop(0)

    #print command

    if command == 'help':
        print 'emit COMMAND'
        print ''
        print 'commands'
        print '\trender      Render current state'
        print '\tadd JSON    add JSON to current path'
        print '\tpatch       Not implemented yet'
        print '\tdebug       Print information'

    if command == 'render':
        path = rel_path
        if len(args):
            subpath = args.pop(0)
            path    = os.path.normpath(os.path.join(path, subpath))
            
        emitdb.renderPath(path)

    if command == 'add':
        path    = args.pop(0)
        path    = os.path.normpath(os.path.join(rel_path, path))
        value   = args.pop(0)
        emitdb.add(path, value)

    if command == 'patch':
        patchstring = args.pop(0)
        emitdb.patch(patchstring)

    if command == 'remove':
        path    = args.pop(0)
        path    = os.path.normpath(os.path.join(rel_path, path))
        emitdb.remove(path)

    if command == 'commit':
        message = args.pop(0)
        emitdb.commit(message)
    if command == 'resolve':
        pointer = args.pop(0)
        gitjson = EmitValue(emitdb.repo.head.commit.tree)
        print gitjson.resolve(pointer)


    if command == 'debug':
        #print 'Arg:            %s' % os.path.normpath(os.path.join(path, sys.argv[2]))
        if len(args):
            subject = args.pop(0)
            if subject == 'index':
                index = emitdb.repo.index
                entries = [item[0] for item in index.entries]
                entries.sort()
                for entry in entries:
                    print entry
                #for item in index.entries:
                #   print item
            if subject == 'tree':
                tree = emitdb.repo.head.commit.tree
                if len(args):
                    tree = tree[args.pop(0)]
                for node in tree:
                    if node.type == 'tree':
                        print "+ %s" % node.name
                    if node.type == 'blob':
                        print "  %s" % node.name
            if subject == 'notes':
                index = emitdb.repo.index
                print dir(index)
            if subject == 'head':
                print emitdb.repo.head.reference
            if subject == 'type':
                path = args.pop(0)
                node = emitdb.getNode(path)
                print emitdb.nodeType(node)
            if subject == 'pointer':
                pointer = jsonpointer.JsonPointer(args.pop(0))
                entry = emitdb.getNode('.')
                gitjson = EmitValue(entry).resolve(pointer)

                print gitjson.value

            if subject == 'gitjson':
                entry = emitdb.getNode('.')
                gitjson = EmitValue(entry)
                print gitjson

        else:
            print 'Path:        %s' % path
            print 'Working dir: %s' % working_dir
            print 'Relpath:     %s' % rel_path
            

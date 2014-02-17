#!/usr/bin/python

import os
import sys
import git
import argparse

from emitdb import EmitDb
from gitdb import IStream

if __name__ == "__main__":
    # Initialize EmitDb
    cwd         = os.getcwd()
    repo        = git.Repo(cwd)
    emitdb      = EmitDb(repo=repo)

    # Define arguments
    parser = argparse.ArgumentParser()
    commands_parser = parser.add_subparsers(dest="command")

    commands = {}

    arguments = {
        'value': dict(
            help="""JavaScript Object Notation (JSON) string

See http://tools.ietf.org/html/rfc4627""",
            metavar='<value>'
        ),
        'pointer': dict(
            help="""String identifying a specific value within a JSON document.

Example:    {"foo": {"bar": 10}, "list": ["a","b","c]}
 ""         // whole document
 "/foo/bar" 10
 "/list/0   "a"

See: http://tools.ietf.org/html/rfc6901
""",
            metavar='<path>'
        ),
        'patch': dict(
            help="""JSON document structure for expressing a
sequence of operations to apply to a JSON document

Example:
{"op": "add", "path": "/a/b/c", "value": ["foo", "bar"]}

See: http://tools.ietf.org/html/rfc6902""",
            metavar='<patch>'
        )
    }

    def add_command(name, **kwargs):
        parser = commands_parser.add_parser(name, **dict(kwargs, formatter_class=argparse.RawTextHelpFormatter))
        commands[name] = parser
        return parser

    # render [<pointer>]
    add_command('render')
    commands['render'].add_argument('pointer', **dict(arguments['pointer'], nargs='?', default=''))

    # add <pointer> <value>
    add_command('add')
    commands['add'].add_argument('pointer', **arguments['pointer'])
    commands['add'].add_argument('value', **arguments['value'])

    # remove <pointer>
    add_command('remove')
    commands['remove'].add_argument('pointer', **arguments['pointer'])

    # patch <patch>
    add_command('patch')
    commands['patch'].add_argument('patch', **dict(arguments['patch'], nargs='+'))

    # parse
    options = parser.parse_args()

    if options.command == 'render':
        pointer = options.pointer
        value = emitdb.resolve(pointer)
        print value

    if options.command == 'add':
        pointer = options.pointer
        jsonvalue = options.value
        #item = emitdb.resolve(pointer)
        #print item.entry.path
        emitdb.add(pointer, jsonvalue)

        print emitdb.tree

    sys.exit(0)

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
            

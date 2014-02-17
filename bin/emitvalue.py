import json
import jsonpointer # easy_install jsonpointer

class EmitValue:
    """ Wraps a Blob or Tree """
    def __init__(self, entry, emitdb):
        self.entry  = entry
        self.emitdb = emitdb
    
    @property
    def type(self):
        """ Returns Python-type for parsed value """
        if self.entry.type == 'blob':
            try:
                data = json.load(self.entry.data_stream)
            except ValueError:
                raise ValueError("Invalid JSON object: %s" % self.entry.data_stream.read())
            return type(data)
        elif self.entry.type == 'tree':
            if len(self.entry) == 0:
                return dict
            for (index, subentry) in enumerate(self.entry):
                if str(index) != subentry.name:
                    return dict
            return list

    def __getitem__(self, key):
        if self.entry.type == 'tree':
            return EmitValue(self.entry[key], self.emitdb)

    def __setitem__(self, key, value):
        #print self.entry.name
        print "SETTING ITEM"
        #print "name = %s" % repr(self.entry.name)
        print "%s = %s" % (repr(self.entry.path), json.dumps(value))

        blob = self.emitdb.storeBlob(json.dumps(value), path='/'.join([self.entry.path, key]))
        self.emitdb.repo.index.add([blob])


    def __repr__(self):
        return self.json

    @property
    def values(self):
        return [EmitValue(entry, self) for entry in self.entry]

    @property
    def index(self):
        if self.type == list:
            return int(self.entry.name)

    @property
    def name(self):
        return self.entry.name

    @property
    def json(self):
        return ''.join([string for string in self.getJson()])

    @property
    def value(self):
        if self.entry.type == 'blob':
            return json.load(self.entry.data_stream)
        if self.entry.type == 'tree':
            etype = self.type
            if etype == list:
                return [EmitValue(entry).value for entry in self.entry]
            if etype == dict:
                return {entry.name:EmitValue(entry).value for entry in self.entry}


    def getJson(self, pretty=True, depth=0):
        if pretty:
            indent              = '  '
            keyvalue_separator  = ': '
            value_separator     = ',\n'
        else:
            indent              = ''
            keyvalue_separator  = ':'
            value_separator     = ','

        if self.entry.type == 'blob':
            yield self.entry.data_stream.read().rstrip('\n')

        if self.entry.type == 'tree':
            nentries = len(self.entry)

            if self.type == list:
                tag_open  = '['
                tag_close = ']'
            else:
                tag_open  = '{'
                tag_close = '}'

            if pretty and nentries:
                tag_open += '\n'

            if pretty:
                if len(self.values):
                    maxkeylen = max([len(value.name) for value in self.values])
                else:
                    maxkeylen = 0

            yield tag_open

            
            
            for index, value in enumerate(self.values):
                yield indent * (depth+1)

                if self.type == dict:
                    yield json.dumps(value.name)
                    yield keyvalue_separator

                if pretty and value.type not in [list, dict]:
                    yield ' ' * (maxkeylen - len(value.name))

                for string in value.getJson(pretty=pretty, depth=depth+1):
                    yield string

                islast = (index == nentries - 1)

                if not islast:
                    yield value_separator

            if pretty and nentries:
                yield '\n'
                if self.entry.path != '':
                    yield indent * (depth)

            if self.type == list:
                yield ']'
            else:
                yield '}'

    def __iter__(self):
        etype = self.type
        if etype == list:
            return iter([EmitValue(entry, self) for entry in self.entry])
        if etype == dict:
            return iter(entry.name for entry in self.entry)

    
    def resolve(self, pointer):
        if not isinstance(pointer, jsonpointer.JsonPointer):
            pointer = jsonpointer.JsonPointer(pointer)

        return pointer.resolve(self)

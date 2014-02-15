#!/usr/bin/python

import os, sys
import git, json

class EmitException(Exception):
	pass

class Emit:
	def __init__(self, repository):
		repo = git.Repo(repository)

		self.repo	= repo
		self.head	= repo.head
		self.master = repo.head.reference

		head	= repo.head
		master	= head.reference
		# log = master.log()
		# for item in log:
		# 	print item
		hc = repo.head.commit
		hct = hc.tree

		# Iterate over tree
		# for t in hct.trees:

		# Traverse Tree
		# for entry in hct.traverse():

	def getJson(self, node=None, pretty=True):
		if node is None:
			node = self.repo.head.commit.tree


		if pretty:
			indent = '  '
			keyvalue_separator = ': '
			value_separator = ',\n'
		else:
			indent = ''
			keyvalue_separator = ':'
			value_separator = ','

			
		if node.type == 'tree':
			islist = True
			maxkeylen = 0
			for index, entry in enumerate(node):
				maxkeylen = max(maxkeylen, len(entry.name))
				if str(index) != entry.name:
					islist = False
					#break

			if islist:
				yield '['
			else:
				yield '{'

			if pretty:
				yield '\n'

			nentries = len(node)
			for index, entry in enumerate(node):
				yield indent * len(entry.path.split('/'))

				if not islist:
					yield json.dumps(entry.name)
					yield keyvalue_separator
				
				if pretty:
					yield ' ' * (maxkeylen - len(entry.name))

				if entry.type == 'tree':
					for subentry in self.getJson(entry):
						yield subentry

				if entry.type == 'blob':
					yield entry.data_stream.read().rstrip('\n')

				if index < nentries - 1:
					yield value_separator
				pass

			if node.type == 'tree':
				if pretty:
					yield '\n'
					if node.path != '':
						yield indent * len(node.path.split('/'))
				if islist:
					yield ']'
				else:
					yield '}'

	def render(self, node=None):
		for buff in self.getJson(node):
			sys.stdout.write(buff)

	def renderPath(self, path):
		if path == '.':
			node = self.head.commit.tree
		else:
			node = self.head.commit.tree[path]
		#print node
		self.render(node)

	def verifyJson(self, value):
		try:
			json.loads(value)
		except ValueError as e:
			raise EmitException('Invalid JSON value: %s' % value)

	def remove(self, path):
		#print self.head.commit.tree[path].data_stream.read()
		tree = self.head.commit.tree
		node = tree[path]

		#self.
		# index = git.IndexFile.from_tree(self.repo, tree)
		index = self.repo.index # Cannot commit
		# index = git.IndexFile(self.repo, '.git/index') # Cannot call 'remove' on indices that do not represent the default git index

		print 'removing'
		index.remove([path])
		# print help(index.remove)

		#print 'committing'
		#new_commit = index.commit("removed %s" % path)
		# for i in index.entries:
		# 	print i

		for node in self.head.commit.tree:
			print node.name

	def add(self, path, value):
		self.verifyJson(value)

		from gitdb import IStream
		from cStringIO import StringIO

		# Create a stream for the value
		istream = IStream("blob", len(value), StringIO(value))

		# Store in Repository
		self.repo.odb.store(istream)

		directory	= path.split('/')
		name		= directory.pop()
		directory	= '/'.join(directory)

		binsha	= istream.binsha
		hexsha	= istream.hexsha
		mode	= 33188

		try:
			#tree = self.repo.head.commit.tree[directory]
			pass
		except KeyError:
			pass
			#tree = git.objects.tree.Tree(self.repo)
			#tree = self.repo.head.commit.tree

			#tree.cache.add()

			return

		#print "TREE:"
		#for node in tree:
		#	print ' - %s' % node.name

		#tree.cache.add(binsha, mode, name)
		#tree.cache.set_done()

		#tmp_index = git.IndexFile(self.repo, '.git/index')
		tmp_index = git.IndexFile.from_tree(self.repo, self.repo.head.commit.tree)

		print ' adding: %s' % hexsha
		blob = self.repo.rev_parse(hexsha)
		blob.path = path
		blob.mode = mode

		tmp_index.add([blob])

		tree = tmp_index.write_tree()


		# print tmp_index.path
		print "INDEX:"
		for e in tmp_index.entries:
			print e


		# Writing to index, and then committing from git commit, doesn't work :-S

		print " committing"
		tmp_index.commit('added %s: %s'% (path, value))


		##tmp_index.write('./git/index')

		#return 
		print "TREE:"
		for entry in tree:
			print ' - %s:\t%s' % (entry.name, entry.hexsha)

			# self.render(tree)

			# self.repo.index.write(tree)
			# for e in self.repo.index.entries:
			# 	print e

		# ----------------
		#assert istream.binsha is None

		#print istream.binsha
		#print istream.hexsha

		# now the sha is set
		#assert len(istream.binsha) == 20
		#assert self.repo.odb.has_object(istream.binsha)

		##assert self.repo.odb.has_object('c7ba33f9e9ae8614f4e8318d043682d4beff1486'.decode('hex'))

		# stream = StringIO()
		# stream.write("foobartjes")
		# streamlen = stream.tell()
		# stream.seek(0)

		# istream = self.repo.odb.store(IStream('blob', streamlen, stream))
		# print istream

		# print '----loop----'
		# for key in istream:
		# 	print key
			#print istream[key]
		#obj = git.objects.base.IndexObject(self, )

if __name__ == "__main__":
	path = os.getcwd()
	emit = Emit(repository=path)
	working_dir = emit.repo.working_dir
	rel_path = os.path.relpath(path, working_dir)

	args = sys.argv[1:]

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
		emit.renderPath(rel_path)

	if command == 'add':
		path	= args.pop(0)
		path	= os.path.normpath(os.path.join(rel_path, path))
		value	= args.pop(0)
		emit.add(path, value)

	if command == 'patch':
		patch = args.pop(0)
		emit.patch(path)

	if command == 'remove':
		path	= args.pop(0)
		path	= os.path.normpath(os.path.join(rel_path, path))
		emit.remove(path)

	if command == 'debug':
		#print 'Arg:	        %s' % os.path.normpath(os.path.join(path, sys.argv[2]))
		if len(args):
			subject = args.pop(0)
			if subject == 'index':
				index = emit.repo.index
				entries = [item[0] for item in index.entries]
				entries.sort()
				for entry in entries:
					print entry
				#for item in index.entries:
				#	print item
			if subject == 'tree':
				tree = emit.repo.head.commit.tree
				if len(args):
					tree = tree[args.pop(0)]
				for node in tree:
					if node.type == 'tree':
						print "+ %s" % node.name
					if node.type == 'blob':
						print "  %s" % node.name
		else:
			print 'Path:        %s' % path
			print 'Working dir: %s' % working_dir
			print 'Relpath:     %s' % rel_path
			

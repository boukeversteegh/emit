#!/usr/bin/python

import os, sys
import git, json

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

	def add(self, path, value):
		#print path, value
		#print repr(self.repo.index)

		from gitdb import IStream
		from cStringIO import StringIO


		# Create a stream for the value
		istream = IStream("blob", len(value), StringIO(value))

		# Store in Repository
		self.repo.odb.store(istream)


		#print dir(self.repo.index)
		tree = self.repo.head.commit.tree
		#tree = self.repo.tree()

		binsha	= istream.binsha
		hexsha	= istream.hexsha
		mode	= 33188
		name	= path.split('/').pop()

		#tmod = git.objects.tree.TreeModifier(tree.cache)
		#tmod.add(binsha, mode, name)
		#tmod.set_done()

		#for blob in tree.blobs:
		#	tree.cache.add(blob.binsha, blob.mode, blob.name)


		print '---'
		for blob in tree.blobs:
			print ' - %s' % blob

		tree.cache.add(binsha, mode, name)
		tree.cache.set_done()

		#tmp_index = git.IndexFile(self.repo, '.git/index')
		tmp_index = git.IndexFile.from_tree(self.repo, tree)

		print 'adding: %s' % hexsha
		blob = self.repo.rev_parse(hexsha)
		blob.path = path
		blob.mode = mode

		tmp_index.add([blob])

		print tmp_index.path
		for e in tmp_index.entries:
			print e, type(tmp_index.entries[e])


		# Writing to index, and then committing from git commit, doesn't work :-S
		#tmp_index.write('.git/index')
		tmp_index.commit('added %s:%s'% (path, value))


		#return 
		print '---'
		for entry in tree:
			print ' - %s: %s' % (entry.name, entry.hexsha)

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
		value	= args.pop(0)
		emit.add(os.path.normpath(os.path.join(rel_path, path)), value)

	if command == 'patch':
		patch = args.pop(0)
		emit.patch(path)

	if command == 'debug':
		#print 'Arg:	        %s' % os.path.normpath(os.path.join(path, sys.argv[2]))
		print 'Path:        %s' % path
		print 'Working dir: %s' % working_dir
		print 'Relpath:     %s' % rel_path
		

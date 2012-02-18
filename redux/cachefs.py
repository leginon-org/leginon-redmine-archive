#!/usr/bin/env python

import fs.osfs
import collections
import itertools
import os

class FileObjectWrapper(object):
	'''
	Override the close method, so we can track changes to files.
	'''
	def __init__(self, fileobj, closecallback, name, mode):
		self.fileobj = fileobj
		self.closecallback = closecallback
		self.name = name
		self.mode = mode

	def __getattr__(self, attr):
		if attr in self.__dict__:
			return getattr(self, attr)
		return getattr(self.fileobj, attr)

	def close(self):
		# close the file, then run close callback
		self.fileobj.close()
		self.closecallback(self.name, self.mode)

# Compare two tuples based on their second value.
# This is used for sorting list of (filename, time) by time.
def cmp2(a, b):
	return cmp(a[1], b[1])

class CacheFS(fs.osfs.OSFS):
	'''
	This is a subclass of fs.osfs.OSFS.  It creates a size-limited
	cache inside the given directory.  The open method is overridden
	such that it returns a custom file object.  The custom file object
	will call back to this class when the file is closed.  This allows
	us to track all file access within the cache.  We track the order
	that files are accessed and if the size of a file changes.  When 
	the total size of all files exceeds the maximum, the oldest files
	are removed to keep the size below the maximum.
	'''
	def __init__(self, cachedir, maxsize):
		fs.osfs.OSFS.__init__(self, cachedir)
		self.max_size = maxsize

		files = list(self.walkfiles())

		filesizes = [self.getsize(f) for f in files]
		self.size_dict = dict(itertools.izip(files,filesizes))

		fileatimes = [(f,self.getinfo(f)['accessed_time']) for f in files]
		fileatimes.sort(cmp2)
		self.order = collections.deque()
		self.order.extendleft([fa[0] for fa in fileatimes])

		self.total_size = sum(filesizes)

		self.clean()

	def close_callback(self, name, mode):
		# update size
		if mode != 'r':
			try:
				oldsize = self.size_dict[name]
				existing = True
			except KeyError:
				existing = False
				oldsize = 0
			newsize = self.getsize(name)
			self.total_size += (newsize - oldsize)
			self.size_dict[name] = newsize
			self.clean()
		else:
			existing = True
		# update order
		if existing:
			# The remove method of a deque can be slow for items
			# farther right in the deque
			self.order.remove(name)
		self.order.appendleft(name)

	def clean(self):
		while self.total_size > self.max_size:
			self.remove_oldest()

	def open(self, *args, **kwargs):
		'''
		Open file, return wrapped file object that allows
		tracking when the file is closed
		'''
		f = fs.osfs.OSFS.open(self, *args, **kwargs)
		name = args[0]
		f = FileObjectWrapper(f, self.close_callback, name, f.mode)
		return f

	def remove_oldest(self):
		oldest = self.order.pop()
		self.remove(oldest)
		try:
			self.removedir(os.path.dirname(oldest), recursive=True)
		except fs.errors.DirectoryNotEmptyError:
			pass

	def remove(self, *args, **kwargs):
		name = args[0]
		oldsize = self.size_dict[name]
		del self.size_dict[name]
		self.total_size -= oldsize
		return fs.osfs.OSFS.remove(self, *args, **kwargs)

test_cache_dir = 'cachedir'

def test_main():
	import time
	cfs = CacheFS(test_cache_dir, 50)
	f = cfs.open('/myfile%s' % (time.time(),), 'w')
	f.write('xxxxxxx')
	f.close()

if __name__ == '__main__':
	test_main()

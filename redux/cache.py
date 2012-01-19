#!/usr/bin/env python

import os
import sys
import pyami.resultcache
import pyami.fileutil
import gdbm

debug = True
def debug(s):
	if debug:
		sys.stderr.write(s)
		sys.stderr.write('\n')

class DiskCacheTracker(object):
	'''
	Tracks a cache of files, maintaining a maximum total disk
	usage.  When the maximum size is reached, the oldest files
	will be removed first.
	'''
	db_labels = ('global', 'size', 'newer', 'older')
	def __init__(self, root_path, maxsize):
		self.root_path = root_path
		self.maxsize = maxsize

	def db_init(self):
		db = self.db_open(init=True)
		db['global']['newest'] = ''
		db['global']['oldest'] = ''
		db['global']['size'] = '0'
		self.db_close(db)

	def db_open(self, init=False):
		db = {}
		for label in self.db_labels:
			filename = os.path.join(self.root_path, 'db_%s.gdbm' % (label,))
			if init:
				writemode = 'n'  # force creation of new db
			else:
				writemode = 'c'  # only create new if not exists
			db[label] = gdbm.open(filename, '%sf' % (writemode,))
		return db

	def db_close(self, db):
		for label in self.db_labels:
			try:
				db[label].close()
			except:
				pass

	def track(self, filename, db=None):
		if db is None:
			db = self.db_open()

		# calculate new size and size difference
		newsize = os.path.getsize(filename)
		try:
			oldsize = int(db['size'][filename])
			existed = True
		except:
			oldsize = 0
			existed = False
		sizediff = newsize - oldsize

		# update db with this file's size and cache total size
		total_size = int(db['global']['size'])
		db['size'][filename] = str(newsize)
		db['global']['size'] = str(total_size + sizediff)

		# bump this file to the newest position in the linked lists
		if existed:
			was_newer = db['newer'][filename]
			was_older = db['older'][filename]
			if was_newer and was_older:
				db['newer'][was_older] = was_newer
				db['older'][was_newer] = was_older
			elif was_newer:
				db['older'][was_newer] = ''
				db['global']['oldest'] = was_newer
		newest = db['global']['newest']
		if newest: # XXX <- edit may be incomplete
			## There was at least one other item
			db['newer'][newest] = filename
			db['older'][filename] = newest
		else:
			## This is the first item to add
			db['older'][filename] = ''
			db['global']['oldest'] = filename
		db['newer'][filename] = ''			
		db['global']['newest'] = filename

		self.clean(db)

		self.db_close(db)

	def clean(self, db):
		'''
		Remove oldest files to stay within limit
		'''
		total_size = int(db['global']['size'])
		oldest = db['global']['oldest']
		while oldest and (total_size > self.maxsize):
			sizeoldest = db['size'][oldest]
			total_size -= int(db['size'][oldest])
			nextoldest = db['newer'][oldest]
			del db['size'][oldest]
			del db['older'][oldest]
			del db['newer'][oldest]
			os.remove(oldest)
			if nextoldest:
				db['older'][nextoldest] = ''
			oldest = nextoldest
		db['global']['size'] = str(total_size)
		db['global']['oldest'] = oldest
		if not oldest:
			db['global']['newest'] = ''

	def print_db(self):
		db = self.db_open()
		print 'global'
		for key in ('size', 'newest', 'oldest'):
			print '  %s:  %s' % (key, db['global'][key])
		print 'files'
		next_oldest = db['global']['oldest']
		i = 0
		while next_oldest:
			print '  %s:  %s' % (next_oldest, db['size'][next_oldest])
			next_oldest = db['newer'][next_oldest]
			i += 1
			if i > 20:
				break
		self.db_close(db)

def test_disk_cache_manager():
	cache_root = '/tmp/redux'
	maxsize = 100
	dcm = DiskCacheTracker(cache_root, maxsize)
	#dcm.db_init()

	#for (filename, size) in (('aaa',10),('bbb',20), ('ccc', 5), ('aaa',15), ('ddd', 11)):
	for (filename, size) in (('eee',40),('fff',50), ('ggg', 10)):
		print 'FILENAME', filename
		fullfilename = os.path.join(cache_root, filename)
		f = open(fullfilename, 'w')
		f.write(size*'x')
		f.close()
		dcm.track(fullfilename)
		dcm.print_db()

class Cache(pyami.resultcache.ResultCache):
	def check_disable(self, pipeline):
		for pipe in pipeline:
			if pipe.disable_cache:
				return True
		return False

	def put(self, pipeline, result):
		if self.check_disable(pipeline):
			return
		pyami.resultcache.ResultCache.put(self, pipeline, result)
		if pipeline[-1].cache_file:
			self.file_put(pipeline, result)

	def get(self, pipeline):
		if self.check_disable(pipeline):
			return
		## try memory cache
		result = pyami.resultcache.ResultCache.get(self, pipeline)

		if result is None:
			debug('NOT IN MEMORY: %s' %(pipeline[-1],))
			## try disk cache
			result = self.file_get(pipeline)
			if result is not None:
				debug('IN FILE: %s' %(pipeline[-1],))
				pyami.resultcache.ResultCache.put(self, pipeline, result)
		else:
			debug('IN MEMORY: %s' % (pipeline[-1],))
			## found in memory cache, but need to touch or rewrite disk cache
			if not self.file_touch(pipeline):
				debug('NOT IN FILE: %s' % (pipeline[-1],))
				self.file_put(pipeline, result)

		return result

	def file_put(self, pipeline, result, permanent=False):
		final_pipe = pipeline[-1]
		# some pipes specify not to be cached to disk
		if not final_pipe.cache_file:
			return
		resultfilename = self.result_filename(pipeline)
		path = os.path.dirname(resultfilename)
		pyami.fileutil.mkdirs(path)
		f = open(resultfilename, 'w')
		final_pipe.put_result(f, result)
		f.close()

	def file_get(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		try:
			f = open(resultfilename, 'r')
		except:
			return None
		result = pipeline[-1].get_result(f)
		f.close()
		return result

	def file_touch(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		exists = os.path.exists(resultfilename)
		if exists:
			os.utime(resultfilename, None)
		return exists

	def file_exists(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		return os.path.exists(resultfilename)

	def result_filename(self, pipeline):
		cache_path = self.cache_path()
		pipeline_path = self.pipeline_path(pipeline)
		resultname = pipeline[-1].resultname()
		path = os.path.join(cache_path, pipeline_path, resultname)
		return path

	def cache_path(self):
		return '/tmp/redux'

	def pipeline_path(self, pipeline):
		parts = [pipe.dirname() for pipe in pipeline]
		parts = filter(None, parts)
		path = os.path.join(*parts)
		return path


if __name__ == '__main__':
	test_disk_cache_manager()

#!/usr/bin/env python

import numarray
import numarray.ma
import Image
import ImageDraw
import numextension

def insidePolygon(points, polygon):
	return numextension.pointsInPolygon(points, polygon)

def filledPolygon(shape, vertices):
	points = numarray.array(numarray.transpose(numarray.indices(shape), (1,2,0)), shape=(-1,2))
	inside = insidePolygon(points, vertices)
	return numarray.array(inside, shape=shape)

def pointsInPolygon(inputpoints, vertices):
	inside = insidePolygon(inputpoints, vertices)
	outputpoints = numarray.compress(inside, inputpoints)
	outputpoints = map(tuple, outputpoints)
	return outputpoints

def polygonSegments(polygon):
	a = numarray.transpose(polygon)
	b = numarray.concatenate((a[:,1:],a[:,:1]),1)
	return a,b

def distancePointsToPolygon(points, polygon):
	a,b = polygonSegments(polygon)
	evectors = b-a
	elengths = numarray.hypot(*evectors)
	eunitvectors = evectors / elengths
	pdists = []
	for p in points:
		pvectors = numarray.array((p[0]-a[0],p[1]-a[1]))
		dotprods = numarray.sum(evectors*pvectors)
		scalerproj = dotprods / elengths
		elengths2 = numarray.clip(scalerproj, 0, elengths)
		epoints = elengths2 * eunitvectors
		d = epoints - pvectors
		dists = numarray.hypot(*d)
		pdists.append(min(dists))
	return numarray.array(pdists)

def getPolygonArea(polygon, signed=False):
	a,b = polygonSegments(polygon)
	area = numarray.sum(a[0]*b[1]-a[1]*b[0]) / 2.0
	if not signed:
		area = numarray.abs(area)
	return area

def getPolygonCenter(polygon):
	a,b = polygonSegments(polygon)
	area = getPolygonArea(polygon, signed=True)
	c = (a[0]*b[1]-b[0]*a[1]) / 6.0 / area
	cx = numarray.sum((a[0]+b[0])*c)
	cy = numarray.sum((a[1]+b[1])*c)
	return (cx,cy)

if __name__ == '__main__':
	if 0:
		import Mrc
		im = filledPolygon((256,256), ((20,20), (40,40), (20,40),(40,20)))
		Mrc.numeric_to_mrc(im.astype(numarray.Int16), 'test.mrc')

	if 1:
		pointsInPolygon( ((1,1),(2,2),(2,3),(3,2),(3,3),(8,8),(12,12)), ((2,2),(2,10),(10,10),(10,2)))
		points= ((1,1),(2,2),(2,3),(3,3),(3,0),)
		print points
		print getPolygonCenter(points)

def plot_polygons(shape,polygons):
	# Input 'polygons' is a list of polygon vertices array
	zeros=numarray.zeros(shape,type=numarray.Int8)
	img=Image.new('L',shape)
	draw=ImageDraw.Draw(img)
	for p in polygons:
		plist =p.tolist()
		for i,point in enumerate(plist):
			plist[i]=tuple(point)
		if len(plist) > 2:
			draw.polygon(plist,fill=1)	  
	seq=list(img.getdata())
	polygon_image=numarray.array(seq,type=numarray.Int8)
	
	# The data sequence coverted this way is transposed in contrast to
	# the numarray that generates it
	polygon_image=numarray.reshape(polygon_image,(shape[1],shape[0]))
	polygon_image=numarray.transpose(polygon_image)
	return polygon_image

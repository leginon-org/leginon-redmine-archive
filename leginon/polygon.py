#!/usr/bin/env python

import numarray
import Image
import ImageDraw

def insidePolygon(indices, polygon):
	'''
	test which points in indices are inside polygon
	'''
	intersections = numarray.zeros(indices.shape[1:])
	p0,p1 = indices
	## test each edge intersection with ray originating at each point in indices
	for v in range(len(polygon)):
		a0,a1 = polygon[v-1]
		b0,b1 = float(polygon[v][0]), float(polygon[v][1])
		if a0 != b0:
			intersection = numarray.logical_and(
					numarray.logical_or(
						numarray.logical_and(b0 < p0, a0 >= p0),
						numarray.logical_and(b0 >= p0, a0 < p0)),
					((b1 - a1) / (b0 - a0) * (p0 - a0) + a1) > p1)
			intersections += intersection
	## if only 1 intersection, then point is inside polygon
	inside = intersections % 2 == 1
	return inside

def filledPolygon(shape, vertices):
	indices = numarray.indices(shape)
	return insidePolygon(indices, vertices)

def pointsInPolygon(inputpoints, vertices):
	indices = numarray.array(inputpoints)
	indices.transpose()
	inside = insidePolygon(indices, vertices)
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

def plot_polygons(shape,gpolygons):
	zeros=numarray.zeros(shape,type=numarray.Int8)
	img=Image.new('L',shape)
	draw=ImageDraw.Draw(img)
	for p in gpolygons:
		plist =p.tolist()
		for i,point in enumerate(plist):
			plist[i]=tuple(point)
		if len(plist) > 2:
			draw.polygon(plist,fill=1)	  
	seq=list(img.getdata())
	polygon_image=numarray.array(seq)
	polygon_image=numarray.reshape(polygon_image,shape)
	polygon_image=numarray.transpose(polygon_image)
	return polygon_image

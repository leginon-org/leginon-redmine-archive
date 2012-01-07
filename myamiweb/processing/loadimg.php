<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET['filename'];
$scale = ($_GET['scale']);
$rescale = ($_GET['rescale']);
$s = $_GET['s'];
$w = $_GET['w'];
$h = $_GET['h'];
$rawgif = $_GET['rawgif'];

if (empty($filename)) {
	return;
}
if (preg_match('`\.gif$`i',$filename) && $rawgif) {
	// --- show raw gif
	header("Content-type: image/gif");
	readfile($filename);
} else {
	require_once "../inc/imagerequest.inc";
	$imagerequest = new imageRequester();
	// find out the proper x, y for display
	$imginfo = $imagerequest->requestInfo($filename);
	$pmin = $imginfo->amin;
	$pmax = $imginfo->amax;
	$height = $imginfo->ny;
	$width = $imginfo->nx;
	$oformat = 'PNG';
	$frame=0;
	if ($scale) {
		$new_width = $width * $scale;
		$new_height = $height * $scale;
	}
	elseif ($w) {
		// set width, maintain height ratio
		$new_width = $w;
		$new_height = $height * $w / $width;
	}
	elseif ($h) {
		// set height, maintain width ratio
		$new_height = $h;
		$new_width = $width * $h / $height;
	}
	elseif ($s) {
		// set width and height, force image to be square
		$new_width = $s;
		$new_height = $s;
	}
	else {
		// set to original width and heigth
		$new_width = $width;
		$new_height = $height;
	}
	$xyDim = array($new_width, $new_height);

	$rgb = (substr_compare($filename,'jpg',-3,true) || substr_compare($filename,'png',-3,true)) ? true:false;
	// request image
	if (!$rescale && $pmin != $pmax) 
		$imgstr = $imagerequest->requestImage($filename,$oformat,$xyDim,'minmax',$pmin,$pmax,0,$rgb,false,$frame);
	else
		$imgstr = $imagerequest->requestImage($filename,$oformat,$xyDim,'stdev',-3,3,0,$rgb,false,$frame);
	$imagerequest->displayImageString($imgstr,$oformat,$filename);
}

?>

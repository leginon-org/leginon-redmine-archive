<?php
class imageUtil{

	/* return an array of x, y dimensions by the following rule
	 * when bin is set to auto:
	 * if either x or y bigger than 1024, then use 1024
	 * and resize the base on their ratio
	 * otherwise use their original image size.
	 * When binning has been set, find x, y by given binning.
	 */
	function imageBinning($dimx, $dimy, $bin, $default_size=1024){
		
		if($bin == 'auto'){
			$dimMax = max((int)$dimx, (int)$dimy);

			if($dimMax > $default_size){
				$xyRatio = $dimx / $dimy;
				switch($xyRatio){
					case ($xyRatio < 1):
						$dimy = $default_size;
						$dimx = $dimy * $xyRatio;
						break;
					default:
						$dimx = $default_size;
						$dimy = $dimx / $xyRatio;
						break;
				}
			}
		}
		else{
			$dimx = (int) ($dimx / $bin);
			$dimy = (int) ($dimy / $bin);
		}
		return array($dimx, $dimy);
	}

	// Fit the image into the frame size with aspect ratio preserved	
	function imageFitIn($dimx, $dimy, $frame_size){
		$ratio = max($dimx,$dimy) / $frame_size;
		$dimx = (int) ($dimx / $ratio);
		$dimy = (int) ($dimy / $ratio);
		
		return array($dimx, $dimy);
	}

	/*
	 * We need to convert the original min and max ratio
	 * to percentage. Original passed from web is between
	 * 0 to 255, so need to convert to between 
	 * 0 to 100
	 * return: an array of the percentage of scaleMin and scaleMax
	 */
	function scaleMinMaxConvert($min, $max){
		$min = (255/100) * $min;
		$max = (255/100) * $max;
		return array('minpix'=>$min, 'maxpix'=>$max);
	}
}
?>

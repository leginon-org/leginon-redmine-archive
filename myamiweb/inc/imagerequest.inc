<?php
require_once 'inc/redux.inc';
class imageRequester {

	function requestImage($filename,$oFormat,$shape=array(512,512),$scaleType='stdev',$scaleMin=-1,$scaleMax=1,$power=false) {
		$redux = new redux($filename, $oFormat);
		$redux->setScaleType($scaleType);
		$redux->setShape($shape);
		$redux->setScaleMin($scaleMin);
		$redux->setScaleMax($scaleMax);
		$redux->setPadShape(array($_POST['padShapeX'], $_POST['padShapeY']));
		$redux->setPadPos(array($_POST['padPosX'], $_POST['padPoxY']));
		$redux->setPadValue($_POST['padValue']);
		$powerValue = ($power == false) ? false : true;
		$redux->setPower($powerValue);
		$redux->setMaskRadius($_POST['maskRadius']);
		$redux->setLpf($_POST['lpf']);

		$errMsg = $redux->getErrMsg();
		//if(!empty($errMsg)){
		//	print_r($errMsg);
		//	exit;
		//}

		$reply = $redux->requestImage();
		return $reply;
	}
}
?>

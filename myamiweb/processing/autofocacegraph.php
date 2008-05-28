<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";

$defaultId= 1766;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET[hg]==1) ? true : false;
$f = $_GET[f];
$preset=$_GET['preset'];
$summary = ($_GET[s]==1 ) ? true : false;
$minimum = $_GET[mconf];

$ctf = new particledata();

//If summary is true, get only the data with the best confidence
if ($summary) {
	$ctfinfo = $ctf->getBestCtfInfoForSessionId($sessionId, $minimum);
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfoWithNominal($sessionId, $runId);
}

function scicallback($a) {
	return format_sci_number($a,3,true);
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}

foreach($ctfinfo as $t) {
	$id = $t['REF|leginondata|AcquisitionImageData|image'];
	$p = $leginondata->getPresetFromImageId($id);
	if ($p['name']!=$preset) {
		continue;
	}
	$data[$id] = $t[$f];
	$datadef[$id] = $t['defocus'];
	$where[] = "DEF_id=".$id;
}
$sqlwhere = "WHERE (".join(' OR ',$where).") and a.`REF|SessionData|session`=".$sessionId ;
$q = 	"select DEF_id, unix_timestamp(DEF_timestamp) as unix_timestamp, "
	." DEF_timestamp as timestamp from AcquisitionImageData a "
	.$sqlwhere;
	$r = $leginondata->getSQLResult($q);
	foreach($r as $row) {
		$e = $leginondata->getPresetFromImageId($row['DEF_id']);
		$ndata[]=array("timestamp" => $row['timestamp'], "$f"=>$data[$row['DEF_id']]);
//		$datax[]=$row['unix_timestamp'];
		$datax[]=$datadef[$row['DEF_id']];
		$datay[]=$data[$row['DEF_id']];
	}

if ($viewdata) {
	$keys = array("timestamp", "$f" );
	echo dumpData($ndata, $keys);
	exit;
}

$width = $_GET['w'];
$height = $_GET['h'];
if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {
	$graph = new Graph(600,400,"auto");    
	if ($histogram) {
		$graph->img->SetMargin(60,30,40,50);
		$histogram = new histogram($data);
		$histogram->setBarsNumber(50);
		$rdata = $histogram->getData();

		$rdatax = $rdata['x'];
		$rdatay = $rdata['y'];
		
		$graph->SetScale("linlin");
                
		$bplot = new BarPlot($rdatay, $rdatax);
		$graph->Add($bplot);

		$graph->title->Set("Histogram $f : $preset ");
		$graph->xaxis->title->Set("$f");
		$graph->xaxis->SetTextLabelInterval(3);
		$graph->xaxis->SetLabelFormatCallback('scicallback');
		$graph->yaxis->title->Set("Frequency");
	} else {

		$graph->SetAlphaBlending();
		$graph->SetScale("linlin",0,'auto'); //,$datax[0],$datax[$n-1]);
		$graph->img->SetMargin(60,40,40,80);
		$graph->xaxis->SetLabelFormatCallback('scicallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(-30);
		$graph->xaxis->SetPos("min");
		$graph->xaxis->title->Set("nominal defocus");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->SetLabelFormatCallback('scicallback');
		$graph->title->Set("$f - nominal : $preset ");

		$sp1 = new ScatterPlot($datay,$datax);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$graph->Add($sp1);
		$y1 = array(0,0);
		$p1 = new LinePlot($y1,array(min($datax),max($datax)));
		$p1->SetColor("blue");
		$graph->Add($p1);
	}
	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>

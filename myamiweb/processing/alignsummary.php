<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";
  
$expId = $_GET['expId'];
$projectId = (int) getProjectFromExpId($expId);
//echo "Project ID: ".$projectId." <br/>\n";
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Aligned Stack Report","Aligned Stack Summary Page", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
//$stackIds = $particle->getAlignStackIds($expId, True);
if ($_GET['coran']) {
	$stackdatas = $particle->getAlignStackIdsWithCoran($expId, $projectId);
	$hidestackdatas = $stackdatas;
} elseif (!$_GET['showHidden']) {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, False);
	$hidestackdatas = $particle->getAlignStackIds($expId, $projectId, True);
} else {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, True);
	$hidestackdatas = $stackdatas;
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden aligned stacks]</a><br/><br/>\n";
}

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	//echo print_r($stackdatas)."<br/>\n";
	foreach ($stackdatas as $stackdata) {
		$alignstackid = $stackdata['alignstackid'];
		echo alignstacksummarytable($alignstackid);
		$corandatas = $particle->getCoranRunForAlignStack($alignstackid, $projectId);
		if ($corandatas) {
			//print_r($corandatas);
			foreach ($corandatas as $corandata) {
				//echo print_r($corandata)."<br/>\n";;
				$coranid = $corandata['DEF_id'];
				echo "<span style='background-color:#dddd44;'>&nbsp;"
					."<a href='runParticleCluster.php?expId=6143&coranId=$coranid'>"
					."Run Particle Clustering On Coran Id $coranid</a>&nbsp;</span><br/>\n";
			}
			echo "<span style='background-color:#dddddd;'>&nbsp;"
				."<a href='runCoranClassify.php?expId=6143&alignId=$alignstackid'>"
				."Run Another Coran Classify On Align Stack Id $alignstackid</a>&nbsp;</span><br/>\n";		
		} else {
			echo "<span style='background-color:#ddbbdd;'>&nbsp;"
				."<a href='runCoranClassify.php?expId=6143&alignId=$alignstackid'>"
				."Run Coran Classify On Align Stack Id $alignstackid</a>&nbsp;</span><br/>\n";	
		}
	}
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<br/><a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden stacks]</a><br/>\n";
}

processing_footer();
exit;

?>

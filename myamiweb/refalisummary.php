<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	List of the reference-based alignment runs
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
// check if coming directly from a session
$expId = $_GET['expId'];
if ($expId) {
        $sessionId=$expId;
        $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
        $sessionId=$_POST['sessionId'];
        $formAction=$_SERVER['PHP_SELF'];
}
$projectId=$_POST['projectId'];

$javascript="<script src='js/viewer.js'></script>\n";

writeTop("Reference-Based Alignment Summary","Reference-Based Alignment Summary", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
echo "</FORM>\n";

// --- Get Refali Data
$particle = new particledata();
$refaliIds = $particle->getRefAliIds($sessionId);
$refaliruns = count($refaliIds);

$stackIds = $particle->getStackIds($sessionId);
$stackruns=count($stackIds);

// --- list out the alignment runs
echo"<P>\n";
foreach ($refaliIds as $refid) {
  echo divtitle("Refali Run Id: $refid[DEF_id]");
  # get list of alignment parameters from database
  $r = $particle->getRefAliParams($refid['DEF_id']);
  $s = $particle->getStackParams($r['REF|ApStackData|stack']);
  $t = $particle->getTemplatesFromId($refid['REF|ApTemplateImageData|refTemplate']);

  // --- get iteration info
  $iters = $particle->getRefAliIters($refid['DEF_id']);
  $numiters = count($iters);
  
  echo "<TABLE BORDER='0'>\n";
  $display_keys['name']=$r['name'];
  $display_keys['description'] = $r['description'];
  $display_keys['time']=$r['DEF_timestamp'];
  $display_keys['path']=$refid['path'];
  $display_keys['template']=$t['templatepath'].'/'.$t['templatename'];
  $display_keys['# particles']=$r['num_particles'];
  $display_keys['lp filt']=$r['lp'];
  $display_keys['mask diam']=$r['mask_diam'];
  $display_keys['imask diam']=$r['imask_diam'];
  $display_keys['xy search range']=$r['xysearch'];
  $display_keys['c-symmetry']=$r['csym'];
  $display_keys['stack run name']=$s['stackRunName'];

  foreach($display_keys as $k=>$v) {
    echo formatHtmlRow($k,$v);
  }
  echo "<TR><TD BGCOLOR='#FFCCCC' COLSPAN=2>
    $numiters iterations: &nbsp;&nbsp;&nbsp;
    <A HREF='refaliIters.php?refaliId=$refid[DEF_id]'>View Iterations</a>
    </TD></TR>";
  echo"</TABLE>\n";
  echo "</FORM>\n";
  echo"<P>\n";
}

writeBottom();
?>

<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runTiltAutoAligner();
}
// CREATE FORM PAGE
else {
  createTiltAutoAlignerForm();
}


function createTiltAutoAlignerForm($extra=false, $title='Tilt Auto Aligner Launcher', $heading='Tilt Auto Aligner') {

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

  // --- find hosts to run Tilt Aligner

  $javafunctions="
        <script src='../js/viewer.js'></script>
        <script LANGUAGE='JavaScript'>
                 function enabledtest(){
                         if (document.viewerform.testimage.checked){
                                 document.viewerform.testfilename.disabled=false;
                                 document.viewerform.testfilename.value='';
                         }  
                         else {
                                 document.viewerform.testfilename.disabled=true;
                                 document.viewerform.testfilename.value='mrc file name';
                         }
                 }
        </SCRIPT>\n";
  $javafunctions .= appionLoopJavaCommands();
  $javafunctions .= writeJavaPopupFunctions('appion');
  $javafunctions .= particleLoopJavaCommands();
  processing_header("Tilt Aligner Launcher","Tilt Aligner Particle Selection and Editing",$javafunctions);

  if ($extra) {
    echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
  }
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>
  <INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

  $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

  // Set any existing parameters in form
  $particle=new particleData;
  $prtlrunIds = $particle->getParticleRunIds($sessionId, True);
  $prtlruns = count($prtlrunIds);
  $defrunid = ($_POST['runid']) ? $_POST['runid'] : 'tiltrun'.($prtlruns+1);
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $prtlrunval = ($_POST['pickrunid']) ? $_POST['pickrunid'] : '';
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

  echo"
  <TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
  <TR>
    <TD VALIGN='TOP'>";

  createAppionLoopTable($sessiondata, $defrunid, "tiltalign");

  if (!$prtlrunIds) {
    echo"<FONT COLOR='RED'><B>No Particles for this Session</B></FONT>\n";
    echo"<INPUT TYPE='HIDDEN' NAME='pickrunid' VALUE='None'>\n";
  }
  else {
    echo "<BR/>Edit Particle Picks:
    <SELECT NAME='pickrunid'>\n";
    echo "<OPTION VALUE='None'>None</OPTION>";
    foreach ($prtlrunIds as $prtlrun){
      $prtlrunId=$prtlrun['DEF_id'];
      $runname=$prtlrun['name'];
      $prtlstats=$particle->getStats($prtlrunId);
      $totprtls=commafy($prtlstats['totparticles']);
      echo "<OPTION VALUE='$prtlrunId'";
      // select previously set prtl on resubmit
      if ($prtlrunval==$prtlrunId) echo " SELECTED";
      echo">$runname ($totprtls prtls)</OPTION>\n";
    }
    echo "</SELECT>\n";
  }
  $diam = ($_POST['diam']) ? $_POST['diam'] : "";
  echo"
    <TD CLASS='tablebg'>
    <B>Particle Diameter:</B><br />
    <INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
  echo docpop('pdiam',' Particle diameter for result images');
  echo "<FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
    <BR><BR>";
  /*echo"
    <B>Picking Icon:</B><BR/>
    <SELECT NAME='shape'>\n";
  $shapes = array('plus', 'circle', 'cross', 'point', 'square', 'diamond', );
  foreach($shapes as $shape) {
    $s = ($_POST['shape']==$shape) ? 'SELECTED' : '';
    echo "<OPTION $s>$shape</OPTION>\n";
  }
  echo "</SELECT>\n&nbsp;Picking icon shape<BR/>";
  $shapesize = (int) $_POST['shapesize'];
  echo"
    <INPUT TYPE='text' NAME='shapesize' VALUE='$shapesize' SIZE='3'>&nbsp;
    Picking icon diameter <FONT SIZE=-2><I>(in pixels)</I></FONT>
    <BR><BR>";
	*/
  echo"
    <B>Output file type:</B><BR/>
    <SELECT NAME='ftype'>\n";
  $ftypes = array('spider', 'text', 'xml', 'pickle', );
  foreach($ftypes as $ftype) {
    $s = ($_POST['ftype']==$ftype) ? 'SELECTED' : '';
    echo "<OPTION $s>$ftype</OPTION>\n";
  }
  echo "</SELECT><BR/>";
  createParticleLoopTable(-1, -1);
  echo "
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'><HR/>";
  /*  <INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
    Test these settings on image:
    <INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
    <HR>
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'>";
	*/
	echo getSubmitForm("Run Tilt Aligner");
	echo "
    </TD>
  </TR>
  </TABLE>";
  processing_footer();
  ?>

  </CENTER>
  </FORM>
  <?
}

function runTiltAutoAligner() {

  $command.="tiltAutoAligner.py ";
  $apcommand = parseAppionLoopParams($_POST);
  if ($apcommand[0] == "<") {
    createTiltAutoAlignerForm($apcommand);
    exit;
  }
  $command .= $apcommand;

  $partcommand = parseParticleLoopParams("manual", $_POST);
  if ($partcommand[0] == "<") {
    createTiltAutoAlignerForm($partcommand);
    exit;
  }
  $command .= $partcommand;
  $pickrunid=$_POST['pickrunid'];
  if ($pickrunid != 'None') {
    $command .= " pickrunid=$pickrunid";
  }

  /*$shape=$_POST['shape'];
  if($shape) {
    $command .= " shape=$shape";
  }

  $shapesize = (int) $_POST['shapesize'];
  if($shapesize && is_int($shapesize)) {
    $command .= " shapesize=$shapesize";
  }*/

  $ftype=$_POST['ftype'];
  if($ftype) {
    $command .= " outtype=$ftype";
  }

  if ($_POST['testimage']=="on") {
    if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
  }

  if ($testimage && $_POST['process']=="Run Tilt Aligner") {
    $host = $_POST['processinghost'];
    $user = $_POST['user'];
    $password = $_POST['password'];
    if (!($user && $password)) {
      createTiltAutoAlignerForm("<B>ERROR:</B> Enter a user name and password");
      exit;
    }
    $prefix =  "source /ami/sw/ami.csh;";
    $prefix .= "source /ami/sw/share/python/usepython.csh cvs32;";
    $cmd = "$prefix $command > tiltAutoAlignerlog.txt";
    $result=exec_over_ssh($host, $user, $password, $cmd, True);
  }

  processing_header("Particle Selection Results","Particle Selection Results");

  if ($testimage) {
    $runid = $_POST[runid];
    $outdir = $_POST[outdir];
    if (substr($outdir,-1,1)!='/') $outdir.='/';
    echo "<B>TiltAutoAligner Command:</B><BR>$command";
    $testjpg=ereg_replace(".mrc","",$testimage);
    $jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
    $ccclist=array();
    //$cccimg=$outdir.$runid."/manualmaps/".$testjpg.".manualmap1.jpg";
    //$ccclist[]=$cccimg;
    $images=writeTestResults($jpgimg,$ccclist);
    createTiltAutoAlignerForm($images,'Particle Selection Test Results','');
    exit;
  }

  echo"
    <TABLE WIDTH='600'>
    <TR><TD COLSPAN='2'>
    <B>Tilt Aligner Command:</B><BR>
    $command<HR>
    </TD></TR>";

  appionLoopSummaryTable();
  particleLoopSummaryTable();
  echo"</TABLE>\n";
  processing_footer();
}

?>

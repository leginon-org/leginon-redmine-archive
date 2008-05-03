<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/ctf.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runNoRefAlign();
} else { // Create the form page
	createNoRefAlignForm();
}

function createNoRefAlignForm($extra=false, $title='norefAlign.py Launcher', $heading='Reference Free Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctf = new ctfdata();
	$ctfdata=$ctf->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$stackIds = $particle->getStackIds($sessionId);
	$norefIds = $particle->getNoRefIds($sessionId);
	$norefruns=count($norefIds);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackvars) {\n";
	$javascript .= "	var stackArray = stackvars.split('|~~|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	// limit stack to 3000 particles
	$javascript .= "	if (stackArray[3] >= 3000) {stackArray[3]=3000};\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	$javascript .= "	document.viewerform.numfactors.value = Math.floor(Math.sqrt(stackArray[3])*.25);\n";
	// set max last ring radius
	$javascript .= "	var maxlastring = (stackArray[2]/2)-2;\n";
	// set particle & mask radius and lp
	$javascript .= "	if (stackArray[1]) {\n";
	$javascript .= "		var maxmask = Math.floor(((stackArray[2]/2)-2)*stackArray[1]);\n";
	$javascript .= "		document.viewerform.maskrad.value = maxmask;\n";
	$javascript .= "		document.viewerform.partrad.value = maxmask-2;\n";
	$javascript .= "		document.viewerform.lowpass.value = Math.floor(maxmask/25);\n";
	$javascript .= "	}\n";
	$javascript .= "	document.viewerform.lastring.value = maxlastring;\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('eman');	

	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	$helpdiv = "
	<div id='dhelp'
		style='position:absolute; 
        	background-color:FFFFDD;
        	color:black;
        	border: 1px solid black;
        	visibility:hidden;
        	z-index:+1'
    		onmouseover='overdiv=1;'
    		onmouseout='overdiv=0;'>
	</div>\n";
	echo $helpdiv;

	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","noref/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'noref'.($norefruns+1);
	$rundescrval = $_POST['description'];
	$stackidval = $_POST['stackid'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$numfactors = ($_POST['numfactors']) ? $_POST['numfactors'] : '10';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$partrad = ($_POST['partrad']) ? $_POST['partrad'] : '150';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '200';
	$firstring = ($_POST['numpart']) ? $_POST['firstring'] : '2';
	$lastring = ($_POST['lastring']) ? $_POST['lastring'] : '150';
	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder>
	<TR>
		<TD VALIGN='TOP'>
		<TABLE CELLPADDING='10' BORDER='0'>
		<TR>
			<TD VALIGN='TOP'>
			<A HREF=\"javascript:infopopup('runid')\"><B>NoRef Run Name:</B></A>
			<INPUT TYPE='text' NAME='runid' VALUE='$runidval'>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>
			<B>Description of NoRef Alignment:</B><BR>
			<TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>	 
			<B>Output Directory:</B><BR>
			<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
			</TD>
		</TR>
		<TR>
			<TD>\n";

	$prtlruns=count($prtlrunIds);

	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		Particles:<BR>
		<select name='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($stackIds as $stack) {
			// echo divtitle("Stack Id: $stack[stackid]");
			$stackparams=$particle->getStackParams($stack[stackid]);

			// get pixel size and box size
			$mpix=$particle->getStackPixelSizeFromStackId($stack['stackid']);
			if ($mpix) {
				$apix = $mpix*1E10;
				$apixtxt=format_angstrom_number($mpix)."/pixel";
			}
			$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

			//handle multiple runs in stack
			$runname=$stackparams[shownstackname];
			$totprtls=commafy($particle->getNumStackParticles($stack[stackid]));
			$stackid = $stack['stackid'];
			echo "<OPTION VALUE='$stackid|~~|$apix|~~|$boxsz|~~|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$stackid) echo " SELECTED";
			echo ">$runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo"</SELECT><BR>\n";
	echo "</TD></TR><TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','Commit to Database');
	echo "";
	echo "<BR></TD></TR>\n</TABLE>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "<TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "<TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><BR>\n";

	echo "<FONT COLOR='#3333DD'>Values in &Aring;ngstroms</FONT><BR>\n";
	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
	echo "<INPUT TYPE='text' NAME='partrad' SIZE='4' VALUE='$partrad'>\n";
	echo docpop('partrad','Particle Radius');
	echo " (in &Aring;ngstroms)<BR>\n";

	echo "<INPUT TYPE='text' NAME='maskrad' SIZE='4' VALUE='$maskrad'>\n";
	echo docpop('maskrad','Mask Radius');
	echo " (in &Aring;ngstroms)<BR>\n";

	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpval','Low Pass Filter Radius');
	echo " (in &Aring;ngstroms)<BR>\n";

	echo "<FONT COLOR='#3333DD'>Values in pixels</FONT><BR>\n";

	echo "<INPUT TYPE='text' NAME='firstring' SIZE='4' VALUE='$firstring'>\n";
	echo docpop('firstring','First Ring Radius');
	echo " (in Pixels)<BR>\n";

	echo "<INPUT TYPE='text' NAME='lastring' SIZE='4' VALUE='$lastring'>\n";
	echo docpop('lastring','Last Ring Radius');
	echo " (in Pixels)<BR>\n";

	echo "<FONT COLOR='#DD3333' SIZE='-2'>WARNING: more than 3000 particles can take forever to process</FONT><BR>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo " to Use<BR>\n";

	echo "<INPUT TYPE='text' NAME='numfactors' VALUE='$numfactors' SIZE='4'>\n";
	echo docpop('numfactors','Number of Factors');
	echo " in Coran<BR>\n";

	echo "</TR>\n";
	echo"</SELECT>\n";
	echo "	</TD>\n";
	echo "</TR>\n";
	echo "</TABLE>\n";
	echo "</TD>\n";
	echo "</TR>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<HR>\n";
	echo"<input type='submit' name='process' value='Start NoRef Alignment'><br />\n";
	echo "  </TD>\n";
	echo "</TR>\n";
	echo "</TABLE>\n";
	echo "</FORM>\n";
	echo "</CENTER>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	writeBottom();
	exit;
}

function runNoRefAlign() {
	$runid=$_POST['runid'];
	$outdir=$_POST['outdir'];
	$stackvars=$_POST['stackid'];
	$partrad=$_POST['partrad'];
	$maskrad=$_POST['maskrad'];
	$lowpass=$_POST['lowpass'];
	$firstring=$_POST['firstring'];
	$lastring=$_POST['lastring'];
	$numpart=$_POST['numpart'];
	$numfactors=$_POST['numfactors'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|~~\|',$stackvars);

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createNoRefAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	//$stackid=$_POST['stackid'];
	if (!$stackid) createNoRefAlignForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$outdir=$outdir.$runid;
	
	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// classification
	if ($numpart > 6000 || $numpart < 10) createNoRefAlignForm("<B>ERROR:</B> Number of particles must be between 10 & 6000");
	if ($numfactors > 20 || $numfactors < 1) createNoRefAlignForm("<B>ERROR:</B> Number of factors must be between 1 & 20");

	$particle = new particledata();

	// check num of particles
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) createNoRefAlignForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls)");

	$stackparams=$particle->getStackParams($stackid);

	// check first & last ring radii
	if ($firstring > (($boxsz/2)-2)) createNoRefAlignForm("<b>ERROR:</b> First Ring Radius too large!");
	if ($lastring > (($boxsz/2)-2)) createNoRefAlignForm("<b>ERROR:</b> Last Ring Radius too large!");

	// check particle radii
	if ($apix) {
		$boxrad = $apix * $boxsz;
		if ($partrad > $boxrad) createNoRefAlignForm("<b>ERROR:</b> Particle radius too large!");
		if ($maskrad > $boxrad) createNoRefAlignForm("<b>ERROR:</b> Mask radius too large!");
	}
	
	$command.="norefAlignment.py ";
	if ($outdir) $command.="--outdir=$outdir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runid ";
	$command.="--stack=$stackid ";
	$command.="--rad=$partrad ";
	$command.="--mask=$maskrad ";
	$command.="--first-ring=$firstring ";
	$command.="--last-ring=$lastring ";
	if ($lowpass) $command.="--lowpass=$lowpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-factors=$numfactors ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	writeTop("No Ref Align Run Params","No Ref Align Params");

	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>NoRef Alignment Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>runid</TD><TD>$runid</TD></TR>
	<TR><TD>stackid</TD><TD>$stackid</TD></TR>
	<TR><TD>partrad</TD><TD>$partrad</TD></TR>
	<TR><TD>maskrad</TD><TD>$maskrad</TD></TR>
	<TR><TD>lowpass</TD><TD>$lowpass</TD></TR>
	<TR><TD>firstring</TD><TD>$firstring</TD></TR>
	<TR><TD>lastring</TD><TD>$lastring</TD></TR>
	<TR><TD>numpart</TD><TD>$numpart</TD></TR>
	<TR><TD>numfactors</TD><TD>$numfactors</TD></TR>
	<TR><TD>outdir</TD><TD>$outdir</TD></TR>
	<TR><TD>commit</TD><TD>$commit</TD></TR>
	</TABLE>\n";
	writeBottom();
}
?>

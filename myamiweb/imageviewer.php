<?php
require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/auth.inc');

$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
$projectId = ($_POST['projectId']) ? $_POST['projectId'] : $_GET['projectId'];
$imageId = ($_POST['imageId']) ? $_POST['imageId'] : $_GET['imageId'];
$preset = $_POST[$_POST['controlpre']];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if($projectdb)
	$projects = $projectdata->getProjects('all');

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);

// --- update SessionId while a project is selected
$sessionId_exists = $leginondata->sessionIdExists($sessions, $sessionId);
if (!$sessionId_exists)
	$sessionId=$sessions[0]['id'];
$filenames = $leginondata->getFilenames($sessionId, $preset);

// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb) {
	foreach($sessions as $s) {
		if ($s['id']==$sessionId) {
			$sessionname = $s['name_org'];
			break;
		}
	}
	$currentproject = $projectdata->getProjectFromSession($sessionname);
	$viewer->setProjectId($projectId);
	$viewer->addProjectSelector($projects, $currentproject);
}
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
$viewer->addFileSelector($filenames);
$viewer->setNbViewPerRow('1');
$pl_refresh_time=".5";
$viewer->addPlaybackControl($pl_refresh_time);
$playbackcontrol=$viewer->getPlaybackControl();
$javascript = $viewer->getJavascript();

$view1 = new view('Main View', 'v1');
$view1->setControl();
$view1->displayParticleIcon(false); 
$view1->addMenuItems($playbackcontrol);
$view1->setDataTypes($datatypes);
$view1->displayPTCL(false);
$view1->setSize(512);
$viewer->add($view1);


$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
?>
<a class="header" target="summary" href="summary.php?expId=<?php echo $sessionId ?>">[summary]</A>
<a class="header" target="processing" href="processing/processing.php?expId=<?php echo $sessionId; ?>">[processing]</A>
<a class="header" target="make jpgs" href="processing/runJpgMaker.php?expId=<?php echo $sessionId; ?>">[make jpgs]</A>
<?php
$viewer->display();
viewer_footer();
?>

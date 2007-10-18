<?php
require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/auth.inc');

$sessionId = ($_POST[sessionId]) ? $_POST[sessionId] : $_GET[expId];
$projectId = ($_POST[projectId]) ? $_POST[projectId] : 'all';
$imageId = $_POST[imageId];
$preset = $_POST[$_POST[controlpre]];

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
	$sessionId=$sessions[0][id];
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
$viewer->setNbViewPerRow('2');
$javascript = $viewer->getJavascript();

$view1 = new view('View 1', 'v1');
$view1->setDataTypes($datatypes);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->setDataTypes($datatypes);
$view2->setSize(512);
$view2->setSpan(2,2);
$viewer->add($view2);

$view3 = new view('View 3', 'v3');
$view3->setDataTypes($datatypes);
$viewer->add($view3);


$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
?>
<a class="header" target="summary" href="summary.php?expId=<?php echo $sessionId; ?>">[summary]</A>
<a class="header" target="processing" href="processing/processing.php?expId=<?php echo $sessionId; ?>">[processing]</A>
<a class="header" target="make jpgs" href="processing/runJpgMaker.php?expId=<?php echo $sessionId; ?>">[make jpgs]</A>
<?php
$viewer->display();
viewer_footer();
?>

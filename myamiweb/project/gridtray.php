<?php
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/gridbox.inc.php";
require "inc/grid.inc.php";
require "inc/utilpj.inc.php";

if($_GET['gid']) {
	$selectedgridId=$_GET['gid'];
}
if($_GET['gbid']) {
	$selectedgridboxId=$_GET['gbid'];
}
if ($_POST['currentgrid']) {
	$selectedgridId=$_POST['currentgrid'];
}
if ($_POST['currentgridbox']) {
	$selectedgridboxId=$_POST['currentgridbox'];
}
$objsel = $_POST['objsel'];

$gid_arg = "gid=".$selectedgridId;
$gbid_arg = "gbid=".$selectedgridboxId;

function build_get_args() {
	$args = array();
	foreach(func_get_args() as $arg)
		if ($arg)
			$args[]=$arg;
	return join('&amp;', $args);
}


$griddata = new grid();
$grids = $griddata->getGrids();
$selectedgridId=(empty($selectedgridId)) ? $grids[0]['gridId'] : $selectedgridId;

$gridboxdata = new gridbox();
$gridboxes = $gridboxdata->getGridBoxes();
$selectedgridboxId=(empty($selectedgridboxId)) ? $gridboxes[0]['gridboxId'] : $selectedgridboxId;

$projectdata=new project();
$projects=$projectdata->getProjects();

project_header("Grid Tray", "init()");
?>
<script type="text/javascript">
	function onChangeGrid(){
		document.dataform.objsel.value="g";
		document.dataform.submit();
	}

	function onChangeGridBox(){
		document.dataform.objsel.value="gb";
		document.dataform.submit();
	}

	function init() {
		if (o=document.dataform.objsel) {
			if (o.value=='g') {
				document.dataform.currentgrid.focus()
			}
			if (o.value=='gb') {
				document.dataform.currentgridbox.focus()
			}
		}
	}

</script>
<form method="POST" name="dataform" action="<?php echo $PHP_SELF ?>">

<?=divtitle('Upload Grids')?>
<p>
<a class="header" href="uploadgrid.php">upload grids / tray</a>
</p>
<?=divtitle('Grids')?>
<input type="hidden" name="objsel" value="<?=$objsel?>">
<table border="0" >
<tr>
<td valign=top>
<select size="10" name="currentgrid" onchange="onChangeGrid()">
<?
foreach ($grids as $grid) {
    $s = ($grid['gridId']==$selectedgridId) ? 'selected' : '';
		$id=$grid['gridId'];
		$value=$grid['project'].' - '.$grid['label'];
    echo "<option value=",$id," $s >",$value."</option>\n";
}
?>
</select>
</td>
<td valign=top >
<?
	$menu = array(
		'new'=>'updategrid.php',
		'edit'=>'updategrid.php?gid='.$selectedgridId,
		'delete'=>'deletegrid.php?gid='.$selectedgridId
	);
	echo edit_menu($menu, true,true);

$gridinfo = $griddata->getGridInfo($selectedgridId);
$projectinfo = $projectdata->getProjectInfo($gridinfo['projectId']);
if (is_array($gridinfo)) {
	$gridId = $gridinfo['gridId'];
	$gridinfo['project'] = $projectinfo['Name'];
	echo display_data_table($gridinfo, 
		array('Project'=>'project', 'Label'=>'label', 'Specimen'=>'specimen', 'number', 'note'), true);
}
$gridboxdata = new gridbox();
$gridboxinfo = $gridboxdata->getGridBoxInfo($gridinfo['boxId']);
if ($gridinfo['boxId']) {
?>Grid Box: <a class="header" href="?<?=build_get_args($spid_arg, $gid_arg, 'gbid='.$gridinfo['boxId'])?>"><?=$gridboxinfo['gridboxlabel']?></a>
<br>

<? } ?>

</td>
</tr>
</table>

<?=divtitle('Grid Boxes')?>
<input type="hidden" name="gridboxId" value="">
<table border="0" >
<tr>
<td valign=top>
<select size="10" name="currentgridbox" onchange="onChangeGridBox()">
<?
$selectedgridId=(empty($selectedgridId)) ? $grids[0]['gridId'] : $selectedgridId;
foreach ($gridboxes as $gridbox) {
    if ($gridbox['gridboxId']==$selectedgridboxId)
    	$s='selected';
    else 
    	$s='';
    echo "<option value=",$gridbox['gridboxId']," $s >",$gridbox['label']."\n";
}
?>
</select>
</td>
<td valign=top >
<?
	$menu = array(
		'new'=>'updategridbox.php',
		'edit'=>'updategridbox.php?id='.$selectedgridboxId,
		'delete'=>'deletegridbox.php?id='.$selectedgridboxId
	);
	echo edit_menu($menu, true,true);
	echo "<br>";
$gridboxinfo = $gridboxdata->getGridBoxInfo($selectedgridboxId);
switch ($gridboxinfo['boxtypeId']) {
	case '1':
		$link="type=cgb&amp;";
		break;
	case '2':
		$link="type=gb&amp;";
		break;
	case '3':
		$link="type=tgb&amp;";
		break;
}

if (is_array($gridboxinfo)) {
	$gridboxId = $gridboxinfo['gridboxId'];
}
if ($gridId) {
	$gridboxId=$selectedgridboxId;
	$gridboxinfo = $gridboxdata->getGridBoxInfo($gridboxId);

switch ($gridboxinfo['boxtypeId']) {
	case '1':
		$cryobox = new gridboxcryo(); 
		$cryobox->generateMap($gridboxId,$gridId,$selectedspecimenId);
		break;
	case '2':
		$size='tiny';
		$gridbox = new drawgridbox($size);
		$gridbox->generateMap($gridboxId,$gridId,$selectedspecimenId);
		break;
	case '3':
		$size='tiny';
		$tray = new tray($size);
		$tray->generateMap($gridboxId,$gridId,$selectedspecimenId);
		break;
}
}
?>
</td>
</tr>
</table>
</form>
<?
project_footer();
?>


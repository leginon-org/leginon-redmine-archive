<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require 'inc/config.inc';

// --- define dbem web tools base --- //
define('PROJECT_NAME', "myamiweb");
define('PROJECT_TITLE', "Appion and Leginon DB tools");
define('BASE_URL', "/~erichou/myamiweb/");
define('PROJECT_URL', BASE_URL."project");

// Administrator email address
define('ADMIN_EMAIL', "erichou@scripps.edu");

// --- Set your MySQL database server parameters
define('DB_HOST', "localhost");		// DB Host name
define('DB_USER', "erichou");		// DB User name
define('DB_PASS', "tynOynk2");		// DB Password
define('DB_LEGINON', "dbemdata");	// DB dbemdata table name
define('DB_PROJECT', "project");	// DB project table name

// --- default URL for project section
define('VIEWER_URL', BASE_URL."3wviewer.php?expId=");
define('SUMMARY_URL', BASE_URL."summary.php?expId=");
define('UPLOAD_URL', BASE_URL."processing/uploadimage.php");

// --- Set cookie session time
define('COOKIE_TIME', 0);		//0 is never expire. 

// --- Default Groups (GroupData table)
define('GP_ADMIN', 1);
define('GP_POWERUSER', 2);
define('GP_USER', 3);
define('GP_GUEST',4);

// --- XML test dataset
$XML_DATA = "test/viewerdata.xml";

// --- Set Default table definition
define('DEF_TABLES_FILE', "defaulttables.xml");
define('DEF_PROJECT_TABLES_FILE', "defaultprojecttables.xml");
define('DEF_PROCESSING_TABLES_FILE', "defaultprocessingtables.xml");

// --- Set External SQL server here (use for import/export application)
// --- You can add as many as you want, just copy and paste the block
// --- to a new one and update the connection parameters

//$SQL_HOSTS[$DB_HOST]['db_host'] = $DB_HOST;
//$SQL_HOSTS[$DB_HOST]['db_user'] = $DB_USER;
//$SQL_HOSTS[$DB_HOST]['db_pass'] = $DB_PASS;
//$SQL_HOSTS[$DB_HOST]['db'] = $DB;

/*
$SQL_HOSTS['name1']['db_host'] = 'name1';
$SQL_HOSTS['name1']['db_user'] = 'usr_object';
$SQL_HOSTS['name1']['db_pass'] = '';
$SQL_HOSTS['name1']['db'] = 'dbemdata';
*/

// --- add plugins --- //

### uncomment to enable processing web pages
# addplugin("processing");

// --- Leginon Viewer login --- //
define('ENABLE_LOGIN', true);

// --- Enable Image Cache --- //
define('ENABLE_CACHE', false);
define('CACHE_PATH', '/srv/www/cache/');
define('CACHE_SCRIPT', $_SERVER['DOCUMENT_ROOT'].'/'.BASE_URL.'/makejpg.php');

// --- define Flash player base url --- //
define('FLASHPLAYER_URL', "/flashplayer/");

// --- path to main --- //
set_include_path(get_include_path().PATH_SEPARATOR."..".PATH_SEPARATOR.$BASE_PATH.PATH_SEPARATOR."project".PATH_SEPARATOR."processing");
?>

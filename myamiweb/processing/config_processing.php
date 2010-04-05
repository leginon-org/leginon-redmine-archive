<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

// --- Processing database --- //
$PROCESSING_DB_HOST = DB_HOST;
$PROCESSING_DB_USER = DB_USER;
$PROCESSING_DB_PASS = DB_PASS;
$PROCESSING_DB = ""; //--- leave empty,  set by projectdb


// --- Add as many processing hosts as you like --- //
$PROCESSING_HOSTS[]="";
$PROCESSING_HOSTS[]="";

// --- register your cluster config file below i.e (default_cluster.php) --- //
$CLUSTER_CONFIGS= array (
	'default_cluster'
);

// --- Restrict file server if you want --- //
// --- Add your allowed processing directory as string in the array
$DATA_DIRS = array(
);

// Better if Cs came out of DB, but for now...
$DEFAULTCS = "";

// --- path to main --- //
set_include_path("..".PATH_SEPARATOR.get_include_path());
?>

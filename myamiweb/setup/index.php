<?php 
require_once('template.inc');
require_once('setupUtils.inc');

	session_start();	
	session_destroy();
	
	$template = new template;
	$template->wizardHeader("Welcome : Start configuration of your system", SETUP_CONFIG);
	
	$fileExist = setupUtils::checkFile(CONFIG_FILE);
	
	if($_POST){
		session_start();

		$_SESSION['time'] = time();
		
		if($_POST['newSetup']){
				// setup session for new config file setup.
			$_SESSION['newSetup'] = true;

			header("Location: setupBase.php");			
			exit;
		}
		else{
			require_once(CONFIG_FILE);
			// if username and password match
			// create session
			// redirect to setupBase page.
			if($_POST['username'] == DB_USER && $_POST['password'] == DB_PASS){
				//if username and password match.

				$_SESSION['loginCheck'] = true;
				// redirect to setupBase.
				header("Location: setupBase.php");
				exit;
			} else {
				$errorMessage = "The username and password you provided are incorrect. Enter again...";
			
				// destroy the session because error.
				session_destroy();
			}
		}
		
	}

?>
	<h3>Start here to setup and configure the web tools configuration file.</h3>
	<p>Please follow each step.</p>
	
	<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
<?php 
	if($fileExist){
?>
		<p>An existing configuration file has been detected.<br />
		Please enter the <b>"Database Username and Password"</b> for verification.<br />
		If you forgot your username and password, it can be found in config.php in the myamiweb folder.</p>

		<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
		<?php if(!empty($errorMessage)) echo"<font color='red'><p>$errorMessage</p></font>"; ?>
		<h3>Enter the Database username:</h3>
		<input type="text" size=20 name="username" value="" /><br /><br />
		<h3>Enter the Database password:</h3>
		<input type="password" size=20 name="password" value="" /><br /><br />
	
<?php 
	}
	else{
		
		echo"<p>This wizard will take you step by step through the process of 
		        setting up the Appion web tools config file.<br /><br />";
		echo"When you are ready to start please click on the \"NEXT\" button.<br />";
		echo"For security reasons, there is a 30 minute time limit for each page. If you exceed this limit, you will be returned to this page.</p><br />";
		echo"<input type='hidden' name='newSetup' value=true />";
 		
	}
?>
	<input type="submit" value="NEXT" />
	</form>

<?php 
	$template->wizardFooter();
?>
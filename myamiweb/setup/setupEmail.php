<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();
	$update = false;	
	if($_SESSION['loginCheck']){
		require_once(CONFIG_FILE);
		$update = true;
	}

	$template = new template;
	$template->wizardHeader("Step 2 : Login System and Administrator Email Address", SETUP_CONFIG);
	
?>
	<script language="javascript">
	<!-- //

		function setLogin(obj){

			if(obj.value == "true"){
				
				wizard_form.email_title.style.backgroundColor = "#ffffff";
				wizard_form.email_title.readOnly = false;
				wizard_form.admin_email.style.backgroundColor = "#ffffff";
				wizard_form.admin_email.readOnly = false;
				wizard_form.enable_smtp[0].disabled = false;
				wizard_form.enable_smtp[0].checked = true;
				wizard_form.enable_smtp[1].disabled = false;
				
			}else{
				
				wizard_form.email_title.style.backgroundColor = "#eeeeee";
				wizard_form.email_title.readOnly = true;
				wizard_form.email_title.value = "";
				wizard_form.admin_email.style.backgroundColor = "#eeeeee";
				wizard_form.admin_email.readOnly = true;
				wizard_form.admin_email.value = "";
				wizard_form.enable_smtp[0].disabled = true;
				wizard_form.enable_smtp[0].checked = false;
				wizard_form.enable_smtp[1].disabled = true;
				wizard_form.enable_smtp[1].checked = false;
				wizard_form.smtp_host.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_host.readOnly = true;
				wizard_form.smtp_host.value = "";
				wizard_form.smtp_auth[0].disabled = true;
				wizard_form.smtp_auth[0].checked = false;
				wizard_form.smtp_auth[1].disabled = true;
				wizard_form.smtp_auth[1].checked = false;
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
			}		
		}
		function setReadOnly_SMTP(obj){

			if(obj.value == "true"){
				
				wizard_form.smtp_host.style.backgroundColor = "#ffffff";
				wizard_form.smtp_host.readOnly = false;
				wizard_form.smtp_auth[0].disabled = false;
				wizard_form.smtp_auth[0].checked = true;
				wizard_form.smtp_auth[1].disabled = false;

			}else{

				wizard_form.smtp_host.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_host.readOnly = true;
				wizard_form.smtp_host.value = "";
				wizard_form.smtp_auth[0].disabled = true;
				wizard_form.smtp_auth[0].checked = false;
				wizard_form.smtp_auth[1].disabled = true;
				wizard_form.smtp_auth[1].checked = false;
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
			}
		}

		function setReadOnly_AUTH(obj){

			if(obj.value == "true"){
				
				wizard_form.smtp_username.style.backgroundColor = "#ffffff";
				wizard_form.smtp_username.readOnly = false;
				wizard_form.smtp_password.style.backgroundColor = "#ffffff";
				wizard_form.smtp_password.readOnly = false;

			}else{
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
				
			}
		}
	// -->
	</script>
	<form name='wizard_form' method='POST' action='setupDatabase.php'>

	<?php 
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
		
	?>
		<h3>Enable Login System:</h3>		
		<p>You can select if you want to use Web Tools Login System for User management and Project management functionally.</p>
		 
		<input type="radio" name="enable_login" value="false" <?php ($update) ? (ENABLE_LOGIN)? print("") : print("checked='yes'") : print("checked='yes'"); ?> 
			onclick="setLogin(this)" />&nbsp;&nbsp;NO<br />
		<input type="radio" name="enable_login" value="true" <?php ($update) ? (ENABLE_LOGIN)? print("checked='yes'") : print("") : print(""); ?> 
			onclick="setLogin(this)" />&nbsp;&nbsp;YES<br />
		<br />
		<h3>Enter outgoing email subject:</h3>
		<p>example: AMI - The Scripps Research Institute</p>
		<input type="text" size=50 name="email_title" <?php ($update && ENABLE_LOGIN === true)? print("value='".EMAIL_TITLE."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter administrator email address:</h3>
		<p>This web tools will use the email address you entered to 
		send out email to the web tools users.</p>
		<input type="text" size=35 name="admin_email" <?php ($update && ENABLE_LOGIN === true)? print("value='".ADMIN_EMAIL."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); ?> /><br /><br />
		<br />
		<h3>Using your SMTP server or regular php mail to send out email?</h3>
		<p>Select SMTP server require to enter your SMTP host information.<br />
		If your email does not provide SMTP server, please select "Use regular PHP mail."</p>
		&nbsp;<input type="radio" name="enable_smtp" value="false" <?php ($update && ENABLE_LOGIN === true) ? (ENABLE_SMTP)? print("") : print("checked='yes'") : print("disabled"); ?> 
			onclick="setReadOnly_SMTP(this)" />&nbsp;&nbsp;I want to use regular PHP mail.<br />
		&nbsp;<input type="radio" name="enable_smtp" value="true" <?php ($update && ENABLE_LOGIN === true) ? (ENABLE_SMTP)? print("checked='yes'") : print("") : print("disabled"); ?> 
			onclick="setReadOnly_SMTP(this)" />&nbsp;&nbsp;I want to use our SMTP server.<br /><br />
		<br />
		<h3>Enter your SMTP host name:</h3>
		<p>example: mail.school.edu</p>
		<input type="text" size=35 name="smtp_host" <?php ($update && ENABLE_SMTP === true)? print("value='".SMTP_HOST."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); ?> /><br /><br />
		<br />
		<h3>Does your SMTP server require authentication?</h3>
		<p>Check with your email administrator<br />
		Select "Yes" if require authentication. "No" if server not using SMTP Authentication</p>
		&nbsp;<input type="radio" name="smtp_auth" value="false" <?php ($update && ENABLE_SMTP === true) ? (SMTP_AUTH)? print("") : print("checked='yes'") : print("disabled"); ?> 
			onclick="setReadOnly_AUTH(this)" />&nbsp;&nbsp;No.<br />
		&nbsp;<input type="radio" name="smtp_auth" value="true" <?php ($update && ENABLE_SMTP === true) ? (SMTP_AUTH)? print("checked='yes'") : print("") : print("disabled"); ?> 
			onclick="setReadOnly_AUTH(this)" />&nbsp;&nbsp;Yes.<br /><br />
		<br />
		<h3>Enter your SMTP Authentication Username and Password:</h3>
		<p>If your SMTP server require authentication, You need to enter username and password</p>
		&nbsp;Username: &nbsp;
		<input type="text" size=20 name="smtp_username" <?php ($update && SMTP_AUTH === true) ? print("value='".SMTP_USERNAME."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); ?> /><br /><br />
		&nbsp;Password: &nbsp;
		<input type="text" size=20 name="smtp_password" <?php ($update && SMTP_AUTH === true) ? print("value='".SMTP_PASSWORD."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); ?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>
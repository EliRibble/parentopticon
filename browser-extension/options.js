function loaded() {
	browser.storage.local.get({
		"denied-url": "http://parentopticon.lan/denied",
		"local-hostname": "my-pc",
		"report-url": "http://parentopticon.lan/website",
		"username": "unknown-user",
	}).then(results => {
		document.getElementById("denied-url").value = results["denied-url"];
		document.getElementById("local-hostname").value = results["local-hostname"];
		document.getElementById("report-url").value = results["report-url"];
		document.getElementById("username").value = results["username"];
	}).catch(error => {
		console.error("Failed to get current values", error);
	});
}

function submit(event) {
	const form = event.target;
	const denied_url = form.elements["denied-url"].value;
	const local_hostname = form.elements["local-hostname"].value;
	const report_url = form.elements["report-url"].value;
	const username = form.elements["username"].value;
	browser.storage.local.set({
		"denied-url": denied_url, 
		"local-hostname": local_hostname,
		"report-url": report_url,
		"username": username,
	}).then(() => {
		console.log("Stored new parentopticon settings");
	}).catch(error => {
		console.error("Failed to save new values", error);
	});
	event.preventDefault();
}

document.querySelector("form").addEventListener("submit", submit);
document.addEventListener("DOMContentLoaded", loaded);

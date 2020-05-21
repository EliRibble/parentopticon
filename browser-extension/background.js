function denied(details, denied_url) {
	return {
		redirectUrl: denied_url + "?url=" + encodeURIComponent(details.url)
	}
}

function destined_for_report_host(details, report_url) {
	return (new URL(details.url)).hostname == (new URL(report_url)).hostname;
}

function listener(details) {
	return new Promise((resolve, reject) => {
		console.log("Checking", details.url);
		browser.storage.local.get({
			"denied-url": "http://parentopticon.lan/denied",
			"local-hostname": "unknown-workstation",
			"report-url": "http://parentopticon.lan/website",
			"username": "unknown-user",
		}).then(results => {
			let denied_url = results["denied-url"];
			let local_hostname = results["local-hostname"];
			let report_url = results["report-url"];
			let username = results["username"];
			// Permit all requests that appear to go to the same host as
			// the report URL
			if(destined_for_report_host(details, report_url)) {
				resolve();
				return;
			}
			fetch(report_url, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					documentUrl: details.documentUrl,
					hostname: local_hostname,
					incognito: details.incognito,
					originUrl: details.originUrl,
					url: details.url,
					username: username,
				}),
			})
			.then(response => {
				if(response.status == 204) {
					resolve();
				}
				resolve(denied(details, denied_url));
			}).catch(error => {
				console.error("Failed to talk to parentopticon", error);
				resolve(denied(details, denied_url));
			});
		});
	});
}


browser.webRequest.onBeforeRequest.addListener(
	listener,
	{urls: ["<all_urls>"], types: ["main_frame"]},
	["blocking"],
);
console.log("Loaded.");

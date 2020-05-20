function listener(details) {
  fetch("http://odroid.lan/website", {
    method: "POST",
	headers: {
	  "Content-Type": "application/json",
    },
	body: JSON.stringify({
	  documentUrl: details.documentUrl,
	  incognito: details.incognito,
	  originUrl: details.originUrl,
	  url: details.url,
	}),
  })
  .then(response => {
    console.log("Response " + response.status);
  });
}

browser.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["<all_urls>"], types: ["main_frame"]}
);

HOST = "http://parentopticon.lan"
WEBSITE = HOST + "/website"

function denied(details) {
  return {
    redirectUrl: HOST + "/denied?url=" + encodeURIComponent(details.url)
  }
}

function listener(details) {
  return new Promise((resolve, reject) => {
    if(details.url.startsWith(HOST)) {
	  resolve();
	  return;
	}
    fetch(WEBSITE, {
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
      if(response.status == 204) {
        resolve();
      }
      resolve(denied(details));
    }).catch(error => {
      console.error("Failed to talk to parentopticon", error);
      resolve(denied(details));
    });
  });
}

browser.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["<all_urls>"], types: ["main_frame"]},
  ["blocking"],
);

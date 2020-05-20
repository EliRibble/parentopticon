function listener(details) {
  return new Promise((resolve, reject) => {
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
      if(response.status == 204) {
        resolve();
      }
      resolve({cancel: true});
    }).catch(error => {
      console.error("Failed to talk to parentopticon", error);
      resolve({cancel: true});
    });
  });
}

browser.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["<all_urls>"], types: ["main_frame"]},
  ["blocking"],
);



(() => {
  "use strict";

  // Regex: https://docs.google.com/document/d/<DOC_ID>/edit...
  function extractDocId(url) {
    const match = url.match(/\/document\/d\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }


  chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.type === "GET_DOC_ID") {
      const docId = extractDocId(window.location.href);
      sendResponse({ docId });
    }
    // Chrome extension API requires returning true for async sendResponse
    return true;
  });
})();

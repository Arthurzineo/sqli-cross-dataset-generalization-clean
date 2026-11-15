(() => {
  const input = document.querySelector("#docs-search-input");
  const results = document.querySelector("#docs-search-results");

  if (!input || !results) {
    return;
  }

  let debounceTimer;
  let pendingRequest;

  const renderResults = (items) => {
    results.replaceChildren();
    items.forEach((item) => {
      const article = document.createElement("article");
      article.className = "docs-search-result";

      const link = document.createElement("a");
      link.href = `/docs/SQL/${item.path}`;
      link.textContent = item.title;

      const snippet = document.createElement("p");
      snippet.textContent = item.snippet;
      article.append(link, snippet);
      results.append(article);
    });
  };

  const search = async () => {
    const value = input.value;
    if (!value) {
      results.replaceChildren();
      return;
    }

    if (pendingRequest) {
      pendingRequest.abort();
    }
    pendingRequest = new AbortController();

    try {
      const response = await fetch(
        `/api/docs/sql/search?q=${encodeURIComponent(value)}`,
        { signal: pendingRequest.signal },
      );
      const items = await response.json();
      if (response.ok) {
        renderResults(items);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        results.replaceChildren();
      }
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(search, 200);
  });
})();

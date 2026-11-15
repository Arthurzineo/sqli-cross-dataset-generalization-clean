(() => {
  const mount = document.querySelector("#docs-app");
  if (!mount || !window.React || !window.ReactDOM || !window.htm) return;

  const { useEffect, useState } = window.React;
  const html = window.htm.bind(window.React.createElement);
  const sections = {
    "select": "recipes", "where": "ingredients", "union": "flavors",
    "sleep": "dough", "join": "pairings", "group-by": "meal-prep",
    "order-by": "cooking-time",
  };

  const fetchJson = async (url, options) => {
    const request = window.authFetch || window.fetch;
    const response = await request(url, options);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Request failed.");
    return payload;
  };

  const pathFromLocation = () => {
    if (window.location.pathname === "/recipes/" || window.location.pathname === "/recipes") return "";
    const parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    const term = parts[0];
    const encoded = sections[term] === parts[1] ? [term, ...parts.slice(2)].join("/") : mount.dataset.path || "";
    try {
      return decodeURIComponent(encoded);
    } catch (_) {
      return encoded;
    }
  };

  const internalPath = (path) => {
    const parts = String(path).replace(/^\/+|\/+$/g, "").split("/").filter(Boolean);
    if (!parts.length) return "/recipes/";
    const term = parts.shift();
    const section = sections[term];
    return section ? `/${term}/${section}/${parts.join("/")}` : "/recipes/";
  };

  const DocLink = ({ path, children, onNavigate }) => html`
    <a href=${internalPath(path)} onClick=${(event) => {
      event.preventDefault();
      onNavigate(path);
    }}>${children}</a>
  `;

  const SearchBox = ({ query, setQuery, results, onNavigate }) => html`
    <section class="docs-app-search" aria-label="Search the cooking wiki">
      <label for="docs-app-search-input">Search recipes and techniques</label>
      <input id="docs-app-search-input" type="search" value=${query}
        onInput=${(event) => setQuery(event.target.value)} autocomplete="off" />
      ${results.length ? html`
        <ul id="docs-app-search-results">
          ${results.map((result) => html`<li key=${result.path}>
            <${DocLink} path=${result.path} onNavigate=${onNavigate}>${result.title}</${DocLink}>
            <small>${result.snippet}</small>
          </li>`)}
        </ul>
      ` : null}
    </section>
  `;

  const RelatedPosts = ({ posts }) => html`
    <aside class="docs-app-related" aria-label="Related community posts">
      <h2>Related community posts</h2>
      ${posts.length ? html`<ul>${posts.map((post) => html`
        <li key=${post.id}><a href="/forum">${post.title}</a></li>
      `)}</ul>` : html`<p>No related posts.</p>`}
    </aside>
  `;

  const App = () => {
    const [path, setPath] = useState(pathFromLocation);
    const [page, setPage] = useState(null);
    const [error, setError] = useState("");
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [related, setRelated] = useState([]);

    const navigate = (nextPath) => {
      const cleanPath = String(nextPath).replace(/^\/+|\/+$/g, "");
      window.history.pushState({ path: cleanPath }, "", internalPath(cleanPath));
      setPath(cleanPath);
    };

    useEffect(() => {
      const onPopState = () => setPath(pathFromLocation());
      window.addEventListener("popstate", onPopState);
      return () => window.removeEventListener("popstate", onPopState);
    }, []);

    useEffect(() => {
      let active = true;
      setError("");
      const params = new URLSearchParams({ path });
      fetchJson(`/api/wiki/page?${params}`)
        .then((payload) => { if (active) setPage(payload); })
        .catch((reason) => { if (active) setError(reason.message); });
      return () => { active = false; };
    }, [path]);

    useEffect(() => {
      const timer = window.setTimeout(() => {
        if (!query) { setResults([]); return; }
        const params = new URLSearchParams({ q: query });
        fetchJson(`/api/wiki/search?${params}`)
          .then(setResults)
          .catch(() => setResults([]));
      }, 200);
      return () => window.clearTimeout(timer);
    }, [query]);

    useEffect(() => {
      if (!page || page.type !== "page") { setRelated([]); return undefined; }
      let active = true;
      const topic = page.title || page.path;
      fetchJson("/graphql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: "query($q:String!){ searchPosts(q:$q){ id title } }",
          variables: { q: topic },
        }),
      }).then((payload) => {
        if (active) setRelated((payload.data && payload.data.searchPosts) || []);
      }).catch(() => { if (active) setRelated([]); });
      return () => { active = false; };
    }, [page]);

    let content = html`<p>Loading the cooking wiki...</p>`;
    if (error) content = html`<p role="alert">${error}</p>`;
    else if (page && page.type === "page") {
      content = html`<article class="docs-app-page">
        <h1>${page.title}</h1>
        <div class="doc-content" dangerouslySetInnerHTML=${{ __html: page.html }}></div>
        <${RelatedPosts} posts=${related} />
      </article>`;
    } else if (page && page.type === "index") {
      content = html`<section class="docs-app-index">
        <h1>${page.title}</h1>
        ${page.categories && page.categories.length ? html`<h2>Categories</h2><ul>
          ${page.categories.map((item) => html`<li key=${item.path}>
            <${DocLink} path=${item.path} onNavigate=${navigate}>${item.name}</${DocLink}>
          </li>`)}
        </ul>` : null}
        ${page.pages && page.pages.length ? html`<h2>Pages</h2><ul>
          ${page.pages.map((item) => html`<li key=${item.path}>
            <${DocLink} path=${item.path} onNavigate=${navigate}>${item.name}</${DocLink}>
          </li>`)}
        </ul>` : null}
      </section>`;
    }

    return html`<div class="docs-app">
      <${SearchBox} query=${query} setQuery=${setQuery} results=${results} onNavigate=${navigate} />
      ${content}
    </div>`;
  };

  window.ReactDOM.createRoot(mount).render(html`<${App} />`);
})();
